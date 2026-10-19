"""Existing SDK CreateNativeGroupV1 attached to APA selector and native registry.

Physical member GUIDs are MODIFY scope; creating membership never grants
permission to change their geometry, materials, children or other groups.
"""
import json,re,copy,hashlib
from pathlib import Path
import archicad_scene_run as R
import apa_ac29_native_copy_verifier as V
import apa_ac29_native_group_clone_verifier as G
from apa_ac29_dynamic_write_scopes import NativeVerifier

SCHEMA='apa-native-group-create/1'
CMD='AddOn.TapirCommand.CreateNativeGroupV1'
VERIFIER='VerifiedNativeGroupCreate'
need=G.require


def members(parameters):
    need(isinstance(parameters,dict) and set(parameters)=={'memberIds','sourceRef'} and
         isinstance(parameters['sourceRef'],str) and len(parameters['sourceRef'])>=8 and
         isinstance(parameters['memberIds'],list) and 2<=len(parameters['memberIds'])<=128,
         'GROUP_CREATE_EXPLICIT_MEMBERS_AND_SOURCE_REQUIRED')
    rows=parameters['memberIds']
    need(all(isinstance(r,dict) and set(r)=={'guid'} and isinstance(r['guid'],str) and
             G.GROUP_GUID.fullmatch(r['guid'].lower()) for r in rows), 'GROUP_CREATE_EXACT_GUIDS_REQUIRED')
    ids=sorted(r['guid'].lower() for r in rows)
    need(len(set(ids))==len(ids),'GROUP_CREATE_DUPLICATE_MEMBER')
    return ids


def attach(router):
    path=Path(__file__).resolve().parents[1]/'schemas/accelerator/native-group-create.json'
    data=path.read_bytes().replace(b'\r\n',b'\n')
    need(hashlib.sha256(data).hexdigest()=='5f567f93f752c941417d1dad80bbedc060d701514d7b3b68780c2968261b6b33',
         'GROUP_CREATE_CODE_OWNED_CONTRACT_DRIFT')
    row=json.loads(data)
    need(row['implementationSHA256']=='f915d0a2f6127e489eacebd242f72fcab3c409ce07ea7290efa3fb38175d0528',
         'GROUP_CREATE_SDK_CONTRACT_SOURCE_DRIFT')
    if CMD not in router.catalog['commands']:router.add_provider('TapirCommand',{'CreateNativeGroupV1':row},str(path))
    current=router.catalog['commands'][CMD]
    need(all(current.get(k)==row.get(k) for k in ('version','parameters','returns')),'GROUP_CREATE_EXISTING_CONTRACT_DRIFT')
    current['implementationSHA256']=row['implementationSHA256']
    router.review_policy(CMD,'MODIFY','MODEL',dict(source='NativeGroupCommands.inc: membership modification of existing physical roots',sha256=router.contract_hash(CMD)))
    router.fingerprint=R.digest(router.catalog)


def prepare(router,task):
    need(isinstance(task,dict) and set(task)=={'schemaVersion','request','sourceRef','memberGuids'} and
         task['schemaVersion']==SCHEMA and isinstance(task['request'],str) and
         isinstance(task['memberGuids'],list) and
         re.search(r'групп|group',task['request'],re.I),'GROUP_CREATE_EXACT_INTENT_REQUIRED')
    params=dict(memberIds=[dict(guid=g) for g in task['memberGuids']],sourceRef=task['sourceRef'])
    members(params);attach(router)
    from archicad_project_accelerator import prepare_native_task
    native=prepare_native_task(router,dict(schemaVersion='apa-native-task/1',request=task['request'],
        graph=dict(operations=[dict(id='create_native_group',command=CMD,params=params,after=[])])))
    registered=router.registration.get(CMD) is True
    return dict(schema='APA_AUTO_NATIVE_TASK_V1',adapterVersion='AC29_GROUP_CREATE_V1',
        status='ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED' if registered else 'GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION',
        selectedNativeTaskPreview=native if registered else None,candidateNativeTaskPreview=native,
        requiredRuntimeCommands=[CMD],nativeCallCountIfAuthorized=1,nativeWritePermission=False,
        automaticNativeExecution=False,physicalMembersModifiedOnlyByGrouping=members(params))


def column_group_roots(api,native):
    ids=sorted(r['guid'].lower() for r in native['elements'] if r['type']=='Column');found={}
    for i in range(0,len(ids),50):
        batch=ids[i:i+50]
        reply=api('GetNativeGroupRootsV1',dict(elements=[dict(elementId=dict(guid=g)) for g in batch]))
        rows=reply.get('groups')
        need(reply.get('nativeModelWrites')==0 and isinstance(rows,list) and len(rows)==len(batch),
             'GROUP_CREATE_COMPLETE_MEMBERSHIP_READ_REQUIRED')
        for row in rows:
            guid=row.get('elementId',{}).get('guid','').lower()
            need('error' not in row and guid in batch and guid not in found and
                 all(G.GROUP_GUID.fullmatch(row.get(k,{}).get('guid','').lower()) for k in ('groupId','rootGroupId')),
                 'GROUP_CREATE_UNKNOWN_MEMBERSHIP')
            found[guid]={k:row[k]['guid'].lower() for k in ('groupId','rootGroupId')}
    need(set(found)==set(ids),'GROUP_CREATE_MEMBERSHIP_SET_DRIFT')
    return found


def before(*,api,command,parameters,affected,native_before):
    ids=members(parameters);nodes={r['guid'].lower():r for r in native_before['elements']}
    need(command==CMD and sorted(affected)==ids and all(g in nodes and nodes[g]['type']=='Column' for g in ids),
         'GROUP_CREATE_ONLY_EXPLICIT_EXISTING_COLUMN_MEMBERS')
    facts=V.facts(api,nodes,ids,native_before);groups=column_group_roots(api,native_before)
    need(all(groups[g]==dict(groupId=V.NULL,rootGroupId=V.NULL) for g in ids),
         'GROUP_CREATE_EXISTING_GROUP_REQUIRES_OWN_EDIT_ADAPTER')
    return dict(status='GROUP_CREATE_FULL_NATIVE_PREFLIGHT_PASS',members=ids,sourceFacts=facts,
        beforeGroups=groups,semanticSHA256=V.semantic_digest(native_before,set(nodes)))


def after(*,api,command,parameters,native_response,before_guids,after_guids,affected,
          native_before,native_after,source_proof):
    ids=members(parameters);reply=native_response
    need(command==CMD and sorted(affected)==ids==source_proof['members'] and before_guids==after_guids and
         isinstance(reply,dict) and set(reply)=={'nativeModelWrites','groupId','memberCount'} and
         reply['nativeModelWrites']==1 and reply['memberCount']==len(ids), 'GROUP_CREATE_NATIVE_RESULT_OR_GUID_DELTA_INVALID')
    group=reply['groupId'].get('guid','').lower()
    need(G.GROUP_GUID.fullmatch(group) and group!=V.NULL and group not in before_guids,
         'GROUP_CREATE_NATIVE_GROUP_GUID_REQUIRED')
    need(V.semantic_digest(native_after,after_guids)==source_proof['semanticSHA256'],
         'GROUP_CREATE_PHYSICAL_GEOMETRY_MATERIAL_OR_RELATION_CHANGED')
    nodes={r['guid'].lower():r for r in native_after['elements']}
    need(V.facts(api,nodes,ids,native_after)==source_proof['sourceFacts'], 'GROUP_CREATE_MEMBER_NATIVE_FACTS_CHANGED')
    groups=column_group_roots(api,native_after);expected=copy.deepcopy(source_proof['beforeGroups'])
    for guid in ids:expected[guid]=dict(groupId=group,rootGroupId=group)
    need(groups==expected and sorted(G.group_member_ids(api,group))==ids,
         'GROUP_CREATE_EXACT_MEMBERSHIP_OR_OTHER_GROUP_CHANGED')
    return dict(status='NATIVE_GROUP_CREATE_SHARED_REGISTRY_READBACK_PASS',groupId=group,memberGuids=ids,
        physicalGuidCount=len(after_guids),allPhysicalGeometryAndMaterialsPreserved=True,otherColumnGroupsUnchanged=True)


def installed_group_create_verifiers():
    return {VERIFIER:NativeVerifier(verifier_id=VERIFIER,command=CMD,effect='MODIFY',before=before,after=after)}
