"""Mass request -> existing shared copy registry -> SceneWriter -> saved reopen.

Representative horizontal Column copy, using an accepted 172-GUID source PLN.
No second Router/writer, retries, project switch API, APX or dependency update.
"""
from pathlib import Path
import argparse,json,sqlite3
import archicad_project_accelerator as A
import archicad_scene_run as R
from archicad_dynamic_commands import DynamicCommands
import archicad_bim_documentation as D
import archicad_connected_components as C
import apa_ac29_group_batch_oneshot as G
import apa_ac29_native_copy_verifier as V
import apa_ac29_installed_factory as F
import apa_ac29_installed_group_provider as P
from apa_ac29_mass_request import placement_offsets
from apa_ac29_dynamic_native_verifiers import installed_verifiers
from apa_ac29_dynamic_write_scopes import build_existing_workflow_scopes
from apa_ac29_save_isolation import ScratchWriteLease,copy_exclusive,preserve_guarded_save,write_new_json,sha256

SCHEMA='APA_AC29_SHARED_NATIVE_COPY_BATCH_V1'
AUTH='USER_APPROVED_AC29_NATIVE_COPY_DISPOSABLE_20261019'
CREATE='SharedNativeCopy20261019V1';SAVE='SharedNativeCopySave20261019V1'
SOURCE_REF='https://github.com/dvikt33-ux/safe-bim-layer/pull/143'
PROTOTYPE='0a17fb15-3639-4dfa-ab01-cd910ae112b0'
read=G.read;need=G.need


def stage(accepted,state,baseline_trace):
    accepted,state,baseline_trace=[Path(p).resolve() for p in (accepted,state,baseline_trace)]
    old,saved=G.saved_state(accepted);receipt=read(accepted/'reopened.json')
    need(receipt['status']=='LIVE_NATIVE_GROUP_BATCH_SAVED_REOPENED_PASS' and receipt['reopenVerified'] and
         saved['finalGuidCount']==172 and not state.exists() and state.parent.is_dir(),
         'SHARED_COPY_ACCEPTED_SOURCE_AND_NEW_STATE_REQUIRED')
    rows=[json.loads(r) for r in baseline_trace.read_text(encoding='utf8').splitlines()]
    native=C.G.normalize_dump([r['response'] for r in rows if r['command']=='GetModelDumpV1'][-1])
    ids=sorted(r['guid'].lower() for r in native['elements'])
    need(R.digest(ids)==saved['finalGuidSetSHA256'] and G.fingerprint(native)==saved['finalBrepSHA256'] and PROTOTYPE in ids,
         'SHARED_COPY_ACCEPTED_FULL_BASELINE_REQUIRED')
    state.mkdir();scratch=state.parent/'native-column-copy.pln'
    need(not scratch.exists(),'SHARED_COPY_FRESH_PLN_REQUIRED')
    copy_exclusive(old['scratch'],scratch)
    need(sha256(scratch)==sha256(old['scratch'])==saved['savedSHA256'],'SHARED_COPY_INITIAL_BYTES_DRIFT')
    write_new_json(state/'baseline-native.json',native)
    m=dict(schema=SCHEMA,source=old['scratch'],sourceSHA256=saved['savedSHA256'],
        originalProtected=old['source'],originalProtectedSHA256=old['sourceSHA256'],
        acceptedState=str(accepted),acceptedReceiptSHA256=sha256(accepted/'reopened.json'),
        scratch=str(scratch),scratchInitialSHA256=saved['savedSHA256'],port=19726,
        baselineSHA256=sha256(state/'baseline-native.json'),baselineGuidSetSHA256=R.digest(ids),
        baselineBrepSHA256=G.fingerprint(native),baselineSemanticSHA256=V.semantic_digest(native,set(ids)),
        prototype=PROTOTYPE,status='STAGED_ONLY_NO_NATIVE_WRITES',automaticReplay=False)
    write_new_json(state/'manifest.json',m);return m


def manifest(state,initial=False):
    state=Path(state).resolve();m=read(state/'manifest.json')
    need(m['schema']==SCHEMA and sha256(m['source'])==m['sourceSHA256'] and
         sha256(m['originalProtected'])==m['originalProtectedSHA256'] and
         sha256(Path(m['acceptedState'])/'reopened.json')==m['acceptedReceiptSHA256'] and
         sha256(state/'baseline-native.json')==m['baselineSHA256'],'SHARED_COPY_SOURCE_OR_BASELINE_DRIFT')
    need(all(sha256(path)==expected for path,expected in m.get('protectedAncestors',{}).items()),
         'SHARED_COPY_PROTECTED_ANCESTOR_DRIFT')
    if initial:need(sha256(m['scratch'])==m['scratchInitialSHA256'] and
        not any((state/n).exists() for n in ('attempted.json','batch-scenewriter.sqlite','saved.json','failed.json')),
        'SHARED_COPY_ONE_SHOT_NO_REPLAY')
    return m


def accepted_copy_source(accepted,*,use_guarded_snapshot=False):
    accepted=Path(accepted).resolve()
    if not use_guarded_snapshot:
        old,saved=saved_state(accepted)
        return old,saved,Path(old['scratch'])
    # Explicit snapshot recovery: never replace or trust a later changed PLN.
    old=manifest(accepted);saved=read(accepted/'saved.json')
    snap=read(accepted/'guarded-snapshot.json');receipt=read(accepted/'reopened.json')
    source=accepted/'guarded-save.snapshot'
    need(saved['status']=='SHARED_COPY_SAVED_PENDING_REOPEN' and
         receipt['status']=='LIVE_SHARED_NATIVE_COPY_BATCH_SAVED_REOPENED_PASS' and receipt['reopenVerified'] and
         receipt['savedSHA256']==saved['savedSHA256']==sha256(source) and
         sha256(accepted/'guarded-snapshot.json')==saved['snapshotReceiptSHA256'] and
         snap['savedSHA256']==snap['snapshotSHA256']==saved['savedSHA256'] and
         snap['protectedSHA256']=={old['source']:old['sourceSHA256'],old['originalProtected']:old['originalProtectedSHA256']},
         'SHARED_COPY_ACCEPTED_GUARDED_SNAPSHOT_REQUIRED')
    return old,saved,source


def stage_placements(accepted,state,baseline_trace,placements,*,use_guarded_snapshot=False):
    """New placement capability in a fresh copy of an accepted individual batch.

    Reuses the original execution, scope, verifier and save/reopen path below.
    A new layout never resets or repeats the accepted operation's state.
    """
    accepted,state,baseline_trace=[Path(p).resolve() for p in (accepted,state,baseline_trace)]
    shifts=placement_offsets(placements)
    old,saved,source=accepted_copy_source(accepted,use_guarded_snapshot=use_guarded_snapshot)
    receipt=read(accepted/'reopened.json')
    need(receipt['status']=='LIVE_SHARED_NATIVE_COPY_BATCH_SAVED_REOPENED_PASS' and receipt['reopenVerified'] and
         not state.exists() and state.parent.is_dir() and all(r['dz']==0 for r in shifts),
         'SHARED_COPY_ACCEPTED_SOURCE_AND_NEW_STATE_REQUIRED')
    rows=[json.loads(r) for r in baseline_trace.read_text(encoding='utf8').splitlines()]
    native=C.G.normalize_dump([r['response'] for r in rows if r['command']=='GetModelDumpV1'][-1])
    ids=sorted(r['guid'].lower() for r in native['elements'])
    need(R.digest(ids)==saved['finalGuidSetSHA256'] and G.fingerprint(native)==saved['finalBrepSHA256'] and
         V.semantic_digest(native,set(ids))==saved['finalSemanticSHA256'] and PROTOTYPE in ids,
         'SHARED_COPY_ACCEPTED_FULL_BASELINE_REQUIRED')
    scratch=state.parent/'native-line-distribution.pln'
    need(not scratch.exists(),'SHARED_COPY_FRESH_PLN_REQUIRED')
    state.mkdir();copy_exclusive(source,scratch)
    need(sha256(scratch)==saved['savedSHA256'],'SHARED_COPY_INITIAL_BYTES_DRIFT')
    write_new_json(state/'baseline-native.json',native)
    m=dict(schema=SCHEMA,source=str(source),sourceSHA256=saved['savedSHA256'],
        originalProtected=old['originalProtected'],originalProtectedSHA256=old['originalProtectedSHA256'],
        protectedAncestors={old['source']:old['sourceSHA256'],**old.get('protectedAncestors',{})},
        acceptedState=str(accepted),acceptedReceiptSHA256=sha256(accepted/'reopened.json'),
        scratch=str(scratch),scratchInitialSHA256=saved['savedSHA256'],port=old['port'],
        baselineSHA256=sha256(state/'baseline-native.json'),baselineGuidSetSHA256=R.digest(ids),
        baselineBrepSHA256=G.fingerprint(native),baselineSemanticSHA256=V.semantic_digest(native,set(ids)),
        prototype=PROTOTYPE,placements=placements,status='STAGED_ONLY_NO_NATIVE_WRITES',automaticReplay=False)
    if use_guarded_snapshot:
        m['acceptedSnapshotSource']=True
        m['laterWorkingCopySHA256Observed']=sha256(old['scratch'])
    write_new_json(state/'manifest.json',m);return m


def api_for(m,state,execute=False,saved_sha=None):
    api,guard=G.prepare_api(m,state,execute=execute,saved_sha=saved_sha,authorization_ref=AUTH)
    # Original code-owned SDK reader; no new write allowlist or transport.
    api.allowed|={'GetNativeGroupRootsV1'}
    return api,guard


def capture(m,api):return G.capture(m,api)


def current_plan(state):
    state=Path(state).resolve();m=manifest(state,True);api,_=api_for(m,state)
    router=F.native_command_router();ids,native=capture(m,api)
    need(R.digest(ids)==m['baselineGuidSetSHA256'] and G.fingerprint(native)==m['baselineBrepSHA256'] and
         V.semantic_digest(native,set(ids))==m['baselineSemanticSHA256'],'SHARED_COPY_PREWRITE_FULL_NATIVE_DRIFT')
    nodes={r['guid'].lower():r for r in native['elements']};source=V.facts(api,nodes,[m['prototype']],native)[m['prototype']]
    existing=[dict(guid=m['prototype'],type=source['type'],storyIndex=0,anchor=source['anchor'],
        familySignature=R.digest(dict(typed=source['typed'],solid=source['solid'])),nativeReadbackVerified=True)]
    task=dict(schemaVersion='apa-native-mass-request/1',request='Тиражировать отдельную проверенную колонну по линии',
        sourceRef=SOURCE_REF,existing=existing,assembly=None,
        placements=m.get('placements',dict(mode='LINEAR',count=2,start=dict(dx=1000,dy=0,dz=0),step=dict(dx=25,dy=0,dz=0))))
    writer=R.SceneWriter(api,journal_path=state/'batch-scenewriter.sqlite',schema_path=G.SCHEMA_PATH,allow_3d_view_for_write=True)
    selected=A.prepare_current_runtime_group_native_task(router,writer,task)['preview']
    ops=selected['selectedNativeTaskPreview']['workflow']['graph']['operations']
    need(len(ops)==1 and ops[0]['command']==V.CMD and selected['groupedTargetCount']==0 and
         selected['individuallyRoutedTargetCount']==len(placement_offsets(task['placements'])),
         'SHARED_COPY_ONE_EXISTING_MOVE_COPY_ROUTE_REQUIRED')
    proof=V.verify_before(api=api,command=V.CMD,parameters=ops[0]['params'],affected=[],native_before=native)
    need(api.write_attempts==0,'SHARED_COPY_PLAN_MUST_BE_READONLY')
    return dict(schema=SCHEMA,status='READONLY_SHARED_COPY_PLAN_PASS',task=task,preview=selected,
        params=ops[0]['params'],sourceProof=proof,runtimeIdentity=P.verify_runtime(api),
        contractSHA256=router.contract_hash(V.CMD),baselineGuids=ids,nativeWrites=0)


def plan(state):
    state=Path(state).resolve();need(not (state/'plan.json').exists(),'SHARED_COPY_PLAN_ALREADY_PINNED')
    r=current_plan(state);write_new_json(state/'plan.json',r);return r


def verify_model(m,api,p,response):
    ids,native=capture(m,api)
    proof=V.verify_after(api=api,command=V.CMD,parameters=p['params'],native_response=response,
        before_guids=set(p['baselineGuids']),after_guids=set(ids),affected=[],
        native_before={},native_after=native,source_proof=p['sourceProof'])
    return ids,native,proof


def execute(state):
    state=Path(state).resolve();m=manifest(state,True);p=read(state/'plan.json')
    need(R.canonical(current_plan(state))==R.canonical(p),'SHARED_COPY_CURRENT_PLAN_DRIFT')
    lease=ScratchWriteLease(m['scratch'],state,m['scratchInitialSHA256']);lease.acquire()
    write_new_json(state/'attempted.json',dict(planSHA256=sha256(state/'plan.json'),automaticReplay=False))
    try:
        api,guard=api_for(m,state,True);router=F.native_command_router();runtime=P.verify_runtime(api)
        need(runtime==p['runtimeIdentity'],'SHARED_COPY_NATIVE_RUNTIME_DRIFT')
        router.probe_runtime(api,V.CMD)
        auto=A.prepare_auto_optimized_native_task(router,p['task']);graph=auto['selectedNativeTaskPreview']['workflow'];op=graph['graph']['operations'][0]
        need(op['params']==p['params'] and router.contract_hash(V.CMD)==p['contractSHA256'],'SHARED_COPY_CONTRACT_DRIFT')
        with sqlite3.connect(state/'batch-scenewriter.sqlite') as db:
            db.execute('CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,plan_hash TEXT NOT NULL,state TEXT NOT NULL,result TEXT NOT NULL)')
            db.execute('CREATE TABLE steps(scene_id TEXT NOT NULL,step_id TEXT NOT NULL,state TEXT NOT NULL,guid TEXT,output TEXT NOT NULL,PRIMARY KEY(scene_id,step_id))')
        writer=R.SceneWriter(api,journal_path=state/'batch-scenewriter.sqlite',schema_path=G.SCHEMA_PATH,allow_3d_view_for_write=True)
        spec=dict(schemaVersion='apa-ac29-dynamic-mutation-scope/1',projectSha256=m['scratchInitialSHA256'],
            sourcePlanHash=graph['sourcePlanHash'],authorizationRef=AUTH,sourceEvidenceRef=SOURCE_REF,
            sceneId=CREATE,stepId=op['id'],command=V.CMD,effect='CREATE',impact='MODEL',
            commandContractHash=p['contractSHA256'],parametersHash=R.digest(p['params']),
            expectedBeforeGuidSetHash=m['baselineGuidSetSHA256'],expectedBeforeNativeBrepHash=m['baselineBrepSHA256'],
            affectedGuids=[],retainedGuids=p['baselineGuids'],verifierId='VerifiedNativeBatchCopy')
        scopes=build_existing_workflow_scopes(spec=spec,plan=graph,router=router,registry=installed_verifiers(),
            writer=writer,api=api,capture_model=D.capture_full_model,guid_inventory=A.inventory_guids,
            current_project_sha=lambda:sha256(m['scratch']),approved_project_sha=m['scratchInitialSHA256'],local_authorization=AUTH)
        result=A.run_auto_optimized_native_task(router,api,auto,writer,scopes)
        need(result['status']=='WORKFLOW_CALLABLE_VERIFIED' and api.calls[V.CMD]==1,'SHARED_COPY_NATIVE_UNKNOWN_NO_REPLAY')
        response=result['results'][op['id']];ids,native,proof=verify_model(m,api,p,response)
        signatures=C.retained_geometry_signatures(native,ids);semantic=V.semantic_digest(native,set(ids));brep=G.fingerprint(native)
        router.review_policy('SaveProject','TRANSACTION','PROJECT',dict(source=SOURCE_REF,sha256=router.contract_hash('SaveProject')))
        guard.enable_after_verified_copy()
        def before_save(live):
            fresh,current,_=verify_model(m,live,p,response)
            need(fresh==ids and V.semantic_digest(current,set(fresh))==semantic and lease.verify() and
                 sha256(m['scratch'])==m['scratchInitialSHA256'],'SHARED_COPY_PRESAVE_DRIFT')
            return dict(status='SHARED_COPY_PRESAVE_PASS')
        def after_save(reply,_):
            need(reply=={'success':True} and guard.new_saved_sha and lease.verify(),'SHARED_COPY_SAVE_NOT_CONFIRMED')
            snap=preserve_guarded_save(m['scratch'],state/'guarded-save.snapshot',guard.new_saved_sha,
                {m['source']:m['sourceSHA256'],m['originalProtected']:m['originalProtectedSHA256']})
            write_new_json(state/'guarded-snapshot.json',snap);return dict(status='SHARED_COPY_SAVE_SNAPSHOT_PASS')
        saved=router.execute(writer,SAVE,router.prepare('SaveProject',{}),[],signatures,m['scratchInitialSHA256'],AUTH,'PROJECT',after_save,verify_before=before_save)
        need(saved['status']=='PASS' and api.calls['SaveProject']==1 and api.write_attempts==2,'SHARED_COPY_ONE_BATCH_ONE_SAVE_REQUIRED')
        receipt=dict(schema=SCHEMA,status='SHARED_COPY_SAVED_PENDING_REOPEN',sourceSHA256=m['sourceSHA256'],
            savedSHA256=guard.new_saved_sha,snapshotReceiptSHA256=sha256(state/'guarded-snapshot.json'),
            nativeResponse=response,nativeReadback=proof,finalGuidCount=len(ids),finalGuidSetSHA256=R.digest(ids),
            finalBrepSHA256=brep,finalSemanticSHA256=semantic,nativeCopyCalls=1,saveCalls=1,automaticReplay=False,reopenVerified=False)
        write_new_json(state/'saved.json',receipt);return receipt
    except Exception as exc:
        write_new_json(state/'failed.json',dict(status='UNKNOWN_NO_REPLAY_READONLY_RECONCILIATION_REQUIRED',error=str(exc),automaticReplay=False))
        raise


def saved_state(state):
    state=Path(state).resolve();m=manifest(state);r=read(state/'saved.json');snap=read(state/'guarded-snapshot.json')
    need(r['status']=='SHARED_COPY_SAVED_PENDING_REOPEN' and
         sha256(m['scratch'])==sha256(state/'guarded-save.snapshot')==r['savedSHA256'] and
         sha256(state/'guarded-snapshot.json')==r['snapshotReceiptSHA256'] and
         snap['savedSHA256']==snap['snapshotSHA256']==r['savedSHA256'] and
         snap['protectedSHA256']=={m['source']:m['sourceSHA256'],m['originalProtected']:m['originalProtectedSHA256']},
         'SHARED_COPY_SAVED_BYTES_OR_SOURCE_PROOF_DRIFT')
    return m,r


def check_closed(state):
    state=Path(state).resolve();m,r=saved_state(state);api,_=api_for(m,state,saved_sha=r['savedSHA256'])
    try:api('GetProjectInfo',{})
    except Exception as exc:need('4001' in str(exc) and 'no open project' in str(exc).lower(),'SHARED_COPY_NATIVE_NO_OPEN_PROJECT_REQUIRED')
    else:raise ValueError('SHARED_COPY_PROJECT_STILL_OPEN')
    record=dict(status='NATIVE_NO_OPEN_PROJECT_CONFIRMED',savedSHA256=r['savedSHA256'],nativeWrites=0)
    write_new_json(state/'closed.json',record);return record


def verify_reopen(state):
    state=Path(state).resolve();m,r=saved_state(state);closed=read(state/'closed.json')
    need(closed['status']=='NATIVE_NO_OPEN_PROJECT_CONFIRMED' and closed['savedSHA256']==r['savedSHA256'],'SHARED_COPY_REAL_GUI_CLOSE_REQUIRED')
    api,_=api_for(m,state,saved_sha=r['savedSHA256']);need(P.verify_runtime(api)==read(state/'plan.json')['runtimeIdentity'],'SHARED_COPY_REOPEN_NATIVE_BUILD_DRIFT')
    ids,native,proof=verify_model(m,api,read(state/'plan.json'),r['nativeResponse'])
    need(len(ids)==r['finalGuidCount'] and R.digest(ids)==r['finalGuidSetSHA256'] and
         G.fingerprint(native)==r['finalBrepSHA256'] and V.semantic_digest(native,set(ids))==r['finalSemanticSHA256'] and api.write_attempts==0,
         'SHARED_COPY_REOPEN_ALL_NATIVE_FACTS_DRIFT')
    result=dict(r,status='LIVE_SHARED_NATIVE_COPY_BATCH_SAVED_REOPENED_PASS',reopenVerified=True,reopenedReadback=proof,
                sourceUnchanged=True,verificationNativeWrites=0)
    write_new_json(state/'reopened.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['plan','execute','check-closed','verify-reopen']);p.add_argument('--state',required=True)
    a=p.parse_args();print(json.dumps({'plan':plan,'execute':execute,'check-closed':check_closed,'verify-reopen':verify_reopen}[a.phase](a.state),ensure_ascii=False,indent=2))
