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
    baseline_diff = subprocess.check_output(['git', 'diff', '27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c',
        '--', 'scripts', 'archicad-addon', 'safe_bim_layer.py', 'qwen_safe_bim_integration.py'], text=True)
    status = 'PASS' if result.wasSuccessful() and all(s['verdict'] == 'PASS' for s in scenarios) and not baseline_diff else 'FAIL'
    requirements = [
        ('S2-C01', 'Single goal, typed acceptance contract and serialized job', 'test_end_to_end_verified_and_durable_complete_trail'),
        ('S2-C02', 'Required legal transitions exercised', 'test_all_declared_legal_edges_are_exercised'),
        ('S2-C03', 'All illegal transitions rejected', 'test_all_illegal_state_edges_are_rejected'),
        ('S2-C04', 'NOT_VERIFIED and DATA_MISSING never promoted', 'test_evidence_status_never_promoted_to_pass'),
        ('S2-C05', 'UNKNOWN_OUTCOME cannot automatically retry', 'test_executor_timeout_is_unknown_and_never_retried'),
        ('S2-C06', 'Terminal BLOCKED cannot become VERIFIED', 'test_all_terminal_states_cannot_transition_or_run'),
        ('S2-C07', 'Full evidence persisted before execution and at completion', 'test_execution_request_is_saved_before_interface_call'),
        ('S2-C08', 'Explicit iteration limit blocks unresolved acceptance', 'test_iteration_limit_blocks_unresolved_correctable_fail'),
        ('S2-C09', 'Stage 2 rejects live interfaces and provenance', 'test_live_component_and_live_payload_are_rejected'),
    ]
    criteria = [{'id': cid, 'required': True, 'expected': expected,
        'actual': any(name.endswith('.'+test) for name in result.passed),
        'verdict': 'PASS' if any(name.endswith('.'+test) for name in result.passed) else 'FAIL',
        'evidenceRefs': ['unit-tests.txt', test]} for cid, expected, test in requirements]
    criteria.append({'id': 'S2-C10', 'required': True, 'expected': 'Stage 1 v0 path unchanged',
        'actual': {'diff': baseline_diff}, 'verdict': 'PASS' if not baseline_diff else 'FAIL',
        'evidenceRefs': ['git diff 27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c -- scripts archicad-addon safe_bim_layer.py qwen_safe_bim_integration.py']})
    report = {'stage': 'STAGE_2_ORCHESTRATOR_SKELETON', 'status': status, 'executionMode': 'OFFLINE',
        'stage1Commit': '27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c',
        'v0Baseline': '565ea2e0414a14bedbca09999690d7b97f877fa3',
        'liveMutationAttempted': False, 'liveRegressionRerun': False,
        'testsRun': result.testsRun, 'testsPassed': result.passed,
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
