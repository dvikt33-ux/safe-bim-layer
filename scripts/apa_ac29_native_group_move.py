"""Whole native group translation with owned-segment scope and exact readback."""
from pathlib import Path
import json,math,hashlib,re
import apa_ac29_native_group_ungroup as U
N,R,V,G,need=U.N,U.R,U.V,U.G,U.need
SCHEMA='apa-native-group-move/1';CMD='AddOn.TapirCommand.MoveNativeGroupV1';VERIFIER='VerifiedNativeGroupMove'

def shift(value):
    need(isinstance(value,dict) and set(value)=={'dx','dy','dz'} and
         all(type(n) in (int,float) and math.isfinite(n) and abs(n)<=10000 for n in value.values()) and
         value['dz']==0 and (value['dx']!=0 or value['dy']!=0),'GROUP_MOVE_EXPLICIT_HORIZONTAL_NONZERO_TRANSLATION_REQUIRED')
    return value

def checked(parameters):
    need(isinstance(parameters,dict) and set(parameters)=={'groupId','sourceRef','translation'},'GROUP_MOVE_EXACT_PARAMETERS_REQUIRED')
    return U.group({k:parameters[k] for k in ('groupId','sourceRef')}),shift(parameters['translation'])

def attach(router):
    p=Path(__file__).resolve().parents[1]/'schemas/accelerator/native-group-move.json';data=p.read_bytes().replace(b'\r\n',b'\n')
    need(hashlib.sha256(data).hexdigest()=='29a37e2e394492339d74428a2bb26e2496684f6a94eb347db3cd39602c74de89','GROUP_MOVE_CONTRACT_DRIFT')
    row=json.loads(data)
    if CMD not in router.catalog['commands']:router.add_provider('TapirCommand',{'MoveNativeGroupV1':row},str(p))
    current=router.catalog['commands'][CMD]
    need(all(current.get(k)==row.get(k) for k in ('version','parameters','returns')),'GROUP_MOVE_EXISTING_CONTRACT_DRIFT')
    current['implementationSHA256']=row['implementationSHA256']
    router.review_policy(CMD,'MODIFY','MODEL',dict(source='NativeGroupCommands.inc: one whole flat-group translation',sha256=router.contract_hash(CMD)))
    router.fingerprint=R.digest(router.catalog)

def prepare(router,task):
    need(isinstance(task,dict) and set(task)=={'schemaVersion','request','sourceRef','groupGuid','memberGuids','translation'} and
         task['schemaVersion']==SCHEMA and isinstance(task['request'],str) and re.search(r'перемест|сдви|move|translat',task['request'],re.I) and
         isinstance(task['memberGuids'],list),'GROUP_MOVE_EXACT_INTENT_REQUIRED')
    ids=N.members(dict(memberIds=[dict(guid=g) for g in task['memberGuids']],sourceRef=task['sourceRef']))
    params=dict(groupId=dict(guid=task['groupGuid']),sourceRef=task['sourceRef'],translation=task['translation']);checked(params);attach(router)
    from archicad_project_accelerator import prepare_native_task
    native=prepare_native_task(router,dict(schemaVersion='apa-native-task/1',request=task['request'],graph=dict(operations=[dict(id='move_native_group',command=CMD,params=params,after=[])])))
    registered=router.registration.get(CMD) is True
    return dict(schema='APA_AUTO_NATIVE_TASK_V1',adapterVersion='AC29_GROUP_MOVE_V1',status='ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED' if registered else 'GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION',
        selectedNativeTaskPreview=native if registered else None,candidateNativeTaskPreview=native,requiredRuntimeCommands=[CMD],nativeCallCountIfAuthorized=1,
        nativeWritePermission=False,automaticNativeExecution=False,physicalMembersModifiedOnlyByTranslation=ids)

def before(*,api,command,parameters,affected,native_before):
    guid,vector=checked(parameters);nodes={r['guid'].lower():r for r in native_before['elements']}
    roots=sorted(g for g in affected if g in nodes and nodes[g]['type']=='Column')
    proof=U.before(api=api,command=U.CMD,parameters={k:parameters[k] for k in ('groupId','sourceRef')},affected=roots,native_before=native_before)
    owned=set(roots)|{c for f in proof['sourceFacts'].values() for c in f['childGuids']}
    need(command==CMD and set(affected)==owned,'GROUP_MOVE_FULL_OWNED_MEMBER_SCOPE_REQUIRED')
    from apa_ac29_reusable_native_copy import native_aabb_overlaps
    moved,others=[],[]
    for g,node in nodes.items():
        for body in node.get('bodies',[]):
            vertices=body.get('vertices',[])
            if not vertices:continue
            delta=[vector['dx'],vector['dy'],0] if g in owned else [0,0,0]
            box=[(min(v[i] for v in vertices)+delta[i],max(v[i] for v in vertices)+delta[i]) for i in range(3)]
            (moved if g in owned else others).append(box)
    need(bool(moved) and not any(native_aabb_overlaps(a,b) for i,a in enumerate(moved) for b in moved[i+1:]+others),
         'GROUP_MOVE_TARGET_SOLIDS_TOUCH_OR_INTERSECT')
    proof.update(status='GROUP_MOVE_FULL_NATIVE_PREFLIGHT_PASS',translation=vector,affectedGuids=sorted(owned),
        retainedSemanticSHA256=V.semantic_digest(native_before,set(nodes)-owned),collisionProof='NATIVE_BREP_AABB_CLEAR_PASS')
    return proof

def after(*,api,command,parameters,native_response,before_guids,after_guids,affected,native_before,native_after,source_proof):
    guid,vector=checked(parameters);p=source_proof;ids=p['members'];reply=native_response
    need(command==CMD and guid==p['groupId'] and vector==p['translation'] and sorted(affected)==p['affectedGuids'] and before_guids==after_guids and
         isinstance(reply,dict) and set(reply)=={'nativeModelWrites','groupId','movedMembers'} and reply['nativeModelWrites']==len(ids) and
         reply['groupId'].get('guid','').lower()==guid and sorted(r.get('guid','').lower() for r in reply['movedMembers'])==ids,
         'GROUP_MOVE_NATIVE_REPLY_OR_GUID_DELTA_INVALID')
    need(V.semantic_digest(native_after,after_guids-set(affected))==p['retainedSemanticSHA256'],'GROUP_MOVE_RETAINED_PHYSICAL_MODEL_CHANGED')
    nodes={r['guid'].lower():r for r in native_after['elements']};facts=V.facts(api,nodes,ids,native_after);mapping=[]
    for g,old in p['sourceFacts'].items():
        current=facts[g];target={k:old['anchor'][k]+vector['d'+k] for k in ('x','y','z')}
        need(all(abs(current['anchor'][k]-target[k])<=1e-6 for k in target) and
             dict(current,anchor=old['anchor'])==old,'GROUP_MOVE_TYPED_POSITION_SHAPE_MATERIAL_OR_OWNERSHIP_CHANGED')
        mapping.append(dict(guid=g,target=target,childGuids=old['childGuids']))
    need(N.column_group_roots(api,native_after)==p['beforeGroups'] and sorted(G.group_member_ids(api,guid))==ids,
         'GROUP_MOVE_GROUP_MEMBERSHIP_CHANGED')
    return dict(status='NATIVE_GROUP_MOVE_SHARED_REGISTRY_READBACK_PASS',groupId=guid,memberGuids=ids,mapping=mapping,
        physicalGuidCount=len(after_guids),retainedModelPreserved=True,translatedShapeAndMaterialsPreserved=True,allColumnGroupsUnchanged=True)

def installed_group_move_verifiers():
    return {VERIFIER:N.NativeVerifier(verifier_id=VERIFIER,command=CMD,effect='MODIFY',before=before,after=after)}
