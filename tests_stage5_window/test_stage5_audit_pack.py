import json
from pathlib import Path
import tempfile
import unittest

from closed_loop.live_wall import ROOT
from closed_loop.stage5_audit_pack import finish_pack
from tests_stage5_window.test_window_attempts import fixture


class Stage5AuditPackTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'work').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='stage5-pack-test-', dir=ROOT/'work')
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        before, after, _, _ = fixture()

        observe = self.output/'session'/'observations'/'001-observe.json'
        executor = self.output/'session'/'iteration-1'/'executor'
        readback = self.output/'session'/'observations'/'002-read-back.json'
        observe.parent.mkdir(parents=True)
        executor.mkdir(parents=True)
        for path, value in (
            (observe, before),
            (executor/'before.json', before),
            (executor/'after-create.json', after),
            (readback, after),
        ):
            path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

        job = {
            'iterations':[{
                'iteration':1,
                'executorRequest':{
                    'type':'create_window',
                    'parameters':{
                        'sourceGuid':'host','centerOffset':5.0,'sillHeight':0.9,
                        'width':1.2,'height':1.5,
                    },
                },
                'readback':{
                    'evidence':{
                        'live.snapshot':{
                            'path':str(readback.resolve()),
                            'modelHash':'synthetic',
                            'elementCount':2,
                        },
                    },
                },
            }],
        }
        (self.output/'job.json').write_text(json.dumps(job), encoding='utf-8')
        (self.output/'verification-report.json').write_text(
            json.dumps({'status':'PASS','physicalMutationCalls':1}), encoding='utf-8')

    def test_stage5_pack_builds_and_independently_verifies(self):
        result = finish_pack(self.output, 'fixture.pln')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['sourceShaVerification'], 'PASS')
        self.assertEqual(result['semanticDelta'], 'PASS')
        self.assertTrue((self.output/'audit-pack'/'source.json').is_file())
        self.assertTrue((self.output/'audit-pack-verification.json').is_file())


if __name__ == '__main__':
    unittest.main()
