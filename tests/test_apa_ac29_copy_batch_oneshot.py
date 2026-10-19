"""Offline one-shot/source/snapshot gates, no Archicad connection."""
from pathlib import Path
import json,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_ac29_copy_batch_oneshot as B

class Gates(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.state=self.root/'state';self.state.mkdir()
        source=self.root/'source.pln';source.write_bytes(b'protected accepted source')
        original=self.root/'original.pln';original.write_bytes(b'original remains')
        scratch=self.root/'scratch.pln';scratch.write_bytes(source.read_bytes())
        accepted=self.root/'accepted';accepted.mkdir();B.write_new_json(accepted/'reopened.json',dict(status='accepted'))
        B.write_new_json(self.state/'baseline-native.json',dict(elements=[]))
        self.m=dict(schema=B.SCHEMA,source=str(source),sourceSHA256=B.sha256(source),
            originalProtected=str(original),originalProtectedSHA256=B.sha256(original),
            scratch=str(scratch),scratchInitialSHA256=B.sha256(scratch),
            acceptedState=str(accepted),acceptedReceiptSHA256=B.sha256(accepted/'reopened.json'),
            baselineSHA256=B.sha256(self.state/'baseline-native.json'))
        B.write_new_json(self.state/'manifest.json',self.m)

    def test_original_drift_stops_before_any_native_call(self):
        Path(self.m['originalProtected']).write_bytes(b'changed')
        with patch.object(B,'api_for') as api:
            with self.assertRaisesRegex(ValueError,'SOURCE_OR_BASELINE_DRIFT'):B.execute(self.state)
            api.assert_not_called()

    def test_attempted_batch_never_replayed(self):
        B.write_new_json(self.state/'attempted.json',dict(status='UNKNOWN'))
        with patch.object(B,'api_for') as api:
            with self.assertRaisesRegex(ValueError,'NO_REPLAY'):B.execute(self.state)
            api.assert_not_called()

    def test_failed_batch_never_replayed(self):
        B.write_new_json(self.state/'failed.json',dict(status='UNKNOWN'))
        with self.assertRaisesRegex(ValueError,'NO_REPLAY'):B.manifest(self.state,True)

    def test_source_acceptance_receipt_tamper_rejected(self):
        (Path(self.m['acceptedState'])/'reopened.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'SOURCE_OR_BASELINE_DRIFT'):B.manifest(self.state)

    def test_plan_json_roundtrip_does_not_change_pinned_semantics(self):
        p=dict(preview=dict(vectors=[(1,2,3)]));B.write_new_json(self.state/'plan.json',p)
        with patch.object(B,'current_plan',return_value=p),patch.object(B,'ScratchWriteLease',side_effect=RuntimeError('BEFORE_NATIVE')):
            with self.assertRaisesRegex(RuntimeError,'BEFORE_NATIVE'):B.execute(self.state)
        self.assertFalse((self.state/'attempted.json').exists())

    def saved(self):
        scratch=Path(self.m['scratch']);scratch.write_bytes(b'saved output stand-in')
        h=B.sha256(scratch)
        snap=B.preserve_guarded_save(scratch,self.state/'guarded-save.snapshot',h,
            {self.m['source']:self.m['sourceSHA256'],self.m['originalProtected']:self.m['originalProtectedSHA256']})
        B.write_new_json(self.state/'guarded-snapshot.json',snap)
        B.write_new_json(self.state/'saved.json',dict(status='SHARED_COPY_SAVED_PENDING_REOPEN',savedSHA256=h,
            snapshotReceiptSHA256=B.sha256(self.state/'guarded-snapshot.json')))

    def test_snapshot_tamper_rejected_before_reopen_api(self):
        self.saved();(self.state/'guarded-save.snapshot').write_bytes(b'changed')
        with patch.object(B,'api_for') as api:
            with self.assertRaisesRegex(ValueError,'SAVED_BYTES'):B.verify_reopen(self.state)
            api.assert_not_called()

    def test_timeout_is_not_native_close_confirmation(self):
        self.saved()
        def timeout(*a):raise TimeoutError('timed out')
        with patch.object(B,'api_for',return_value=(timeout,None)):
            with self.assertRaisesRegex(ValueError,'NO_OPEN_PROJECT_REQUIRED'):B.check_closed(self.state)
        self.assertFalse((self.state/'closed.json').exists())

    def test_real_native_4001_can_record_close_without_write(self):
        self.saved()
        def closed(*a):raise ValueError('4001: no open project')
        with patch.object(B,'api_for',return_value=(closed,None)):
            self.assertEqual(B.check_closed(self.state)['nativeWrites'],0)


if __name__=='__main__':unittest.main()
