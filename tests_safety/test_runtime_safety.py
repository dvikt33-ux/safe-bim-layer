"""Safety-invariant acceptance tests. Fake BIM only; these assert absence of audit bugs."""
import copy
import json
import sqlite3
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from contextlib import contextmanager
from safe_bim_runtime import SQLiteCheckpointStore, ResumableExecutor, StepSpec, JobStatus, LeaseLost
from safe_bim_operations import SafeBIMOperations
from safe_bim_layer import ModalStateError, SafeBIMLayer
from safe_bim_ipc import PaletteHTTPServer
from safe_bim_service import load_plan
from controller.client import SafeBIMClient, ControllerConnectionError
from tests_safety.fake_bim import FakeBIM, PROJECT, WALL, PLINTH, SLAB, envelope


class CountingOps(SafeBIMOperations):
    def __init__(self, fake):
        super().__init__(fake)
        self.executes = self.reconciles = 0
    def execute(self, *args):
        self.executes += 1
        return super().execute(*args)
    def reconcile(self, *args):
        self.reconciles += 1
        return super().reconcile(*args)


class Crash(BaseException):
    pass


@contextmanager
def server(executor):
    http = PaletteHTTPServer(('127.0.0.1', 0), executor)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield http, f'http://127.0.0.1:{http.server_address[1]}'
    finally:
        http.shutdown()
        http.server_close()
        thread.join(3)


def post(base, path, body, token, **headers):
    heads = {'Content-Type':'application/json', 'X-Safe-BIM-Token':token, **headers}
    req = urllib.request.Request(base+path, data=body, headers=heads, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=9) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


class RuntimeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.counter = 0
    def tearDown(self):
        self.temp.cleanup()
    def make(self, operation='create_wall_loop', params=None, count=1, job='job'):
        self.counter += 1
        params = copy.deepcopy(params if params is not None else WALL)
        fake = FakeBIM()
        ops = CountingOps(fake)
        store = SQLiteCheckpointStore(self.folder/f'{self.counter}.sqlite3')
        store.create_job(job, 'offline safety', PROJECT, [StepSpec(str(i), operation, params, params.get('floor_index')) for i in range(count)])
        ex = ResumableExecutor(store, ops.execute, ops.reconcile, ops.current_project)
        return fake, ops, store, ex
    def receipt_crash(self, operation='create_plinth_segment', params=PLINTH):
        f, op, st, ex = self.make(operation, params)
        original = st.set_step
        def set_step(j, pos, status, **kwargs):
            if status == JobStatus.DONE:
                raise Crash('verified receipt saved, step DONE not committed')
            return original(j, pos, status, **kwargs)
        st.set_step = set_step
        with self.assertRaises(Crash):
            ex.run('job')
        st.set_step = original
        self.assertTrue(st.job('job')['steps'][0]['result']['readbackVerified'])
        return f, op, st, ex

    def test_plinth_json_plan_complete_runtime_and_nonzero_vertical(self):
        plan = {'job_id':'plinth','task_name':'plinth','project_path':PROJECT,'steps':[
            {'name':'segment','operation':'create_plinth_segment','params':PLINTH,'floor_index':1}]}
        file = self.folder/'plan.json'; file.write_text(json.dumps(plan))
        data, steps = load_plan(file)
        f=FakeBIM(); op=CountingOps(f); st=SQLiteCheckpointStore(self.folder/'plan.sqlite3')
        st.create_job(data['job_id'],data['task_name'],data['project_path'],steps)
        ex=ResumableExecutor(st,op.execute,op.reconcile,op.current_project)
        self.assertEqual(ex.run('plinth'), JobStatus.DONE)
        step=st.job('plinth')['steps'][0];fp=step['checkpoint']['payload']['expectedZFingerprint']
        self.assertAlmostEqual(fp['story_elevation'],4.5)
        self.assertAlmostEqual(fp['relative_offset'],-.6)
        self.assertAlmostEqual(step['result']['actual_bottom'],3.9)
        self.assertAlmostEqual(step['result']['actual_top'],4.5)
        self.assertEqual(len(f.dispatches),1)
        self.assertEqual(fp,step['result']['expectedZFingerprint'])

    def test_plinth_verified_receipt_reconciles_after_restart_without_write(self):
        f,op,st,_=self.receipt_crash()
        reopened=ResumableExecutor(SQLiteCheckpointStore(st.path),op.execute,op.reconcile,op.current_project)
        self.assertEqual(reopened.resume('job'),JobStatus.DONE)
        self.assertEqual(op.reconciles,1)
        self.assertEqual(len(f.dispatches),1)

    def test_modal_after_dispatch_is_unknown_no_repeat(self):
        f,op,st,ex=self.make()
        def modal(*_):raise ModalStateError('Invalid program status after apply')
        f.on_created=modal
        self.assertEqual(ex.run('job'),JobStatus.UNKNOWN_OUTCOME)
        f.on_created=lambda *_:None
        self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
        self.assertEqual((op.executes,op.reconciles,len(f.dispatches)),(1,1,1))

    def test_legacy_waiting_user_after_dispatch_reconciles_before_continue(self):
        f,op,st,ex=self.make()
        f.on_created=lambda *_:(_ for _ in ()).throw(ModalStateError('modal'))
        ex.run('job')
        st.set_step('job',0,JobStatus.WAITING_USER,result={'status':'WAITING_USER','retryAllowed':False})
        st.set_job('job',JobStatus.WAITING_USER)
        f.on_created=lambda *_:None
        self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
        self.assertEqual((op.executes,op.reconciles,len(f.dispatches)),(1,1,1))

    def test_pre_dispatch_modal_has_durable_absence_proof_then_one_attempt(self):
        for command in ('GetProjectInfo','GetStories'):
            with self.subTest(command=command):
                f,op,st,ex=self.make()
                def fail(cmd,p):
                    if cmd==command:raise ModalStateError('Invalid program status')
                f.on_call=fail
                self.assertEqual(ex.run('job'),JobStatus.WAITING_USER)
                self.assertFalse(st.job('job')['steps'][0]['checkpoint']['dispatchStarted'])
                self.assertEqual(len(f.dispatches),0)
                f.on_call=lambda *_:None
                self.assertEqual(ex.resume('job'),JobStatus.DONE)
                self.assertEqual(op.reconciles,1)
                self.assertEqual(len(f.dispatches),1)

    def test_32_concurrent_resume_exactly_one_dispatch(self):
        f,op,st,ex=self.make();f.block=True
        barrier=threading.Barrier(32)
        def run():barrier.wait(8);return ex.resume('job')
        with ThreadPoolExecutor(max_workers=32) as pool:
            futures=[pool.submit(run) for _ in range(32)]
            try:
                self.assertTrue(f.entered.wait(8))
                # Busy callers must return while owner is blocked, not queue retries.
                from concurrent.futures import wait
                done,_=wait(futures,timeout=2)
                self.assertEqual(len(done),31)
                self.assertEqual(len(f.dispatches),1)
            finally:f.release.set()
            results=[x.result(8) for x in futures]
        self.assertEqual(len(f.dispatches),1)
        self.assertEqual(op.executes,1)
        self.assertEqual(st.job('job')['status'],'DONE')
        self.assertIn(JobStatus.DONE,results)

    def test_24_concurrent_http_continue_exactly_one_dispatch(self):
        f,op,st,ex=self.make();f.block=True
        with server(ex) as (srv,base):
            client=SafeBIMClient(base);state=client.state('job')
            body=json.dumps({'job_id':'job','action':'continue','revision':state.revision}).encode()
            barrier=threading.Barrier(24)
            def send():barrier.wait(8);return post(base,'/jobs/job/continue',body,state.capability)
            with ThreadPoolExecutor(max_workers=24) as pool:
                futures=[pool.submit(send) for _ in range(24)]
                try:
                    self.assertTrue(f.entered.wait(8))
                    from concurrent.futures import wait
                    done,_=wait(futures,timeout=3)
                    self.assertEqual(len(done),23)
                    self.assertEqual(len(f.dispatches),1)
                finally:f.release.set()
                responses=[x.result(10) for x in futures]
            self.assertTrue(all(code in {200,409} for code,_ in responses))
        self.assertEqual(len(f.dispatches),1)

    def test_two_executors_same_db_single_flight(self):
        f,op,st,ex=self.make();f.block=True
        second=ResumableExecutor(SQLiteCheckpointStore(st.path),op.execute,op.reconcile,op.current_project)
        with ThreadPoolExecutor(max_workers=2) as pool:
            worker=pool.submit(ex.resume,'job')
            try:
                self.assertTrue(f.entered.wait(5))
                self.assertEqual(second.resume('job'),JobStatus.RUNNING)
                self.assertEqual(op.reconciles,0)
            finally:f.release.set()
            self.assertEqual(worker.result(5),JobStatus.DONE)
        self.assertEqual(len(f.dispatches),1)

    def test_stop_revokes_worker_preserves_cancelled_no_next_step(self):
        f,op,st,ex=self.make(count=2);f.block=True
        with ThreadPoolExecutor(max_workers=1) as pool:
            worker=pool.submit(ex.resume,'job')
            try:
                self.assertTrue(f.entered.wait(5))
                self.assertEqual(ex.stop('job'),JobStatus.CANCELLED)
                for status in (JobStatus.RUNNING,JobStatus.DONE,JobStatus.FAILED,JobStatus.PAUSED):
                    self.assertFalse(st.set_job('job',status))
                self.assertEqual(ex.resume('job'),JobStatus.CANCELLED)
            finally:f.release.set()
            self.assertEqual(worker.result(5),JobStatus.CANCELLED)
        self.assertEqual((op.executes,len(f.dispatches)),(1,1))
        self.assertEqual(st.job('job')['status'],'CANCELLED')
        self.assertEqual(st.job('job')['steps'][1]['status'],'PENDING')

    def test_pause_while_running_stops_at_boundary_without_second_write(self):
        f,op,st,ex=self.make(count=2);f.block=True
        with ThreadPoolExecutor(max_workers=1) as pool:
            worker=pool.submit(ex.resume,'job')
            try:
                self.assertTrue(f.entered.wait(5));ex.pause('job')
            finally:f.release.set()
            self.assertEqual(worker.result(5),JobStatus.PAUSED)
        self.assertEqual(len(f.dispatches),1)
        f.block=False
        self.assertEqual(ex.resume('job'),JobStatus.DONE)
        self.assertEqual(len(f.dispatches),2)

    def test_pause_during_preflight_not_cleared_by_admission(self):
        f,op,st,ex=self.make();entered=threading.Event();release=threading.Event()
        def block(cmd,p):
            if cmd=='GetProjectInfo':entered.set();release.wait(6)
        f.on_call=block
        with ThreadPoolExecutor(max_workers=1) as pool:
            worker=pool.submit(ex.resume,'job')
            try:self.assertTrue(entered.wait(4));ex.pause('job')
            finally:release.set()
            self.assertEqual(worker.result(5),JobStatus.PAUSED)
        self.assertEqual(len(f.dispatches),0)

    def test_project_switch_after_step_done_blocks_second_execute_and_restart(self):
        f,op,st,ex=self.make(count=2)
        original=st.set_step
        def step(j,pos,status,**kw):
            value=original(j,pos,status,**kw)
            if pos==0 and status==JobStatus.DONE:f.project='/fake/project-B.pln'
            return value
        st.set_step=step
        self.assertEqual(ex.run('job'),JobStatus.WAITING_USER)
        self.assertEqual(st.job('job')['steps'][0]['status'],'DONE')
        self.assertEqual((op.executes,len(f.dispatches)),(1,1))
        reopened=ResumableExecutor(SQLiteCheckpointStore(st.path),op.execute,op.reconcile,op.current_project)
        self.assertEqual(reopened.resume('job'),JobStatus.WAITING_USER)
        self.assertEqual(len(f.dispatches),1)
        self.assertTrue(all(p==PROJECT for _,_,p in f.dispatches))

    def test_identity_checked_again_immediately_before_physical_write(self):
        f,op,st,ex=self.make();original=op.prepare
        def prepare(*args):
            result=original(*args);f.project='/fake/B.pln';return result
        op.prepare=prepare
        self.assertEqual(ex.run('job'),JobStatus.WAITING_USER)
        self.assertEqual(len(f.dispatches),0)
        self.assertFalse(st.job('job')['steps'][0]['checkpoint']['dispatchStarted'])

    def test_transport_variants_after_apply_never_failed_or_retried(self):
        for error in (TimeoutError('lost'),ConnectionResetError('lost'),urllib.error.URLError(TimeoutError('lost')),ValueError('invalid response JSON')):
            with self.subTest(error=type(error).__name__):
                f,op,st,ex=self.make()
                def lost(*_):raise error
                f.on_created=lost
                self.assertEqual(ex.run('job'),JobStatus.UNKNOWN_OUTCOME)
                f.on_created=lambda *_:None
                self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
                self.assertEqual(len(f.dispatches),1)
                self.assertFalse(st.job('job')['steps'][0]['result']['retryAllowed'])

    def test_reconcile_read_failures_are_ambiguous_not_absence(self):
        for variant in ('exception','empty','malformed','incomplete'):
            with self.subTest(variant=variant):
                f,op,st,ex=self.receipt_crash();reads=[]
                def fault(cmd,p):
                    if cmd!='GetDetailsOfElements':return
                    reads.append(cmd)
                    if variant=='exception':raise ConnectionResetError('read lost')
                    if variant=='empty':return {}
                    if variant=='malformed':return envelope(detailsOfElements={})
                    return envelope(detailsOfElements=[])
                f.on_call=fault
                row=st.job('job')['steps'][0]
                evidence=op.reconcile(row['operation'],row['params'],{'checkpoint':row['checkpoint'],'result':row['result'],'job_id':'job','position':0,'attempt':row['attempts'],'projectPath':PROJECT})
                self.assertEqual(evidence['classification'],'AMBIGUOUS')
                self.assertTrue(reads)
                self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
                self.assertEqual(len(f.dispatches),1)

    def test_external_reconcile_exception_cannot_dispatch(self):
        f,op,st,ex=self.make()
        f.on_created=lambda *_:(_ for _ in ()).throw(TimeoutError('unknown'))
        ex.run('job')
        ex.reconcile_operation=lambda *_:(_ for _ in ()).throw(RuntimeError('read failure'))
        self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
        self.assertEqual(len(f.dispatches),1)

    def test_foreign_similar_and_multiple_candidates_never_applied(self):
        for count in (1,2):
            with self.subTest(count=count):
                f,op,st,ex=self.make('create_plinth_segment',PLINTH)
                f.on_created=lambda *_:(_ for _ in ()).throw(TimeoutError('lost response'))
                ex.run('job')
                old=copy.deepcopy(next(iter(f.elements.values())))
                f.elements={f'foreign-{i}':copy.deepcopy(old) for i in range(count)}
                f.on_created=lambda *_:None
                self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
                self.assertEqual(len(f.dispatches),1)
                self.assertFalse(st.job('job')['steps'][0]['result'].get('readbackVerified',False))

    def test_unproven_not_applied_flag_rejected(self):
        f,op,st,ex=self.make();f.on_created=lambda *_:(_ for _ in ()).throw(TimeoutError('lost'))
        ex.run('job');ex.reconcile_operation=lambda *_:{'classification':'NOT_APPLIED'}
        self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
        self.assertEqual(len(f.dispatches),1)

    def test_wrong_wall_fields_and_missing_fields_never_done(self):
        cases=[('floorIndex',2),('zCoordinate',5),('height',99),('structureType','Composite'),
               ('bottomOffset',8),('relativeTopStory',1),('begThickness',9),('endThickness',9),
               ('begCoordinate',{'x':99,'y':99}),('guid','foreign')]
        for key,value in cases:
            for missing in (False,True):
                with self.subTest(key=key,missing=missing):
                    f,op,st,ex=self.make()
                    def corrupt(rows):
                        for row in rows:
                            target=row if key in {'floorIndex','guid'} else row['details']
                            if missing:
                                if key=='guid':row.pop('details',None)
                                else:target.pop(key,None)
                            else:target[key]=value
                        return rows
                    f.on_details=corrupt
                    self.assertNotEqual(ex.run('job'),JobStatus.DONE)
                    self.assertEqual(len(f.dispatches),1)

    def test_partial_or_duplicate_creation_identity_never_done(self):
        for mode in ('empty_details','two_details','bad_create_count','duplicate_guids'):
            with self.subTest(mode=mode):
                f,op,st,ex=self.make()
                if mode=='empty_details':f.on_details=lambda rows:[]
                elif mode=='two_details':f.on_details=lambda rows:rows+rows
                else:
                    original=f.call
                    def call(cmd,p):
                        result=original(cmd,p)
                        if cmd=='CreateWalls':
                            elements=result['result']['addOnCommandResponse']['elements']
                            result['result']['addOnCommandResponse']['elements']=elements[:1] if mode=='bad_create_count' else [elements[0]]*4
                        return result
                    f.call=call
                self.assertNotEqual(ex.run('job'),JobStatus.DONE)

    def test_slab_wrong_or_missing_fields_never_done(self):
        for key in ('floorIndex','level','referencePlaneLocation','thickness','zCoordinate','offsetFromTop','polygonOutline','structureType'):
            with self.subTest(key=key):
                f,op,st,ex=self.make('create_basic_slab',SLAB)
                def corrupt(rows):
                    for row in rows:(row if key=='floorIndex' else row['details']).pop(key,None)
                    return rows
                f.on_details=corrupt
                self.assertNotEqual(ex.run('job'),JobStatus.DONE)
                self.assertEqual(len(f.dispatches),1)

    def test_slab_top_and_bottom_reference_vertical(self):
        for plane in ('TOP','BOTTOM'):
            f,op,st,ex=self.make('create_basic_slab',dict(SLAB,reference_plane=plane))
            self.assertEqual(ex.run('job'),JobStatus.DONE)
            r=st.job('job')['steps'][0]['result']
            top=4.7 if plane=='TOP' else 4.95
            self.assertAlmostEqual(r['actual_top'],top)
            self.assertAlmostEqual(r['actual_bottom'],top-.25)
            self.assertEqual(f.dispatches[0][1]['slabsData'][0]['referencePlaneLocation'],plane.title())

    def test_plinth_all_required_fingerprint_fields_fail_closed(self):
        for key in ('floorIndex','zCoordinate','bottomOffset','height','structureType','type'):
            with self.subTest(key=key):
                f,op,st,ex=self.make('create_plinth_segment',PLINTH)
                def corrupt(rows):
                    for row in rows:(row if key in {'floorIndex','type'} else row['details']).pop(key,None)
                    return rows
                f.on_details=corrupt
                self.assertNotEqual(ex.run('job'),JobStatus.DONE)
        f,op,st,ex=self.make('create_plinth_segment',dict(PLINTH,expectedZFingerprint={'expected_bottom':999}))
        self.assertEqual(ex.run('job'),JobStatus.WAITING_USER)
        self.assertEqual(len(f.dispatches),0)

    def test_fingerprint_metadata_is_checkpointed_not_forwarded_as_kwargs(self):
        f,op,st,ex=self.make('create_plinth_segment',dict(PLINTH,expectedZFingerprint={'expected_bottom':3.9},verticalContext={'project_zero_z':4.5,'grade_z':3.9}))
        self.assertEqual(ex.run('job'),JobStatus.DONE)
        fp=st.job('job')['steps'][0]['checkpoint']['payload']['expectedZFingerprint']
        self.assertAlmostEqual(fp['expected_bottom'],3.9)

    def test_preexisting_guid_returned_by_create_is_rejected(self):
        f,op,st,ex=self.make('create_plinth_segment',PLINTH)
        first=SafeBIMLayer(f).create_plinth_segment(**PLINTH);self.assertEqual(first['status'],'PASS')
        foreign=first['guids'][0];original=f.call
        def call(cmd,p):
            response=original(cmd,p)
            return envelope(elements=[{'elementId':{'guid':foreign}}]) if cmd=='CreateWalls' else response
        f.call=call
        self.assertEqual(ex.run('job'),JobStatus.UNKNOWN_OUTCOME)
        self.assertEqual(ex.resume('job'),JobStatus.WAITING_USER)
        self.assertEqual(len(f.dispatches),2)  # one seed + one intended create, never a retry

    def test_checkpoint_failure_rolls_back_and_prevents_dispatch(self):
        f,op,st,ex=self.make();original=st._event
        def event(db,j,pos,name,payload):
            if name=='CHECKPOINT_BEFORE_WRITE':raise sqlite3.OperationalError('injected commit failure')
            return original(db,j,pos,name,payload)
        st._event=event
        with self.assertRaises(sqlite3.OperationalError):ex.run('job')
        row=SQLiteCheckpointStore(st.path).job('job')['steps'][0]
        self.assertEqual(row['attempts'],0);self.assertIsNone(row['checkpoint']);self.assertEqual(len(f.dispatches),0)

    def test_malformed_post_matrix_zero_mutations_and_bim_calls(self):
        f,op,st,ex=self.make()
        with server(ex) as (_,base):
            state=SafeBIMClient(base).state('job');before=st.job('job')
            valid={'job_id':'job','action':'continue','revision':state.revision}
            cases=[b'',b'{broken',b'[]',json.dumps({'job_id':'job','revision':0}).encode(),
                   json.dumps(dict(valid,action='erase')).encode(),json.dumps(dict(valid,job_id=1)).encode(),
                   b'{"job_id":"job","job_id":"job","action":"continue","revision":0}',
                   json.dumps(dict(valid,extra='x')).encode(),b'x'*5000,json.dumps(dict(valid,revision=True)).encode()]
            for body in cases:
                code,_=post(base,'/jobs/job/continue',body,state.capability);self.assertGreaterEqual(code,400)
                self.assertEqual(st.job('job'),before)
            for path,body in (('/missing',valid),('/jobs/job/erase',valid),('/jobs/missing/continue',dict(valid,job_id='missing')),('/jobs/active/continue',dict(valid,job_id='active'))):
                code,_=post(base,path,json.dumps(body).encode(),state.capability);self.assertGreaterEqual(code,400)
            code,_=post(base,'/jobs/job/continue',json.dumps(valid).encode(),state.capability,Origin='https://untrusted.invalid')
            self.assertEqual(code,403)
            code,_=post(base,'/jobs/job/continue',json.dumps(valid).encode(),'wrong-token');self.assertEqual(code,403)
            self.assertEqual(st.job('job'),before)
        self.assertEqual(f.calls,[]);self.assertEqual(op.executes,0)

    def test_controller_history_A_command_never_changes_current_B(self):
        f,op,st,ex=self.make(job='A')
        st.create_job('B','current B',PROJECT,[StepSpec('b','create_wall_loop',WALL,0)])
        with server(ex) as (_,base):
            client=SafeBIMClient(base);a=client.state('A');b=copy.deepcopy(st.job('B'))
            self.assertEqual(client.state('active').job_id,'B')
            result=client.command('continue','A',revision=a.revision,capability=a.capability)
            self.assertEqual(result['job_id'],'A')
            self.assertEqual(st.job('B'),b)
        self.assertEqual(st.job('A')['status'],'DONE')
        self.assertEqual(len(f.dispatches),1)

    def test_explicit_unicode_space_id_roundtrip_and_stale_revision(self):
        f,op,st,ex=self.make(job='Дом one')
        with server(ex) as (_,base):
            client=SafeBIMClient(base);state=client.state('Дом one')
            ex.pause('Дом one')
            with self.assertRaises(ControllerConnectionError):client.command('continue','Дом one',revision=state.revision,capability=state.capability)
            self.assertEqual(len(f.dispatches),0)
            client.state('Дом one');self.assertEqual(client.command('continue','Дом one')['status'],'DONE')
        self.assertEqual(len(f.dispatches),1)

    def test_active_selection_has_no_history_limit_and_terminal_controls(self):
        f,op,st,ex=self.make();st.set_job('job',JobStatus.RUNNING)
        for i in range(55):
            name=f'history-{i}';st.create_job(name,name,PROJECT,[StepSpec('x','create_wall_loop',WALL,0)]);st.set_job(name,JobStatus.DONE)
        self.assertEqual(ex.resolve_job_id('active'),'job')
        ex.stop('job')
        for row in st.jobs(50):
            self.assertFalse(any(ex.palette_state(row['job_id'])['controls'].values()))
        self.assertEqual(ex.palette_state('active')['selection'],'history')

    def test_command_alias_rejected_and_cancelled_remains_terminal(self):
        f,op,st,ex=self.make()
        for action in (ex.run,ex.resume,ex.pause,ex.stop):
            with self.assertRaises(Exception):action('active')
        self.assertEqual(ex.stop('job'),JobStatus.CANCELLED)
        self.assertEqual(ex.resume('job'),JobStatus.CANCELLED)
        self.assertEqual(len(f.dispatches),0)

    def test_untrusted_plan_rejects_unknown_operation_and_duplicate_fields(self):
        path=self.folder/'invalid.json'
        base=dict(job_id='j',task_name='t',project_path=PROJECT,steps=[dict(name='s',operation='unknown',params={})])
        path.write_text(json.dumps(base))
        with self.assertRaises(Exception):load_plan(path)
        path.write_text('{"job_id":"a","job_id":"b"}')
        with self.assertRaises(Exception):load_plan(path)

if __name__=='__main__':unittest.main()
