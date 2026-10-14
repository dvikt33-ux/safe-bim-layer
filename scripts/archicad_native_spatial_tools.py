"""Bounded Grid and exact Stair adapters for the EXISTING SceneWriter.

SDK build/source schemas never authorize installed runtime capabilities. No
installer, project switch, automatic retry, preference edit or second executor.
"""
import copy,hashlib,json,math,sqlite3
from contextlib import closing
from pathlib import Path
import xml.etree.ElementTree as ET
import archicad_project_accelerator as A
import archicad_authored_extension as E
RUN=A.RUN
CREATES=frozenset({'CreateNativeGridElementsV1','CreateExactStairsV1'})
EDITS=frozenset({'ModifyNativeGridElementsV1','ModifyNativeStairGeometryV1'})
COMMANDS=CREATES|EDITS
READS=frozenset({'GetNativeGridDefaultsV1','GetNativeGridElementsV1','GetNativeStairGeometryV1','EvaluateNativeStairGeometryV1'})

def finite(v):return type(v) in (int,float) and math.isfinite(v)

def qualify_operation(command,parameters,owned,retained):
    """Exact payload scope; source/preflight and native identity are separate."""
    if command not in COMMANDS:raise ValueError('SDK_SPATIAL_COMMAND_NOT_QUALIFIED')
    if command=='ModifyNativeStairGeometryV1':
        row=parameters;guid=row.get('elementId',{}).get('guid','').lower()
    else:
        slot={'CreateNativeGridElementsV1':'gridsData','ModifyNativeGridElementsV1':'gridsWithDetails','CreateExactStairsV1':'stairsData'}[command]
        if set(parameters)!={slot} or not isinstance(parameters[slot],list) or len(parameters[slot])!=1:raise ValueError('SDK_SPATIAL_ONE_TARGET_REQUIRED')
        row=parameters[slot][0];guid=row.get('elementId',{}).get('guid','').lower()
    if command in EDITS and (guid not in owned or guid in retained):raise ValueError('SDK_SPATIAL_ONLY_EXPLICIT_OWNED_TARGET')
    if command=='CreateNativeGridElementsV1':
        if set(row)!={'x','y','angle','floorIndex','expectedLibraryPartIndex','parameters'} or any(not finite(row[k]) for k in ['x','y','angle']) or type(row['floorIndex']) is not int or type(row['expectedLibraryPartIndex']) is not int or row['expectedLibraryPartIndex']<1:raise ValueError('SOURCE_GRID_PLACEMENT_AND_DEFAULTS_REQUIRED')
        changes=row['parameters'];names=[]
        if not isinstance(changes,list) or not changes:raise ValueError('SOURCE_GRID_PARAMETERS_REQUIRED')
        for p in changes:
            if set(p)!={'name','nativeType','value'} or not isinstance(p['name'],str) or not p['name'] or type(p['nativeType']) is not int or not (isinstance(p['value'],str) or finite(p['value'])):raise ValueError('SOURCE_GRID_PARAMETER_TYPE_REQUIRED')
            names.append(p['name'])
        if len(set(names))!=len(names):raise ValueError('DUPLICATE_NATIVE_GRID_PARAMETER')
    elif command=='ModifyNativeGridElementsV1':
        if set(row)!={'elementId','x','y','angle','expectedX','expectedY','expectedAngle'} or any(not finite(row[k]) for k in set(row)-{'elementId'}):raise ValueError('EXACT_GRID_EDIT_BASELINE_REQUIRED')
    else:
        common={'baseLinePoints','zCoordinate','floorIndex','totalHeight','flightWidth','stepNum','riserHeight','treadDepth','treadDepthLocked','finishVisible'}
        extra={'favoriteName'} if command in CREATES else {'elementId','expectedTotalHeight','expectedGoing','expectedStepNum'}
        if set(row)!=common|extra or row['treadDepthLocked'] is not True or type(row['finishVisible']) is not bool or type(row['floorIndex']) is not int or type(row['stepNum']) is not int or row['stepNum']<2:raise ValueError('EXACT_LOCKED_STAIR_SOURCE_REQUIRED')
        points=row['baseLinePoints']
        if len(points)!=2 or points[0]==points[1] or any(set(p)!={'x','y'} or any(not finite(v) for v in p.values()) for p in points):raise ValueError('EXACT_STAIR_STRAIGHT_BASELINE_REQUIRED')
        if any(not finite(row[k]) or row[k]<=0 for k in ['totalHeight','flightWidth','riserHeight','treadDepth']) or not finite(row['zCoordinate']) or not RUN.close(row['stepNum']*row['riserHeight'],row['totalHeight']):raise ValueError('EXACT_STAIR_INCONSISTENT_SOURCE_DIMENSIONS')
        if command in CREATES and (not isinstance(row['favoriteName'],str) or not row['favoriteName']):raise ValueError('EXACT_STAIR_SOURCE_FAVORITE_REQUIRED')
        if command in EDITS and (not finite(row['expectedTotalHeight']) or not finite(row['expectedGoing']) or type(row['expectedStepNum']) is not int):raise ValueError('EXACT_STAIR_EDIT_BASELINE_REQUIRED')

def runtime_catalog(writer,command,parameters,read_command):
    catalog=A.catalog_with_provenance(writer.schema_path)
    if not {command,read_command}<=catalog['commands'].keys():raise ValueError('BLOCKED_INSTALLED_NATIVE_SPATIAL_CONTRACT_MISSING')
    if writer.api('GetAddOnVersion',{}).get('version')!=A.SCENE.GRAPH.CONTRACTS.source_version(catalog):raise ValueError('SDK_SPATIAL_RUNTIME_SCHEMA_VERSION_CHANGED')
    A.verify_native_runtime_identity(writer.api,catalog)
    A.SCENE.GRAPH.CONTRACTS._validator(catalog,command).validate(parameters)
    return catalog

def prepare_axis(axis,outline,defaults,profile,floor_index=0):
    """Bind an existing semantic axis to REAL default parameter names and types.

    profile requires a caller-qualified mapping of the loaded native Grid library;
    no fallback to guessed A/label names or generic Objects.
    """
    if defaults.get('nativeVariationName')!='APIVarId_GridElement' or defaults.get('libraryPartIndex',0)<1:raise ValueError('TRUE_NATIVE_GRID_DEFAULTS_REQUIRED')
    if set(axis)!={'id','direction','coordinate'} or axis['direction'] not in {'X','Y'} or not finite(axis['coordinate']):raise ValueError('EXISTING_SEMANTIC_AXIS_REQUIRED')
    if profile.get('status')!='SOURCE_VERIFIED' or profile.get('defaultsHash')!=RUN.digest(defaults):raise ValueError('GRID_LIBRARY_ROLE_MAPPING_NOT_VERIFIED')
    lookup={p['name']:p for p in defaults['nativeParameters']};length=lookup.get(profile.get('lengthParameter'));label=lookup.get(profile.get('labelParameter'))
    if not length or not label or length.get('isArray') or label.get('isArray') or length.get('nativeTypeName')!='Length' or label.get('nativeTypeName')!='String':raise ValueError('ACTUAL_NATIVE_GRID_LENGTH_LABEL_PARAMETERS_REQUIRED')
    for k in ['xMin','xMax','yMin','yMax']:
        if not finite(outline.get(k)):raise ValueError('SOURCE_AXIS_OUTLINE_REQUIRED')
    vertical=axis['direction']=='X';lower=outline['xMin' if vertical else 'yMin'];upper=outline['xMax' if vertical else 'yMax']
    if not lower<=axis['coordinate']<=upper:raise ValueError('SOURCE_AXIS_OUTSIDE_OUTLINE')
    span=outline['yMax']-outline['yMin'] if vertical else outline['xMax']-outline['xMin']
    if span<=0 or type(floor_index) is not int:raise ValueError('SOURCE_AXIS_SPAN_FLOOR_REQUIRED')
    row=dict(x=axis['coordinate'] if vertical else outline['xMin'],y=outline['yMin'] if vertical else axis['coordinate'],angle=math.pi/2 if vertical else 0.,floorIndex=floor_index,expectedLibraryPartIndex=defaults['libraryPartIndex'],parameters=[dict(name=length['name'],nativeType=length['nativeType'],value=span),dict(name=label['name'],nativeType=label['nativeType'],value=axis['id'])])
    if profile.get('angleParameter'):
        angle=lookup.get(profile['angleParameter'])
        if not angle or angle.get('isArray') or angle.get('nativeTypeName')!='Angle':raise ValueError('ACTUAL_NATIVE_GRID_ANGLE_PARAMETER_REQUIRED')
        row['parameters'].append(dict(name=angle['name'],nativeType=angle['nativeType'],value=row['angle']))
    params={'gridsData':[row]};qualify_operation('CreateNativeGridElementsV1',params,set(),{'retained'})
    recipe=dict(schema='APA_NATIVE_AXIS_GRID_V1',axis=copy.deepcopy(axis),outline=copy.deepcopy(outline),defaults=copy.deepcopy(defaults),profile=copy.deepcopy(profile),parameters=params)
    recipe['sourceHash']=RUN.digest(recipe)
    recipe['graph']={'operations':[{'id':axis['id'],'command':'CreateNativeGridElementsV1','params':params,'dependsOn':[]}]}
    return recipe

def verify_grid(api,guid,recipe):
    r=api('GetNativeGridElementsV1',{'elements':[{'elementId':{'guid':guid}}]})['grids']
    if len(r)!=1:raise ValueError('NATIVE_GRID_READBACK_COUNT_MISMATCH')
    actual=r[0];row=recipe['parameters']['gridsData'][0]
    if actual['elementId']['guid'].lower()!=guid.lower() or actual.get('nativeTypeName')!='GridElement' or actual.get('nativeVariationName')!='APIVarId_GridElement' or actual.get('nativeVariationId')!=recipe['defaults']['nativeVariationId'] or actual.get('nativeTypeId')!=recipe['defaults']['nativeTypeId']:raise ValueError('TRUE_GRID_VARIATION_READBACK_REQUIRED')
    if actual['floorIndex']!=row['floorIndex'] or actual['libraryPartIndex']!=row['expectedLibraryPartIndex'] or any(not RUN.close(actual.get(k),row[k]) for k in ['x','y','angle']):raise ValueError('GRID_PLACEMENT_OR_LIBRARY_READBACK_MISMATCH')
    lookup={p['name']:p for p in actual['nativeParameters']}
    for p in row['parameters']:
        q=lookup.get(p['name'],{})
        if q.get('nativeType')!=p['nativeType'] or (q.get('value')!=p['value'] if isinstance(p['value'],str) else not RUN.close(q.get('value'),p['value'])):raise ValueError('GRID_SOURCE_PARAMETER_READBACK_MISMATCH')
    return dict(status='NATIVE_AXIS_GRID_SOURCE_READBACK_PASS',guid=guid,axisId=recipe['axis']['id'],sourceHash=recipe['sourceHash'],nativeVariation=actual['nativeVariationId'],nativePlacement={k:actual[k] for k in ['x','y','angle','floorIndex']},nativeParameters=row['parameters'],engineeringAcceptance='NOT_VERIFIED',renderedSpanAcceptance='REQUIRES_INDEPENDENT_NATIVE_VIEW_GEOMETRY')

def create_or_reuse_axis(writer,recipe,scene_id,retained_signatures,saved_sha256,authorization_ref,existing_guid=None):
    runtime_catalog(writer,'CreateNativeGridElementsV1',recipe['parameters'],'GetNativeGridElementsV1')
    if recipe['sourceHash']!=RUN.digest({k:v for k,v in recipe.items() if k not in {'sourceHash','graph'}}):raise ValueError('AXIS_SOURCE_RECIPE_CHANGED')
    if existing_guid:
        return dict(status='NATIVE_AXIS_GRID_REUSE_PASS',createdGuid=existing_guid,readback=verify_grid(writer.api,existing_guid,recipe),nativeCreateCalls=0)
    if writer.journal_path.exists():
        with closing(sqlite3.connect(writer.journal_path)) as db:
            exists=db.execute("SELECT 1 FROM sqlite_master WHERE name='steps'").fetchone()
            prior=db.execute("SELECT state,guid,output FROM steps WHERE scene_id=? AND step_id='operation'",(scene_id,)).fetchone() if exists else None
        if prior:
            if prior[0]!='PASS' or not prior[1]:raise ValueError('AXIS_PREVIOUS_OPERATION_REQUIRES_RECONCILIATION_NEVER_RETRY')
            proof=json.loads(prior[2]).get('readback',{})
            if proof.get('sourceHash')!=recipe['sourceHash']:raise ValueError('AXIS_EXISTING_SOURCE_CHANGED_EXPLICIT_EDIT_REQUIRED')
            return dict(status='NATIVE_AXIS_GRID_REUSE_PASS',createdGuid=prior[1],readback=verify_grid(writer.api,prior[1],recipe),nativeCreateCalls=0)
    def before(api):
        if api('GetNativeGridDefaultsV1',{})!=recipe['defaults']:raise ValueError('NATIVE_GRID_DEFAULTS_CHANGED_BEFORE_CREATE')
    def after(reply,*_):return verify_grid(writer.api,RUN.created_guid(reply),recipe)
    result=E.execute_model_operation(writer,scene_id,'CreateNativeGridElementsV1',recipe['parameters'],recipe['sourceHash'],[],retained_signatures,after,authorization_ref,saved_sha256,owned_before_check=before)
    return {**result,'nativeCreateCalls':1}

def edit_axis(writer,guid,recipe,new_position,scene_id,retained_signatures,saved_sha256,authorization_ref):
    verify_grid(writer.api,guid,recipe);prior=recipe['parameters']['gridsData'][0]
    if set(new_position)!={'x','y','angle'} or any(not finite(v) for v in new_position.values()):raise ValueError('EXACT_NEW_GRID_POSITION_REQUIRED')
    vertical=recipe['axis']['direction']=='X';key='x' if vertical else 'y';fixed='y' if vertical else 'x'
    if not RUN.close(new_position[fixed],prior[fixed]) or not RUN.close(new_position['angle'],prior['angle']):raise ValueError('AXIS_EDIT_REQUIRES_SAME_SOURCE_SPAN_ORIENTATION')
    if not recipe['outline'][key+'Min']<=new_position[key]<=recipe['outline'][key+'Max']:raise ValueError('EDITED_SEMANTIC_AXIS_OUTSIDE_OUTLINE')
    params={'gridsWithDetails':[dict(elementId={'guid':guid},**new_position,expectedX=prior['x'],expectedY=prior['y'],expectedAngle=prior['angle'])]}
    runtime_catalog(writer,'ModifyNativeGridElementsV1',params,'GetNativeGridElementsV1')
    updated=copy.deepcopy(recipe);updated['parameters']['gridsData'][0].update(new_position)
    updated['axis']['coordinate']=new_position[key]
    updated['sourceHash']=RUN.digest({k:v for k,v in updated.items() if k not in {'sourceHash','graph'}})
    updated['graph']={'operations':[{'id':recipe['axis']['id']+'-edit','command':'ModifyNativeGridElementsV1','params':params,'dependsOn':[]}]}
    def after(*_):return verify_grid(writer.api,guid,updated)
    result=E.execute_model_operation(writer,scene_id,'ModifyNativeGridElementsV1',params,RUN.digest([recipe['sourceHash'],params]),[guid],retained_signatures,after,authorization_ref,saved_sha256)
    if result['status']=='PASS':result.update(updatedRecipe=updated,nativeAxisBinding={'axisId':updated['axis']['id'],'guid':guid,'coordinate':updated['axis']['coordinate'],'sourceHash':updated['sourceHash']})
    return result

def qualify_grid_parameter_edit(parameters,owned,retained):
    if set(parameters)!={'elementsWithGDLParameters'} or len(parameters['elementsWithGDLParameters'])!=1:raise ValueError('GRID_PARAMETER_SINGLE_OWNED_TARGET_REQUIRED')
    row=parameters['elementsWithGDLParameters'][0];guid=row.get('elementId',{}).get('guid','').lower()
    if set(row)!={'elementId','gdlParameters'} or guid not in owned or guid in retained:raise ValueError('GRID_PARAMETERS_ONLY_NEW_OWNED_AXIS')
    changes=row['gdlParameters']
    if len(changes)!=2 or {p.get('name') for p in changes}!={'AC_Length','AC_Angle'} or any(set(p)!={'name','value'} or not finite(p['value']) for p in changes):raise ValueError('GRID_PARAMETERS_EXACT_LENGTH_ANGLE_REQUIRED')
    if next(p['value'] for p in changes if p['name']=='AC_Length')<=0:raise ValueError('GRID_PARAMETER_LENGTH_MUST_BE_POSITIVE')

def synchronize_grid_geometry(writer,guid,recipe,scene_id,retained_signatures,saved_sha256,authorization_ref):
    """Run the existing native GDL parameter script on only this true Grid.

    Grid's AC_Angle is independent of Object.angle. A/B or raw memo fields are
    not a substitute for the library's native dimension/angle parameters.
    """
    verify_grid(writer.api,guid,recipe);row=recipe['parameters']['gridsData'][0]
    actual=writer.api('GetNativeGridElementsV1',{'elements':[{'elementId':{'guid':guid}}]})['grids'][0]
    lookup={p['name']:p for p in actual['nativeParameters']}
    if lookup.get('AC_Length',{}).get('nativeTypeName')!='Length' or lookup.get('AC_Angle',{}).get('nativeTypeName')!='Angle':raise ValueError('GRID_SOURCE_NATIVE_LENGTH_ANGLE_NOT_FOUND')
    length=next(p['value'] for p in row['parameters'] if p['name']==recipe['profile']['lengthParameter'])
    # Existing ChangeAParameter consumes degrees; native memo/GetGrid uses radians.
    params={'elementsWithGDLParameters':[{'elementId':{'guid':guid},'gdlParameters':[{'name':'AC_Length','value':length},{'name':'AC_Angle','value':math.degrees(row['angle'])}]}]}
    runtime_catalog(writer,'SetGDLParametersOfElements',params,'GetNativeGridElementsV1')
    updated=copy.deepcopy(recipe);updated['profile']['angleParameter']='AC_Angle'
    updated['parameters']['gridsData'][0]['parameters']=[p for p in updated['parameters']['gridsData'][0]['parameters'] if p['name']!='AC_Angle']+[{'name':'AC_Angle','nativeType':lookup['AC_Angle']['nativeType'],'value':row['angle']}]
    updated['sourceHash']=RUN.digest({k:v for k,v in updated.items() if k not in {'sourceHash','graph'}})
    updated['graph']={'operations':[{'id':recipe['axis']['id']+'-parameters','command':'SetGDLParametersOfElements','params':params,'dependsOn':[]}]}
    def before(api):
        if api('GetNativeGridDefaultsV1',{})!=recipe['defaults']:raise ValueError('GRID_NATIVE_DEFAULTS_CHANGED')
        verify_grid(api,guid,recipe)
        current=api('GetNativeGridElementsV1',{'elements':[{'elementId':{'guid':guid}}]})['grids'][0]
        now={p['name']:p for p in current['nativeParameters']}
        if not RUN.close(now['AC_Angle']['value'],lookup['AC_Angle']['value']):raise ValueError('GRID_NATIVE_ANGLE_CHANGED_BEFORE_PARAMETER_EDIT')
    def after(*_):
        proof=verify_grid(writer.api,guid,updated)
        if writer.api('GetNativeGridDefaultsV1',{})!=recipe['defaults']:raise ValueError('GRID_NATIVE_DEFAULTS_MODIFIED_UNEXPECTEDLY')
        return dict(proof,nativeParameterScript='EXISTING_SET_GDL_API',globalDefaultsUnchanged=True)
    result=E.execute_model_operation(writer,scene_id,'SetGDLParametersOfElements',params,RUN.digest([recipe['sourceHash'],params,lookup['AC_Angle']['value']]),[guid],retained_signatures,after,authorization_ref,saved_sha256,owned_before_check=before)
    if result['status']=='PASS':result.update(updatedRecipe=updated,nativeAxisBinding={'axisId':updated['axis']['id'],'guid':guid,'coordinate':updated['axis']['coordinate'],'sourceHash':updated['sourceHash']})
    return result

def favorite_rules(xml_path):
    raw=Path(xml_path).read_bytes();root=ET.fromstring(raw);stair=root.find('.//StairDefault')
    if root.tag!='Favorites' or stair is None:raise ValueError('EXACT_STAIR_SOURCE_FAVORITE_REQUIRED')
    fields={}
    for name in ['RuleMin','RuleMax','TreadDepthMin','TreadDepthMax','RiserHeightMin','RiserHeightMax']:
        for suffix in ['Value','Applied']:
            key=name+suffix;nodes=list(stair.iter(key))
            if len(nodes)!=1:raise ValueError('STAIR_FAVORITE_RULE_MISSING_OR_AMBIGUOUS:'+key)
            value=nodes[0].text
            if suffix=='Applied':
                if value not in {'true','false'}:raise ValueError('STAIR_FAVORITE_RULE_FLAG_INVALID')
                value=value=='true'
            else:
                value=float(value)
                if not finite(value) or value<0:raise ValueError('STAIR_FAVORITE_RULE_VALUE_INVALID')
            fields[key]=value
    return dict(sourceSHA256=hashlib.sha256(raw).hexdigest(),source='EXISTING_FAVORITE_RULES_NOT_REGULATORY_ACCEPTANCE',rules=fields,engineeringAcceptance='NOT_VERIFIED')

def check_source_combination(source,height,steps,going):
    if not finite(height) or height<=0 or type(steps) is not int or steps<2 or not finite(going) or going<=0:raise ValueError('EXACT_STAIR_COMBINATION_INVALID')
    r=height/steps;rules=source['rules'];failed=[]
    for prefix,value in [('Rule',2*r+going),('TreadDepth',going),('RiserHeight',r)]:
        for side in ['Min','Max']:
            key=prefix+side
            if key+'Applied' not in rules or key+'Value' not in rules:raise ValueError('STAIR_SOURCE_RULE_INCOMPLETE')
            if rules[key+'Applied'] and ((value<rules[key+'Value']-1e-9) if side=='Min' else (value>rules[key+'Value']+1e-9)):failed.append(dict(rule=key,actual=value,limit=rules[key+'Value']))
    return dict(status='SOURCE_RULE_CONFLICT' if failed else 'SOURCE_RULE_COMPATIBLE_NATIVE_SOLVER_NOT_VERIFIED',height=height,stepNum=steps,riser=r,requestedGoing=going,twoRiserPlusGoing=2*r+going,violations=failed,sourceSHA256=source['sourceSHA256'],nativeGeometry='NOT_VERIFIED',engineeringAcceptance='NOT_VERIFIED')

def verify_exact_stair(api,guid,row):
    actual=api('GetNativeStairGeometryV1',{'elementId':{'guid':guid}})
    if actual.get('nativeType')!='Stair' or actual.get('elementId',{}).get('guid','').lower()!=guid.lower() or actual.get('treadDepthLocked') is not True or actual.get('stepNum')!=row['stepNum'] or actual.get('floorIndex')!=row['floorIndex']:raise ValueError('EXACT_STAIR_NATIVE_IDENTITY_LOCK_COUNT_REQUIRED')
    for key in ['totalHeight','riserHeight','treadDepth','flightWidth']:
        if not RUN.close(actual.get(key),row[key]):raise ValueError('EXACT_STAIR_SOURCE_DIMENSION_MISMATCH:'+key)
    points=actual.get('worldBaseLinePoints',actual.get('baseLinePoints',[]))
    if actual.get('baseLineCoordinateFrame')=='LOCAL_BASE_PLANE' and 'worldBaseLinePoints' not in actual:raise ValueError('EXACT_STAIR_NATIVE_WORLD_FRAME_REQUIRED')
    if len(points)!=2 or any(not RUN.close(q.get(k),p[k]) for p,q in zip(row['baseLinePoints'],points) for k in ['x','y']):raise ValueError('EXACT_STAIR_SOURCE_BASELINE_MISMATCH')
    return dict(status='NATIVE_EXACT_STAIR_DIMENSION_READBACK_PASS',guid=guid,native=actual,sourceDimensionStatus='SOURCE_DIMENSION_PASS',engineeringAcceptance='NOT_VERIFIED')

def require_detached_stair_proof(writer,row,retained_signatures,saved_sha256,source):
    """A compatible Favourite is insufficient after a failed native solver probe.

    Consume an independently recorded, hash-pinned detached result; never run or
    retry the solver here. The known terminating candidate cannot qualify itself.
    """
    artifact=source.get('detachedPreflight',{})
    if not artifact.get('path') or not artifact.get('sha256'):raise ValueError('EXACT_STAIR_DETACHED_NATIVE_PROOF_REQUIRED_NO_WRITE')
    raw=Path(artifact['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=artifact['sha256']:raise ValueError('EXACT_STAIR_DETACHED_PROOF_BYTES_CHANGED')
    proof=json.loads(raw)
    if proof.get('status')!='DETACHED_NATIVE_SOURCE_DIMENSION_PASS_NO_CREATE' or proof.get('preservationReadback') is not True:raise ValueError('EXACT_STAIR_DETACHED_PROBE_FAILED_NO_WRITE')
    candidate=proof.get('candidateSHA256','')
    if len(candidate)!=64 or any(c not in '0123456789abcdef' for c in candidate) or candidate=='8ad672092aa93e4bf1b4d469cbf7840cb60acd538820183bb68d5d6786ea221d':raise ValueError('EXACT_STAIR_FAILED_CANDIDATE_REQUIRES_REQUALIFICATION')
    expected={'rowHash':RUN.digest(row),'sourceSHA256':source['sourceSHA256'],'targetBinding':writer.guarded_binding(),'savedSHA256':saved_sha256,'retainedSignaturesHash':RUN.digest(retained_signatures),'schemaSHA256':hashlib.sha256(writer.schema_path.read_bytes()).hexdigest()}
    if any(proof.get(k)!=v for k,v in expected.items()):raise ValueError('EXACT_STAIR_DETACHED_PROOF_BINDING_CHANGED_NO_WRITE')
    actual=proof.get('result',{})
    if actual.get('status')!='DETACHED_NATIVE_SOLVER_PASS_NOT_CREATED' or type(actual.get('nativeModelWrites')) is not int or actual['nativeModelWrites']!=0:raise ValueError('EXACT_STAIR_DETACHED_RESULT_NOT_QUALIFIED')
    for key in ['totalHeight','riserHeight','treadDepth','flightWidth']:
        if not RUN.close(actual.get(key),row[key]):raise ValueError('EXACT_STAIR_DETACHED_DIMENSION_MISMATCH')
    if actual.get('stepNum')!=row['stepNum'] or actual.get('treadDepthLocked') is not True:raise ValueError('EXACT_STAIR_DETACHED_LOCK_COUNT_MISMATCH')
    points=actual.get('baseLinePoints',[])
    if len(points)!=2 or any(not RUN.close(q.get(k),p[k]) for p,q in zip(row['baseLinePoints'],points) for k in ['x','y']):raise ValueError('EXACT_STAIR_DETACHED_BASELINE_FRAME_NOT_VERIFIED')
    verify_stair_rules(actual,source)
    return artifact['sha256']

def create_exact_stair(writer,row,scene_id,retained_signatures,saved_sha256,authorization_ref,source):
    if source.get('favoriteName')!=row['favoriteName'] or not source.get('sourcePath') or hashlib.sha256(Path(source['sourcePath']).read_bytes()).hexdigest()!=source.get('sourceSHA256'):raise ValueError('EXACT_STAIR_FAVORITE_SOURCE_CHANGED')
    current=favorite_rules(source['sourcePath'])
    if current['rules']!=source.get('rules'):raise ValueError('EXACT_STAIR_FAVORITE_RULE_PROFILE_CHANGED')
    allowed=check_source_combination(source,row['totalHeight'],row['stepNum'],row['treadDepth'])
    if allowed['violations']:raise ValueError('EXACT_STAIR_SOURCE_RULE_CONFLICT_NO_CREATE')
    params={'stairsData':[copy.deepcopy(row)]};qualify_operation('CreateExactStairsV1',params,set(),set(retained_signatures))
    runtime_catalog(writer,'CreateExactStairsV1',params,'GetNativeStairGeometryV1')
    source_hash=RUN.digest([row,source['sourceSHA256']])
    binding=writer.guarded_binding()
    if writer.journal_path.exists():
        with closing(sqlite3.connect(writer.journal_path)) as db:
            exists=db.execute("SELECT 1 FROM sqlite_master WHERE name='steps'").fetchone()
            prior=db.execute("SELECT state,guid,output FROM steps WHERE scene_id=? AND step_id='operation'",(scene_id,)).fetchone() if exists else None
        if prior:
            if prior[0]!='PASS' or not prior[1]:raise ValueError('STAIR_PREVIOUS_OPERATION_REQUIRES_RECONCILIATION_NEVER_RETRY')
            proof=json.loads(prior[2]).get('readback',{})
            if proof.get('sourceHash')!=source_hash:raise ValueError('STAIR_EXISTING_SOURCE_CHANGED_EXPLICIT_EDIT_REQUIRED')
            if proof.get('targetBinding')!=binding:raise ValueError('STAIR_COMPLETED_TARGET_BINDING_CHANGED')
            if prior[1].lower() in {g.lower() for g in retained_signatures}:raise ValueError('STAIR_COMPLETED_GUID_IS_RETAINED_NOT_OWNED')
            if hashlib.sha256(Path(binding['path']).read_bytes()).hexdigest()!=saved_sha256:raise ValueError('MODEL_SAVED_FILE_HASH_CHANGED')
            import archicad_connected_components as C
            native=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
            if C.retained_geometry_signatures(native,list(retained_signatures))!=retained_signatures:raise ValueError('MODEL_RETAINED_GEOMETRY_CHANGED')
            current_proof=verify_exact_stair(writer.api,prior[1],row)
            verify_stair_rules(current_proof['native'],source)
            return dict(status='NATIVE_EXACT_STAIR_REUSE_PASS',createdGuid=prior[1],readback=current_proof,nativeCreateCalls=0)
    require_detached_stair_proof(writer,row,retained_signatures,saved_sha256,source)
    def before(api):
        if source['favoriteName'] not in api('GetFavoritesByType',{'elementType':'Stair'}).get('favorites',[]):raise ValueError('EXACT_STAIR_FAVORITE_NO_LONGER_AVAILABLE')
        if hashlib.sha256(Path(source['sourcePath']).read_bytes()).hexdigest()!=source['sourceSHA256']:raise ValueError('EXACT_STAIR_SOURCE_CHANGED_BEFORE_DISPATCH')
        require_detached_stair_proof(writer,row,retained_signatures,saved_sha256,source)
    def after(reply,*_):
        proof=verify_exact_stair(writer.api,RUN.created_guid(reply),row)
        verify_stair_rules(proof['native'],source)
        proof['sourceHash']=source_hash
        proof['targetBinding']=binding
        return proof
    result=E.execute_model_operation(writer,scene_id,'CreateExactStairsV1',params,source_hash,[],retained_signatures,after,authorization_ref,saved_sha256,owned_before_check=before)
    return {**result,'nativeCreateCalls':1}

def verify_stair_rules(native,source):
    actual=native.get('rules',{})
    for key,value in source['rules'].items():
        native_key=key[0].lower()+key[1:]
        if native_key not in actual or (actual[native_key]!=value if type(value) is bool else not RUN.close(actual[native_key],value)):raise ValueError('EXACT_STAIR_NATIVE_FAVORITE_RULE_READBACK_MISMATCH')

def edit_exact_stair(writer,guid,row,scene_id,retained_signatures,saved_sha256,authorization_ref,source=None):
    if source is None:raise ValueError('EXACT_STAIR_DETACHED_NATIVE_PROOF_REQUIRED_NO_WRITE')
    require_detached_stair_proof(writer,row,retained_signatures,saved_sha256,source)
    actual=writer.api('GetNativeStairGeometryV1',{'elementId':{'guid':guid}})
    params={k:v for k,v in row.items() if k!='favoriteName'};params.update(elementId={'guid':guid},expectedTotalHeight=actual['totalHeight'],expectedGoing=actual['treadDepth'],expectedStepNum=actual['stepNum'])
    qualify_operation('ModifyNativeStairGeometryV1',params,{guid.lower()},set(retained_signatures))
    runtime_catalog(writer,'ModifyNativeStairGeometryV1',params,'GetNativeStairGeometryV1')
    def after(*_):return verify_exact_stair(writer.api,guid,row)
    return E.execute_model_operation(writer,scene_id,'ModifyNativeStairGeometryV1',params,RUN.digest(params),[guid],retained_signatures,after,authorization_ref,saved_sha256,owned_before_check=lambda _:require_detached_stair_proof(writer,row,retained_signatures,saved_sha256,source))
