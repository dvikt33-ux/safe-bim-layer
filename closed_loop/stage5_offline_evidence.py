"""Source-persisted Stage 5 offline gate. Never performs Archicad mutation."""
import argparse
import contextlib
import hashlib
import io
import os
from pathlib import Path
import tempfile
import time
import unittest

from .live_wall import ROOT, read
from .wall_attempts import durable_json
from .stage4_offline_evidence import fast_historical_verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'outputs/closed-loop-stage5'):
        raise ValueError('Stage 5 output must be under outputs/closed-loop-stage5')
    output.mkdir(parents=True, exist_ok=False)

    started = time.perf_counter()
    stream = io.StringIO()
    counts = {}
    env_names = (
        'SAFE_BIM_STAGE4_PROJECT_PATH','SAFE_BIM_STAGE4_FIXTURE_REPORT',
        'SAFE_BIM_STAGE5_PROJECT_PATH',
    )
    saved_env = {name:os.environ.pop(name, None) for name in env_names}
    try:
        for folder in (
            'tests_stage2','tests_stage3','tests_audit_pack',
            'tests_stage4_live','tests_stage5_window',
        ):
            phase = time.perf_counter()
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
                    unittest.TestLoader().discover(str(ROOT/folder)))
            counts[folder] = {
                'testsRun':result.testsRun,
                'status':'PASS' if result.wasSuccessful() else 'FAIL',
                'failures':len(result.failures),
                'errors':len(result.errors),
                'seconds':round(time.perf_counter()-phase, 3),
            }
            if not result.wasSuccessful():
                (output/'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
                raise RuntimeError('Stage 5 offline tests failed')
    finally:
        for name,value in saved_env.items():
            if value is not None:
                os.environ[name]=value
            else:
                os.environ.pop(name, None)

    (output/'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    print('Stage 2-5 regression tests PASS', flush=True)

    archived = {}
    for key,path in (
        ('stage1','outputs/closed-loop-stage1/audit-pack'),
        ('stage3','outputs/closed-loop-stage3/run-002/audit-pack'),
    ):
        phase=time.perf_counter()
        archived[key]=fast_historical_verify(key,path)
        archived[key]['wallSeconds']=round(time.perf_counter()-phase,3)
        print(key+' historical evidence PASS in '+str(archived[key]['wallSeconds'])+'s', flush=True)

    performance = read(ROOT/'outputs/closed-loop-stage4/stage4-performance-acceptance.json')
    if performance.get('status') != 'PASS':
        raise RuntimeError('Verified Stage 4 performance baseline is not PASS')

    implementation = (
        'closed_loop/models.py',
        'closed_loop/live_wall.py',
        'closed_loop/window_attempts.py',
        'closed_loop/live_window.py',
        'closed_loop/stage5_window_scenario.py',
        'scripts/archicad_executor.py',
    )
    report = {
        'status':'PASS',
        'provenance':'OFFLINE_FIXTURE',
        'physicalMutationCalls':0,
        'tests':counts,
        'stage5Tests':counts['tests_stage5_window']['testsRun'],
        'archivedRegressions':archived,
        'stage4PerformanceBaseline':'PASS',
        'stage5Status':'NOT_VERIFIED',
        'mandatoryLiveHostedWindow':'NOT_VERIFIED',
        'totalSeconds':round(time.perf_counter()-started,3),
        'implementationFiles':[
            {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
            for path in implementation
        ],
    }
    durable_json(output/'offline-verification-report.json',report)
    print('Stage 5 offline proof PASS in '+str(report['totalSeconds'])+
          's; LIVE Hosted Window remains NOT_VERIFIED', flush=True)


if __name__ == '__main__':
    main()
