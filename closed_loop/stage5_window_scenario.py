"""Stage 5 Hosted Window scenario. Planning is read-only unless --execute is explicit."""
import argparse
from dataclasses import asdict
import os
from pathlib import Path
from types import SimpleNamespace

from .live_wall import ROOT, read, save
from .live_window import (
    WindowExecutor, WindowModelCheck, WindowObserver, WindowPlanner,
    WindowReadBack, WindowSession, acceptance,
)
from .orchestrator import Orchestrator
from .stage5_audit_pack import finish_pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true',
                        help='Perform the single CreateWindows mutation. Without this flag the command is read-only.')
    parser.add_argument('--approved-plan', type=Path,
                        help='Required with --execute: exact prior plan-only report to bind host/dimensions/model hash.')
    args = parser.parse_args()

    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'outputs/closed-loop-stage5'):
        raise ValueError('Stage 5 output must be under outputs/closed-loop-stage5')
    if output.exists():
        raise FileExistsError('Stage 5 evidence output must be new')
    if not os.environ.get('SAFE_BIM_STAGE5_PROJECT_PATH'):
        raise ValueError('SAFE_BIM_STAGE5_PROJECT_PATH must explicitly bind the disposable/test PLN')

    goal_id = 'stage5-hosted-window-001'
    approved = None
    if args.execute:
        if args.approved_plan is None:
            raise ValueError('--execute requires --approved-plan from a prior plan-only run')
        approved_path = args.approved_plan.resolve()
        if not approved_path.is_relative_to(ROOT/'outputs/closed-loop-stage5'):
            raise ValueError('Approved plan must be retained under outputs/closed-loop-stage5')
        approved = read(approved_path)
        if (approved.get('status') != 'PLANNED' or approved.get('executionMode') != 'PLAN_ONLY'
                or approved.get('physicalMutationCalls') != 0):
            raise ValueError('Approved plan-only report is not a valid zero-mutation Stage 5 plan')
    session = WindowSession(output/'session', goal_id, approved_plan=approved)
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
    journals = [read(p) for p in output.rglob('attempts/*.json')]
    journal_ids = [j['mutationAttemptId'] for j in journals]
    report = {
        'status':'PASS' if job.finalStatus == 'VERIFIED' else job.finalStatus,
        'executionMode':'LIVE',
        'goalId':goal_id,
        'jobFinalStatus':job.finalStatus,
        'terminalReason':job.terminalReason,
        'physicalMutationCalls':sum(j.get('nativeCalls',0) for j in journals),
        'duplicateMutationCount':len(journal_ids)-len(set(journal_ids)),
        'mutationAttemptIds':journal_ids,
        'confirmedNativeResponses':sum(j.get('phase') == 'CONFIRMED' for j in journals),
        'createdGuid':session.window_row.get('createdGuid') if session.window_row else None,
        'sourceGuid':session.window_row.get('sourceGuid') if session.window_row else None,
        'readbackPass':bool(session.window_row and session.window_row.get('pass')),
        'stage5Status':'NOT_VERIFIED',
        'auditPackStatus':'PENDING',
    }
    save(output/'verification-report.json', report)
    if job.finalStatus == 'VERIFIED':
        try:
            pack = finish_pack(output, session.identity['projectPath'])
            report['auditPackStatus'] = pack['status']
            if pack['status'] != 'PASS':
                report['status'] = 'BLOCKED'
        except Exception as exc:
            report['status'] = 'BLOCKED'
            report['auditPackStatus'] = 'BLOCKED'
            report['auditPackError'] = f'{type(exc).__name__}: {exc}'
    save(output/'completion-report.json', report)
    print(report)


if __name__ == '__main__':
    main()
