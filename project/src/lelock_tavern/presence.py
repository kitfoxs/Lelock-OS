"""Opt-in Pulse integration: same selected runtime -> real brokered tools -> local inbox.
Never installs a launch agent, records audio, sends DMs, or transfers credentials.
"""
import json, threading, time
from lelock_entity.jobs import JobQueue, Pulse, PulseWorker, QuietHours
from lelock_entity.channels import LocalInbox
from .common import BridgeError, bounded, fields, ident

class Presence:
    def __init__(self,manager,*,enabled=False,quiet=None):
        self.manager=manager;self.enabled=enabled;self.closed=threading.Event();self.thread=None
        self.queue=JobQueue(manager.store);self.pulse=Pulse(self.queue)
        self.worker=PulseWorker(self.queue,self.dispatch,quiet=quiet or QuietHours())
        # Manager is protected by the CLI's single-owner lease. Never replay interrupted native work.
        with manager.store.connect() as db:
            db.execute("UPDATE jobs SET state='needs_review' WHERE state='running'")
    def add(self,eid,data):
        if not self.enabled:raise BridgeError('Start the gateway with --enable-pulse before authorizing scheduled model use')
        fields(data,{'prompt','interval','ttl','timezone'},{'prompt'})
        prompt=bounded(data['prompt'],10000);interval=data.get('interval',3600);ttl=data.get('ttl',3600)
        if type(interval)is not int or not 600<=interval<=86400:raise BridgeError('Use an interval of at least 600 seconds')
        if type(ttl)is not int or not 60<=ttl<=7200:raise BridgeError('Schedule lease must be 60–7200 seconds')
        slot=self.manager.slot(eid);slot.core.stop.check()
        if slot.entity['config']['provider'] not in self.manager.runtimes:raise BridgeError('Schedule needs an account-chat runtime')
        with self.manager.store.connect() as db:
            count=db.execute("SELECT COUNT(*) FROM schedules WHERE enabled=1").fetchone()[0]
        if count>=8:raise BridgeError('Disable an existing schedule before adding another')
        import uuid
        sid=uuid.uuid4().hex;expires=min(time.time()+ttl,slot.core.session.expires_at)
        self.pulse.add(sid,kind='interval',policy_id=slot.core.session.ident,payload={'entity':eid,'prompt':prompt},
                       expires_at=expires,interval=interval,timezone=data.get('timezone','America/Chicago'))
        # Do not fire immediately during setup. First event is at the next interval boundary.
        with self.manager.store.connect() as db:
            db.execute('UPDATE schedules SET last_slot=? WHERE id=?',(str(int(time.time()//interval)),sid))
        return {'schedule':sid,'entity':eid,'expires_at':expires,'delivery':'local_inbox','not_a_dollar_budget':True}
    def list(self,eid):
        with self.manager.store.connect() as db:rows=db.execute('SELECT * FROM schedules').fetchall()
        return [{**dict(r),'config':json.loads(r['config'])} for r in rows if json.loads(r['config'])['payload'].get('entity')==eid]
    def disable(self,eid,sid):
        ident(sid)
        if sid not in {r['id'] for r in self.list(eid)}:raise BridgeError('Schedule belongs to another character')
        with self.manager.store.connect() as db:db.execute('UPDATE schedules SET enabled=0 WHERE id=?',(sid,))
        return {'disabled':sid}
    def dispatch(self,payload,jid):
        if self.closed.is_set() or not self.enabled:raise BridgeError('Pulse stopped')
        data=payload['data'];eid=ident(data['entity']);slot=self.manager.slot(eid)
        if slot.core.session.ident!=payload['policy_id']:raise BridgeError('Schedule authorization expired; operator must reauthorize')
        slot.core.stop.check()
        self.manager.start_turn(eid,'pulse',jid,data['prompt'],[])
        while not self.closed.wait(.1):
            turn=self.manager.public_turn(jid,eid)
            if turn['state']=='completed':
                result=turn['result'];receipt=LocalInbox(self.manager.store,eid).send(result.get('text','') or '(No final text; inspect the turn receipt.)',jid)
                return {'turn_id':jid,'actor':eid,'delivery':receipt}
            if turn['state'] in {'failed','needs_review'}:raise BridgeError('Scheduled turn did not complete; inspect receipts')
        self.manager.stop(eid);raise BridgeError('Pulse stopped while a turn was running')
    def start(self):
        if not self.enabled:return self
        def loop():
            while not self.closed.wait(1):
                try:self.pulse.tick();self.worker.run_once()
                except Exception:pass  # Job failure is durable needs_review; never retry an uncertain effect.
        self.thread=threading.Thread(target=loop,name='lelock-pulse',daemon=True);self.thread.start();return self
    def close(self):
        self.closed.set()
        if self.thread:self.thread.join(timeout=2)
    def inbox(self,eid):return LocalInbox(self.manager.store,eid).unread()
