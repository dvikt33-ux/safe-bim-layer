"""One source-scoped group creation via existing APA Router/SceneWriter/SQLite."""
from pathlib import Path
import json,sqlite3
import apa_ac29_copy_batch_oneshot as B
import apa_ac29_native_group_create as N
from apa_ac29_dynamic_native_verifiers import installed_verifiers
from apa_ac29_dynamic_write_scopes import build_existing_workflow_scopes

A,R,G,V,F,P=B.A,B.R,B.G,B.V,B.F,B.P
need,read,sha256,write=B.need,B.read,B.sha256,B.write_new_json
SCHEMA='APA_AC29_SHARED_GROUP_CREATE_ONESHOT_V1'
AUTH='USER_APPROVED_AC29_NATIVE_GROUP_CREATE_DISPOSABLE_20261020'
CREATE='SharedGroupCreate20261020V1';SAVE='SharedGroupCreateSave20261020V1'
SOURCE_REF='https://github.com/dvikt33-ux/safe-bim-layer/pull/157'


def operation(m):
    if m.get('operation','CREATE')=='CREATE':return N,AUTH,CREATE,SAVE
    if m['operation']=='MOVE':
        import apa_ac29_native_group_move as M
        return M,'USER_APPROVED_AC29_NATIVE_GROUP_MOVE_DISPOSABLE_20261020','SharedGroupMove20261020V1','SharedGroupMoveSave20261020V1'
    need(m['operation']=='UNGROUP','GROUP_EDIT_UNKNOWN_OPERATION')
    import apa_ac29_native_group_ungroup as U
    return U,'USER_APPROVED_AC29_NATIVE_GROUP_UNGROUP_DISPOSABLE_20261020','SharedGroupUngroup20261020V1','SharedGroupUngroupSave20261020V1'


def stage(accepted,state,trace,members):
    accepted,state,trace=[Path(p).resolve() for p in (accepted,state,trace)]
    old,saved,source=B.accepted_copy_source(accepted,use_guarded_snapshot=True)
    members=N.members(dict(memberIds=[dict(guid=g) for g in members],sourceRef=SOURCE_REF))
    rows=[json.loads(l) for l in trace.read_text(encoding='utf8').splitlines()]
    native=B.C.G.normalize_dump([r['response'] for r in rows if r['command']=='GetModelDumpV1'][-1])
    ids=sorted(r['guid'].lower() for r in native['elements'])
    need(R.digest(ids)==saved['finalGuidSetSHA256'] and G.fingerprint(native)==saved['finalBrepSHA256'] and
         V.semantic_digest(native,set(ids))==saved['finalSemanticSHA256'] and set(members)<=set(ids) and
         not state.exists() and state.parent.is_dir(),'GROUP_CREATE_ACCEPTED_SOURCE_OR_NEW_STATE_REQUIRED')
    scratch=state.parent/'native-group-create.pln';need(not scratch.exists(),'GROUP_CREATE_FRESH_SCRATCH_REQUIRED')
    state.mkdir();B.copy_exclusive(source,scratch);need(sha256(scratch)==saved['savedSHA256'],'GROUP_CREATE_COPY_SHA_DRIFT')
    write(state/'baseline-native.json',native)
    m=dict(schema=SCHEMA,source=str(source),sourceSHA256=saved['savedSHA256'],scratch=str(scratch),
        scratchInitialSHA256=saved['savedSHA256'],port=old['port'],members=members,
        originalProtected=old['originalProtected'],originalProtectedSHA256=old['originalProtectedSHA256'],
        protectedAncestors={old['source']:old['sourceSHA256'],**old.get('protectedAncestors',{})},
        acceptedState=str(accepted),acceptedReceiptSHA256=sha256(accepted/'reopened.json'),
        baselineSHA256=sha256(state/'baseline-native.json'),baselineGuidSetSHA256=R.digest(ids),
        baselineBrepSHA256=G.fingerprint(native),baselineSemanticSHA256=V.semantic_digest(native,set(ids)),automaticReplay=False)
    write(state/'manifest.json',m);return m


def manifest(state,initial=False):
    state=Path(state).resolve();m=read(state/'manifest.json')
    need(m['schema']==SCHEMA and sha256(m['source'])==m['sourceSHA256'] and
         sha256(m['originalProtected'])==m['originalProtectedSHA256'] and
         all(sha256(path)==h for path,h in m['protectedAncestors'].items()) and
         sha256(Path(m['acceptedState'])/'reopened.json')==m['acceptedReceiptSHA256'] and
         sha256(state/'baseline-native.json')==m['baselineSHA256'],'GROUP_CREATE_SOURCE_OR_BASELINE_DRIFT')
    if initial:need(sha256(m['scratch'])==m['scratchInitialSHA256'] and
        not any((state/n).exists() for n in ('attempted.json','batch-scenewriter.sqlite','saved.json','failed.json')),
        'GROUP_CREATE_ONE_SHOT_NO_REPLAY')
    return m


def stage_group_edit(accepted,state,trace,edit='UNGROUP',translation=None):
    accepted,state,trace=[Path(p).resolve() for p in (accepted,state,trace)]
    need(edit in {'UNGROUP','MOVE'},'GROUP_EDIT_EXACT_OPERATION_REQUIRED')
    if edit=='MOVE':
        import apa_ac29_native_group_move as M
        M.shift(translation)
    old=manifest(accepted);saved=read(accepted/'saved.json');receipt=read(accepted/'reopened.json')
    source=accepted/'guarded-save.snapshot';snap=read(accepted/'guarded-snapshot.json')
    need(receipt['status']=='LIVE_SHARED_NATIVE_GROUP_CREATE_SAVED_REOPENED_PASS' and receipt['reopenVerified'] and
         receipt['savedSHA256']==saved['savedSHA256']==sha256(source) and
         sha256(accepted/'guarded-snapshot.json')==saved['snapshotReceiptSHA256'] and
         snap['savedSHA256']==snap['snapshotSHA256']==saved['savedSHA256'] and
         not state.exists() and state.parent.is_dir(),'GROUP_UNGROUP_ACCEPTED_SNAPSHOT_AND_NEW_STATE_REQUIRED')
    rows=[json.loads(l) for l in trace.read_text(encoding='utf8').splitlines()]
    native=B.C.G.normalize_dump([r['response'] for r in rows if r['command']=='GetModelDumpV1'][-1])
    ids=sorted(r['guid'].lower() for r in native['elements'])
    need(R.digest(ids)==saved['finalGuidSetSHA256'] and G.fingerprint(native)==saved['finalBrepSHA256'] and
         V.semantic_digest(native,set(ids))==saved['finalSemanticSHA256'],'GROUP_UNGROUP_ACCEPTED_BASELINE_REQUIRED')
    scratch=state.parent/('native-group-move.pln' if edit=='MOVE' else 'native-group-ungroup.pln');need(not scratch.exists(),'GROUP_UNGROUP_FRESH_SCRATCH_REQUIRED')
    state.mkdir();B.copy_exclusive(source,scratch);need(sha256(scratch)==saved['savedSHA256'],'GROUP_UNGROUP_COPY_SHA_DRIFT')
    write(state/'baseline-native.json',native)
    m=dict(old,source=str(source),sourceSHA256=saved['savedSHA256'],scratch=str(scratch),scratchInitialSHA256=saved['savedSHA256'],
        protectedAncestors={old['source']:old['sourceSHA256'],**old['protectedAncestors']},
        acceptedState=str(accepted),acceptedReceiptSHA256=sha256(accepted/'reopened.json'),
        baselineSHA256=sha256(state/'baseline-native.json'),baselineGuidSetSHA256=R.digest(ids),
        baselineBrepSHA256=G.fingerprint(native),baselineSemanticSHA256=V.semantic_digest(native,set(ids)),
        operation=edit,groupGuid=receipt['reopenedReadback']['groupId'])
    if edit=='MOVE':m['translation']=translation
    write(state/'manifest.json',m);return m


def stage_ungroup(accepted,state,trace):return stage_group_edit(accepted,state,trace)


def stage_move(accepted,state,trace,translation):return stage_group_edit(accepted,state,trace,'MOVE',translation)


def affected_guids(m,native):
    if m.get('operation')!='MOVE':return m['members']
    nodes={r['guid'].lower():r for r in native['elements']}
    return sorted(set(m['members'])|{g for parent in m['members'] for g,_ in V.M.owned_children(nodes,parent,'Column')})


def api_for(m,state,execute=False,saved_sha=None):
    api,guard=G.prepare_api(m,state,execute=execute,saved_sha=saved_sha,authorization_ref=operation(m)[1])
    api.allowed|={'GetNativeGroupRootsV1'}
    return api,guard


def current_plan(state):
    state=Path(state).resolve();m=manifest(state,True);api,_=api_for(m,state)
    ids,native=B.capture(m,api)
    need(R.digest(ids)==m['baselineGuidSetSHA256'] and G.fingerprint(native)==m['baselineBrepSHA256'] and
         V.semantic_digest(native,set(ids))==m['baselineSemanticSHA256'],'GROUP_CREATE_CURRENT_MODEL_DRIFT')
    adapter,_,_,_=operation(m)
    router=F.native_command_router();task=dict(schemaVersion=adapter.SCHEMA,request='Сгруппировать проверенные существующие колонны' if adapter is N else 'Разгруппировать проверенную нативную группу',sourceRef=SOURCE_REF,memberGuids=m['members'])
    if adapter is not N:task['groupGuid']=m['groupGuid']
    if m.get('operation')=='MOVE':task.update(translation=m['translation'],request='Переместить целую проверенную нативную группу')
    writer=R.SceneWriter(api,journal_path=state/'batch-scenewriter.sqlite',schema_path=G.SCHEMA_PATH,allow_3d_view_for_write=True)
    selected=A.prepare_current_runtime_group_native_task(router,writer,task)['preview']
    ops=selected['selectedNativeTaskPreview']['workflow']['graph']['operations']
    need(len(ops)==1 and ops[0]['command']==adapter.CMD,'GROUP_CREATE_ONE_NATIVE_GROUP_COMMAND_REQUIRED')
    affected=affected_guids(m,native)
    proof=adapter.before(api=api,command=adapter.CMD,parameters=ops[0]['params'],affected=affected,native_before=native)
    need(api.write_attempts==0,'GROUP_CREATE_PLAN_READONLY_REQUIRED')
    return dict(status='GROUP_CREATE_CURRENT_NATIVE_PLAN_PASS',task=task,params=ops[0]['params'],sourceProof=proof,
        runtimeIdentity=P.verify_runtime(api),contractSHA256=router.contract_hash(adapter.CMD),baselineGuids=ids,affectedGuids=affected,nativeWrites=0)


def plan(state):
    state=Path(state).resolve();need(not (state/'plan.json').exists(),'GROUP_CREATE_PLAN_ALREADY_PINNED')
    p=current_plan(state);write(state/'plan.json',p);return p


def verify_model(m,api,p,response):
    ids,native=B.capture(m,api)
    adapter,_,_,_=operation(m)
    proof=adapter.after(api=api,command=adapter.CMD,parameters=p['params'],native_response=response,
        before_guids=set(p['baselineGuids']),after_guids=set(ids),affected=p.get('affectedGuids',m['members']),
        native_before={},native_after=native,source_proof=p['sourceProof'])
    return ids,native,proof


def execute(state):
    state=Path(state).resolve();m=manifest(state,True);p=read(state/'plan.json')
    need(R.canonical(current_plan(state))==R.canonical(p),'GROUP_CREATE_PINNED_PLAN_DRIFT')
    lease=B.ScratchWriteLease(m['scratch'],state,m['scratchInitialSHA256']);lease.acquire()
    write(state/'attempted.json',dict(planSHA256=sha256(state/'plan.json'),automaticReplay=False))
    try:
        adapter,auth,create_scene,save_scene=operation(m)
        api,guard=api_for(m,state,True);router=F.native_command_router()
        need(P.verify_runtime(api)==p['runtimeIdentity'],'GROUP_CREATE_RUNTIME_DRIFT')
        adapter.attach(router);router.probe_runtime(api,adapter.CMD)
        selected=A.prepare_auto_optimized_native_task(router,p['task']);graph=selected['selectedNativeTaskPreview']['workflow'];op=graph['graph']['operations'][0]
        need(op['params']==p['params'] and router.contract_hash(adapter.CMD)==p['contractSHA256'],'GROUP_CREATE_CONTRACT_DRIFT')
        with sqlite3.connect(state/'batch-scenewriter.sqlite') as db:
            db.execute('CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,plan_hash TEXT NOT NULL,state TEXT NOT NULL,result TEXT NOT NULL)')
            db.execute('CREATE TABLE steps(scene_id TEXT NOT NULL,step_id TEXT NOT NULL,state TEXT NOT NULL,guid TEXT,output TEXT NOT NULL,PRIMARY KEY(scene_id,step_id))')
        writer=R.SceneWriter(api,journal_path=state/'batch-scenewriter.sqlite',schema_path=G.SCHEMA_PATH,allow_3d_view_for_write=True)
        spec=dict(schemaVersion='apa-ac29-dynamic-mutation-scope/1',projectSha256=m['scratchInitialSHA256'],sourcePlanHash=graph['sourcePlanHash'],
            authorizationRef=auth,sourceEvidenceRef=SOURCE_REF,sceneId=create_scene,stepId=op['id'],command=adapter.CMD,effect='MODIFY',impact='MODEL',
            commandContractHash=p['contractSHA256'],parametersHash=R.digest(p['params']),expectedBeforeGuidSetHash=m['baselineGuidSetSHA256'],
            expectedBeforeNativeBrepHash=m['baselineBrepSHA256'],affectedGuids=p['affectedGuids'],retainedGuids=sorted(set(p['baselineGuids'])-set(p['affectedGuids'])),verifierId=adapter.VERIFIER)
        scopes=build_existing_workflow_scopes(spec=spec,plan=graph,router=router,registry=installed_verifiers(),writer=writer,api=api,
            capture_model=B.D.capture_full_model,guid_inventory=A.inventory_guids,current_project_sha=lambda:sha256(m['scratch']),
            approved_project_sha=m['scratchInitialSHA256'],local_authorization=auth)
        result=A.run_auto_optimized_native_task(router,api,selected,writer,scopes)
        need(result['status']=='WORKFLOW_CALLABLE_VERIFIED' and api.calls[adapter.CMD]==1,'GROUP_CREATE_UNKNOWN_NO_REPLAY')
        response=result['results'][op['id']];ids,native,proof=verify_model(m,api,p,response)
        signatures=B.C.retained_geometry_signatures(native,ids);verified_semantic=V.semantic_digest(native,set(ids));guard.enable_after_verified_copy()
        router.review_policy('SaveProject','TRANSACTION','PROJECT',dict(source=SOURCE_REF,sha256=router.contract_hash('SaveProject')))
        def before_save(live):
            manifest(state);fresh,current,_=verify_model(m,live,p,response)
            need(fresh==ids and V.semantic_digest(current,set(ids))==verified_semantic and lease.verify() and
                 sha256(m['scratch'])==m['scratchInitialSHA256'],'GROUP_CREATE_PRESAVE_DRIFT')
            return dict(status='GROUP_CREATE_PRESAVE_PASS')
        def after_save(reply,_):
            need(reply=={'success':True} and guard.new_saved_sha and lease.verify(),'GROUP_CREATE_SAVE_UNCONFIRMED')
            protected={m['source']:m['sourceSHA256'],m['originalProtected']:m['originalProtectedSHA256'],**m['protectedAncestors']}
            snap=B.preserve_guarded_save(m['scratch'],state/'guarded-save.snapshot',guard.new_saved_sha,protected)
            write(state/'guarded-snapshot.json',snap);return dict(status='GROUP_CREATE_SAVE_SNAPSHOT_PASS')
        saved=router.execute(writer,save_scene,router.prepare('SaveProject',{}),[],signatures,m['scratchInitialSHA256'],auth,'PROJECT',after_save,verify_before=before_save)
        need(saved['status']=='PASS' and api.calls['SaveProject']==1 and api.write_attempts==2,'GROUP_CREATE_ONE_GROUP_ONE_SAVE_REQUIRED')
        r=dict(schema=SCHEMA,status='SHARED_GROUP_CREATE_SAVED_PENDING_REOPEN',nativeResponse=response,nativeReadback=proof,
            finalGuidCount=len(ids),finalGuidSetSHA256=R.digest(ids),finalBrepSHA256=G.fingerprint(native),
            finalSemanticSHA256=V.semantic_digest(native,set(ids)),savedSHA256=guard.new_saved_sha,
            snapshotReceiptSHA256=sha256(state/'guarded-snapshot.json'),nativeGroupCommand=adapter.CMD,
            groupCreateCalls=int(adapter is N),ungroupCalls=int(adapter.CMD.endswith('.UngroupNativeGroupV1')),
            groupMoveCalls=int(adapter.CMD.endswith('.MoveNativeGroupV1')),saveCalls=1,reopenVerified=False,automaticReplay=False)
        write(state/'saved.json',r);return r
    except Exception as exc:
        write(state/'failed.json',dict(status='UNKNOWN_NO_REPLAY_READONLY_RECONCILIATION_REQUIRED',error=str(exc),automaticReplay=False));raise


def saved_state(state):
    state=Path(state).resolve();m=manifest(state);r=read(state/'saved.json');snap=read(state/'guarded-snapshot.json')
    need(r['status']=='SHARED_GROUP_CREATE_SAVED_PENDING_REOPEN' and sha256(m['scratch'])==sha256(state/'guarded-save.snapshot')==r['savedSHA256'] and
         sha256(state/'guarded-snapshot.json')==r['snapshotReceiptSHA256'] and snap['savedSHA256']==snap['snapshotSHA256']==r['savedSHA256'],
         'GROUP_CREATE_SAVED_BYTES_DRIFT')
    return m,r


def check_closed(state):
    state=Path(state).resolve();m,r=saved_state(state);api,_=api_for(m,state,saved_sha=r['savedSHA256'])
    try:api('GetProjectInfo',{})
    except Exception as exc:need('4001' in str(exc) and 'no open project' in str(exc).lower(),'GROUP_CREATE_REAL_CLOSE_REQUIRED')
    else:raise ValueError('GROUP_CREATE_PROJECT_STILL_OPEN')
    result=dict(status='NATIVE_NO_OPEN_PROJECT_CONFIRMED',savedSHA256=r['savedSHA256'],nativeWrites=0)
    write(state/'closed.json',result);return result


def verify_reopen(state):
    state=Path(state).resolve();m,r=saved_state(state);closed=read(state/'closed.json');p=read(state/'plan.json')
    need(closed['status']=='NATIVE_NO_OPEN_PROJECT_CONFIRMED' and closed['savedSHA256']==r['savedSHA256'],'GROUP_CREATE_GUI_CLOSE_REQUIRED')
    api,_=api_for(m,state,saved_sha=r['savedSHA256']);need(P.verify_runtime(api)==p['runtimeIdentity'],'GROUP_CREATE_REOPEN_RUNTIME_DRIFT')
    ids,native,proof=verify_model(m,api,p,r['nativeResponse'])
    need(R.digest(ids)==r['finalGuidSetSHA256'] and G.fingerprint(native)==r['finalBrepSHA256'] and
         V.semantic_digest(native,set(ids))==r['finalSemanticSHA256'] and api.write_attempts==0,'GROUP_CREATE_REOPEN_NATIVE_DRIFT')
    status={'CREATE':'LIVE_SHARED_NATIVE_GROUP_CREATE_SAVED_REOPENED_PASS','UNGROUP':'LIVE_SHARED_NATIVE_GROUP_UNGROUP_SAVED_REOPENED_PASS',
            'MOVE':'LIVE_SHARED_NATIVE_GROUP_MOVE_SAVED_REOPENED_PASS'}[m.get('operation','CREATE')]
    result=dict(r,status=status,reopenVerified=True,reopenedReadback=proof,sourceUnchanged=True,verificationNativeWrites=0)
    write(state/'reopened.json',result);return result
