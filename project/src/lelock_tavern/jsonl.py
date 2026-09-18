"""Bounded NDJSON subprocess and request multiplexer; never logs raw account responses."""
from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
import os, queue, signal, subprocess, threading, time
from .common import BridgeError, canonical, strict_load

class JsonlProcess:
    def __init__(self,argv,*,cwd=None,env=None,line_limit=4_000_000):
        if not argv or any(not isinstance(x,str) or '\0' in x for x in argv):raise BridgeError("Invalid native command")
        self.proc=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
             stderr=subprocess.DEVNULL,start_new_session=True,bufsize=0)
        self.lines=queue.Queue(maxsize=512);self.lock=threading.Lock();self.closed=threading.Event()
        self.line_limit=line_limit
        self.thread=threading.Thread(target=self._read,daemon=True);self.thread.start()
    def _read(self):
        try:
            while not self.closed.is_set():
                line=self.proc.stdout.readline(self.line_limit+1)
                if not line:break
                if len(line)>self.line_limit or not line.endswith(b'\n'):raise BridgeError("Native output exceeds framing limit")
                value=strict_load(line)
                if not isinstance(value,dict):raise BridgeError("Native output is not an object")
                self.lines.put(value,timeout=2)
        except BaseException:
            try:self.lines.put(BridgeError("Native transport failed; inspect locally, no success claimed"),timeout=.1)
            except queue.Full:pass
        finally:
            try:self.lines.put(None,timeout=.1)
            except queue.Full:pass
    def send(self,value):
        data=(canonical(value)+'\n').encode()
        if len(data)>self.line_limit:raise BridgeError("Native input exceeds limit")
        with self.lock:
            if self.proc.poll() is not None or self.closed.is_set():raise BridgeError("Native process is closed")
            try:self.proc.stdin.write(data);self.proc.stdin.flush()
            except (BrokenPipeError,OSError) as e:raise BridgeError("Native process closed its input") from e
    def receive(self,timeout=.1):
        return self.lines.get(timeout=timeout)
    def close(self):
        if self.closed.is_set():return
        self.closed.set()
        try:self.proc.stdin.close()
        except OSError:pass
        try:os.killpg(self.proc.pid,signal.SIGTERM)
        except (ProcessLookupError,PermissionError):
            try:self.proc.terminate()
            except OSError:pass
        try:self.proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            try:os.killpg(self.proc.pid,signal.SIGKILL)
            except (ProcessLookupError,PermissionError):self.proc.kill()
            self.proc.wait(timeout=2)
        self.proc.stdout.close();self.thread.join(timeout=1)

class RPC:
    """Codex uses JSON-RPC-shaped messages without a jsonrpc field. Requests may flow both ways."""
    def __init__(self,argv,*,cwd=None,env=None,on_request=None,on_event=None):
        self.wire=JsonlProcess(argv,cwd=cwd,env=env);self.pending={};self.lock=threading.Lock();self.seq=0
        self.on_request=on_request or (lambda m,p: (_ for _ in ()).throw(BridgeError("Unsupported native request")))
        self.on_event=on_event or (lambda m,p:None);self.stopped=threading.Event()
        self.pool=ThreadPoolExecutor(max_workers=8,thread_name_prefix='lelock-native-callback')
        self.reader=threading.Thread(target=self._reader,daemon=True);self.reader.start()
    def _reader(self):
        try:
            while not self.stopped.is_set():
                try:msg=self.wire.receive(.2)
                except queue.Empty:continue
                if msg is None or isinstance(msg,BaseException):raise BridgeError("Native runtime disconnected")
                if 'method'in msg:
                    if 'id'in msg:self.pool.submit(self._answer,msg)
                    else:self.on_event(msg['method'],msg.get('params',{}))
                else:
                    with self.lock:future=self.pending.pop(msg.get('id'),None)
                    if future and not future.done():
                        if 'error'in msg:future.set_exception(BridgeError("Native runtime rejected request; no fallback was billed"))
                        else:future.set_result(msg.get('result'))
        except BaseException:
            with self.lock:
                for f in self.pending.values():
                    if not f.done():f.set_exception(BridgeError("Native runtime disconnected"))
                self.pending.clear()
            self.stopped.set()
    def _answer(self,msg):
        try:answer={'id':msg['id'],'result':self.on_request(msg['method'],msg.get('params',{}))}
        except BaseException:answer={'id':msg['id'],'error':{'code':-32601,'message':'Operation not authorized by this client'}}
        try:self.wire.send(answer)
        except BridgeError:pass
    def request(self,method,params=None,timeout=45):
        f=Future()
        with self.lock:
            self.seq+=1;rid=self.seq;self.pending[rid]=f
        try:
            self.wire.send({'id':rid,'method':method,'params':params or {}})
            return f.result(timeout=timeout)
        except FutureTimeout as e:
            raise BridgeError('Native request timed out; do not replay uncertain effects') from e
        finally:
            with self.lock:self.pending.pop(rid,None)
    def notify(self,method,params=None):self.wire.send({'method':method,'params':params or {}})
    def close(self):
        self.stopped.set();self.wire.close();self.reader.join(timeout=1)
        self.pool.shutdown(wait=False,cancel_futures=True)
