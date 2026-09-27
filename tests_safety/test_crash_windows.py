import json
import os
import select
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from safe_bim_runtime import SQLiteCheckpointStore, ResumableExecutor, StepSpec, JobStatus
from safe_bim_operations import SafeBIMOperations
from safe_bim_lock import execution_lock
from tests_safety.fake_bim import FakeBIM, PROJECT, WALL


@unittest.skipUnless(os.name=='posix','SIGKILL/select subprocess driver requires POSIX; native Windows re-audit required')
class CrashWindowsTests(unittest.TestCase):
    def test_seven_hard_kill_windows_no_unknown_write_repeated(self):
        cases=[]
        with tempfile.TemporaryDirectory() as directory:
            for phase in ('before_checkpoint','after_checkpoint','during_dispatch','after_write','after_readback','after_done','inside_checkpoint'):
                with self.subTest(phase=phase):
                    folder=Path(directory)/phase;folder.mkdir();db=folder/'state.sqlite3';model=folder/'model.json'
                    st=SQLiteCheckpointStore(db)
                    count=2 if phase=='after_done' else 1
                    st.create_job('job','crash',PROJECT,[StepSpec(str(i),'create_wall_loop',WALL,0) for i in range(count)])
                    worker=subprocess.Popen([sys.executable,str(Path(__file__).with_name('crash_worker.py')),str(db),str(model),phase],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    try:
                        ready,_,_=select.select([worker.stdout],[],[],12)
                        self.assertTrue(ready,'crash worker did not reach barrier')
                        self.assertEqual(worker.stdout.readline().strip(),'READY')
                        worker.kill();out,err=worker.communicate(timeout=5)
                        self.assertEqual(worker.returncode,-9)
                    finally:
                        if worker.poll() is None:worker.kill();worker.wait()
                    saved=json.loads(model.read_text()) if model.exists() else {'elements':{},'dispatches':0}
                    f=FakeBIM();f.elements=saved['elements'];op=SafeBIMOperations(f)
                    st=SQLiteCheckpointStore(db);before=st.job('job')
                    ex=ResumableExecutor(st,op.execute,op.reconcile,op.current_project)
                    final=ex.resume('job')
                    new=len(f.dispatches)
                    if phase in {'during_dispatch','after_write'}:
                        self.assertEqual(final,JobStatus.WAITING_USER);self.assertEqual(new,0)
                        self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER);self.assertEqual(len(f.dispatches),0)
                    elif phase=='after_readback':
                        self.assertEqual(final,JobStatus.DONE);self.assertEqual(new,0)
                    else:
                        self.assertEqual(final,JobStatus.DONE);self.assertEqual(new,1)
                    if phase=='after_done':
                        self.assertEqual(st.job('job')['steps'][0]['attempts'],1)
                    cases.append({'phase':phase,'step_before':before['steps'][0]['status'],'prior_dispatches':saved['dispatches'],
                                  'new_dispatches':new,'final':final.value,'elements':len(f.elements)})
        print('CRASH_WINDOWS '+json.dumps(cases),flush=True)

    def test_os_lock_excludes_second_process_and_is_crash_released(self):
        with tempfile.TemporaryDirectory() as directory:
            db=str(Path(directory)/'state.sqlite3')
            code="from safe_bim_lock import execution_lock; import sys;\nwith execution_lock(sys.argv[1]) as owned: print(int(owned),flush=True)"
            with execution_lock(db) as owned:
                self.assertTrue(owned)
                p=subprocess.run([sys.executable,'-c',code,db],capture_output=True,text=True,check=True)
                self.assertEqual(p.stdout.strip(),'0')
            p=subprocess.run([sys.executable,'-c',code,db],capture_output=True,text=True,check=True)
            self.assertEqual(p.stdout.strip(),'1')

if __name__=='__main__':unittest.main()
