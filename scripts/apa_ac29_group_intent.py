"""Bounded user-language intent -> already accepted native group adapters.

The request chooses the action. GUIDs, source and translation remain explicit;
no model writes, tool permission or dimensions are inferred from prose.
"""
import copy,re
import apa_ac29_native_group_create as N
import apa_ac29_native_group_ungroup as U
import apa_ac29_native_group_move as M
SCHEMA='apa-native-group-request/1'
need=N.need

def normalize(task):
    need(isinstance(task,dict) and set(task)=={'schemaVersion','request','sourceRef','memberGuids','groupGuid','translation'} and
         task['schemaVersion']==SCHEMA and isinstance(task['request'],str) and task['request'].strip() and
         isinstance(task['memberGuids'],list),'AUTO_GROUP_EXACT_EXPLICIT_SOURCE_TASK_REQUIRED')
    text=task['request'].casefold()
    need(re.search(r'групп|group',text),'AUTO_GROUP_EXPLICIT_GROUP_INTENT_REQUIRED')
    need(not re.search(r'булев|boolean|\bunion\b|слить.*тел',text),'AUTO_GROUP_BOOLEAN_BODY_UNION_UNSUPPORTED')
    need(not re.search(r'копир|тираж|клонир|размнож|\bcopy\b|\bclone\b|\bmultiply\b|\barray\b',text),
         'AUTO_GROUP_COPY_REQUIRES_EXISTING_MASS_REQUEST_WITH_PLACEMENTS')
    actions=[]
    if re.search(r'разгрупп|\bungroup\b',text):actions.append(('UNGROUP',U))
    if re.search(r'перемест|сдви|\bmove\b|\btranslat',text):actions.append(('MOVE',M))
    if re.search(r'сгруппир|^группир|созд[а-яё]*.*групп|объедин[а-яё]*.*групп|(?:create|make|form)\s+(?:a\s+)?group|^group\s+',text):
        actions.append(('CREATE_GROUP',N))
    need(len(actions)==1,'AUTO_GROUP_AMBIGUOUS_OR_UNSUPPORTED_ACTION_REQUIRES_SINGLE_INTENT')
    action,adapter=actions[0]
    ids=N.members(dict(memberIds=[dict(guid=g) for g in task['memberGuids']],sourceRef=task['sourceRef']))
    typed=dict(schemaVersion=adapter.SCHEMA,request=task['request'],sourceRef=task['sourceRef'],memberGuids=ids)
    if adapter is N:
        need(task['groupGuid'] is None and task['translation'] is None,'AUTO_GROUP_CREATE_CANNOT_IMPLICITLY_REGROUP_OR_MOVE')
    else:
        U.group(dict(groupId=dict(guid=task['groupGuid']),sourceRef=task['sourceRef']))
        typed['groupGuid']=task['groupGuid'].lower()
        if adapter is M:typed['translation']=copy.deepcopy(M.shift(task['translation']))
        else:need(task['translation'] is None,'AUTO_GROUP_UNGROUP_CANNOT_SILENTLY_MOVE')
    return typed,dict(action=action,nativeCommand=adapter.CMD,codeOwnedVerifier=adapter.VERIFIER,
        sourceMembers=ids,coordinatesInferred=False,nativeWritePermission=False)
