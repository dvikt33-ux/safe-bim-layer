"""Authorized live-only S4-01/02/03/06 scenarios; identity gate before any write."""
import argparse
from copy import deepcopy
from dataclasses import asdict
import json
import hashlib
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from .live_wall import (ROOT, COMMAND, LiveSession, LiveObserver, LivePlanner, LiveModelCheck,
    LiveModelFingerprint, acceptance, read, load)
from .models import AcceptanceContract, Action, Criterion, PlannerDecision
from .stage4_preflight import preflight, IMPLEMENTATION_FILES
from .wall_attempts import RecoverableWallOrchestrator, durable_json
from .live_wall_hardening import ControlledWallExecutor, ControlledWallReadBack, WallReconciler
from scripts.stage4_audit_pack import source_contract, build_pack, verify_pack
from scripts.audit_pack import file_info


def restore_session(output, goal_id, offline, regression):
    session = LiveSession.__new__(LiveSession)
    session.output, session.goal_id = Path(output), goal_id
    session.offline_report, session.regression_report = offline, regression
    session.identity = read(session.output/'preflight.json')['identity']
    session.rows = [read(p) for p in sorted(session.output.glob('iteration-*/summary.json'))]
    session.api_count = max([int(p.name.split('-')[0]) for p in session.output.glob('identity/*.request.json')]+[0])
    session.snapshots = max([int(p.name.split('-')[0]) for p in session.output.glob('observations/*.fingerprint.json')]+[0])
    session.active_plan = session.last_check = None
    session.dump_module = load('stage4_restart_dump','archicad-addon/Examples/model_dump_v1.py')
    session.chat = load('stage4_restart_chat','scripts/archicad_chat_executor.py')
    session.check_identity()
    return session


def helper_change(directory, offline, regression):
    """Distinct +0.5 m helper invalidates the old +1.0 m decision."""
    session = LiveSession(directory/'live-job', 'stage4-stale-external-helper', offline, regression)
    class HelperPlanner(LivePlanner):
        def plan(self, job, observation):
            data = read(observation.evidence['live.snapshot']['path'])
            plan = session.chat.instruction_to_request('Продолжи последнюю созданную стену ещё на 0,5 метра.', 'execute', data)
            if plan['status'] != 'PLANNED':
                return PlannerDecision('BLOCKED', reason=str(plan))
            session.active_plan = {'number':1,'jobIteration':job.iteration,'modelHash':observation.modelHash,
                'selection':plan['selection'],'sourceGuid':plan['request']['sourceGuid'],'length':.5}
            durable_json(directory/'plan.json', {'goalId':session.goal_id,'planner':plan,'modelHash':observation.modelHash})
            return PlannerDecision('PLANNED', Action('create_wall',{'sourceGuid':plan['request']['sourceGuid'],'length':.5}),
                plannedAgainstModelIdentity=observation.modelIdentity, plannedAgainstModelHash=observation.modelHash)
    contract = AcceptanceContract(session.goal_id,(Criterion('H01',True,'C03',True),))
    job = RecoverableWallOrchestrator(contract,'Controlled +0.5 m external Wall edit for stale test',
        LiveObserver(session),HelperPlanner(session),ControlledWallExecutor(session),ControlledWallReadBack(session),
        directory/'job.json',model_check=LiveModelCheck(session),execution_mode='LIVE',max_iterations=1).run()
    if job.finalStatus != 'VERIFIED':
        raise RuntimeError('External helper not VERIFIED; no automatic repeat: '+str(job.terminalReason))
    durable_json(directory/'verification-report.json',{'status':'PASS','provenance':'LIVE',
        'createdGuid':session.rows[0]['createdGuid'],'mutationAttemptIds':[a['mutationAttemptId'] for a in job.mutationAttempts]})


def make_orchestrator(output, session, fault=None, stale=False):
    checker = LiveModelCheck(session)
    if stale:
        class StaleCheck(LiveModelCheck):
            injected = False
            def check(self, observation):
                if not self.injected:
                    self.injected = True
                    helper_change(output/'external-helper',session.offline_report,session.regression_report)
                return super().check(observation)
        checker = StaleCheck(session)
    return RecoverableWallOrchestrator(acceptance(session.goal_id),COMMAND,LiveObserver(session),LivePlanner(session),
        ControlledWallExecutor(session,fault=fault),ControlledWallReadBack(session),output/'job.json',
        model_check=checker,execution_mode='LIVE',max_iterations=5,no_progress_limit=2)


def recover(output, goal_id, offline, regression):
    session = restore_session(output/'live-job',goal_id,offline,regression)
    orch = RecoverableWallOrchestrator.restore(output/'job.json',observer=LiveObserver(session),planner=LivePlanner(session),
        executor=ControlledWallExecutor(session),readback=ControlledWallReadBack(session),model_check=LiveModelCheck(session))
    job = orch.reconcile_and_continue(WallReconciler(session))
    return job, session


def finish_pack(output, identity):
    snapshots, records, pairs = [], [], []
    for path in sorted(output.rglob('*.json')):
        if 'audit-pack' in path.parts or path.name == 'audit-pack-verification.json': continue
        records.append(path)
        observation_sidecar = path.name.endswith(('.request.json','.native-response.json','.metrics.json','.fingerprint.json'))
        if ((path.parent.name == 'observations' and not observation_sidecar) or
                (path.parent.name == 'executor' and path.name in ('before.json','after-create.json')) or
                path.name == 'planner-model-dump.json'):
            snapshots.append(path)
    snapshot_set = {p.resolve() for p in snapshots}
    for before in snapshots:
        if before.name == 'before.json':
            after = before.with_name('after-create.json')
            if after.resolve() in snapshot_set: pairs.append((before,after))
    for path in output.rglob('job.json'):
        job = read(path)
        for step in job.get('iterations',[]):
            if step.get('readback') and step.get('executorRequest'):
                after_name = step['readback']['evidence'].get('live.snapshot',{}).get('path')
                before = path.parent/'live-job'/f'iteration-{step["iteration"]}'/'executor/before.json'
                if after_name and before.resolve() in snapshot_set and Path(after_name).resolve() in snapshot_set:
                    pairs.append((before,Path(after_name)))
    contract = source_contract(ROOT,output,snapshots,pairs,records,identity,'LIVE')
    build_pack(ROOT,contract,output/'audit-pack')
    result = verify_pack(ROOT,output/'audit-pack')
    durable_json(output/'audit-pack-verification.json',result)
    # Exact-path LFS attributes, not a blanket filter for source/pack JSON.
    large = [p for p in records if p.stat().st_size > 1_000_000]
    if large:
        attributes = ROOT/'.gitattributes'
        current = attributes.read_text(encoding='utf-8')
        additions = [p.resolve().relative_to(ROOT).as_posix()+' filter=lfs diff=lfs merge=lfs -text' for p in large]
        with attributes.open('a',encoding='utf-8',newline='\n') as stream:
            for line in additions:
                if line not in current: stream.write(line+'\n')
    durable_json(output/'full-evidence-manifest.json', {'files':[file_info(ROOT,p.resolve().relative_to(ROOT).as_posix()) for p in records],
        'largeFileStorage':'GIT_LFS','auditPackStorage':'ORDINARY_GIT'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',choices=('S4-01','S4-02','S4-03','S4-06'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--offline-proof',type=Path,required=True)
    parser.add_argument('--happy-report',type=Path)
    parser.add_argument('--live',action='store_true',required=True)
    parser.add_argument('--crash-worker-token')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'outputs/closed-loop-stage4'):
        raise ValueError('Dedicated Stage 4 scenario directory required')
    proof = read(args.offline_proof)
    if proof['status'] != 'PASS' or proof['oldTests'] != 95 or any(r['status'] != 'PASS' for r in proof['tests'].values()):
        raise ValueError('All 95 old tests and new Stage 4 tests must pass first')
    if (len(proof['implementationFiles'])!=len(IMPLEMENTATION_FILES) or
            {record['path'] for record in proof['implementationFiles']}!=set(IMPLEMENTATION_FILES)):
        raise ValueError('Complete implementation and frozen-v0 fingerprint set required')
    for record in proof['implementationFiles']:
        if hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Implementation changed after offline proof: '+record['path'])
    offline = {'status':'PASS','provenance':'OFFLINE_UNIT_TESTS','testsRun':proof['oldTests']+proof['newTests']}
    goal_id = 'stage4-'+args.scenario.lower()+'-wall-goal'
    if args.crash_worker_token:
        marker = read(output/'crash-worker-authorization.json')
        if args.scenario != 'S4-06' or marker['token'] != args.crash_worker_token:
            raise ValueError('Invalid dedicated crash worker authorization')
        with (output/'crash-worker.claim').open('x') as stream: stream.write(args.crash_worker_token)
        happy = read(args.happy_report)
        if happy['status'] != 'PASS': raise ValueError('Happy path must PASS before crash recovery test')
        regression = happy['baselineRegression']
        session = LiveSession(output/'live-job',goal_id,offline,regression)
        make_orchestrator(output,session,fault='crash').run()
        return 1  # Expected execution exits at the guarded physical boundary.
    output.mkdir(parents=True,exist_ok=False)
    gate = preflight(output/'identity-gate')
    report = {'scenarioId':args.scenario,'status':'BLOCKED','provenance':'LIVE','mutationAttemptIds':[],
        'physicalMutationCalls':0,'duplicateMutationCount':0,'auditPackStatus':'NOT_VERIFIED','automaticRetry':False}
    if gate['status'] != 'PASS':
        report['reason']=gate.get('reason')
        durable_json(output/'verification-report.json',report)
        print(json.dumps(report,ensure_ascii=True))
        return 1
    durable_json(output/'preflight.json',gate)
    durable_json(output/'goal.json',{'goalId':goal_id,'command':COMMAND,'userCommandCount':1})
    try:
        if args.scenario == 'S4-01':
            baseline = proof['archivedRegressions']['stage1']
            if baseline['status'] != 'PASS': raise ValueError('Archived Stage 1 baseline regression must PASS')
            regression = {'status':'PASS','provenance':'ARCHIVED_LIVE_EVIDENCE_RECOMPUTED',
                'stage1Commit':'27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c','verification':baseline}
        else:
            if args.happy_report is None: raise ValueError('Fresh S4-01 happy path report required')
            happy = read(args.happy_report)
            if happy['status'] != 'PASS': raise ValueError('Prior fresh happy path regression failed')
            regression = happy['baselineRegression']
        report['baselineRegression'] = regression
        if args.scenario == 'S4-06':
            token = str(uuid4())
            durable_json(output/'crash-worker-authorization.json',{'token':token,'scenarioId':args.scenario,'nativeAttemptLimit':1})
            with (output/'crash-worker.log').open('w',encoding='utf-8') as stream:
                child = subprocess.run([sys.executable,'-m','closed_loop.stage4_live_scenario','--scenario',args.scenario,
                    '--output',str(output),'--offline-proof',str(args.offline_proof.resolve()),'--happy-report',str(args.happy_report.resolve()),
                    '--live','--crash-worker-token',token],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            if child.returncode != 86:
                raise RuntimeError('Crash worker did not reach the expected durable boundary; do not replay')
            durable_json(output/'checkpoints/crashed-job.json',read(output/'job.json'))
            job, session = recover(output,goal_id,offline,regression)
            report['crashWorkerExitCode']=86
        else:
            session = LiveSession(output/'live-job',goal_id,offline,regression)
            orch = make_orchestrator(output,session,fault='lost-response' if args.scenario == 'S4-03' else None,
                                     stale=args.scenario == 'S4-02')
            job = orch.run()
            if args.scenario == 'S4-03':
                if job.finalStatus != 'UNKNOWN_OUTCOME': raise RuntimeError('Lost response did not produce UNKNOWN_OUTCOME')
                durable_json(output/'checkpoints/unknown-outcome-job.json',job.to_dict())
                job, session = recover(output,goal_id,offline,regression)
        journals=[read(p) for p in output.rglob('mutation-attempts/*.json')]
        ids = [j['mutationAttemptId'] for j in journals]
        invalidated = [step for step in job.iterations if step.decisionInvalidated]
        report.update(jobFinalStatus=job.finalStatus,terminalReason=job.terminalReason,mutationAttemptIds=ids,
            duplicateMutationCount=len(ids)-len(set(ids)),recoveredFromCrash=job.recoveredFromCrash,
            reconciliationOutcomes=[a['reconciliationStatus'] for a in job.mutationAttempts if a['reconciliationStatus']],
            staleActionExecutorCalls=sum(step.executorRequest is not None for step in invalidated),
            invalidatedDecisionCount=len(invalidated),iterations=session.rows)
        report['physicalMutationCalls']=sum(j['nativeCalls'] for j in journals)
        if job.finalStatus != 'VERIFIED' or len(session.rows)!=2 or report['duplicateMutationCount']:
            raise RuntimeError('Live two-segment goal not fully VERIFIED')
        if args.scenario == 'S4-02' and (not invalidated or report['staleActionExecutorCalls'] != 0):
            raise RuntimeError('Stale action was not demonstrably rejected before execution')
        if args.scenario in ('S4-03','S4-06') and 'RECONCILED_APPLIED' not in report['reconciliationOutcomes']:
            raise RuntimeError('Applied recovery not proven')
        report['status']='PASS'
    except Exception as exc:
        report.update(status='BLOCKED',reason=f'{type(exc).__name__}: {exc}',automaticRetry=False)
    journals=[read(p) for p in output.rglob('mutation-attempts/*.json')]
    ids=[j['mutationAttemptId'] for j in journals]
    report.update(mutationAttemptIds=ids,physicalMutationCalls=sum(j['nativeCalls'] for j in journals),
        duplicateMutationCount=len(ids)-len(set(ids)),confirmedNativeResponses=sum(j['phase']=='CONFIRMED' for j in journals))
    durable_json(output/'verification-report.json',report)
    try:
        pack = finish_pack(output,gate['identity']['projectPath'])
        report['auditPackStatus']=pack['status']
    except Exception as exc:
        report.update(status='BLOCKED',auditPackStatus='BLOCKED',auditPackError=str(exc))
    durable_json(output/'completion-report.json',report)
    print(json.dumps(report,ensure_ascii=True))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
