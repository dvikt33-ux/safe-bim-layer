"""Killed subprocess for real checkpoint/adapter crash-window acceptance; fake BIM only."""
import json
import os
import sys
import threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safe_bim_runtime import SQLiteCheckpointStore, ResumableExecutor, JobStatus
from safe_bim_operations import SafeBIMOperations
from tests_safety.fake_bim import FakeBIM


def main():
    db, model, phase = sys.argv[1:]
    f=FakeBIM();op=SafeBIMOperations(f);store=SQLiteCheckpointStore(db)
    def park():
        print('READY',flush=True)
        threading.Event().wait(60)
        raise RuntimeError('parent failed to kill worker')
    def persist():
        with open(model,'w') as out:
            json.dump({'elements':f.elements,'dispatches':len(f.dispatches)},out)
            out.flush();os.fsync(out.fileno())
    def dispatch(*_):
        persist()
        if phase=='during_dispatch':park()
    def created(*_):
        persist()
        if phase=='after_write':park()
    f.on_dispatch=dispatch;f.on_created=created
    checkpoint=store.checkpoint_before_write
    step=store.set_step
    event=store._event
    def cp(*args,**kw):
        if phase=='before_checkpoint':park()
        result=checkpoint(*args,**kw)
        if phase=='after_checkpoint':park()
        return result
    def set_step(j,pos,status,**kw):
        result=step(j,pos,status,**kw)
        if phase=='after_readback' and status==JobStatus.RUNNING and (kw.get('result') or {}).get('readbackVerified') is True:park()
        if phase=='after_done' and pos==0 and status==JobStatus.DONE:park()
        return result
    def ev(db,j,pos,name,payload):
        if phase=='inside_checkpoint' and name=='CHECKPOINT_BEFORE_WRITE':park()
        return event(db,j,pos,name,payload)
    store.checkpoint_before_write=cp;store.set_step=set_step;store._event=ev
    ResumableExecutor(store,op.execute,op.reconcile,op.current_project).run('job')
    raise RuntimeError('requested crash window not reached')


if __name__=='__main__':main()
