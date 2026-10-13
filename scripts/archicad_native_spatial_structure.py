"""Source-bound global story operations through the existing SceneWriter.

No project creation, switching, authorization inference or second executor.
The target must be an explicitly approved saved empty/fully owned test PLN.
"""
import copy
import hashlib
import math
from pathlib import Path
import archicad_project_accelerator as A
import archicad_authored_extension as E

RUN=A.RUN


def template_reference_signatures(api,guids):
    """Only pinned ground-floor, bodyless native Elevations and built-in markers.

    A fresh project from the same template can retain these GUIDs; their presence
    is not proof that a previously created physical building was copied.
    """
    import archicad_connected_components as C
    native=C.G.normalize_dump(api('GetModelDumpV1',{}),allow_empty=True)
    rows={e['guid'].lower():e for e in native['elements']}
    for guid in guids:
        row=rows.get(guid.lower())
        if (not row or row['type'] not in {'Elevation','Object'} or row['homeStory']!=0
                or row['bodies']):
            raise ValueError('SPATIAL_TEMPLATE_REFERENCE_IS_NOT_BODYLESS_GROUND_MARKER')
        if row['type']=='Object':
            part=RUN.requested_details(api,guid)['details'].get('libPart',{})
            name=part.get('name','').casefold()
            if not ('маркер' in name or 'marker' in name) or not part.get('ownUnID',{}).get('guid'):
                raise ValueError('SPATIAL_TEMPLATE_OBJECT_IS_NOT_SOURCE_VERIFIED_MARKER')
    return C.retained_geometry_signatures(native,[g.lower() for g in guids])


def story_settings(rows):
    if not isinstance(rows,list) or not rows:
        raise ValueError('SPATIAL_EXPLICIT_STORIES_REQUIRED')
    result=[]
    for r in rows:
        if (not isinstance(r,dict) or not {'index','name','level','dispOnSections'}<=r.keys()
                or type(r['index']) is not int or type(r['level']) not in (int,float)
                or not math.isfinite(r['level']) or not isinstance(r['name'],str)
                or type(r['dispOnSections']) is not bool):
            raise ValueError('SPATIAL_INVALID_STORY_SETTINGS')
        result.append({k:r[k] for k in ['index','name','level','dispOnSections']})
    if ([r['index'] for r in result]!=list(range(result[0]['index'],result[0]['index']+len(result)))
            or any(b['level']<=a['level'] for a,b in zip(result,result[1:]))):
        raise ValueError('SPATIAL_STORIES_MUST_BE_CONSECUTIVE_AND_ASCENDING')
    return result


def qualify_spatial_operation(scope,command,parameters,source_hash):
    if (scope.get('schema')!='APA_NATIVE_STORY_OPERATION_V1' or command!='SetStories'
            or scope.get('command')!=command or scope.get('parameters')!=parameters
            or scope.get('sourceHash')!=source_hash or not scope.get('authorizationRef')
            or scope.get('scopeHash')!=RUN.digest({k:v for k,v in scope.items() if k!='scopeHash'})):
        raise ValueError('SPATIAL_OPERATION_SCOPE_MISMATCH')
    target=story_settings(parameters.get('stories'))
    if set(parameters)!={'stories'} or target!=parameters['stories']:
        raise ValueError('SPATIAL_EXACT_STORY_SETTINGS_REQUIRED')
    before=story_settings(scope['beforeStories'])
    owned=set(scope['ownedGuids']);forbidden=set(scope['forbiddenGuids'])
    template=scope.get('templateSignatures',{})
    if (owned&forbidden or owned&set(template) or set(template)&forbidden
            or scope['phase'] not in {'EMPTY_SETUP','OWNED_EDIT'}):
        raise ValueError('SPATIAL_PROJECT_OWNERSHIP_INVALID')
    if scope['phase']=='EMPTY_SETUP' and owned:
        raise ValueError('SPATIAL_SETUP_REQUIRES_EMPTY_PROJECT')
    if scope['phase']=='OWNED_EDIT' and (not owned or [r['index'] for r in before]!=[r['index'] for r in target]):
        raise ValueError('SPATIAL_EDIT_CANNOT_INSERT_OR_DELETE_OCCUPIED_STORIES')
    # The retained writer pins active floor0/ID1/elevation0. Do not move its anchor.
    anchor=[r for r in target if r['index']==0]
    if len(anchor)!=1 or anchor[0]['level']!=0 or scope.get('activeStory')!=0:
        raise ValueError('SPATIAL_ACTIVE_GROUND_ANCHOR_REQUIRED')
    if before==target:
        raise ValueError('SPATIAL_NO_STORY_CHANGE')


def prepare_story_operation(api,target_settings,owned_guids,forbidden_guids,
                            authorization_ref,phase='OWNED_EDIT',template_guids=()):
    binding=RUN.guarded_project(api)
    if not RUN.authorized_authored_target(binding['path']):
        raise ValueError('SPATIAL_EXPLICIT_SAVED_TARGET_REQUIRED')
    state=api('GetStories',{});before=story_settings(state['stories'])
    actual=A.inventory_guids(api)
    owned={g.lower() for g in owned_guids};forbidden={g.lower() for g in forbidden_guids}
    template=template_reference_signatures(api,template_guids) if template_guids else {}
    if set(actual)!=owned|set(template) or set(actual)&forbidden:
        raise ValueError('SPATIAL_FOREIGN_OR_ACCEPTED_ELEMENTS_PRESENT')
    parameters={'stories':story_settings(target_settings)}
    source=RUN.digest([binding,state,sorted(owned),parameters])
    scope=dict(schema='APA_NATIVE_STORY_OPERATION_V1',command='SetStories',parameters=parameters,
        sourceHash=source,beforeStories=state['stories'],activeStory=state['actStory'],
        ownedGuids=sorted(owned),forbiddenGuids=sorted(forbidden),phase=phase,
        authorizationRef=authorization_ref,templateSignatures=template)
    scope['scopeHash']=RUN.digest(scope)
    qualify_spatial_operation(scope,'SetStories',parameters,source)
    return dict(sourcePlanHash=source,binding=binding,
        integrationBindings={'dependencies':{'spatialOperation':scope}})


def execute_story_operation(writer,prepared,run_id,saved_sha256):
    scope=prepared['integrationBindings']['dependencies']['spatialOperation']
    params=scope['parameters'];qualify_spatial_operation(scope,'SetStories',params,prepared['sourcePlanHash'])
    def check_owned():
        actual=set(A.inventory_guids(writer.api))
        template=scope.get('templateSignatures',{})
        if actual!=set(scope['ownedGuids'])|set(template) or actual&set(scope['forbiddenGuids']):
            raise ValueError('SPATIAL_PROJECT_INVENTORY_DRIFT')
        if template and template_reference_signatures(writer.api,template)!=template:
            raise ValueError('SPATIAL_TEMPLATE_MARKER_CHANGED')
        if hashlib.sha256(Path(prepared['binding']['path']).read_bytes()).hexdigest()!=saved_sha256:
            raise ValueError('SPATIAL_SAVED_HASH_CHANGED')
    def before():
        check_owned();state=writer.api('GetStories',{})
        if state['stories']!=scope['beforeStories'] or state['actStory']!=scope['activeStory']:
            raise ValueError('SPATIAL_STORY_BASELINE_CHANGED')
        return {'status':'SPATIAL_EMPTY_OR_FULLY_OWNED_BASELINE_PASS','stories':state}
    def after(reply,baseline):
        check_owned();state=writer.api('GetStories',{})
        if story_settings(state['stories'])!=params['stories']:
            raise ValueError('SPATIAL_NATIVE_STORY_READBACK_MISMATCH')
        previous={r['index']:r['floorId'] for r in baseline['stories']['stories']}
        if any(r['floorId']!=previous[r['index']] for r in state['stories'] if r['index'] in previous):
            raise ValueError('SPATIAL_EXISTING_FLOOR_IDENTIFIERS_CHANGED')
        return {'status':'NATIVE_GLOBAL_STORIES_READBACK_PASS','stories':state,
            'ownedIdentityCount':len(scope['ownedGuids']),'nativeElementCreates':0,
            'geometryAcceptance':'REQUIRES_DEPENDENT_ELEMENT_READBACK'}
    intent=dict(sceneId=run_id,sourcePlanHash=prepared['sourcePlanHash'],command='SetStories',
        parameters=params,target=prepared['binding'])
    return writer.execute_bound_operation(prepared,run_id,'SetStories',params,RUN.digest(intent),before,after)


def prepare_height_change(api,plan,created,new_intent,target_settings,schema_path,forbidden_guids,authorization_ref,template_guids=()):
    """Compile source against future stories, never claim overlay as live readback."""
    E.verify_model(api,plan,created)
    prepared=prepare_story_operation(api,target_settings,[v['guid'] for v in created.values()],
        forbidden_guids,authorization_ref,template_guids=template_guids)
    old_state=api('GetStories',{})
    targets={r['index']:r for r in prepared['integrationBindings']['dependencies']['spatialOperation']['parameters']['stories']}
    future=copy.deepcopy(old_state)
    for r in future['stories']:
        r.update(targets[r['index']])
    for a,b in zip(future['stories'],future['stories'][1:]):a['height']=b['level']-a['level']
    def planning_read(command,params):
        return future if command=='GetStories' else api(command,params)
    next_plan=A.compile_authored_intent(new_intent,schema_path,planning_read)
    old={s['id']:s for s in plan['graph']['operations']}
    new={s['id']:s for s in next_plan['graph']['operations']}
    if old.keys()!=new.keys():raise ValueError('SPATIAL_STORY_EDIT_CANNOT_RECREATE_BUILDING')
    old_levels={r['nativeIndex']:r['level'] for r in plan['storyBindings']}
    companion=[]
    for sid,before in old.items():
        after=new[sid]
        if before['command']!=after['command']:raise ValueError('SPATIAL_TOOL_CHANGE_DENIED')
        a=next(iter(before['params'].values()))[0];b=next(iter(after['params'].values()))[0]
        floor=created[sid]['floorIndex'];delta=targets[floor]['level']-old_levels[floor]
        expected=copy.deepcopy(a)
        if before['command'] in {'CreateSlabs','CreateRoofs'}:expected['level']+=delta
        if before['command']=='CreateWalls' and a['height']!=b['height']:
            companion.append(dict(id=sid,command='ModifyWalls',parameters={'wallsWithDetails':[
                {'elementId':{'guid':created[sid]['guid']},'height':b['height']}]}))
            expected['height']=b['height']
        if expected!=b:raise ValueError('SPATIAL_UNQUALIFIED_DEPENDENT_PARAMETER_CHANGE:'+sid)
    # Retain native attribute expectations and pre-SEO areas, which compilation cannot reconstruct.
    updated=copy.deepcopy(plan)
    for field in ['graph','storyBindings','sourcePlanHash','intent','envelope','metrics']:
        if field in next_plan:updated[field]=copy.deepcopy(next_plan[field])
    result=dict(schema='APA_NATIVE_STORY_CHANGE_V1',storyOperation=prepared,
        oldPlan=plan,newPlan=updated,created=created,companionOperations=companion,
        newElementCreates=0,planningEvidence='FUTURE_STORY_OVERLAY_NOT_LIVE_PASS')
    result['sourceHash']=RUN.digest(result)
    return result


def verify_height_change(api,change):
    """Typed native fields, floor IDs, materials and GUIDs after all scoped operations."""
    plan=change['newPlan'];verified=E.verify_model(api,plan,change['created'])
    template=change['storyOperation']['integrationBindings']['dependencies']['spatialOperation'].get('templateSignatures',{})
    if set(A.inventory_guids(api))!={v['guid'].lower() for v in verified.values()}|set(template):
        raise ValueError('SPATIAL_HEIGHT_CHANGE_FOREIGN_OR_DUPLICATE_ELEMENTS')
    return {'status':'NATIVE_BUILDING_STORY_DEPENDENCIES_PASS','verified':verified,
        'storyBindings':plan['storyBindings'],'newCreates':0,
        'physicalGeometry':'REQUIRES_EXISTING_NATIVE_GEOMETRY_AUDIT'}


def prepare_dependency_corrections(api,change):
    """Native stories move home-story elements but can leave hosted sills fixed.

    Compare actual native scalar fields with the already authored target. Only
    supported Wall-height and hosted sill corrections are emitted; no guesses,
    Z-only story substitute or new elements.
    """
    scope=change['storyOperation']['integrationBindings']['dependencies']['spatialOperation']
    if story_settings(api('GetStories',{})['stories'])!=scope['parameters']['stories']:
        raise ValueError('SPATIAL_CORRECTION_REQUIRES_VERIFIED_TARGET_STORIES')
    expected=set(scope['ownedGuids'])|set(scope.get('templateSignatures',{}))
    if set(A.inventory_guids(api))!=expected:
        raise ValueError('SPATIAL_CORRECTION_INVENTORY_DRIFT')
    result=[]
    for op in change['newPlan']['graph']['operations']:
        if op['command'] not in {'CreateWalls','CreateWindows','CreateDoors'}:continue
        data=next(iter(op['params'].values()))[0];guid=change['created'][op['id']]['guid']
        info=RUN.requested_details(api,guid);actual=info['details']
        field='height' if op['command']=='CreateWalls' else 'sillHeight'
        if field not in data:continue
        if type(actual.get(field)) not in (int,float):raise ValueError('SPATIAL_DEPENDENT_FIELD_UNAVAILABLE')
        if RUN.close(actual[field],data[field]):continue
        command='Modify'+op['command'][6:];slot=op['command'][6:].lower()+'WithDetails'
        result.append(dict(id=op['id'],command=command,parameters={slot:[{
            'elementId':{'guid':guid},field:data[field]}]},beforeValue=actual[field],
            field=field,targetValue=data[field]))
    return result


def finish_height_change(writer,change,run_id,saved_sha256,output):
    """Reconcile a known target story table without reissuing SetStories/Create."""
    import archicad_authored_geometry as G
    scope=change['storyOperation']['integrationBindings']['dependencies']['spatialOperation']
    corrections=prepare_dependency_corrections(writer.api,change);proofs=[]
    for op in corrections:
        guid=change['created'][op['id']]['guid'];field=op['field']
        def before_check(api,g=guid,f=field,old=op['beforeValue']):
            if not RUN.close(RUN.requested_details(api,g)['details'].get(f),old):
                raise ValueError('SPATIAL_DEPENDENT_FIELD_CHANGED_AFTER_READ')
        def after(*_,g=guid,f=field,wanted=op['targetValue']):
            actual=RUN.requested_details(writer.api,g)['details'].get(f)
            if not RUN.close(actual,wanted):raise ValueError('SPATIAL_DEPENDENT_FIELD_READBACK_MISMATCH')
            return dict(status='NATIVE_STORY_DEPENDENT_PARAMETER_PASS',guid=g,field=f,actual=actual)
        r=E.execute_model_operation(writer,run_id+'-'+op['id'],op['command'],op['parameters'],
            RUN.digest([change['sourceHash'],op]),scope['ownedGuids'],scope.get('templateSignatures',{}),
            after,scope['authorizationRef'],saved_sha256,owned_before_check=before_check)
        if r['status']!='PASS':raise ValueError('SPATIAL_DEPENDENT_UNKNOWN_OUTCOME_STOP')
        proofs.append(r)
    typed=verify_height_change(writer.api,change)
    physical=G.run(writer.api,change['newPlan'],change['created'],A.inventory_guids(writer.api),output)
    if len(physical['relationshipComponents'])!=1 or physical['nativeVolumeIntersectionPairs']:
        raise ValueError('SPATIAL_DEPENDENT_GEOMETRY_NOT_ACCEPTED')
    junctions=E.complete_roof_junctions(writer,change['newPlan'],change['created'],
        scope.get('templateSignatures',{}),run_id+'-junction-readback',scope['authorizationRef'],saved_sha256)
    if junctions['nativeWriteCount']!=0:raise ValueError('SPATIAL_EXISTING_JUNCTIONS_MUST_NOT_BE_RECREATED')
    return dict(status='NATIVE_BUILDING_STORY_CHANGE_PASS',typed=typed,geometry=physical,
        junctions=junctions,correctionPlans=corrections,correctionResults=proofs,
        nativeCorrectionWrites=len(proofs),newCreates=0,newSetStoriesCalls=0)


def execute_height_change(writer,change,run_id,saved_sha256,output):
    result=execute_story_operation(writer,change['storyOperation'],run_id+'-stories',saved_sha256)
    if result['status']!='PASS':return result
    finished=finish_height_change(writer,change,run_id+'-dependents',saved_sha256,output)
    return {**finished,'globalStoryOperation':result,'newSetStoriesCalls':1}
