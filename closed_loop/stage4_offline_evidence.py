"""Persist actual deterministic fault-test artifacts; never label fixtures live."""
import argparse
import contextlib
import io
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import subprocess
import unittest

from .live_wall import ROOT, COMMAND, read
from .wall_attempts import durable_json
from .stage4_preflight import IMPLEMENTATION_FILES
from scripts.stage4_audit_pack import source_contract, build_pack, verify_pack


VERIFIED_STAGE4_BASELINE = 'faf2fd8adcfd3329ae77a137b37f739a9a462225'


def _baseline_bytes(path):
    try:
        return subprocess.check_output(
            ['git', 'show', VERIFIED_STAGE4_BASELINE + ':' + path],
            cwd=ROOT, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError('Verified baseline path unavailable: '+path) from exc


def _baseline_sha256(path):
    return hashlib.sha256(_baseline_bytes(path)).hexdigest()


def _check_spec(spec):
    path = ROOT / spec['path']
    if not path.is_file():
        raise RuntimeError('Historical source missing: '+spec['path'])
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    actual = {'sha256': h.hexdigest(), 'bytes': path.stat().st_size}
    expected = {'sha256': spec['sha256'], 'bytes': spec['bytes']}
    if actual != expected:
        raise RuntimeError('Historical source SHA/size mismatch: '+spec['path'])
    return actual['bytes']


def fast_historical_verify(stage, pack_path):
    """Reuse the accepted semantic PASS only for identical verifier + pinned bytes."""
    started = time.perf_counter()
    pack = ROOT / pack_path
    source_path = pack / 'source.json'
    manifest_path = pack / 'audit-pack-manifest.json'
    if not source_path.is_file() or not manifest_path.is_file():
        raise RuntimeError('Historical Audit Pack missing')

    # Semantic reuse is only authorized when the historical verifier itself is
    # byte-identical to the VERIFIED Stage-4 milestone.
    verifier_path = 'scripts/audit_pack.py'
    current_verifier = hashlib.sha256((ROOT/verifier_path).read_bytes()).hexdigest()
    baseline_verifier = _baseline_sha256(verifier_path)
    if current_verifier != baseline_verifier:
        raise RuntimeError('Historical verifier changed since VERIFIED baseline')

    # The compact pack contract/manifests must be exactly the ones accepted at
    # the VERIFIED milestone; this prevents a self-consistent local rewrite.
    source_rel = source_path.relative_to(ROOT).as_posix()
    manifest_rel = manifest_path.relative_to(ROOT).as_posix()
    if source_path.read_bytes() != _baseline_bytes(source_rel):
        raise RuntimeError('Historical source contract differs from VERIFIED baseline')
    if manifest_path.read_bytes() != _baseline_bytes(manifest_rel):
        raise RuntimeError('Historical Audit Pack manifest differs from VERIFIED baseline')

    baseline_acceptance = json.loads(_baseline_bytes(
        'outputs/closed-loop-stage4/stage4-acceptance-report.json').decode('utf-8'))
    if (baseline_acceptance.get('stage4Status') != 'VERIFIED' or
            any(row.get('verdict') != 'PASS'
                for row in baseline_acceptance.get('criteria', []) if row.get('required'))):
        raise RuntimeError('Verified Stage-4 acceptance anchor is not PASS')

    source = json.loads(source_path.read_text(encoding='utf-8'))
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

    # Re-hash every raw source/evidence record referenced by the accepted
    # source contract. This is linear byte I/O only: no JSON parse of 100-MiB
    # dumps, no element indexing and no geometry re-extraction.
    specs = {}
    for spec in source.get('sourceFullDumps', []):
        specs[spec['path']] = spec
    for spec in source.get('evidenceRecords', []):
        specs[spec['path']] = spec
    contract = source.get('contract', {})
    for key in ('historicalManifest', 'identityEvidence'):
        spec = contract.get(key)
        if spec:
            specs[spec['path']] = spec
    for snapshot in contract.get('snapshots', []):
        specs[snapshot['path']] = snapshot
        fp = snapshot.get('fingerprint')
        if fp:
            specs[fp['path']] = fp
    for step in contract.get('iterations', []):
        for spec in step.get('compactEvidence', []):
            specs[spec['path']] = spec

    source_bytes = sum(_check_spec(spec) for spec in specs.values())

    # Check every compact derived pack file against the accepted pack manifest.
    pack_bytes = 0
    listed = set()
    for spec in manifest.get('files', []):
        listed.add(spec['path'])
        path = pack / spec['path']
        if not path.is_file():
            raise RuntimeError('Historical pack file missing: '+spec['path'])
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        if h != spec['sha256'] or path.stat().st_size != spec['bytes']:
            raise RuntimeError('Historical pack SHA/size mismatch: '+spec['path'])
        pack_bytes += spec['bytes']
    actual = {p.relative_to(pack).as_posix() for p in pack.rglob('*') if p.is_file()}
    if actual != listed | {'audit-pack-manifest.json'}:
        raise RuntimeError('Historical pack file set mismatch')

    elapsed = time.perf_counter() - started
    return {
        'status':'PASS',
        'provenance':'FAST_REVALIDATION_OF_VERIFIED_STAGE4_BASELINE',
        'historicalStage':stage,
        'baselineCommit':VERIFIED_STAGE4_BASELINE,
        'verifierSha256':current_verifier,
        'sourceFilesChecked':len(specs),
        'sourceBytesHashed':source_bytes,
        'packFilesChecked':len(listed),
        'packBytesHashed':pack_bytes,
        'seconds':round(elapsed, 3),
    }


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
    parser.add_argument('--full-historical', action='store_true',
                        help='Force full Stage 1/3 semantic re-extraction instead of fast verified-baseline revalidation')
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
    live_env = {name: os.environ.pop(name, None) for name in
        ('SAFE_BIM_STAGE4_PROJECT_PATH','SAFE_BIM_STAGE4_FIXTURE_REPORT')}
    try:
        for folder in ('tests_stage2','tests_stage3','tests_audit_pack','tests_stage4_live'):
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
                    unittest.TestLoader().discover(str(ROOT/folder)))
            counts[folder] = {'testsRun':result.testsRun,'status':'PASS' if result.wasSuccessful() else 'FAIL',
                              'failures':len(result.failures),'errors':len(result.errors)}
            if not result.wasSuccessful():
                (output/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
                raise RuntimeError('Test failure; no scenario or live execution allowed')
    finally:
        for name, value in live_env.items():
            if value is not None:
                os.environ[name] = value
            else:
                os.environ.pop(name, None)
    (output/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    from scripts.audit_pack import verify_pack as verify_historical
    archived = {}
    historical_timings = {}
    for key, path in (('stage1','outputs/closed-loop-stage1/audit-pack'),
                      ('stage3','outputs/closed-loop-stage3/run-002/audit-pack')):
        phase = time.perf_counter()
        if args.full_historical:
            print('Full recompute '+key+' archived source SHA/geometry proof',flush=True)
            archived[key] = verify_historical(ROOT,ROOT/path)
        else:
            print('Fast revalidating '+key+' archived verified evidence',flush=True)
            try:
                archived[key] = fast_historical_verify(key, path)
            except Exception as exc:
                print('Fast revalidation unavailable ('+str(exc)+'); falling back to full recompute',flush=True)
                archived[key] = verify_historical(ROOT,ROOT/path)
                archived[key]['provenance'] = 'FULL_RECOMPUTE_FALLBACK'
                archived[key]['fastRevalidationError'] = str(exc)
        historical_timings[key] = round(time.perf_counter()-phase, 3)
        if archived[key]['status'] != 'PASS':
            raise RuntimeError('Historical live baseline failed')
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
        'newTests':counts['tests_stage4_live']['testsRun'],'scenarios':rows,'physicalMutationCalls':0,
        'archivedRegressions':archived,'historicalTimingsSeconds':historical_timings,
        'mandatoryLiveScenarios':'NOT_VERIFIED','stage4Status':'BLOCKED','stage5Started':False,
        'implementationFiles':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in IMPLEMENTATION_FILES]})
    print('Offline proof PASS; mandatory live remains NOT_VERIFIED',flush=True)


if __name__ == '__main__': main()
