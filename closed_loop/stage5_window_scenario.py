"""Stage 5 Hosted Window scenario. Planning is read-only unless --execute is explicit."""
import argparse
from dataclasses import asdict
import os
from pathlib import Path
from types import SimpleNamespace

from .live_wall import ROOT, save
from .live_window import (
    WindowExecutor, WindowModelCheck, WindowObserver, WindowPlanner,
    WindowReadBack, WindowSession, acceptance,
)
from .orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true',
                        help='Perform the single CreateWindows mutation. Without this flag the command is read-only.')
    args = parser.parse_args()

    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'outputs/closed-loop-stage5'):
        raise ValueError('Stage 5 output must be under outputs/closed-loop-stage5')
    if output.exists():
        raise FileExistsError('Stage 5 evidence output must be new')
    if not os.environ.get('SAFE_BIM_STAGE5_PROJECT_PATH'):
        raise ValueError('SAFE_BIM_STAGE5_PROJECT_PATH must explicitly bind the disposable/test PLN')

    goal_id = 'stage5-hosted-window-001'
    session = WindowSession(output/'session', goal_id)
    observer = WindowObserver(session)
    planner = WindowPlanner(session)

    if not args.execute:
        observed = observer.observe()
        decision = planner.plan(SimpleNamespace(iteration=1, goalId=goal_id), observed)
        report = {
            'status':'PLANNED' if decision.status == 'PLANNED' else 'BLOCKED',
            'executionMode':'PLAN_ONLY',
            'physicalMutationCalls':0,
            'goalId':goal_id,
            'modelIdentity':observed.modelIdentity,
            'modelHash':observed.modelHash,
            'plannerDecision':asdict(decision),
            'stage5Status':'NOT_VERIFIED',
        }
        save(output/'plan-only-report.json', report)
        print(report)
        return

    executor = WindowExecutor(session)
    reader = WindowReadBack(session)
    checker = WindowModelCheck(session)
    orch = Orchestrator(
        acceptance(goal_id),
        'Create exactly one model-bound Hosted Window and verify factual host/aperture geometry.',
        observer, planner, executor, reader,
        output/'job.json',
        max_iterations=2,
        model_check=checker,
        execution_mode='LIVE',
    )
    job = orch.run()
    report = {
        'status':'PASS' if job.finalStatus == 'VERIFIED' else job.finalStatus,
        'executionMode':'LIVE',
        'goalId':goal_id,
        'jobFinalStatus':job.finalStatus,
        'terminalReason':job.terminalReason,
        'physicalMutationCalls':1 if job.liveMutationAttempted else 0,
        'duplicateMutationCount':0,
        'mutationAttemptIds':[a['mutationAttemptId'] for a in job.mutationAttempts],
        'createdGuid':session.window_row.get('createdGuid') if session.window_row else None,
        'sourceGuid':session.window_row.get('sourceGuid') if session.window_row else None,
        'readbackPass':bool(session.window_row and session.window_row.get('pass')),
        'stage5Status':'NOT_VERIFIED',
        'auditPackStatus':'PENDING',
    }
    save(output/'verification-report.json', report)
    print(report)


if __name__ == '__main__':
    main()
