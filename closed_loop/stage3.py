"""Explicit Stage 3 command: offline regression, v0 regression, then one live goal."""
import argparse
from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import unittest

from .live_wall import (ROOT, COMMAND, DESCRIPTIONS, LiveSession, LiveObserver, LivePlanner, LiveModelCheck,
    LiveExecutor, LiveReadBack, acceptance, load, save, read, verify_wall)
from .orchestrator import Orchestrator


def offline(output):
    stream = io.StringIO()
    suite = unittest.TestSuite([unittest.TestLoader().discover('tests_stage2', pattern='test_*.py'),
                              unittest.TestLoader().discover('tests_stage3', pattern='test_*.py')])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (output/'offline-tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    report = {'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'testsRun': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'provenance': 'OFFLINE_UNIT_TESTS'}
    save(output/'offline-report.json', report)
    if not result.wasSuccessful(): raise RuntimeError('Offline regression failed; live writes prohibited')
    return report


def v0_regression(output, offline_report):
    session = LiveSession(output, 'stage3-v0-regression', offline_report, {})
    rows = []
    for number, length in enumerate((1.0, 0.5), 1):
        session.check_identity()
        step = output/f'iteration-{number}'
        step.mkdir()
        os.environ['SAFE_BIM_MVP_EVIDENCE'] = str(step)
        chat = load('stage3_original_chat', 'scripts/archicad_chat_executor.py')
        # Independent baseline regression only; the actual Stage 3 job below
        # receives one goal and never invokes two chat.run user commands.
        instruction = f'Продолжи последнюю созданную стену ещё на {length} метра.'
        data, metrics = chat.current_dump()
        plan = chat.instruction_to_request(instruction, 'execute', data)
        if plan['status'] != 'PLANNED': raise RuntimeError(plan)
        if rows and plan['selectedGuid'].lower() != rows[0]['createdGuid'].lower():
            raise RuntimeError('Baseline regression automatic source does not match created Wall')
        response = chat.run(instruction, 'execute')
        save(step/'adapter-result.json', response)
        if response.get('status') != 'PASS': raise RuntimeError('Baseline executor outcome not proven; stop without retry')
        before = read(step/'executor/before.json')
        after, path, signature = session.snapshot('regression-readback')
        witness = verify_wall(before, after, response['executorResult'], response['selectedGuid'], length)
        if rows and witness['sourceGuid'].lower() != rows[0]['createdGuid'].lower():
            raise RuntimeError('Baseline dependency differs from actual first created GUID')
        save(step/'readback-witness.json', witness)
        rows.append({k: v for k, v in witness.items() if k not in ('sourceBefore', 'sourceAfter', 'createdWall')})
        save(step/'summary.json', rows[-1])
        print(f'v0 regression iteration {number}: PASS', flush=True)
    report = {'status': 'PASS', 'iterations': rows, 'dependencyMatches': rows[1]['sourceGuid'] == rows[0]['createdGuid'],
              'executionPath': 'unchanged scripts/archicad_chat_executor.py run -> scripts/archicad_executor.py'}
    save(output/'v0-regression-report.json', report)
    return report


def manifest(output):
    entries = []
    local = []
    for path in sorted(output.rglob('*')):
        if not path.is_file() or path.name == 'manifest.json': continue
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024*1024), b''): digest.update(chunk)
        is_local = path.stat().st_size > 1_000_000
        relative = path.relative_to(ROOT).as_posix()
        entries.append({'path': relative, 'absolutePath': str(path.resolve()), 'bytes': path.stat().st_size,
                        'sha256': digest.hexdigest(), 'storage': 'LOCAL_ONLY' if is_local else 'COMMITTED'})
        if is_local: local.append('/'+relative)
    save(output/'manifest.json', {'algorithm': 'SHA-256', 'files': entries})
    with (ROOT/'.git/info/exclude').open('a', encoding='utf-8') as stream:
        stream.write('\n'+'\n'.join(local)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--goal', required=True)
    parser.add_argument('--live', action='store_true', required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT): raise ValueError('Evidence must stay in the authorized repository')
    if args.goal != COMMAND: raise ValueError('This Stage 3 entry point accepts only the specified two-segment goal')
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output/'goal.json', {'goalId': 'stage3-live-wall-001', 'command': args.goal, 'userCommandCount': 1})
    try:
        tests = offline(args.output)
        regression = v0_regression(args.output/'v0-regression', tests)
        session = LiveSession(args.output/'live-job', 'stage3-live-wall-001', tests, regression)
        contract = acceptance(session.goal_id)
        save(args.output/'acceptance-contract.json', asdict(contract))
        job = Orchestrator(contract, args.goal, LiveObserver(session), LivePlanner(session), LiveExecutor(session),
            LiveReadBack(session), args.output/'job.json', max_iterations=5, no_progress_limit=2,
            model_check=LiveModelCheck(session), execution_mode='LIVE').run()
        criteria = [asdict(c) | {'description': DESCRIPTIONS[int(c.id[1:])-1]} for c in (job.auditHistory[-1] if job.auditHistory else [])]
        if len(criteria) < 24:
            criteria = [{'id': f'C{i:02}', 'required': True, 'expected': True, 'actual': None,
                         'verdict': 'NOT_VERIFIED', 'evidenceRefs': ['job.json'], 'description': description}
                        for i, description in enumerate(DESCRIPTIONS, 1)]
        status = 'PASS' if job.finalStatus == 'VERIFIED' and len(session.rows) == 2 and all(c['verdict'] == 'PASS' for c in criteria) else (job.finalStatus or 'BLOCKED')
        report = {'stage': 'STAGE_3_LIVE_WALL_CLOSED_LOOP', 'status': status, 'goalId': session.goal_id,
            'command': args.goal, 'userCommandCount': 1, 'branch': subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
            'preflight': read(session.output/'preflight.json'), 'iterations': session.rows, 'criteria': criteria,
            'requiredSummary': {verdict: sum(c['verdict'] == verdict for c in criteria) for verdict in ('PASS','FAIL','NOT_VERIFIED')},
            'dependencyMatches': len(session.rows) == 2 and session.rows[1]['sourceGuid'] == session.rows[0]['createdGuid'],
            'offline': tests, 'v0Regression': regression, 'terminalReason': job.terminalReason,
            'blockingIssues': [] if status == 'PASS' else [job.terminalReason],
            'backlog': ['Stage 4, recovery and all other BIM capabilities remain deferred.'],
            'plnSaveExecuted': False}
        save(args.output/'stage3-verification-report.json', report)
        print(json.dumps({'status': status, 'iterations': session.rows, 'requiredSummary': report['requiredSummary']},ensure_ascii=False),flush=True)
    except Exception as exc:
        # Never replay a partially executed baseline regression or live job.
        dispatched = any(args.output.rglob('executor-create_wall.request.json')) or any(args.output.rglob('native-dispatch.json'))
        save(args.output/'blocked-report.json', {'status': 'UNKNOWN_OUTCOME' if dispatched else 'BLOCKED', 'reason': f'{type(exc).__name__}: {exc}',
            'automaticRetry': False, 'note': 'Inspect retained native receipts/read-back before any new write.'})
        raise
    finally:
        manifest(args.output)


if __name__ == '__main__': main()
