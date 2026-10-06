"""Persist actual deterministic fault-test artifacts; never label fixtures live."""
import argparse
import io
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from .live_wall import ROOT, COMMAND, read
from .wall_attempts import durable_json
from .stage4_preflight import IMPLEMENTATION_FILES
from scripts.stage4_audit_pack import source_contract, build_pack, verify_pack


def run_fixture(output, scenario_id, case_class, method):
    directory = output / scenario_id
    directory.mkdir()
    case = case_class(method)
    try:
        case.setUp()
        getattr(case, method)()
        root = Path(case.temp.name)
        for path in root.rglob('*'):
            if path.is_file():
                target = directory / path.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        job = read(directory / 'job.json')
        snapshots = []
        for number, step in enumerate(job['iterations'], 1):
            for role in ('observation', 'readback'):
                value = step.get(role)
                if value and 'readback' in value['evidence'] and 'model' in value['evidence']['readback']:
                    path = directory / 'iterations' / f'{number:03}-{role}.json'
                    durable_json(path, value['evidence']['readback']['model'])
                    snapshots.append(path)
        pairs = [(a,b) for a,b in zip(snapshots, snapshots[1:])]
        attempts = job.get('mutationAttempts', [])
        journals = list(directory.glob('attempts/*.json'))
        durable_json(directory/'goal.json', {'scenarioId': scenario_id, 'provenance': 'OFFLINE_FIXTURE',
            'command': COMMAND, 'fixtureTest': case.id(), 'physicalMutationCalls': 0})
        durable_json(directory/'preflight.json', {'status':'PASS','provenance':'OFFLINE_FIXTURE',
            'networkUsed':False,'archicadAccessed':False})
        durable_json(directory/'mutation-attempts.json', attempts)
        durable_json(directory/'reconciliation.json', [a['reconciliationEvidence'] for a in attempts if a['reconciliationStatus']])
        ids = [a['mutationAttemptId'] for a in attempts]
        report = {'scenarioId':scenario_id,'status':'PASS','provenance':'OFFLINE_FIXTURE','liveVerdict':'NOT_RUN',
            'test':case.id(),'expectedFailureIsSuccessfulProof':job['finalStatus'] != 'VERIFIED',
            'jobFinalStatus':job['finalStatus'],'terminalReason':job['terminalReason'],
            'physicalMutationCalls':0,'simulatedNativeCalls':sum(read(p)['nativeCalls'] for p in journals),
            'mutationAttemptIds':ids,'duplicateMutationCount':len(ids)-len(set(ids)),
            'reconciliationOutcomes':[a['reconciliationStatus'] for a in attempts if a['reconciliationStatus']],
            'recoveredFromCrash':job.get('recoveredFromCrash',False), 'auditPackStatus':'PENDING'}
        durable_json(directory/'verification-report.json', report)
        records = sorted(directory.rglob('*.json'))
        contract = source_contract(ROOT, directory, snapshots, pairs, records,
                                   job['observedModelIdentity'] or 'fixture-model', 'OFFLINE_FIXTURE')
        build_pack(ROOT, contract, directory/'audit-pack')
        verification = verify_pack(ROOT, directory/'audit-pack')
        durable_json(directory/'audit-pack-verification.json', verification)
        # Keep the source-pinned report unchanged; its independent pack receipt
        # carries PASS after build to avoid circular source/manfiest hashes.
        report['auditPackStatus'] = verification['status']
        return report
    finally:
        case.doCleanups()


def main():
    from tests_stage4_live.test_attempts import RecoveryTests
    from tests_stage4_live.test_guards import LivePathGuardTests
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'outputs/closed-loop-stage4'):
        raise ValueError('Dedicated repository Stage 4 output required')
    output.mkdir(parents=True, exist_ok=False)
    tempfile.tempdir = str(ROOT/'work/stage4-live-temp')
    Path(tempfile.tempdir).mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    counts = {}
    # Offline proof must be hermetic: never inherit the operator's live PLN
    # binding from the shell. Tests that exercise rebinding opt in explicitly.
    live_binding = os.environ.pop('SAFE_BIM_STAGE4_PROJECT_PATH', None)
    try:
        for folder in ('tests_stage2','tests_stage3','tests_audit_pack','tests_stage4_live'):
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestLoader().discover(str(ROOT/folder)))
            counts[folder] = {'testsRun':result.testsRun,'status':'PASS' if result.wasSuccessful() else 'FAIL',
                              'failures':len(result.failures),'errors':len(result.errors)}
            if not result.wasSuccessful():
                (output/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
                raise RuntimeError('Test failure; no scenario or live execution allowed')
    finally:
        if live_binding is not None:
            os.environ['SAFE_BIM_STAGE4_PROJECT_PATH'] = live_binding
    (output/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    from scripts.audit_pack import verify_pack as verify_historical
    archived = {}
    for key, path in (('stage1','outputs/closed-loop-stage1/audit-pack'),
                      ('stage3','outputs/closed-loop-stage3/run-002/audit-pack')):
        print('Recomputing '+key+' archived source SHA/geometry proof',flush=True)
        archived[key] = verify_historical(ROOT,ROOT/path)
        if archived[key]['status'] != 'PASS': raise RuntimeError('Historical live baseline failed')
        durable_json(output/(key+'-archived-regression.json'),archived[key])
    cases = [('S4-04',RecoveryTests,'test_not_applied_requires_new_observation_plan_and_new_attempt_id'),
             ('S4-05',RecoveryTests,'test_ambiguous_recovery_blocks_without_execute'),
             ('S4-06-offline',RecoveryTests,'test_crash_checkpoint_restores_without_repeating_first_mutation'),
             ('S4-07',LivePathGuardTests,'test_no_progress_is_independent_and_blocks_in_live_adapter_path'),
             ('S4-08',LivePathGuardTests,'test_iteration_limit_with_changing_live_adapter_fingerprint'),
             ('S4-09',RecoveryTests,'test_pre_native_transport_failure_is_blocked_not_unknown'),
             ('S4-10',RecoveryTests,'test_confirmed_response_with_missing_readback_never_verifies')]
    rows = []
    for scenario_id, case_class, method in cases:
        print('Saving '+scenario_id+' OFFLINE_FIXTURE evidence',flush=True)
        rows.append(run_fixture(output,scenario_id,case_class,method))
    durable_json(output/'offline-verification-report.json', {'status':'PASS','provenance':'OFFLINE_FIXTURE',
        'tests':counts,'oldTests':sum(counts[k]['testsRun'] for k in ('tests_stage2','tests_stage3','tests_audit_pack')),
        'newTests':counts['tests_stage4_live']['testsRun'],'scenarios':rows,'physicalMutationCalls':0,'archivedRegressions':archived,
        'mandatoryLiveScenarios':'NOT_VERIFIED','stage4Status':'BLOCKED','stage5Started':False,
        'implementationFiles':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in IMPLEMENTATION_FILES]})
    print('Offline proof PASS; mandatory live remains NOT_VERIFIED',flush=True)


if __name__ == '__main__': main()
