"""Run a single offline goal through observation, mock execution and audit."""
import argparse
import json
from pathlib import Path

from .models import AcceptanceContract, Action, Fact, Observation, PlannerDecision
from .mocks import FixtureObserver, FixtureReadBack, FixedPlanner, MockExecutor
from .orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    contract = AcceptanceContract.from_dict({'goalId': 'stage2-offline-goal-001', 'criteria': [
        {'id': 'C01', 'required': True, 'check': 'length', 'expected': 1.0, 'tolerance': 1e-6}]})
    before = Observation('fixture-model', 'fixture-before', {}, {'fixture.before': {'length': 0.0}})
    after = Observation('fixture-model', 'fixture-after',
        {'length': Fact(1.0, evidenceRefs=('fixture.after',))}, {'fixture.after': {'length': 1.0}})
    job = Orchestrator(contract, 'Offline fixture: verify a 1 metre continuation.',
        FixtureObserver(before), FixedPlanner(PlannerDecision('PLANNED', Action('create_wall', {'length': 1.0}))),
        MockExecutor(), FixtureReadBack([after]), args.output).run()
    print(json.dumps({'status': job.finalStatus, 'executionMode': job.executionMode,
        'liveMutationAttempted': job.liveMutationAttempted, 'iterations': job.iteration,
        'evidence': str(args.output)}, indent=2))
    if job.finalStatus != 'VERIFIED':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
