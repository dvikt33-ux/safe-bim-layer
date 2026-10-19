"""Fail-closed, offline file race tests. Never call an actual Archicad process."""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apa_ac29_save_isolation as S
import apa_ac29_hotlink_batch_oneshot as B


class SaveIsolationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.parent = self.base / "parent-state"
        self.parent.mkdir()
        self.source = self.base / "original.pln"
        self.module = self.base / "module.pln"
        self.scratch = self.base / "scratch.pln"
        self.source.write_bytes(b"unchanged accepted original PLN")
        self.module.write_bytes(b"unchanged hotlink module PLN")
        self.scratch.write_bytes(b"pln with native batch changes after save")
        self.saved_sha = S.sha256(self.scratch)
        self.source_sha = S.sha256(self.source)
        self.module_sha = S.sha256(self.module)

    def _protected(self):
        return {str(self.source): self.source_sha,
                str(self.module): self.module_sha}

    def _snapshot(self):
        target = self.parent / "guarded-save.snapshot"
        evidence = S.preserve_guarded_save(
            self.scratch, target, self.saved_sha, self._protected())
        S.write_new_json(self.parent / "guarded-snapshot.json", evidence)
        return evidence

    def _saved_parent(self):
        snapshot = self._snapshot()
        manifest = {"schema": B.SCHEMA,
                    "status": "STAGED_NO_MODEL_WRITES",
                    "source": str(self.source),
                    "sourceSHA256": self.source_sha,
                    "module": str(self.module),
                    "moduleSHA256": self.module_sha,
                    "scratch": str(self.scratch),
                    "scratchInitialSHA256": self.source_sha,
                    "port": 19726,
                    "count": 2, "gapMeters": 10,
                    "nodeGuid": "e06d3a5b-9797-aff7-49e3-87741c205118",
                    "prototypeGuid": "2a4d7d8f-06dc-4c79-97f1-34e7dc91b7ae"}
        receipt = {"schema": B.SCHEMA,
                   "status": "BATCH_NATIVE_SAVED_PENDING_REAL_REOPEN",
                   "savedSHA256": self.saved_sha,
                   "sourceSHA256": self.source_sha,
                   "moduleSHA256": self.module_sha,
                   "batchCount": 2, "afterGuidCount": 119,
                   "afterBrepSHA256": "0" * 64,
                   "afterGuidSetSHA256": "1" * 64,
                   "instanceGuids": [], "sourceOwnedCount": 24}
        for name, value in (
            ("manifest.json", manifest), ("saved.json", receipt),
            ("plan.json", {"baselineGuids": [], "geometry": {}}),
            ("attempted.json", {"status": "BATCH_NATIVE_DISPATCH_RESERVED"}),
        ):
            S.write_new_json(self.parent / name, value)
        with closing(sqlite3.connect(self.parent / "batch-scenewriter.sqlite")) as db:
            db.execute("CREATE TABLE scenes(scene_id TEXT PRIMARY KEY, state TEXT)")
            db.execute("INSERT INTO scenes VALUES('BatchCreate','PASS')")
            db.commit()
        return manifest, receipt, snapshot

    def test_cooperative_scratch_lock_excludes_second_job(self):
        job_a = S.ScratchWriteLease(self.scratch, self.parent, self.saved_sha)
        job_b = S.ScratchWriteLease(self.scratch, self.base, self.saved_sha)
        job_a.acquire()
        self.assertTrue(job_a.verify())
        self.assertIn("ONE_SHOT_NATIVE_WRITE_RESERVED",
                      job_a.lock.read_text(encoding="utf8"))
        with self.assertRaisesRegex(ValueError, "LEASE_"):
            job_b.acquire()
        self.assertEqual(S.sha256(self.scratch), self.saved_sha)

    def test_scratch_lock_rejects_changed_initial_source(self):
        self.scratch.write_bytes(b"changed by another session")
        with self.assertRaisesRegex(ValueError, "LEASE_SCRATCH"):
            S.ScratchWriteLease(self.scratch, self.parent,
                                self.saved_sha).acquire()
        self.assertFalse((self.base / "scratch.pln.apa-write.lock").exists())

    def test_scratch_lock_tamper_denied_after_reservation(self):
        lease = S.ScratchWriteLease(self.scratch, self.parent, self.saved_sha)
        lease.acquire()
        lease.lock.write_text("forged permit")
        with self.assertRaisesRegex(ValueError, "LEASE_LOST_OR_TAMPERED"):
            lease.verify()

    def test_snapshots_exact_post_guarded_save_bytes(self):
        snap = self._snapshot()
        self.assertEqual(snap["status"],
                         "BYTE_EXACT_GUARDED_SAVE_SNAPSHOT_CAPTURED")
        self.assertEqual(snap["savedSHA256"], self.saved_sha)
        self.assertEqual(snap["snapshotSHA256"], self.saved_sha)
        self.assertEqual(S.sha256(self.parent / "guarded-save.snapshot"),
                         self.saved_sha)
        self.assertEqual(snap["protectedSHA256"],
                         {str(self.source.resolve()): self.source_sha,
                          str(self.module.resolve()): self.module_sha})
        self.assertFalse(snap["blocksExternalArchicadWrites"])

    def test_snapshot_refuses_overwrite_or_wrong_expected_hash(self):
        self._snapshot()
        with self.assertRaisesRegex(ValueError, "FRESH_TARGET"):
            S.preserve_guarded_save(
                self.scratch, self.parent / "guarded-save.snapshot",
                self.saved_sha, self._protected())
        with self.assertRaisesRegex(ValueError, "CHANGED_BEFORE_COPY"):
            S.preserve_guarded_save(
                self.scratch, self.parent / "other.snapshot",
                "0" * 64, self._protected())

    def test_snapshot_refuses_tampered_module_and_preserves_sources(self):
        self.module.write_bytes(b"mutated by unrelated process")
        with self.assertRaisesRegex(ValueError, "PROTECTED_SOURCE_DRIFT"):
            S.preserve_guarded_save(
                self.scratch, self.parent / "other.snapshot",
                self.saved_sha, self._protected())
        self.assertFalse((self.parent / "other.snapshot").exists())

    def test_snapshot_detects_write_in_middle_of_capture(self):
        real_copy = S.copy_exclusive
        def concurrent_writer(src, dst):
            real_copy(src, dst)
            self.scratch.write_bytes(b"parallel Archicad write")
        with patch.object(S, "copy_exclusive", side_effect=concurrent_writer):
            with self.assertRaisesRegex(ValueError, "CONCURRENT_WRITE"):
                S.preserve_guarded_save(
                    self.scratch, self.parent / "guarded-save.snapshot",
                    self.saved_sha, self._protected())
        self.assertEqual(S.sha256(self.parent / "guarded-save.snapshot"),
                         self.saved_sha)
        self.assertNotEqual(S.sha256(self.scratch), self.saved_sha)

    def test_derivation_preserves_parent_receipt_even_after_original_drifts(self):
        self._saved_parent()
        parent_manifest_sha = S.sha256(self.parent / "manifest.json")
        parent_saved_sha = S.sha256(self.parent / "saved.json")
        parent_ledger_sha = S.sha256(self.parent / "batch-scenewriter.sqlite")
        self.scratch.write_bytes(b"unattributed later save on original")
        target_pln = self.base / "reopen-snapshot.pln"
        target_state = self.base / "reopen-state"
        result = S.stage_readonly_reopen(
            self.parent, target_pln, target_state, 19727)
        self.assertEqual(result["status"],
                         "SNAPSHOT_ONLY_READBACK_NO_MODEL_WRITES")
        self.assertEqual(result["nativeCalls"], 0)
        self.assertEqual(S.sha256(target_pln), self.saved_sha)
        self.assertEqual(S.sha256(self.parent / "saved.json"),
                         parent_saved_sha)
        self.assertEqual(S.sha256(self.parent / "manifest.json"),
                         parent_manifest_sha)
        self.assertEqual(S.sha256(self.parent / "batch-scenewriter.sqlite"),
                         parent_ledger_sha)
        derivative = json.loads(
            (target_state / "manifest.json").read_text(encoding="utf8"))
        self.assertTrue(derivative["snapshotVerificationOnly"])
        self.assertEqual(derivative["scratch"], str(target_pln))
        self.assertEqual(derivative["port"], 19727)
        self.assertTrue((target_state / "attempted.json").is_file())
        self.assertTrue((target_state / "batch-scenewriter.sqlite").is_file())
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_SOURCE_DRIFT"):
            B.validate_stage(target_state, allow_plan=True)

    def test_derivation_fails_if_snapshot_hash_or_parent_evidence_changed(self):
        self._saved_parent()
        (self.parent / "guarded-save.snapshot").write_bytes(b"bad snapshot")
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_AND_PARENT"):
            S.stage_readonly_reopen(
                self.parent, self.base / "reopen.pln",
                self.base / "state2", 19727)

    def test_derivation_requires_one_shot_forensic_receipts(self):
        self._saved_parent()
        (self.parent / "attempted.json").unlink()
        with self.assertRaisesRegex(ValueError, "FORENSICS_REQUIRED"):
            S.stage_readonly_reopen(
                self.parent, self.base / "reopen.pln",
                self.base / "state2", 19727)

    def test_derivation_rejects_existing_destination(self):
        self._saved_parent()
        target = self.base / "reopen.pln"
        target.write_text("already exists")
        with self.assertRaisesRegex(ValueError, "FRESH_COPY"):
            S.stage_readonly_reopen(
                self.parent, target, self.base / "state2", 19727)

    def test_derivation_requires_manifest_saved_receipt_concordance(self):
        self._saved_parent()
        receipt = json.loads(
            (self.parent / "saved.json").read_text(encoding="utf8"))
        receipt["savedSHA256"] = "a" * 64
        (self.parent / "saved.json").write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "GUARDED_SAVE_CHAIN"):
            S.stage_readonly_reopen(
                self.parent, self.base / "reopen.pln",
                self.base / "state2", 19727)

    def test_no_native_api_or_automatic_open_in_snapshot_helper(self):
        src = (ROOT / "scripts/apa_ac29_save_isolation.py"
               ).read_text(encoding="utf8")
        batch = (ROOT / "scripts/apa_ac29_hotlink_batch_oneshot.py"
                 ).read_text(encoding="utf8")
        self.assertNotIn('api("OpenProject"', src)
        self.assertNotIn("CreateHotlinkInstances", src)
        self.assertIn("preserve_guarded_save(", batch)
        self.assertIn("lease.acquire()", batch)
        self.assertIn("lease.verify()", batch)
        self.assertIn("snapshotVerificationOnly", batch)
        self.assertIn('"confirm-open-snapshot"', batch)
        self.assertIn('"stage-snapshot-reopen"', batch)
        self.assertIn("GuardedSaveTransport(", batch)

    def test_derived_snapshot_must_be_opened_before_close_check(self):
        self._saved_parent()
        target = self.base / "reopen.pln"
        state = self.base / "state2"
        S.stage_readonly_reopen(self.parent, target, state, 19727)
        with self.assertRaises(FileNotFoundError):
            B.check_closed(state)

    def test_only_read_only_provenance_ever_created_by_derivation(self):
        self._saved_parent()
        target = self.base / "reopen.pln"
        state = self.base / "state2"
        S.stage_readonly_reopen(self.parent, target, state, 19727)
        self.assertFalse((state / "opened-before-close.json").exists())
        self.assertFalse((state / "closed.json").exists())
        self.assertFalse((state / "reopened.json").exists())
        self.assertFalse((state / "trace-write").exists())
        self.assertFalse((state / "failed.json").exists())


if __name__ == "__main__":
    unittest.main()
