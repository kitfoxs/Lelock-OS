"""Authenticated local multi-character gateway. The public Internet is outside this threat model."""
from __future__ import annotations
import hmac, http.server, json, secrets, threading, time
from urllib.parse import urlsplit, parse_qs
from .common import BridgeError, canonical, fields, ident, strict_load
from .providers import catalog, native_login_command

class Server:
    def __init__(self,manager,*,port=0,origins=(),native_login=None):
        self.manager=manager;self.origins=set(origins);self.native_login=native_login
        if any(o in {'*','null'} or not o.startswith(('http://localhost:','http://127.0.0.1:')) for o in origins):
            raise BridgeError('Use exact local browser origins; native/remote clients need separate verification')
        self.agent_token=secrets.token_urlsafe(32);self.operator_token=secrets.token_urlsafe(32)
        self.pair_code=secrets.token_urlsafe(12);self.pair_expires=time.time()+600;self.pair_used=False;self.pair_failures=0
        self.pair_lock=threading.Lock();outer=self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def setup(self):super().setup();self.connection.settimeout(10)
            def boundary(self):
                if len(self.headers.get_all('Host',[]))!=1 or self.headers['Host'] not in {f'localhost:{outer.port}',f'127.0.0.1:{outer.port}'}:
                    raise BridgeError('Host refused')
                origins=self.headers.get_all('Origin',[])
                if len(origins)>1 or (origins and origins[0] not in outer.origins):raise BridgeError('Origin refused')
                if self.headers.get('Transfer-Encoding'):raise BridgeError('Transfer-Encoding is unsupported')
            def token(self):
                values=self.headers.get_all('Authorization',[])
                if len(values)!=1 or not values[0].startswith('Bearer '):raise BridgeError('Authentication required')
                return values[0][7:]
            def auth(self,operator=False):
                t=self.token()
                ok=hmac.compare_digest(t,outer.operator_token) or (not operator and hmac.compare_digest(t,outer.agent_token))
                if not ok:raise BridgeError('Authentication refused')
            def body(self):
                lengths=self.headers.get_all('Content-Length',[])
                if len(lengths)!=1 or self.headers.get('Content-Type','').split(';')[0]!='application/json':raise BridgeError('Expected JSON body')
                try:n=int(lengths[0])
                except ValueError:raise BridgeError('Invalid content length')
                if not 0<n<=1_000_000:raise BridgeError('Body too large')
                data=self.rfile.read(n)
                if len(data)!=n:raise BridgeError('Incomplete request')
                result=strict_load(data)
                if not isinstance(result,dict):raise BridgeError('Expected object')
                return result
            def respond(self,code,value):
                raw=canonical(value).encode();self.send_response(code)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
                origin=self.headers.get('Origin')
                if origin in outer.origins:
                    self.send_header('Access-Control-Allow-Origin',origin);self.send_header('Vary','Origin')
                    self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type')
                    self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
                self.end_headers()
                try:self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError):pass
            def do_OPTIONS(self):
                try:self.boundary();self.respond(200,{'preflight':True})
                except BridgeError:self.respond(403,{'error':'boundary_refused'})
            def do_GET(self):self.route(False)
            def do_POST(self):self.route(True)
            def route(self,post):
                try:
                    self.boundary();u=urlsplit(self.path);path=u.path;data=self.body() if post else {}
                    if u.fragment:raise BridgeError('Unexpected fragment')
                    if path=='/v2/pair' and post:
                        fields(data,{'code'},{'code'})
                        with outer.pair_lock:
                            if outer.pair_used or time.time()>outer.pair_expires or outer.pair_failures>=10:raise BridgeError('Pairing expired; restart or use private pairing file')
                            if not isinstance(data['code'],str) or not hmac.compare_digest(data['code'],outer.pair_code):
                                outer.pair_failures+=1;raise BridgeError('Pairing refused')
                            outer.pair_used=True
                        return self.respond(200,{'agent_token':outer.agent_token,'operator_token':outer.operator_token})
                    if path.startswith('/v2/runtime/'):
                        token=self.token()
                        with outer.manager.lock:entry=outer.manager.runtime_credentials.get(token)
                        if not entry or entry['expires']<time.time():raise BridgeError('Expired runtime token')
                        if path=='/v2/runtime/tools' and not post:out={'tools':entry['core'].schemas()}
                        elif path=='/v2/runtime/invoke' and post:
                            fields(data,{'tool','arguments','request_id'},{'tool','arguments','request_id'})
                            out=outer.manager.runtime_call(token,data['tool'],data['arguments'],data['request_id'])
                        else:raise BridgeError('Unknown runtime route')
                        return self.respond(200,out)
                    operator=path.startswith(('/v2/operator/','/v2/accounts/','/v2/native/')) or (path=='/v2/bindings')
                    self.auth(operator)
                    if path=='/v2/providers' and not post:out={'providers':catalog()}
                    elif path=='/v2/operator/entities' and not post:out={'entities':outer.manager.db.list_entities()}
                    elif path=='/v2/operator/actions' and not post:
                        out={'actions':[a for e in outer.manager.db.list_entities() for a in outer.manager.actions(e['id'])]}
                    elif path=='/v2/operator/skills/inspect' and post:
                        fields(data,{'name'},{'name'});out=outer.manager.knowledge.inspect(data['name'])
                    elif path=='/v2/operator/skills/approve' and post:
                        fields(data,{'name','sha256'},{'name','sha256'});out=outer.manager.knowledge.approve(data['name'],data['sha256'])
                    elif path=='/v2/bindings' and post:
                        fields(data,{'client_id','card_key','card','config','attach'},{'client_id','card_key','card'})
                        out=outer.manager.bind(data['client_id'],data['card_key'],data['card'],data.get('config'),data.get('attach'))
                    elif path=='/v2/native/login' and post:
                        fields(data,{'provider'},{'provider'})
                        if not outer.native_login:raise BridgeError('Native login launcher unavailable; use documented terminal command')
                        out=outer.native_login(data['provider'])
                    elif path.startswith('/v2/accounts/codex/'):
                        provider=outer.manager.runtimes.get('codex')
                        if not provider:raise BridgeError('Codex adapter unavailable')
                        action=path.rsplit('/',1)[-1]
                        if action=='status' and not post:out=provider.account()
                        elif action=='quotas' and not post:out=provider.quotas()
                        elif action=='models' and not post:out={'models':provider.models()}
                        elif action=='login' and post:
                            fields(data,{'device'})
                            if 'device'in data and not isinstance(data['device'],bool):raise BridgeError('Expected boolean')
                            out=provider.login(data.get('device',False))
                        elif action=='logout' and post:fields(data,{});out=provider.logout()
                        else:raise BridgeError('Unknown account action')
                    else:
                        parts=path.strip('/').split('/')
                        op=False
                        if len(parts)>=4 and parts[0]=='v2' and parts[1]=='operator':parts.pop(1);op=True
                        if len(parts)<4 or parts[:2]!=['v2','entities']:raise BridgeError('Unknown route')
                        eid=ident(parts[2]);action=parts[3]
                        if action=='status' and not post:out=outer.manager.status(eid)
                        elif action=='tools' and not post:out={'tools':outer.manager.tools(eid)}
                        elif action=='invoke' and post:
                            fields(data,{'tool','arguments','request_id'},{'tool','arguments','request_id'})
                            out=outer.manager.invoke(eid,data['tool'],data['arguments'],data['request_id'])
                        elif action=='config' and op and post:out=outer.manager.configure(eid,data)
                        elif action=='approve' and op and post:
                            fields(data,{'action_id','digest'},{'action_id','digest'});out=outer.manager.approve(eid,data['action_id'],data['digest'])
                        elif action=='reject' and op and post:
                            fields(data,{'action_id'},{'action_id'});out=outer.manager.reject(eid,data['action_id'])
                        elif action=='stop' and op and post:fields(data,{});out=outer.manager.stop(eid)
                        elif action=='computer-stop' and op and post:
                            fields(data,{})
                            if not outer.manager.computer:raise BridgeError('Computer adapter unavailable')
                            out=outer.manager.computer.call(eid,'stop',{})
                        elif action=='inbox' and not post:
                            if not outer.manager.presence:raise BridgeError('Presence module not initialized')
                            out={'messages':outer.manager.presence.inbox(eid)}
                        elif action=='schedules' and op:
                            if not outer.manager.presence:raise BridgeError('Presence module not initialized')
                            out=outer.manager.presence.add(eid,data) if post else {'schedules':outer.manager.presence.list(eid)}
                        elif action=='schedule-disable' and op and post:
                            fields(data,{'id'},{'id'})
                            if not outer.manager.presence:raise BridgeError('Presence module not initialized')
                            out=outer.manager.presence.disable(eid,data['id'])
                        elif action=='turns' and post and len(parts)==4:
                            fields(data,{'chat_id','turn_id','message','history'},{'chat_id','turn_id','message','history'})
                            out=outer.manager.start_turn(eid,data['chat_id'],data['turn_id'],data['message'],data['history'])
                        elif action=='turns' and not post and len(parts)==5:
                            q=parse_qs(u.query);after=int(q.get('after',['0'])[0]);out=outer.manager.public_turn(ident(parts[4]),eid,max(0,after))
                        else:raise BridgeError('Unknown operation')
                    self.respond(200,out)
                except (BridgeError,ValueError,KeyError,TypeError) as e:self.respond(409,{'error':'refused_or_failed','message':str(e)[:500]})
                except Exception:self.respond(500,{'error':'internal_failure','message':'Inspect local runtime state; no success or fallback claimed.'})
        self.http=http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler);self.http.daemon_threads=True
        self.port=self.http.server_address[1];self.base=f'http://127.0.0.1:{self.port}';manager.server_root=self.base
        self.thread=None
    def start(self):
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start();return self
    def close(self):
        if self.thread:self.http.shutdown();self.thread.join(timeout=2)
        self.http.server_close()
