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
        expectations=plan.get('nativeAttributeExpectations',{}).get(sid,{})
        if expectations:
            params=copy.deepcopy(params)
            next(iter(params.values()))[0].update(expectations)
        if step['command'] in ('CreateDoors', 'CreateWindows'):
            host = step['params'][step['command'][6:].lower()+'Data'][0]['ownerWallId']['guid']['$createdGuid']
            floor = verified[host]['floorIndex']
            owner = created[host]['guid']
        else:
            floor = next(iter(params.values()))[0]['floorIndex']
            owner = None
        if step['command']=='CreateRoofs':
            from archicad_connected_components import NativeAdapter
            kind=NativeAdapter('CreateRoofs').verify(api,created[sid]['guid'],params,
                RUN.requested_details(api,created[sid]['guid']),floor,
                RUN.story_level_for_floor(plan['storyBindings'],floor))
            verified[sid]={'guid':created[sid]['guid'],'kind':kind,'floorIndex':floor}
            continue
        kind = RUN.verify_readback(step['command'], params,
            RUN.requested_details(api, created[sid]['guid']), owner,
            expected_floor=floor,
            expected_story_level=RUN.story_level_for_floor(plan['storyBindings'], floor),
            expected_slab_material_guid=plan['slabBasicMaterialGuid'] if step['command']=='CreateSlabs' else None,
            slab_level_is_absolute=True)
        library=plan.get('nativeLibraryExpectations',{}).get(sid)
        if library:
            part=RUN.requested_details(api,created[sid]['guid'])['details'].get('libPart',{})
            if part.get('name')!=library['name'] or part.get('ownUnID',{}).get('guid','').casefold()!=library['guid'].casefold():
                raise ValueError('PLAN_LIBRARY_IDENTITY_READBACK_MISMATCH')
        verified[sid] = {'guid': created[sid]['guid'], 'kind': kind, 'floorIndex': floor}
    return verified


MODEL_COMMANDS = frozenset({'MoveElements', 'ModifyWalls', 'ModifyWindows', 'ModifyDoors',
                           'CreateSolidElementLinks','SetPropertyValuesOfElements','CreateStairs','ModifySlabs',
                           'CreateNativeGridElementsV1','ModifyNativeGridElementsV1','CreateExactStairsV1','ModifyNativeStairGeometryV1','SetGDLParametersOfElements'})


def model_operation_scope(command, parameters, source_hash, owned_guids,
                          retained_guids, authorization_ref, isolated_inventory=None):
    """Exact new-building edit scope for the existing SceneWriter, not a grant."""
    scope={'schema':'APA_AUTHORED_MODEL_OPERATION_V1','command':command,
        'parameters':parameters,'sourceHash':source_hash,
        'ownedGuids':sorted(g.lower() for g in owned_guids),
        'retainedGuids':sorted(g.lower() for g in retained_guids),
        'authorizationRef':authorization_ref}
    if isolated_inventory is not None:
        scope['isolatedInventory']=sorted(g.lower() for g in isolated_inventory)
    scope['scopeHash']=RUN.digest(scope)
    qualify_model_operation(scope,command,parameters,source_hash)
    return scope


def qualify_model_operation(scope,command,parameters,source_hash):
    if (scope.get('schema')!='APA_AUTHORED_MODEL_OPERATION_V1' or
            command not in MODEL_COMMANDS or not scope.get('authorizationRef') or
            scope.get('command')!=command or scope.get('parameters')!=parameters or
            scope.get('sourceHash')!=source_hash or scope.get('scopeHash')!=RUN.digest(
                {k:v for k,v in scope.items() if k!='scopeHash'})):
        raise ValueError('MODEL_OPERATION_SCOPE_MISMATCH')
    owned=set(scope['ownedGuids']);retained=set(scope['retainedGuids'])
    if ((not owned and command not in {'CreateNativeGridElementsV1','CreateExactStairsV1'}) or owned&retained or (not retained and
            (scope.get('isolatedInventory')!=sorted(owned)))):
        raise ValueError('MODEL_OWNERSHIP_SCOPE_INVALID')
    if command=='SetGDLParametersOfElements':
        from archicad_native_spatial_tools import qualify_grid_parameter_edit
        qualify_grid_parameter_edit(parameters,owned,retained)
        return
    if command in {'CreateNativeGridElementsV1','ModifyNativeGridElementsV1','CreateExactStairsV1','ModifyNativeStairGeometryV1'}:
        from archicad_native_spatial_tools import qualify_operation
        qualify_operation(command,parameters,owned,retained)
        return
    slots={'MoveElements':'elementsWithMoveVectors','ModifyWalls':'wallsWithDetails',
        'ModifyWindows':'windowsWithDetails','ModifyDoors':'doorsWithDetails',
        'CreateSolidElementLinks':'solidLinks','SetPropertyValuesOfElements':'elementPropertyValues',
        'CreateStairs':'stairsData','ModifySlabs':'slabsWithDetails'}
    if set(parameters)!={slots[command]} or len(parameters[slots[command]])!=1:
        raise ValueError('MODEL_OPERATION_REQUIRES_ONE_EXPLICIT_TARGET')
    row=parameters[slots[command]][0]
    ids=[row.get('elementId',{}).get('guid','').lower()]
    import math
    if command=='CreateStairs':
        ids=[]
        fields={'favoriteName','baseLinePoints','zCoordinate','floorIndex','totalHeight',
                'flightWidth','stepNum','riserHeight','treadDepth','finishVisible'}
        points=row.get('baseLinePoints',[])
        if (set(row)!=fields or not isinstance(row['favoriteName'],str) or not row['favoriteName']
                or type(row['floorIndex']) is not int or type(row['stepNum']) is not int or row['stepNum']<2
                or len(points)!=2 or any(set(p)!={'x','y'} or any(type(v) not in (int,float)
                    or not math.isfinite(v) for v in p.values()) for p in points)
                or points[0]==points[1] or type(row['finishVisible']) is not bool
                or any(type(row[k]) not in (int,float) or not math.isfinite(row[k]) or row[k]<=0
                    for k in ['totalHeight','flightWidth','riserHeight','treadDepth'])
                or type(row['zCoordinate']) not in (int,float) or not math.isfinite(row['zCoordinate'])
                or abs(row['stepNum']*row['riserHeight']-row['totalHeight'])>1e-6):
            raise ValueError('MODEL_STAIR_REQUIRES_COMPLETE_SOURCE_BASELINE_AND_DIMENSIONS')
    elif command=='ModifySlabs':
        if set(row)!={'elementId','holes'} or not isinstance(row['holes'],list) or len(row['holes'])!=1:
            raise ValueError('MODEL_SLAB_HOLE_REQUIRES_EXACT_OWNED_CONTOUR')
        hole=row['holes'][0]
        points=hole.get('polygonCoordinates',[])
        if set(hole)!={'polygonCoordinates'} or len(points)!=4 or any(set(p)!={'x','y'} or
                any(type(v) not in (int,float) or not math.isfinite(v) for v in p.values()) for p in points):
            raise ValueError('MODEL_STAIR_HOLE_REQUIRES_MEASURED_RECTANGULAR_FOOTPRINT')
    elif command=='MoveElements':
        vector=row.get('moveVector',{})
        if (set(row)!={'elementId','moveVector','copy'} or row['copy'] is not False or
                set(vector)!={'x','y','z'} or any(type(v) not in (int,float) or not math.isfinite(v) for v in vector.values())):
            raise ValueError('MODEL_MOVE_REQUIRES_EXPLICIT_OWNED_TRANSFORM_NO_COPY')
    elif command=='CreateSolidElementLinks':
        ids=[row.get(k,{}).get('guid','').lower() for k in ['targetId','operatorId']]
        if (set(row)!={'targetId','operatorId','operation','linkFlags'} or
                row['operation']!='SubtractionUpwards' or
                row['linkFlags']!={'inheritOperatorAttributes':False,'skipPolygonHoles':True} or ids[0]==ids[1]):
            raise ValueError('MODEL_SEO_REQUIRES_EXPLICIT_UNDERSIDE_CONSTRUCTION_LINK')
    elif command=='SetPropertyValuesOfElements':
        value=row.get('propertyValue',{})
        if (set(row)!={'elementId','propertyId','propertyValue'} or
                not RUN._GUID.fullmatch(row.get('propertyId',{}).get('guid','')) or
                set(value)!={'value'} or not isinstance(value['value'],str) or not value['value']):
            raise ValueError('MODEL_ROLE_REQUIRES_EXPLICIT_NATIVE_ENUM_AND_PROPERTY_ID')
    else:
        fields=set(row)-{'elementId'}
        allowed={'height'} if command=='ModifyWalls' else {'width','height','sillHeight'}
        if not fields or not fields<=allowed or any(
                type(row[k]) not in (int,float) or not math.isfinite(row[k]) or
                (k!='sillHeight' and row[k]<=0) for k in fields):
            raise ValueError('MODEL_EDIT_REQUIRES_SOURCE_DIMENSIONS')
    if any(g not in owned or g in retained for g in ids):
        raise ValueError('MODEL_EDIT_ONLY_NEW_OWNED_ELEMENTS')


def prepare_building_parameter_edit(api,old_plan,created,new_intent,schema_path):
    """Diff the existing authored graph into native edits; never recreate a host."""
    verified=verify_model(api,old_plan,created)
    if set(verified)!=set(s['id'] for s in old_plan['graph']['operations']):
        raise ValueError('MODEL_EDIT_REQUIRES_COMPLETE_AUTHORED_SOURCE')
    proposed=A.compile_authored_intent(new_intent,schema_path,api)
    old={s['id']:s for s in old_plan['graph']['operations']}
    new={s['id']:s for s in proposed['graph']['operations']}
    if old.keys()!=new.keys():raise ValueError('MODEL_EDIT_CANNOT_ADD_REMOVE_OR_RECREATE_ELEMENTS')
    operations=[]
    for sid,before in old.items():
        after=new[sid]
        if before['command']!=after['command']:raise ValueError('MODEL_EDIT_TOOL_CHANGE_UNSUPPORTED')
        a=next(iter(before['params'].values()))[0];b=next(iter(after['params'].values()))[0]
        changed={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
        if not changed:continue
        guid=created[sid]['guid'];command=before['command']
        if command=='CreateWalls' and changed=={'height'}:
            native='ModifyWalls';params={'wallsWithDetails':[{'elementId':{'guid':guid},'height':b['height']}]}
        elif command in {'CreateWindows','CreateDoors'} and changed<={'width','height','sillHeight'}:
            native='Modify'+command[6:];key=command[6:].lower()+'WithDetails'
            params={key:[{'elementId':{'guid':guid},**{k:b[k] for k in sorted(changed)}}]}
        elif command=='CreateRoofs' and changed=={'level'}:
            native='MoveElements';params={'elementsWithMoveVectors':[{'elementId':{'guid':guid},
                'moveVector':{'x':0,'y':0,'z':b['level']-a['level']},'copy':False}]}
        else:raise ValueError('MODEL_PARAMETER_EDIT_UNSUPPORTED:'+sid+':'+','.join(sorted(changed)))
        operations.append({'id':sid,'command':native,'parameters':params})
    if not operations:raise ValueError('MODEL_EDIT_NO_PARAMETER_CHANGE')
    if old_plan['storyBindings']!=proposed['storyBindings']:
        raise ValueError('MODEL_EDIT_GLOBAL_STORIES_REQUIRE_SEPARATE_PROJECT_SCOPE')
    next_plan=copy.deepcopy(old_plan)
    next_plan.update(graph=proposed['graph'],intent=copy.deepcopy(new_intent))
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(schema_path),
        next_plan['graph'],runtime_version=RUN.EXPECTED_TAPIR)
    next_plan['sourcePlanHash']=RUN.native_plan_hash(next_plan,checked['sourcePlanHash'])
    payload={'schema':'APA_AUTHORED_MODEL_PARAMETER_EDIT_V1','oldPlanHash':old_plan['sourcePlanHash'],
        'newPlan':next_plan,'created':verified,'operations':operations,'newCreates':0,
        'guidPolicy':'PRESERVE_ALL_EXISTING','automaticRetry':False}
    payload['sourceHash']=RUN.digest(payload)
    return payload


def execute_model_operation(writer,scene_id,command,parameters,source_hash,owned_guids,
                            retained_signatures,verify_after,authorization_ref,saved_sha256,
                            owned_before_check=None):
    """Delegate one exact model operation to the retained SceneWriter journal."""
    from pathlib import Path
    import hashlib
    import archicad_connected_components as C
    isolated_inventory=A.inventory_guids(writer.api) if not retained_signatures else None
    scope=model_operation_scope(command,parameters,source_hash,owned_guids,
        retained_signatures,authorization_ref,isolated_inventory=isolated_inventory)
    pre={'sourcePlanHash':source_hash,'binding':writer.guarded_binding(),
        'integrationBindings':{'dependencies':{'modelOperation':scope}}}
    def retained():
        if not retained_signatures and A.inventory_guids(writer.api)!=scope['isolatedInventory']:
            raise ValueError('MODEL_ISOLATED_INVENTORY_CHANGED')
        native=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
        if C.retained_geometry_signatures(native,list(retained_signatures))!=retained_signatures:
            raise ValueError('MODEL_RETAINED_GEOMETRY_CHANGED')
        if not set(scope['ownedGuids'])<={e['guid'].lower() for e in native['elements']}:
            raise ValueError('MODEL_OWNED_GUID_MISSING')
        return native
    def before():
        if owned_before_check is not None:owned_before_check(writer.api)
        if hashlib.sha256(Path(pre['binding']['path']).read_bytes()).hexdigest()!=saved_sha256:
            raise ValueError('MODEL_SAVED_FILE_HASH_CHANGED')
        native=retained()
        if command=='SetPropertyValuesOfElements':
            binding=resolve_structural_function(writer.api)
            row=parameters['elementPropertyValues'][0]
            if row['propertyId']!=binding['propertyId'] or row['propertyValue']['value'] not in binding['displayValues'].values():
                raise ValueError('MODEL_STRUCTURAL_FUNCTION_DEFINITION_CHANGED')
        return {'status':'NATIVE_RETAINED_MODEL_PASS','retainedCount':len(retained_signatures),
            'inventoryCount':len(native['elements'])}
    def after(reply,prior):
        proof=verify_after(reply,prior)
        if not isinstance(proof,dict) or not str(proof.get('status','')).endswith('PASS'):
            raise ValueError('MODEL_INDEPENDENT_READBACK_REQUIRED')
        retained()
        return {**proof,'retainedGuidCount':len(retained_signatures)}
    token=RUN.digest({'sceneId':scene_id,'sourcePlanHash':source_hash,'command':command,
        'parameters':parameters,'target':pre['binding']})
    return writer.execute_bound_operation(pre,scene_id,command,parameters,token,before,after)


def resolve_structural_function(api):
    """Read the installed built-in definition and localized enum display values."""
    rows=api('API.GetPropertyIds',{'properties':[{'type':'BuiltIn',
        'nonLocalizedName':'Category_StructuralFunction'}]})['properties']
    if len(rows)!=1 or 'error' in rows[0]:raise ValueError('NATIVE_STRUCTURAL_FUNCTION_UNAVAILABLE')
    prop=rows[0]['propertyId']
    definition=api('API.GetDetailsOfProperties',{'properties':[{'propertyId':prop}]})['propertyDefinitions'][0]['propertyDefinition']
    values={r['enumValue']['nonLocalizedValue']:r['enumValue']['displayValue'] for r in definition['possibleEnumValues']}
    allowed={'LoadBearingElement','NonLoadBearingElement'}
    if definition.get('isEditable') is not True or definition.get('type')!='singleEnum' or not allowed<=values.keys():
        raise ValueError('NATIVE_STRUCTURAL_FUNCTION_NOT_EDITABLE_ENUM')
    return {'propertyId':prop,'displayValues':{k:values[k] for k in allowed},
        'definitionHash':RUN.digest(definition),'engineeringCapacity':'NOT_VERIFIED'}


def assign_structural_functions(writer,plan,created,roles,retained_signatures,run_id,
                                authorization_ref,saved_sha256):
    verify_model(writer.api,plan,created)
    binding=resolve_structural_function(writer.api);owned=[v['guid'] for v in created.values()]
    proof={};writes=[]
    for sid,role in roles.items():
        if sid not in created or created[sid]['kind'] not in {'Wall','Slab','Roof'} or role not in binding['displayValues']:
            raise ValueError('MODEL_ROLE_NOT_EXPLICIT_OWNED_STRUCTURAL_ELEMENT')
        guid=created[sid]['guid'];value={'value':binding['displayValues'][role]}
        def read(g=guid):
            return writer.api('GetPropertyValuesOfElements',{'elements':[{'elementId':{'guid':g}}],
                'properties':[{'propertyId':binding['propertyId']}]})['propertyValuesForElements'][0]['propertyValues'][0]['propertyValue']
        if read()==value:
            proof[sid]={'role':role,'nativeDisplay':value['value'],'reused':True};continue
        params={'elementPropertyValues':[{'elementId':{'guid':guid},'propertyId':binding['propertyId'],'propertyValue':value}]}
        def verify(*_,g=guid,expected=value):
            actual=writer.api('GetPropertyValuesOfElements',{'elements':[{'elementId':{'guid':g}}],
                'properties':[{'propertyId':binding['propertyId']}]})['propertyValuesForElements'][0]['propertyValues'][0]['propertyValue']
            if actual!=expected:raise ValueError('NATIVE_STRUCTURAL_FUNCTION_VALUE_MISMATCH')
            return {'status':'NATIVE_STRUCTURAL_FUNCTION_PASS','guid':g,'nativeValue':actual}
        result=execute_model_operation(writer,run_id+'-'+sid,'SetPropertyValuesOfElements',params,
            RUN.digest([plan['sourcePlanHash'],binding,sid,role]),owned,retained_signatures,verify,
            authorization_ref,saved_sha256)
        if result['status']!='PASS':raise ValueError('MODEL_ROLE_UNKNOWN_OUTCOME_STOP')
        writes.append(result);proof[sid]={'role':role,'nativeDisplay':value['value'],'reused':False}
    return {'status':'NATIVE_BUILDING_STRUCTURAL_FUNCTIONS_PASS','roles':proof,
        'nativeWriteCount':len(writes),'propertyBinding':binding,'journalResults':writes,
        'engineeringCapacity':'NOT_VERIFIED_EXPLICIT_TEST_ROLE_ASSIGNMENTS'}


def complete_roof_junctions(writer,plan,created,retained_signatures,run_id,
                            authorization_ref,saved_sha256):
    """Native underside completion of one rectangular authored roof, no renderer.

    Actual native lower contours supply the placement correction. Existing
    complete SEO links are independently checked and reused without writes;
    a partial or unexpected link set requires reconciliation, never replay.
    """
    import archicad_connected_components as C
    import archicad_native_operations as N
    verify_model(writer.api,plan,created)
    roofs=[sid for sid,v in created.items() if v['kind']=='Roof']
    if len(roofs)!=1:raise ValueError('MODEL_JUNCTION_REQUIRES_ONE_NATIVE_ROOF')
    roof_id=roofs[0];roof_guid=created[roof_id]['guid'];floor=created[roof_id]['floorIndex']
    targets=[sid for sid,v in created.items() if v['kind']=='Wall' and v['floorIndex']==floor]
    if not targets:raise ValueError('MODEL_JUNCTION_HAS_NO_UPPER_WALLS')
    owned=[v['guid'] for v in created.values()];updated=copy.deepcopy(plan);proofs={};writes=[]
    def capture():
        native=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
        if C.retained_geometry_signatures(native,list(retained_signatures))!=retained_signatures:
            raise ValueError('MODEL_RETAINED_GEOMETRY_CHANGED')
        return {e['guid'].lower():e for e in native['elements']}
    native=capture();roof=native[roof_guid.lower()]
    if RUN.requested_details(writer.api,roof_guid)['details'].get('holes'):
        raise ValueError('MODEL_ROOF_HOLE_POLICY_NOT_QUALIFIED')
    link_counts={}
    for sid in targets:
        rows=writer.api('GetSolidElementLinks',{'elements':[{'elementId':{'guid':created[sid]['guid']}}]})['solidLinks']
        links=[x for r in rows for x in r.get('solidLinksWithTheGivenTarget',[])]
        if any(x.get('operatorId',{}).get('guid','').lower()!=roof_guid.lower() or
                x.get('operation')!='SubtractionUpwards' for x in links):
            raise ValueError('MODEL_JUNCTION_UNEXPECTED_EXISTING_LINK')
        link_counts[sid]=len(links)
    if any(link_counts.values()) and set(link_counts.values())!={1}:
        raise ValueError('MODEL_JUNCTION_PARTIAL_SET_MANUAL_RECONCILIATION_REQUIRED')
    already=all(v==1 for v in link_counts.values())
    def coverage(current):
        reports={}
        for sid in targets:
            cap,lower,overlap,top,plane=N.wall_roof_face_overlap(current[created[sid]['guid'].lower()],current[roof_guid.lower()])
            missing=cap.difference(lower).area
            if missing>1e-6:raise ValueError('MODEL_ROOF_DOES_NOT_COVER_COMPLETE_WALL_FOOTPRINT:'+sid)
            reports[sid]={'expectedArea':cap.area/plane['normal'][2], 'uncoveredArea':missing}
        return reports
    if not already:
        try:coverage(native)
        except ValueError:
            calibration=N.assess_single_plane_contour_candidate(roof,RUN.requested_details(writer.api,roof_guid))
            dx,dy=calibration['memoToLowerFaceCentroidOffsetXY']
            params={'elementsWithMoveVectors':[{'elementId':{'guid':roof_guid},
                'moveVector':{'x':-dx,'y':-dy,'z':0},'copy':False}]}
            def verify_alignment(*_):
                checks=coverage(capture())
                return {'status':'NATIVE_ROOF_LOWER_FOOTPRINT_ALIGNMENT_PASS','coverage':checks}
            result=execute_model_operation(writer,run_id+'-align','MoveElements',params,
                RUN.digest([plan['sourcePlanHash'],'align',params]),owned,retained_signatures,
                verify_alignment,authorization_ref,saved_sha256)
            if result['status']!='PASS':raise ValueError('MODEL_ALIGNMENT_UNKNOWN_OUTCOME_STOP')
            writes.append(result)
            data=next(s for s in updated['graph']['operations'] if s['id']==roof_id)['params']['roofsData'][0]
            for point in data['polygonCoordinates']+list(data['pivotLine'].values()):
                point['x']-=dx;point['y']-=dy
            checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(writer.schema_path),
                updated['graph'],runtime_version=RUN.EXPECTED_TAPIR)
            updated['sourcePlanHash']=RUN.native_plan_hash(updated,checked['sourcePlanHash'])
    if already:
        areas=plan.get('integrationBindings',{}).get('dependencies',{}).get('authoredRoofJunctions',{}).get('expectedContactAreas',{})
        if set(areas)!=set(targets):
            raise ValueError('MODEL_EXISTING_JUNCTION_SOURCE_AREAS_REQUIRED')
        expectations={sid:{'expectedArea':areas[sid]} for sid in targets}
    else:
        expectations=coverage(capture())
    for sid in targets:
        target=created[sid]['guid'];current=capture();plane=N.roof_underside_plane(current[roof_guid.lower()])
        area=expectations[sid]['expectedArea']
        if already:
            proofs[sid]=N.underside_contact_geometry(current[target.lower()],current[roof_guid.lower()],area,plane)
            continue
        before=N.element_body(writer.api,target)
        params={'solidLinks':[{'targetId':{'guid':target},'operatorId':{'guid':roof_guid},
            'operation':'SubtractionUpwards','linkFlags':{'inheritOperatorAttributes':False,'skipPolygonHoles':True}}]}
        def verify(*_,t=target,b=before,a=area,p=plane):
            return N.roof_bearing_seo_readback(writer.api,t,roof_guid,b,a,p)
        result=execute_model_operation(writer,run_id+'-'+sid,'CreateSolidElementLinks',params,
            RUN.digest([updated['sourcePlanHash'],'seo',params]),owned,retained_signatures,
            verify,authorization_ref,saved_sha256)
        if result['status']!='PASS':raise ValueError('MODEL_JUNCTION_UNKNOWN_OUTCOME_STOP')
        writes.append(result);proofs[sid]=result['readback']
    updated.setdefault('integrationBindings',{}).setdefault('dependencies',{})['authoredRoofJunctions']={
        'roofStepId':roof_id,'targetStepIds':targets,'status':'NATIVE_UNDERSIDE_LINKS_VERIFIED',
        'expectedContactAreas':{sid:v['expectedArea'] for sid,v in expectations.items()}}
    return {'status':'NATIVE_BUILDING_ROOF_JUNCTIONS_PASS','plan':updated,'junctions':proofs,
        'nativeWriteCount':len(writes),'reusedCompleteLinks':already,'journalResults':writes,
        'engineeringAcceptance':'NOT_VERIFIED'}


def finish_created_model(writer,plan,created,intent,retained_signatures,run_id,
                         authorization_ref,saved_sha256):
    """Complete only verified existing creation GUIDs after a read-stage failure.

    No CreateWalls/Slabs/Roof or blind scene retry. Partial native relation
    outcomes remain reconciliation gates in complete_roof_junctions.
    """
    verified=verify_model(writer.api,plan,created)
    if set(verified)!=set(s['id'] for s in plan['graph']['operations']):
        raise ValueError('MODEL_COMPLETION_REQUIRES_VERIFIED_COMPLETE_CREATION')
    if {v['guid'].lower() for v in verified.values()} & set(retained_signatures):
        raise ValueError('MODEL_COMPLETION_CANNOT_OWN_RETAINED_ELEMENTS')
    result={'status':'NATIVE_AUTHORED_MODEL_COMPLETION_PASS','newCreationCalls':0,'plan':plan}
    if intent.get('nativeRoofJunctions'):
        junctions=complete_roof_junctions(writer,plan,verified,retained_signatures,
            run_id+'-junctions',authorization_ref,saved_sha256)
        result.update(plan=junctions['plan'],junctions=junctions)
    if intent.get('structuralFunctions'):
        result['roles']=assign_structural_functions(writer,result['plan'],verified,
            intent['structuralFunctions'],retained_signatures,run_id+'-roles',authorization_ref,saved_sha256)
    return result


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
        children = A.column_subelements(api, {k:v for k,v in created.items() if k!='__plan__'})
        expected = sorted((set(record['inventory'])-original_owned) |
            {g for group in children.values() for g in group} |
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


def prepare_opening_width(api, plan, created, step_id, width, journal, operation_id):
    """One explicit existing opening edit, including independently requested restore."""
    if RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding']:
        raise ValueError('OPENING_EDIT_TARGET_DRIFT')
    if plan['binding']['path']!=RUN.APPROVED_ISOLATED_WRITER_PATH:
        raise ValueError('OPENING_EDIT_TARGET_NOT_APPROVED')
    verified=verify_model(api,plan,created)
    if set(verified)!=set(s['id'] for s in plan['graph']['operations']):
        raise ValueError('OPENING_EDIT_SOURCE_INCOMPLETE')
    changed=copy.deepcopy(plan)
    step=next((s for s in changed['graph']['operations'] if s['id']==step_id),None)
    if step is None or step['command'] not in {'CreateDoors','CreateWindows'}:
        raise ValueError('OPENING_EDIT_NOT_AN_OPENING')
    data=next(iter(step['params'].values()))[0]
    data['width']=width
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(RUN.DEFAULT_SCENE_SCHEMA),changed['graph'],runtime_version=RUN.EXPECTED_TAPIR)
    if checked['status']!='PLAN_VALIDATED_OFFLINE':
        raise ValueError('OPENING_EDIT_GRAPH_REFUSED')
    changed['sourcePlanHash']=RUN.native_plan_hash(changed,checked['sourcePlanHash'])
    command='ModifyWindows' if step['command']=='CreateWindows' else 'ModifyDoors'
    key='windowsWithDetails' if command=='ModifyWindows' else 'doorsWithDetails'
    record={'operationId':operation_id,'oldPlan':plan,'newPlan':changed,'created':verified,
        'inventory':A.inventory_guids(api),'columnSegments':A.column_subelements(api,verified),
        'command':command,'parameters':{key:[{'elementId':{'guid':created[step_id]['guid']},'width':width}]}}
    if not RUN._SCENE_ID.fullmatch(operation_id):raise ValueError('INVALID_OPENING_EDIT_ID')
    with closing(sqlite3.connect(journal)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS authored_opening_edits(operation_id TEXT PRIMARY KEY,state TEXT,intent TEXT,result TEXT)');db.commit()
        if db.execute('SELECT 1 FROM authored_opening_edits WHERE operation_id=?',(operation_id,)).fetchone():
            raise ValueError('OPENING_EDIT_ALREADY_RESERVED_NEVER_RETRY')
    return {'status':'READY_FOR_EXISTING_OPENING_EDIT','confirmPlanHash':RUN.digest(record),'intent':record}


def execute_opening_width(api,ticket,journal,token):
    record=ticket['intent'];plan=record['oldPlan']
    if token!=ticket['confirmPlanHash'] or RUN.digest(record)!=token:
        raise ValueError('OPENING_EDIT_TOKEN_MISMATCH')
    with closing(sqlite3.connect(journal)) as db:
        db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO authored_opening_edits VALUES(?,?,?,?)',
            (record['operationId'],'ATTEMPTED',RUN.canonical(record),'{}'));db.commit()
        try:
            if RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding'] or A.inventory_guids(api)!=record['inventory']:
                raise ValueError('OPENING_EDIT_OPERATION_BOUNDARY_DRIFT')
            verify_model(api,plan,record['created'])
            response=api(record['command'],record['parameters'])
            if response.get('executionResults')!=[{'success':True}]:raise ValueError('OPENING_EDIT_NOT_CONFIRMED')
            verify_model(api,record['newPlan'],record['created'])
            if (A.inventory_guids(api)!=record['inventory'] or
                    A.column_subelements(api,record['created'])!=record['columnSegments'] or
                    RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding']):
                raise ValueError('OPENING_EDIT_GUID_HOST_OR_TARGET_DRIFT')
            result={'status':'EXISTING_OPENING_EDIT_READBACK_PASS','guidsPreserved':True,
                    'newCreates':0,'planHash':record['newPlan']['sourcePlanHash'],'automaticRetry':False}
        except Exception as exc:
            result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME','reason':str(exc),'automaticRetry':False}
        db.execute('UPDATE authored_opening_edits SET state=?,result=? WHERE operation_id=?',
            (result['status'],RUN.canonical(result),record['operationId']));db.commit()
    return result


def prepare_attribute_edit(api,plan,created,step_id,selection,journal,operation_id):
    """Resolve a real project attribute for one explicitly owned existing element."""
    from archicad_native_material_selection import compile_change
    if RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding'] or plan['binding']['path']!=RUN.APPROVED_ISOLATED_WRITER_PATH:
        raise ValueError('ATTRIBUTE_EDIT_TARGET_DRIFT')
    if set(created)!=set(s['id'] for s in plan['graph']['operations']):raise ValueError('ATTRIBUTE_EDIT_SOURCE_INCOMPLETE')
    verify_model(api,plan,created)
    change=compile_change(api,plan,created,step_id,selection)
    record={'operationId':operation_id,'oldPlan':plan,'created':created,'inventory':A.inventory_guids(api),
        'columnSegments':A.column_subelements(api,created),'selection':selection,
        'beforeDetails':RUN.requested_details(api,created[step_id]['guid'])['details'],**change}
    return _reserve_attribute_ticket(record,journal)


def _reserve_attribute_ticket(record,journal):
    if not RUN._SCENE_ID.fullmatch(record['operationId']):raise ValueError('INVALID_ATTRIBUTE_EDIT_ID')
    with closing(sqlite3.connect(journal)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS authored_attribute_edits(operation_id TEXT PRIMARY KEY,state TEXT,intent TEXT,result TEXT)');db.commit()
        if db.execute('SELECT 1 FROM authored_attribute_edits WHERE operation_id=?',(record['operationId'],)).fetchone():
            raise ValueError('ATTRIBUTE_EDIT_ALREADY_RESERVED_NEVER_RETRY')
    return {'status':'READY_FOR_EXISTING_ATTRIBUTE_EDIT','intent':record,'confirmPlanHash':RUN.digest(record),'modelWriteAttempts':0}


def prepare_attribute_restore(api,applied,journal,operation_id):
    """Explicit restore is a separate operation; no automatic rollback or retry."""
    record=applied['intent']
    if RUN.guarded_project(api,record['newPlan']['storyBindings'][0])!=record['newPlan']['binding']:
        raise ValueError('ATTRIBUTE_RESTORE_TARGET_DRIFT')
    verify_model(api,record['newPlan'],record['created'])
    step=next(s for s in record['oldPlan']['graph']['operations'] if s['id']==record['stepId'])
    original=next(iter(step['params'].values()))[0];before=record['beforeDetails']
    target=record['created'][record['stepId']]['guid'];kind=record['selection']['kind']
    if kind=='Composite':
        params={'wallsWithDetails':[{'elementId':{'guid':target},'structureType':'Basic',
            'buildingMaterialId':original['buildingMaterialId'],'thickness':original['thickness']}]}
    elif kind=='Surface':
        params={'wallsWithDetails':[{'elementId':{'guid':target},'referenceMaterial':before['referenceMaterial']}]}
    elif kind=='Profile':
        params={'columnsWithDetails':[{'elementId':{'guid':target},'buildingMaterialId':original['buildingMaterialId'],
            'width':original['width'],'depth':original['depth'],'coreAnchor':before['coreAnchor'],
            'isWidthAndHeightLinked':before['isWidthAndHeightLinked']}]}
    else:raise ValueError('ATTRIBUTE_RESTORE_UNSUPPORTED')
    restore={'operationId':operation_id,'oldPlan':record['newPlan'],'newPlan':record['oldPlan'],
        'created':record['created'],'inventory':record['inventory'],'columnSegments':record['columnSegments'],
        'stepId':record['stepId'],'command':record['command'],'parameters':params,'explicitRestoreOf':record['operationId']}
    return _reserve_attribute_ticket(restore,journal)


def execute_attribute_edit(api,ticket,journal,token):
    from archicad_native_material_selection import resolve
    record=ticket['intent'];plan=record['oldPlan']
    if token!=ticket['confirmPlanHash'] or RUN.digest(record)!=token:raise ValueError('ATTRIBUTE_EDIT_TOKEN_MISMATCH')
    with closing(sqlite3.connect(journal)) as db:
        db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO authored_attribute_edits VALUES(?,?,?,?)',
            (record['operationId'],'ATTEMPTED',RUN.canonical(record),'{}'));db.commit()
        try:
            if RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding'] or A.inventory_guids(api)!=record['inventory']:
                raise ValueError('ATTRIBUTE_EDIT_OPERATION_BOUNDARY_DRIFT')
            verify_model(api,plan,record['created'])
            if 'selection' in record:
                s=record['selection']
                if resolve(api,s['kind'],s['name'],s['expectedGuid'])!=record['selected']:
                    raise ValueError('SELECTED_ATTRIBUTE_CHANGED_BEFORE_WRITE')
            response=api(record['command'],record['parameters'])
            if response.get('executionResults')!=[{'success':True}]:raise ValueError('ATTRIBUTE_EDIT_NOT_CONFIRMED')
            verify_model(api,record['newPlan'],record['created'])
            if (A.inventory_guids(api)!=record['inventory'] or A.column_subelements(api,record['created'])!=record['columnSegments'] or
                    RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding']):
                raise ValueError('ATTRIBUTE_EDIT_GUID_HOST_OR_TARGET_DRIFT')
            result={'status':'EXISTING_ATTRIBUTE_EDIT_READBACK_PASS','guidsPreserved':True,'newCreates':0,
                'newPlanHash':record['newPlan']['sourcePlanHash'],'automaticRetry':False}
        except Exception as exc:
            result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME','reason':str(exc),'automaticRetry':False}
        db.execute('UPDATE authored_attribute_edits SET state=?,result=? WHERE operation_id=?',
            (result['status'],RUN.canonical(result),record['operationId']));db.commit()
    return result
