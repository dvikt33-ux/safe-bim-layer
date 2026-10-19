"""Offline persistence gates; no Archicad calls or LIVE evidence."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_ac29_group_batch_oneshot as G
from apa_ac29_save_isolation import sha256, write_new_json, preserve_guarded_save


class GroupBatchGates(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name);self.state=self.root/'state';self.state.mkdir()
        self.source=self.root/'source.pln';self.source.write_bytes(b'protected accepted source')
        self.scratch=self.root/'copy.pln';self.scratch.write_bytes(self.source.read_bytes())
        self.trace=self.root/'old.jsonl';self.trace.write_text('{}\n')
        write_new_json(self.state/'baseline-native.json',dict(elements=[]))
        self.m=dict(schema=G.SCHEMA,status='STAGED_NO_MODEL_WRITES',source=str(self.source),
            sourceSHA256=sha256(self.source),scratch=str(self.scratch),
            scratchInitialSHA256=sha256(self.scratch),port=19727,
            baselineSHA256=sha256(self.state/'baseline-native.json'),
            sourceBaselineTrace=str(self.trace),sourceBaselineTraceSHA256=sha256(self.trace),
            safe01State=str(self.root/'accepted-safe01'),safe01ReceiptSHA256='a'*64)
        write_new_json(self.state/'manifest.json',self.m)
        self.gate=patch.object(G,'safe01_gate',return_value='a'*64)
        self.gate.start();self.addCleanup(self.gate.stop)

    def saved(self):
        self.scratch.write_bytes(b'new valid-byte stand-in for saved group batch')
        s=sha256(self.scratch)
        proof=preserve_guarded_save(self.scratch,self.state/'guarded-save.snapshot',s,
                                    {str(self.source):sha256(self.source)})
        write_new_json(self.state/'guarded-snapshot.json',proof)
        saved=dict(schema=G.SCHEMA,status='GROUP_BATCH_SAVED_PENDING_REAL_REOPEN',
            savedSHA256=s,snapshotReceiptSHA256=sha256(self.state/'guarded-snapshot.json'))
        write_new_json(self.state/'saved.json',saved)
        return saved

    def test_replay_reservation_rejected_before_transport_or_native_probe(self):
        write_new_json(self.state/'attempted.json',dict(status='UNKNOWN'))
        with patch.object(G,'prepare_api') as api:
            with self.assertRaisesRegex(ValueError,'NO_REPLAY'): G.execute(self.state)
            api.assert_not_called()

    def test_plan_json_roundtrip_preserves_tuple_geometry_before_lease(self):
        plan=dict(preview=dict(offsets=[(25,0,0)]),
                  sourceProof=dict(vertices=[(1.25,2.5,0)]))
        write_new_json(self.state/'plan.json',plan)
        with patch.object(G,'build_plan',return_value=plan), \
             patch.object(G,'ScratchWriteLease',side_effect=RuntimeError('LEASE_SENTINEL')):
            with self.assertRaisesRegex(RuntimeError,'LEASE_SENTINEL'):G.execute(self.state)
        self.assertFalse((self.state/'attempted.json').exists())

    def test_real_plan_value_drift_still_stops_before_lease(self):
        write_new_json(self.state/'plan.json',dict(offsets=[(25,0,0)]))
        with patch.object(G,'build_plan',return_value=dict(offsets=[(26,0,0)])), \
             patch.object(G,'ScratchWriteLease') as lease:
            with self.assertRaisesRegex(ValueError,'CURRENT_PLAN_DRIFT'):G.execute(self.state)
            lease.assert_not_called()

    def test_safe01_proof_drift_blocks_every_new_batch(self):
        with patch.object(G,'safe01_gate',return_value='b'*64),patch.object(G,'prepare_api') as api:
            with self.assertRaisesRegex(ValueError,'SAFE01_PROOF_DRIFT'):G.execute(self.state)
            api.assert_not_called()

    def test_unknown_clone_cannot_enter_save_only_reconciliation(self):
        write_new_json(self.state/'failed.json',dict(error='native timeout'))
        with patch.object(G,'prepare_api') as api:
            with self.assertRaisesRegex(ValueError,'ONLY_COMPLETED_UNSAVED'):
                G.reconcile_completed_clone(self.state)
            api.assert_not_called()

    def test_changed_reconciliation_cannot_reserve_or_save(self):
        write_new_json(self.state/'completed-clone-reconciliation.json',dict(hash='old'))
        with patch.object(G,'reconcile_completed_clone',return_value=dict(hash='new')), \
             patch.object(G,'prepare_api') as api:
            with self.assertRaisesRegex(ValueError,'PROOF_DRIFT'):G.save_reconciled_clone(self.state)
            api.assert_not_called()
        self.assertFalse((self.state/'reconciled-save-attempted.json').exists())

    def test_reconciled_save_has_no_clone_or_workflow_dispatch(self):
        import inspect
        for fn in (G.save_reconciled_clone,G.save_verified_batch):
            code=inspect.getsource(fn)
            self.assertNotIn('run_auto_optimized_native_task',code)
            self.assertNotIn('router.prepare(V.CMD',code)

    def test_save_only_continuation_binds_original_writer_and_never_clones(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        h='c'*64
        api=SimpleNamespace(write_attempts=0,calls={'SaveProject':0})
        guard=SimpleNamespace(new_saved_sha=h,enable_after_verified_copy=Mock())
        lease=SimpleNamespace(lock_sha=h,verify=lambda:True)
        router=Mock()
        def save(writer,scene,*args,**kwargs):
            self.assertIs(writer,original_writer)
            self.assertEqual(scene,G.SAVE_SCENE)
            api.calls['SaveProject']=1;api.write_attempts=1
            return dict(status='PASS')
        router.execute.side_effect=save
        m=dict(self.m,groupCount=32);planned=dict(baselineGuids=['old'])
        original_writer=object()
        with patch.object(G.R,'SceneWriter',return_value=original_writer) as factory, \
             patch.object(G,'verify_group_model',return_value=(['old','new'],{},{})), \
             patch.object(G,'fingerprint',return_value=h), \
             patch.object(G.C,'retained_geometry_signatures',return_value={}), \
             patch.object(G,'sha256',return_value=h):
            result=G.save_verified_batch(self.state,m,planned,api,guard,router,lease,{})
        factory.assert_called_once()
        self.assertEqual(result['saveCalls'],1)
        self.assertEqual(api.calls,{'SaveProject':1})

    def test_historical_pool_requires_exact_original_source_solid(self):
        native=dict(elements=[dict(guid='old')])
        planned=dict(baselineGuids=['old'],sourceProof=dict(sourceFacts={'old':dict(anchor={},solid=dict(v=1))}))
        folder=self.state/'trace-write';folder.mkdir()
        (folder/'raw.jsonl').write_text('\n'.join(json.dumps(r) for r in [dict(command='GetModelDumpV1',response={}),dict(command=G.V.CMD)]),encoding='utf8')
        with patch.object(G.C.G,'normalize_dump',return_value=native), \
             patch.object(G,'fingerprint',return_value='b'*64), \
             patch.object(G.V.M,'owned_children',return_value=[]), \
             patch.object(G.V.M,'solid_fingerprint',return_value=dict(v=2)):
            with self.assertRaisesRegex(ValueError,'SOURCE_FACTS_DRIFT'):
                G.original_plan_native(self.state,dict(baselineBrepSHA256='b'*64),planned)

    def test_missing_instance_command_stops_before_model_or_group_reads(self):
        with patch.object(G,'prepare_api',return_value=(object(),None)), \
             patch.object(G,'router_for',side_effect=ValueError('COMMAND_NOT_REGISTERED')), \
             patch.object(G,'capture') as model:
            with self.assertRaisesRegex(ValueError,'NOT_REGISTERED'):G.build_plan(self.state)
            model.assert_not_called()

    def prior174(self):
        group='00000000-0000-4000-8000-000000000001'
        layout=dict(mode='GRID',columns=8,rows=4,stepX=25,stepY=8,startDx=25,startDy=0)
        prior=self.root/'prior174';prior.mkdir()
        record=dict(schema='APA_AC29_GROUP_GRID_STAGE_V1',status='STAGED_SAVED_COPY_ONLY_NO_ARCHICAD_CALLS',
            sourceProject=str(self.source),scratchProject=str(self.scratch),
            sourceSavedSha256=sha256(self.source),sourceGroupId=group,
            shifts=G.placement_offsets(layout),expectedOriginalGuids=44,expectedPostGuids=172)
        write_new_json(prior/'stage.json',record)
        self.trace.write_text(json.dumps(dict(command='GetModelDumpV1',response=dict(elements=[])))+'\n')
        model=dict(elements=[dict(guid=f'00000000-0000-4000-8000-{i:012d}') for i in range(44)])
        return prior,group,layout,model

    def test_exact_prior174_adoption_does_not_recopy_or_edit_old_receipt(self):
        prior,group,layout,model=self.prior174()
        original=self.scratch.read_bytes();proof=(prior/'stage.json').read_bytes()
        with patch.object(G,'PRIOR174_SCRATCH',self.scratch), \
             patch.object(G.C.G,'normalize_dump',return_value=model), \
             patch.object(G,'fingerprint',return_value='b'*64),patch.object(G,'copy_exclusive') as copy:
            m=G.stage(self.source,self.scratch,self.root/'state2',self.trace,self.root/'safe01',
                      group,layout,19726,prior_stage=prior/'stage.json')
            copy.assert_not_called()
        self.assertTrue(m['existingSavedTestCopyAdoptedWithoutFileWrite'])
        self.assertEqual(self.scratch.read_bytes(),original)
        self.assertEqual((prior/'stage.json').read_bytes(),proof)

    def test_prior174_attempt_cannot_be_adopted_even_when_saved_sha_matches(self):
        prior,group,layout,model=self.prior174()
        write_new_json(prior/'attempted.json',dict(status='UNKNOWN'))
        with patch.object(G,'PRIOR174_SCRATCH',self.scratch), \
             patch.object(G.C.G,'normalize_dump',return_value=model), \
             patch.object(G,'fingerprint',return_value='b'*64):
            with self.assertRaisesRegex(ValueError,'EXACT_UNATTEMPTED'):
                G.stage(self.source,self.scratch,self.root/'state2',self.trace,self.root/'safe01',
                        group,layout,19726,prior_stage=prior/'stage.json')
        self.assertFalse((self.root/'state2').exists())

    def test_baseline_or_original_source_drift_is_denied(self):
        for p in (self.source,self.state/'baseline-native.json',self.trace):
            old=p.read_bytes();p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'IMMUTABLE_SOURCE'):G.manifest_for(self.state)
            p.write_bytes(old)

    def test_saved_snapshot_and_proof_are_pinned_before_gui_read(self):
        self.saved();G.saved_state(self.state)
        (self.state/'guarded-save.snapshot').write_bytes(b'changed snapshot')
        with patch.object(G,'prepare_api') as api:
            with self.assertRaisesRegex(ValueError,'SNAPSHOT_PROOF_DRIFT'):G.verify_reopen(self.state)
            api.assert_not_called()

    def test_reopen_requires_real_native_close_record(self):
        self.saved()
        with patch.object(G,'prepare_api') as api:
            with self.assertRaises(FileNotFoundError):G.verify_reopen(self.state)
            api.assert_not_called()

    def test_still_open_project_cannot_be_recorded_closed(self):
        self.saved()
        with patch.object(G,'prepare_api',return_value=(lambda *a:dict(projectPath=str(self.scratch)),None)):
            with self.assertRaisesRegex(ValueError,'STILL_OPEN'):G.check_closed(self.state)
        self.assertFalse((self.state/'closed.json').exists())

    def test_socket_error_cannot_be_promoted_to_gui_closed(self):
        self.saved()
        def failed(*a):raise TimeoutError('read timed out')
        with patch.object(G,'prepare_api',return_value=(failed,None)):
            with self.assertRaisesRegex(ValueError,'NOT_CONFIRMED'):G.check_closed(self.state)
        self.assertFalse((self.state/'closed.json').exists())


if __name__=='__main__':unittest.main()
