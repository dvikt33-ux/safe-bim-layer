import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import closed_loop.stage4_offline_evidence as offline


class FastHistoricalRevalidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'scripts').mkdir()
        (self.root/'scripts/audit_pack.py').write_text('VERIFIER = 1\n', encoding='utf-8')
        self.pack = self.root/'outputs/history/audit-pack'
        self.pack.mkdir(parents=True)
        self.raw = self.root/'outputs/history/raw.json'
        self.raw.parent.mkdir(parents=True, exist_ok=True)
        self.raw.write_bytes(b'{"elements":[]}')

        raw_spec = {
            'path':'outputs/history/raw.json',
            'sha256':hashlib.sha256(self.raw.read_bytes()).hexdigest(),
            'bytes':self.raw.stat().st_size,
        }
        source = {
            'schemaVersion':1,
            'sourceFullDumps':[raw_spec],
            'evidenceRecords':[],
            'contract':{},
        }
        source_bytes = json.dumps(source, separators=(',', ':')).encode()
        (self.pack/'source.json').write_bytes(source_bytes)
        manifest = {
            'schemaVersion':1,
            'files':[{
                'path':'source.json',
                'sha256':hashlib.sha256(source_bytes).hexdigest(),
                'bytes':len(source_bytes),
            }],
        }
        manifest_bytes = json.dumps(manifest, separators=(',', ':')).encode()
        (self.pack/'audit-pack-manifest.json').write_bytes(manifest_bytes)

        self.baseline = {
            'scripts/audit_pack.py': (self.root/'scripts/audit_pack.py').read_bytes(),
            'outputs/history/audit-pack/source.json': source_bytes,
            'outputs/history/audit-pack/audit-pack-manifest.json': manifest_bytes,
            'outputs/closed-loop-stage4/stage4-acceptance-report.json': json.dumps({
                'stage4Status':'VERIFIED',
                'criteria':[{'required':True,'verdict':'PASS'}],
            }).encode(),
        }

    def baseline_bytes(self, path):
        return self.baseline[path]

    def run_fast(self, baseline_blob='same-blob', head_blob='same-blob', tracked_clean=True):
        def git_blob(ref, path):
            return baseline_blob if ref == offline.VERIFIED_STAGE4_BASELINE else head_blob

        with patch.object(offline, 'ROOT', self.root), \
             patch.object(offline, '_baseline_bytes', side_effect=self.baseline_bytes), \
             patch.object(offline, '_git_blob_sha', side_effect=git_blob), \
             patch.object(offline, '_tracked_file_clean', return_value=tracked_clean):
            return offline.fast_historical_verify('stageX', 'outputs/history/audit-pack')

    def test_fast_revalidation_passes_for_identical_verified_bytes(self):
        result = self.run_fast()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['provenance'], 'FAST_REVALIDATION_OF_VERIFIED_STAGE4_BASELINE')
        self.assertEqual(result['sourceFilesChecked'], 1)

    def test_fast_revalidation_rejects_changed_raw_evidence(self):
        self.raw.write_bytes(b'{"elements":[1]}')
        with self.assertRaisesRegex(RuntimeError, 'SHA/size mismatch'):
            self.run_fast()

    def test_fast_revalidation_rejects_changed_historical_verifier(self):
        with self.assertRaisesRegex(RuntimeError, 'verifier changed'):
            self.run_fast(baseline_blob='baseline', head_blob='changed')

    def test_fast_revalidation_rejects_local_verifier_edits(self):
        with self.assertRaisesRegex(RuntimeError, 'local working-tree/index changes'):
            self.run_fast(tracked_clean=False)


if __name__ == '__main__':
    unittest.main()
