"""Extend a verified authored shell through the existing SceneWriter.

Supports an explicit Basic wall material change and added hosted openings or
columns. Existing geometry must match; durable reservation precedes mutation.
"""
from contextlib import closing
import copy
import sqlite3
import archicad_project_accelerator as A

RUN = A.RUN
TABLE = 'authored_extensions'


def verify_model(api, plan, created):
    operations = {s['id']: s for s in plan['graph']['operations']}
    verified = {}
    for sid in plan['executionOrder']:
        if sid not in created:
            continue
        step = operations[sid]
        params = RUN.resolve_params(step, {'__plan__': plan['graph'], **created})
        if step['command'] in ('CreateDoors', 'CreateWindows'):
            host = step['params'][step['command'][6:].lower()+'Data'][0]['ownerWallId']['guid']['$createdGuid']
            floor = verified[host]['floorIndex']
            owner = created[host]['guid']
        else:
            floor = next(iter(params.values()))[0]['floorIndex']
            owner = None
        kind = RUN.verify_readback(step['command'], params,
            RUN.requested_details(api, created[sid]['guid']), owner,
            expected_floor=floor,
            expected_story_level=RUN.story_level_for_floor(plan['storyBindings'], floor),
            expected_slab_material_guid=plan['slabBasicMaterialGuid'] if step['command']=='CreateSlabs' else None,
            slab_level_is_absolute=True)
        verified[sid] = {'guid': created[sid]['guid'], 'kind': kind, 'floorIndex': floor}
    return verified


def prepare(api, intent, old_plan, old_created, journal, operation_id):
    binding = RUN.guarded_project(api, old_plan['storyBindings'][0])
    if binding != old_plan['binding'] or binding['path'] != RUN.APPROVED_ISOLATED_WRITER_PATH:
        raise ValueError('EXTENSION_TARGET_CHANGED')
    if not isinstance(operation_id, str) or not RUN._SCENE_ID.fullmatch(operation_id):
        raise ValueError('INVALID_EXTENSION_ID')
    # Historical checkpoint must be complete, with distinct explicit owned GUIDs.
    old_ops = {s['id']:s for s in old_plan['graph']['operations']}
    if set(old_created) != set(old_ops):
        raise ValueError('INCOMPLETE_SOURCE_MODEL')
    owned = {v['guid'].lower() for v in old_created.values()}
    inventory = A.inventory_guids(api)
    if len(owned) != len(old_created) or not owned <= set(inventory):
        raise ValueError('SOURCE_GUIDS_MISSING_OR_DUPLICATED')
    verify_model(api, old_plan, old_created)
    compiled = A.compile_authored_intent(intent, RUN.DEFAULT_SCENE_SCHEMA, api)
    new_ops = {s['id']:s for s in compiled['graph']['operations']}
    if not set(old_ops) <= set(new_ops):
        raise ValueError('EXTENSION_REMOVES_SOURCE_OPERATION')
    modify = []
    for sid, old in old_ops.items():
        proposed = copy.deepcopy(new_ops[sid])
        if old['command']=='CreateWalls':
            material = proposed['params']['wallsData'][0].pop('buildingMaterialId', None)
            original = copy.deepcopy(old)
            original['params']['wallsData'][0].pop('buildingMaterialId', None)
            if proposed != original or not material:
                raise ValueError('EXTENSION_CHANGES_SOURCE_GEOMETRY')
            modify.append({'elementId':{'guid':old_created[sid]['guid']},
                           'structureType':'Basic', 'buildingMaterialId':material})
        elif proposed != old:
            raise ValueError('EXTENSION_CHANGES_SOURCE_GEOMETRY')
    if any(new_ops[sid]['command'] not in {'CreateColumns','CreateDoors','CreateWindows'}
           for sid in set(new_ops)-set(old_ops)):
        raise ValueError('EXTENSION_UNSUPPORTED_ADDITION')
    def scan(command, params):
        result = api(command, params)
        if command=='GetAllElements':
            if sorted(r['elementId']['guid'].lower() for r in result['elements']) != inventory:
                raise ValueError('EXTENSION_INVENTORY_DRIFT')
            return {'elements':[r for r in result['elements'] if r['elementId']['guid'].lower() not in owned]}
        return result
    writer = RUN.SceneWriter(scan, journal,
        preview_factory=A.AUTHORED_NATIVE.make_read_only_scene_writer_preview_factory(compiled['authoredCandidate']))
    envelope = compiled['envelope']
    plan = writer.preflight(envelope['xMin'], envelope['yMin'])
    record = {'operationId':operation_id, 'binding':binding, 'inventory':inventory,
              'oldCreated':old_created, 'oldPlan':old_plan, 'oldPlanHash':old_plan['sourcePlanHash'],
              'newPlanHash':plan['sourcePlanHash'], 'modify':{'wallsWithDetails':modify}}
    with closing(sqlite3.connect(journal)) as db:
        db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE}(operation_id TEXT PRIMARY KEY,state TEXT,intent TEXT,result TEXT)')
        db.commit()
        if db.execute(f'SELECT 1 FROM {TABLE} WHERE operation_id=?',(operation_id,)).fetchone():
            raise ValueError('EXTENSION_ALREADY_RESERVED_NEVER_RETRY')
    return {'status':'READY_FOR_AUTHORED_EXTENSION','confirmPlanHash':RUN.digest(record),
            'intent':record,'preflight':plan,'modelWriteAttempts':0}


def execute(api, ticket, journal, confirm_hash):
    record, plan = ticket['intent'], ticket['preflight']
    if confirm_hash != ticket['confirmPlanHash'] or RUN.digest(record)!=confirm_hash:
        raise ValueError('EXTENSION_TOKEN_MISMATCH')
    if plan['sourcePlanHash'] != record['newPlanHash']:
        raise ValueError('EXTENSION_PLAN_DRIFT')
    with closing(sqlite3.connect(journal)) as db:
        db.execute('PRAGMA synchronous=FULL'); db.execute('BEGIN IMMEDIATE')
        db.execute(f'INSERT INTO {TABLE} VALUES(?,?,?,?)',
            (record['operationId'],'ATTEMPTED',RUN.canonical(record),'{}'))
        db.commit()
        try:
            if RUN.guarded_project(api, plan['storyBindings'][0])!=record['binding'] or A.inventory_guids(api)!=record['inventory']:
                raise ValueError('EXTENSION_OPERATION_BOUNDARY_DRIFT')
            verify_model(api, record['oldPlan'], record['oldCreated'])
            response = api('ModifyWalls',record['modify'])
            if response.get('executionResults') != [{'success':True}]*len(record['modify']['wallsWithDetails']):
                raise ValueError('WALL_MATERIAL_MODIFY_NOT_CONFIRMED')
            prefix = verify_model(api, plan, record['oldCreated'])
            if A.inventory_guids(api)!=record['inventory']:
                raise ValueError('GUIDS_CHANGED_DURING_WALL_MATERIAL_CHANGE')
        except Exception as exc:
            result = {'status':'PARTIAL_OR_UNKNOWN_OUTCOME','reason':str(exc),'automaticRetry':False}
            db.execute(f'UPDATE {TABLE} SET state=?,result=? WHERE operation_id=?',
                (result['status'],RUN.canonical(result),record['operationId'])); db.commit()
            return result
    def final_check(preflight, created):
        verify_model(api, preflight, {k:v for k,v in created.items() if k!='__plan__'})
        original_owned = {v['guid'].lower() for v in record['oldCreated'].values()}
        expected = sorted((set(record['inventory'])-original_owned) |
            {v['guid'].lower() for k,v in created.items() if k!='__plan__'})
        if A.inventory_guids(api)!=expected:
            raise ValueError('EXTENSION_FINAL_WHOLE_MODEL_GUID_DIFF')
    writer = RUN.SceneWriter(api, journal); writer.required_story = plan['storyBindings'][0]
    result = writer._execute_verified_plan(plan,record['operationId'],plan['sourcePlanHash'],
        seeded_created=prefix, approval_source='Current user: запись в pln разрешаю любую, продолжай',
        on_before_complete=final_check)
    with closing(sqlite3.connect(journal)) as db:
        db.execute(f'UPDATE {TABLE} SET state=?,result=? WHERE operation_id=?',
            (result['status'],RUN.canonical(result),record['operationId'])); db.commit()
    return result
