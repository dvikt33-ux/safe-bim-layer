"""Run the Stage 2 offline acceptance suite and retain reviewable evidence."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import unittest

from closed_loop.models import AcceptanceContract, Action, Criterion, ExecutionResult, Fact, Observation, PlannerDecision
from closed_loop.mocks import FixtureObserver, FixtureReadBack, FixedPlanner, MockExecutor
from closed_loop.orchestrator import Orchestrator
from tests_stage2.completion_fixtures import build_case


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed.append(test.id())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New evidence directory; existing runs are preserved')
    parser.add_argument('--git-ref-evidence', type=Path, help='Captured remote-ref receipt; absent receipt cannot verify main')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    suite = unittest.defaultTestLoader.discover('tests_stage2', pattern='test_*.py')
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult).run(suite)
    (args.output / 'unit-tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    cases = [
        ('verified', [('OBSERVED', 1.0)], 'VERIFIED'),
        ('replan', [('OBSERVED', 0.5), ('OBSERVED', 1.0)], 'VERIFIED'),
        ('not-verified', [('NOT_VERIFIED', 1.0)], 'BLOCKED'),
        ('data-missing', [('DATA_MISSING', 1.0)], 'WAITING_FOR_DATA'),
        ('conflict', [('CONFLICT', 1.0)], 'BLOCKED'),
        ('transport', [('BLOCKED_BY_TRANSPORT', 1.0)], 'BLOCKED'),
        ('unknown-outcome', [], 'UNKNOWN_OUTCOME'),
        ('iteration-limit', [('OBSERVED', 0.5), ('OBSERVED', 0.5)], 'BLOCKED'),
    ]
    scenarios = []
    for name, fixtures, expected in cases:
        contract = AcceptanceContract('stage2-'+name, (Criterion('C01', True, 'length', 1.0, 1e-6, True),))
        before = Observation('fixture-model', 'before', {}, {})
        observations = [Observation('fixture-model', f'after-{i}',
            {'length': Fact(actual, status, (f'fixture.{i}',))}, {f'fixture.{i}': {'actual': actual, 'status': status}})
            for i, (status, actual) in enumerate(fixtures, 1)]
        executor = MockExecutor()
        job = Orchestrator(contract, 'Stage 2 offline acceptance fixture: '+name,
            FixtureObserver(before), FixedPlanner(PlannerDecision('PLANNED', Action('create_wall', {'length': 1.0}))),
            executor, FixtureReadBack(observations), args.output / (name+'.job.json'), max_iterations=2,
            clock=lambda: '2026-10-05T00:00:00+00:00').run()
        scenarios.append({'id': name, 'expected': expected, 'actual': job.finalStatus,
            'verdict': 'PASS' if job.finalStatus == expected else 'FAIL', 'evidenceRefs': [name+'.job.json'],
            'mockExecuteCalls': len(executor.requests), 'liveMutationAttempted': job.liveMutationAttempted})
    for name, expected in [('stale-rejected', 'BLOCKED'), ('stale-replan', 'VERIFIED'),
                           ('no-progress', 'BLOCKED'), ('changed-model', 'VERIFIED'), ('changed-audit', 'VERIFIED')]:
        orch, observer, planner, executor, check = build_case(name, args.output / (name+'.job.json'))
        job = orch.run()
        valid = job.finalStatus == expected
        if name == 'no-progress':
            valid = valid and job.terminalReason == 'BLOCKED_NO_PROGRESS' and job.iteration < job.maxIterations
        if name.startswith('stale-'):
            valid = valid and job.iterations[0].decisionInvalidated and job.iterations[0].executorResult is None
        scenarios.append({'id': name, 'expected': expected, 'actual': job.finalStatus,
            'verdict': 'PASS' if valid else 'FAIL', 'evidenceRefs': [name+'.job.json'],
            'mockExecuteCalls': len(executor.requests), 'liveMutationAttempted': job.liveMutationAttempted,
            'plannerObservedHashes': planner.observedHashes, 'terminalReason': job.terminalReason,
            'noProgressCounts': [i.noProgressCount for i in job.iterations]})
    baseline_diff = subprocess.check_output(['git', 'diff', '27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c',
        '--', 'scripts', 'archicad-addon', 'safe_bim_layer.py', 'qwen_safe_bim_integration.py'], text=True)
    stage1_diff = subprocess.check_output(['git', 'diff', '27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c',
        '--', 'outputs/closed-loop-stage1'], text=True)
    existing_tests_diff = subprocess.check_output(['git', 'diff', 'fab04cf88d3cd621faf3a9f5a6f417290417e620',
        '--', 'tests_stage2/test_orchestrator.py'], text=True)
    existing_passed = sum('.Stage2Tests.' in name for name in result.passed)
    new_passed = sum('.CompletionTests.' in name for name in result.passed)
    requirements = [
        ('S2-C01', 'Separate Orchestrator implementation exists', 'test_end_to_end_verified_and_durable_complete_trail'),
        ('S2-C02', 'Explicit state machine; permitted and forbidden transitions tested', 'test_all_declared_legal_edges_are_exercised'),
        ('S2-C03', 'Goal stored machine-readably', 'test_end_to_end_verified_and_durable_complete_trail'),
        ('S2-C04', 'Acceptance criteria machine-readable', 'test_invalid_contracts_and_parameters_are_rejected'),
        ('S2-C05', 'Auditor produces per-criterion verdicts', 'test_evidence_status_never_promoted_to_pass'),
        ('S2-C06', 'Required NOT_VERIFIED blocks VERIFIED', 'test_verified_with_nonpass_audit_is_rejected'),
        ('S2-C07', 'Correctable FAIL can lead to REPLAN', 'test_correctable_fail_replans_from_readback'),
        ('S2-C08', 'DATA_MISSING leads to WAITING_FOR_DATA', 'test_missing_check_waits_for_data'),
        ('S2-C09', 'Transport failure leads to BLOCKED', 'test_model_check_transport_failure_blocks_before_executor'),
        ('S2-C10', 'Ambiguous mutation leads to UNKNOWN_OUTCOME', 'test_executor_results_route_fail_closed'),
        ('S2-C11', 'UNKNOWN_OUTCOME cannot automatically retry', 'test_executor_timeout_is_unknown_and_never_retried'),
        ('S2-C12', 'Iteration limit works', 'test_iteration_limit_blocks_unresolved_correctable_fail'),
        ('S2-C13', 'No-progress detection works', 'test_C_repeated_identical_failure_blocks_before_iteration_limit'),
        ('S2-C14', 'Stale observation detection works', 'test_B_stale_replan_succeeds'),
        ('S2-C15', 'Full evidence trail persisted', 'test_end_to_end_verified_and_durable_complete_trail'),
        ('S2-C16', 'Typed action allowlist works', 'test_invalid_contracts_and_parameters_are_rejected'),
    ]
    criteria = [{'id': cid, 'required': True, 'expected': expected,
        'actual': any(name.endswith('.'+test) for name in result.passed),
        'verdict': 'PASS' if any(name.endswith('.'+test) for name in result.passed) else 'FAIL',
        'evidenceRefs': ['unit-tests.txt', test]} for cid, expected, test in requirements]
    criteria[1]['evidenceRefs'].append('test_all_illegal_state_edges_are_rejected')
    criteria[12]['evidenceRefs'].extend(['no-progress.job.json', 'changed-model.job.json', 'changed-audit.job.json'])
    criteria[13]['evidenceRefs'].extend(['stale-rejected.job.json', 'stale-replan.job.json'])
    criteria.append({'id': 'S2-C17', 'required': True, 'expected': 'All Stage 2 tests PASS; 33 existing tests unchanged',
        'actual': {'existingPassed': existing_passed, 'newPassed': new_passed, 'existingTestsDiff': existing_tests_diff},
        'verdict': 'PASS' if result.wasSuccessful() and existing_passed == 33 and new_passed >= 5 and not existing_tests_diff else 'FAIL',
        'evidenceRefs': ['unit-tests.txt']})
    criteria.append({'id': 'S2-C18', 'required': True, 'expected': 'V0 runtime path unchanged',
        'actual': {'diff': baseline_diff}, 'verdict': 'PASS' if not baseline_diff else 'FAIL',
        'evidenceRefs': ['git diff 27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c -- scripts archicad-addon safe_bim_layer.py qwen_safe_bim_integration.py']})
    criteria.append({'id': 'S2-C19', 'required': True, 'expected': 'Stage 1 evidence unchanged',
        'actual': {'diff': stage1_diff}, 'verdict': 'PASS' if not stage1_diff else 'FAIL',
        'evidenceRefs': ['git diff 27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c -- outputs/closed-loop-stage1']})
    receipt = json.loads(args.git_ref_evidence.read_text(encoding='utf-8-sig')) if args.git_ref_evidence else None
    if receipt:
        (args.output / 'git-refs.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    main_current = next((line.split()[0] for line in receipt['remoteRefs'] if line.endswith('refs/heads/main')), None) if receipt else None
    criteria.append({'id': 'S2-C20', 'required': True, 'expected': 'main unchanged',
        'actual': {'before': receipt['mainBefore'] if receipt else None, 'current': main_current},
        'verdict': 'PASS' if receipt and main_current == receipt['mainBefore'] else ('NOT_VERIFIED' if not receipt else 'FAIL'),
        'evidenceRefs': ['git-refs.json']})
    status = 'PASS' if result.wasSuccessful() and all(s['verdict'] == 'PASS' for s in scenarios) and all(c['verdict'] == 'PASS' for c in criteria) else 'FAIL'
    report = {'stage': 'STAGE_2_ORCHESTRATOR_SKELETON', 'status': status, 'executionMode': 'OFFLINE',
        'stage1Commit': '27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c',
        'v0Baseline': '565ea2e0414a14bedbca09999690d7b97f877fa3',
        'liveMutationAttempted': False, 'liveRegressionRerun': False,
        'testsRun': result.testsRun, 'testsPassed': result.passed,
        'existingTestsPassed': existing_passed, 'newTestsPassed': new_passed, 'existingTestsUnchanged': not existing_tests_diff,
        'failures': [{'test': t.id(), 'traceback': tb} for t, tb in result.failures],
        'errors': [{'test': t.id(), 'traceback': tb} for t, tb in result.errors],
        'criteria': criteria, 'requiredSummary': {verdict: sum(c['verdict'] == verdict for c in criteria) for verdict in ('PASS', 'FAIL', 'NOT_VERIFIED')},
        'scenarios': scenarios, 'blockingIssues': [] if status == 'PASS' else ['Offline acceptance failed']}
    (args.output / 'stage2-verification-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'stage': report['stage'], 'status': status, 'testsRun': result.testsRun,
        'scenarios': len(scenarios), 'liveMutationAttempted': False}, indent=2))
    if status != 'PASS':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
