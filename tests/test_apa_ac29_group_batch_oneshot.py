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

    def test_safe01_proof_drift_blocks_every_new_batch(self):
        with patch.object(G,'safe01_gate',return_value='b'*64),patch.object(G,'prepare_api') as api:
            with self.assertRaisesRegex(ValueError,'SAFE01_PROOF_DRIFT'):G.execute(self.state)
            api.assert_not_called()

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
