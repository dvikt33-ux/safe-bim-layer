"""New group caller one-shot gates, no network or native mutation."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from test_apa_ac29_native_group_create import N
import apa_ac29_group_create_oneshot as B

class Gates(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);root=Path(t.name).resolve()
        self.state=root/'state';self.state.mkdir();source=root/'source.snapshot';source.write_bytes(b'accepted')
        original=root/'original.pln';original.write_bytes(b'protected');scratch=root/'scratch.pln';scratch.write_bytes(source.read_bytes())
        accepted=root/'accepted';accepted.mkdir();B.write(accepted/'reopened.json',dict(status='previous accepted'))
        B.write(self.state/'baseline-native.json',dict(elements=[]))
        self.m=dict(schema=B.SCHEMA,source=str(source),sourceSHA256=B.sha256(source),originalProtected=str(original),
            originalProtectedSHA256=B.sha256(original),protectedAncestors={},scratch=str(scratch),scratchInitialSHA256=B.sha256(scratch),
            acceptedState=str(accepted),acceptedReceiptSHA256=B.sha256(accepted/'reopened.json'),baselineSHA256=B.sha256(self.state/'baseline-native.json'))
        B.write(self.state/'manifest.json',self.m)
    def test_protected_source_drift_prevents_any_native_access(self):
        Path(self.m['source']).write_bytes(b'changed')
        with patch.object(B,'api_for') as api:
            with self.assertRaisesRegex(ValueError,'SOURCE_OR_BASELINE'):B.execute(self.state)
            api.assert_not_called()
    def test_attempted_or_failed_native_group_is_never_replayed(self):
        for name in ('attempted.json','failed.json'):
            with self.subTest(name=name):
                B.write(self.state/name,dict(status='UNKNOWN'))
                with patch.object(B,'api_for') as api:
                    with self.assertRaisesRegex(ValueError,'NO_REPLAY'):B.execute(self.state)
                    api.assert_not_called()
    def test_declared_ancestor_drift_rejected(self):
        self.m['protectedAncestors']={self.m['originalProtected']:'0'*64}
        (self.state/'manifest.json').write_text(__import__('json').dumps(self.m),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'SOURCE_OR_BASELINE'):B.manifest(self.state)

if __name__=='__main__':unittest.main()
