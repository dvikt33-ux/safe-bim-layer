"""Native flat-group edit: retain every physical member and other group."""
from pathlib import Path
import json,copy,re,hashlib
import apa_ac29_native_group_create as N
R,V,G,need=N.R,N.V,N.G,N.need
SCHEMA='apa-native-group-ungroup/1'
CMD='AddOn.TapirCommand.UngroupNativeGroupV1'
VERIFIER='VerifiedNativeGroupUngroup'

def group(parameters):
    need(isinstance(parameters,dict) and set(parameters)=={'groupId','sourceRef'} and
         isinstance(parameters['groupId'],dict) and set(parameters['groupId'])=={'guid'} and
         isinstance(parameters['groupId']['guid'],str) and G.GROUP_GUID.fullmatch(parameters['groupId']['guid'].lower()) and
         parameters['groupId']['guid'].lower()!=V.NULL and isinstance(parameters['sourceRef'],str) and len(parameters['sourceRef'])>=8,
         'GROUP_UNGROUP_EXPLICIT_GROUP_AND_SOURCE_REQUIRED')
    return parameters['groupId']['guid'].lower()

def attach(router):
    p=Path(__file__).resolve().parents[1]/'schemas/accelerator/native-group-ungroup.json'
    data=p.read_bytes().replace(b'\r\n',b'\n')
    need(hashlib.sha256(data).hexdigest()=='19fb1ee32ac08f74be1632e1ddc5390adb2b48bd72825fa31f5b24ca1d91d126',
         'GROUP_UNGROUP_CODE_OWNED_CONTRACT_DRIFT')
    row=json.loads(data)
    need(row['implementationSHA256']=='f915d0a2f6127e489eacebd242f72fcab3c409ce07ea7290efa3fb38175d0528',
         'GROUP_UNGROUP_SDK_SOURCE_DRIFT')
    if CMD not in router.catalog['commands']:router.add_provider('TapirCommand',{'UngroupNativeGroupV1':row},str(p))
    current=router.catalog['commands'][CMD]
    need(all(current.get(k)==row.get(k) for k in ('version','parameters','returns')),'GROUP_UNGROUP_EXISTING_CONTRACT_DRIFT')
    current['implementationSHA256']=row['implementationSHA256']
    router.review_policy(CMD,'MODIFY','MODEL',dict(source='NativeGroupCommands.inc: explicitly release flat group membership only',sha256=router.contract_hash(CMD)))
    router.fingerprint=R.digest(router.catalog)

def prepare(router,task):
    need(isinstance(task,dict) and set(task)=={'schemaVersion','request','sourceRef','groupGuid','memberGuids'} and
         task['schemaVersion']==SCHEMA and isinstance(task['request'],str) and re.search(r'разгрупп|ungroup',task['request'],re.I) and
         isinstance(task['memberGuids'],list),'GROUP_UNGROUP_EXACT_INTENT_REQUIRED')
    ids=N.members(dict(memberIds=[dict(guid=g) for g in task['memberGuids']],sourceRef=task['sourceRef']))
    params=dict(groupId=dict(guid=task['groupGuid']),sourceRef=task['sourceRef']);group(params);attach(router)
    from archicad_project_accelerator import prepare_native_task
    native=prepare_native_task(router,dict(schemaVersion='apa-native-task/1',request=task['request'],
        graph=dict(operations=[dict(id='ungroup_native_group',command=CMD,params=params,after=[])])))
    registered=router.registration.get(CMD) is True
    return dict(schema='APA_AUTO_NATIVE_TASK_V1',adapterVersion='AC29_GROUP_UNGROUP_V1',
        status='ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED' if registered else 'GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION',
        selectedNativeTaskPreview=native if registered else None,candidateNativeTaskPreview=native,
        requiredRuntimeCommands=[CMD],nativeCallCountIfAuthorized=1,nativeWritePermission=False,
        automaticNativeExecution=False,physicalMembersModifiedOnlyByGrouping=ids)

def before(*,api,command,parameters,affected,native_before):
    guid=group(parameters);ids=sorted(G.group_member_ids(api,guid));nodes={r['guid'].lower():r for r in native_before['elements']}
    need(command==CMD and 2<=len(ids)<=128 and ids==sorted(affected) and
         all(g in nodes and nodes[g]['type']=='Column' for g in ids),'GROUP_UNGROUP_EXACT_EXISTING_COLUMN_MEMBERS_REQUIRED')
    groups=N.column_group_roots(api,native_before)
    need(all(groups[g]==dict(groupId=guid,rootGroupId=guid) for g in ids),'GROUP_UNGROUP_FLAT_COMPLETE_GROUP_REQUIRED')
    return dict(status='GROUP_UNGROUP_FULL_NATIVE_PREFLIGHT_PASS',groupId=guid,members=ids,
        sourceFacts=V.facts(api,nodes,ids,native_before),beforeGroups=groups,
        semanticSHA256=V.semantic_digest(native_before,set(nodes)))

def after(*,api,command,parameters,native_response,before_guids,after_guids,affected,native_before,native_after,source_proof):
    guid=group(parameters);ids=source_proof['members'];reply=native_response
    need(command==CMD and guid==source_proof['groupId'] and sorted(affected)==ids and before_guids==after_guids and
         isinstance(reply,dict) and set(reply)=={'nativeModelWrites','previousGroupId','releasedMembers'} and
         reply['nativeModelWrites']==1 and reply['previousGroupId'].get('guid','').lower()==guid and
         sorted(r.get('guid','').lower() for r in reply['releasedMembers'])==ids,
         'GROUP_UNGROUP_NATIVE_RESPONSE_OR_GUID_DELTA_INVALID')
    need(V.semantic_digest(native_after,after_guids)==source_proof['semanticSHA256'],
         'GROUP_UNGROUP_PHYSICAL_GEOMETRY_MATERIAL_OR_RELATION_CHANGED')
    nodes={r['guid'].lower():r for r in native_after['elements']}
    need(V.facts(api,nodes,ids,native_after)==source_proof['sourceFacts'],'GROUP_UNGROUP_MEMBER_NATIVE_FACTS_CHANGED')
    groups=N.column_group_roots(api,native_after);expected=copy.deepcopy(source_proof['beforeGroups'])
    for g in ids:expected[g]=dict(groupId=V.NULL,rootGroupId=V.NULL)
    need(groups==expected,'GROUP_UNGROUP_RELEASE_OR_OTHER_GROUP_CHANGED')
    return dict(status='NATIVE_GROUP_UNGROUP_SHARED_REGISTRY_READBACK_PASS',previousGroupId=guid,memberGuids=ids,
        physicalGuidCount=len(after_guids),allPhysicalGeometryAndMaterialsPreserved=True,otherColumnGroupsUnchanged=True)

def installed_group_ungroup_verifiers():
    return {VERIFIER:N.NativeVerifier(verifier_id=VERIFIER,command=CMD,effect='MODIFY',before=before,after=after)}
