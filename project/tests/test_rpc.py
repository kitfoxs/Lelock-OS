import json,threading,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from lelock.palace import PalaceRPC,TOOLS
from lelock.common import LelockError

class RPC(unittest.TestCase):
    def setUp(self):
        self.mode='ok';outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*a): pass
            def do_POST(self):
                if self.headers.get('Authorization')!='Bearer test-token': self.send_error(403);return
                r=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if outer.mode=='redirect':
                    self.send_response(302);self.send_header('Location','http://example.com');self.end_headers();return
                if r['method']=='tools/list':
                    fields=['wing','room','content','drawer_id','query']
                    result={'tools':[{'name':n,'inputSchema':{'properties':{k:{'type':'string'} for k in fields}}} for n in TOOLS]}
                else:
                    result={'content':[{'type':'text','text':json.dumps({'success':True,'value':42})}]}
                if outer.mode=='error': result={'isError':True,'content':[]}
                if outer.mode=='malformed': result={'content':[{'type':'text','text':'not json'}]}
                payload={'jsonrpc':'2.0','id':'wrong' if outer.mode=='wrong-id' else r['id'],'result':result}
                raw=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.rpc=PalaceRPC('http://127.0.0.1:'+str(self.server.server_port),'test-token',timeout=1)
    def tearDown(self): self.server.shutdown();self.server.server_close();self.thread.join()
    def test_contract_live_http_fixture(self): self.assertEqual(set(self.rpc.contract()['tools']),TOOLS)
    def test_response_decoded(self): self.assertEqual(self.rpc.call('mempalace_search',{'query':'hello'})['value'],42)
    def test_wrong_id_denied(self):
        self.mode='wrong-id'
        with self.assertRaises(LelockError): self.rpc.call('mempalace_search',{'query':'hello'})
    def test_tool_error_denied(self):
        self.mode='error'
        with self.assertRaises(LelockError): self.rpc.call('mempalace_search',{'query':'hello'})
    def test_bad_json_denied(self):
        self.mode='malformed'
        with self.assertRaises(LelockError): self.rpc.call('mempalace_search',{'query':'hello'})
    def test_redirect_denied(self):
        self.mode='redirect'
        with self.assertRaises(LelockError): self.rpc.call('mempalace_search',{'query':'hello'})
    def test_unlisted_tool_denied(self):
        with self.assertRaises(LelockError): self.rpc.call('mempalace_mine',{'source':'/'})
    def test_remote_palace_denied(self):
        with self.assertRaises(LelockError): PalaceRPC('https://example.com','secret')

if __name__=='__main__': unittest.main()
