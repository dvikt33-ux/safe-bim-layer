"""Prepare shared parameter edits; execute only through existing SceneWriter.

No transport, retries, journal, geometric kernel or independent SDK dispatcher.
New SDK mutation paths are BUILD_ONLY until explicit copy/write authorization
and native readback. Existing GDL command preparation is reused unchanged.
"""
import copy
import hashlib
import json
import math


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def command(router,name):
    return name if name in router.catalog['commands'] else 'AddOn.TapirCommand.'+name


def native_material_retention(before_model,after_model,element_ids):
    """Compare per-element native typed assignments, including GDL materials.

    An unchanged aggregate face-surface set missed real BuildingMaterial drift
    in the live Railing edit. Require every captured assignment for every scoped
    GUID; never infer preservation from appearance or a material name.
    """
    def snapshot(model):
        result={}
        for row in model['elements']:
            key=row['guid'].lower()
            if key in result:raise ValueError('AMBIGUOUS_NATIVE_MATERIAL_ELEMENT')
            result[key]=row.get('materialBindings')
        return result
    before,after=snapshot(before_model),snapshot(after_model);ids={g.lower() for g in element_ids}
    if not ids or not ids<=before.keys() or not ids<=after.keys():raise ValueError('MATERIAL_SCOPE_MISSING_NATIVE_ELEMENT')
    if any(before[g] is None or after[g] is None for g in ids):raise ValueError('NATIVE_MATERIAL_ASSIGNMENTS_NOT_CAPTURED')
    changed=sorted(g for g in ids if before[g]!=after[g])
    return dict(status='NATIVE_TYPED_MATERIAL_RETENTION_'+('FAIL' if changed else 'PASS'),elements=len(ids),changedElementGUIDs=changed,
                authority='PER_ELEMENT_NATIVE_MATERIAL_BINDINGS_INCLUDING_GDL_ASSIGNMENTS',faceSurfaceEqualityIsInsufficient=True,nativeModelWrites=0)


def gdl_parameter_disabled(row):
    flags=row.get('flags',[])
    # API_ParFlg_Disabled is 0x40. Fixed/Hidden are different native flags.
    if isinstance(flags,int) and not isinstance(flags,bool):return bool(flags & 0x40)
    if isinstance(flags,list):return 'Disabled' in flags
    raise ValueError('GDL_PARAMETER_FLAGS_NOT_TYPED')


def prepare_assembly_edit(router,state,changes):
    state,changes=copy.deepcopy(state),copy.deepcopy(changes)
    applicable=(set(state['values'])-set(state.get('readOnlyFields',[])))|set(state['attributes'])|set(state.get('memoEdits',[]))
    if state['kind']=='CurtainWall' and 'heightMetres' in changes:
        raise ValueError('CW_SCALAR_HEIGHT_NATIVE_NO_EFFECT_USE_QUALIFIED_CONTOUR_MEMO')
    if state['kind']=='Shell' and 'extrusionXMetres' in state['values']:applicable.add('profileCoordinates')
    if not changes or not set(changes)<=applicable:raise ValueError('ASSEMBLY_FIELD_NOT_APPLICABLE_TO_CAPTURED_STATE')
    params=dict(elementId=state['elementId'],expectedKind=state['kind'],expectedModificationStamp=state['modificationStamp'],changes=changes)
    ticket=router.prepare(command(router,'ModifyNativeAssemblyV1'),params)
    return dict(schema='APA_NATIVE_PARAMETER_EDIT_V1',state=state,stateHash=digest(state),ticket=ticket,
                executionPermission=False,executor='SceneWriter',nativeModelWrites=0,
                childGUIDPolicy='ROOT_TARGET_RETAINED_COMPONENTS_RECONCILED_INDEPENDENTLY',engineering='NOT_VERIFIED')


def execute_assembly_edit(router,writer,preview,*,scene_id,affected,retained_signatures,saved_sha256,authorization,verify_geometry=None,verify_geometry_before=None,verify_materials=None,verify_gdl=None,verify_ownership=None,verify_dependent_changes=None,verify_acceptance_before=None):
    """One intent. Fresh state before, independent state/membership after.

    Caller authorizes the isolated copy and complete affected root subtree.
    Existing router/SceneWriter enforce identity, retained bodies, SQLite
    intent-before-write and UNKNOWN_OUTCOME no-replay. No dependent writes.
    """
    import archicad_project_accelerator as A
    state=preview['state'];ticket=preview['ticket'];router.validate(ticket)
    if digest(state)!=preview['stateHash'] or ticket['parameters']!=dict(elementId=state['elementId'],expectedKind=state['kind'],expectedModificationStamp=state['modificationStamp'],changes=ticket['parameters']['changes']):
        raise ValueError('ASSEMBLY_PREVIEW_STATE_DRIFT')
    # Preparation remains available; incomplete acceptance cannot start a write.
    verifiers=dict(resultantGeometry=verify_geometry,typedMaterialBindings=verify_materials,gdlParameters=verify_gdl,nativeOwnership=verify_ownership,dependentChanges=verify_dependent_changes,beforeSnapshot=verify_acceptance_before)
    missing=[name for name,fn in verifiers.items() if not callable(fn)]
    if missing:return dict(status='NOT_VERIFIED',reason='COMPOUND_MODIFY_ACCEPTANCE_INCOMPLETE',unverifiedAreas=missing,nativeModelWrites=0,executionPermission=False,automaticRetry=False)
    target=state['elementId']['guid'].lower();affected={x.lower() for x in affected};root=state.get('rootElementId',{}).get('guid')
    if state['kind'] in {'CurtainWall','Railing','Shell'}:root=target
    if not root or root.lower() not in affected or target not in affected:raise ValueError('EXPLICIT_AFFECTED_ASSEMBLY_ROOT_REQUIRED')
    baseline={}
    def read_state(api):
        reply=router.read(api,router.prepare(command(router,'GetNativeAssemblyEditStateV1'),dict(elements=[dict(elementId=state['elementId'])])),True)
        if len(reply['elements'])!=1:raise ValueError('ASSEMBLY_STATE_CARDINALITY_MISMATCH')
        return reply['elements'][0]
    def members(api):
        if state['kind']=='Shell':return set()
        reply=api('GetSubelementsOfHierarchicalElements',dict(elements=[dict(elementId=dict(guid=root))]))
        if not isinstance(reply.get('subelements'),list) or len(reply['subelements'])!=1:raise ValueError('ASSEMBLY_MEMBERSHIP_RESULT_CARDINALITY_MISMATCH')
        result=set()
        def visit(v):
            if isinstance(v,dict):
                if 'error' in v:raise ValueError('NATIVE_ASSEMBLY_MEMBERSHIP_QUERY_FAILED')
                if isinstance(v.get('elementId'),dict):result.add(v['elementId']['guid'].lower())
                for item in v.values():visit(item)
            elif isinstance(v,list):
                for item in v:visit(item)
        visit(reply);return result
    def before(api):
        current=read_state(api)
        if digest(current)!=preview['stateHash']:raise ValueError('NATIVE_ASSEMBLY_STATE_CHANGED')
        baseline['children']=members(api)
        if not baseline['children']<=affected:raise ValueError('ASSEMBLY_CHILDREN_OUTSIDE_AUTHORIZED_SCOPE')
        baseline['acceptance']=verify_acceptance_before(api,current,affected)
        if not isinstance(baseline['acceptance'],dict) or not str(baseline['acceptance'].get('status','')).endswith('_PASS'):raise ValueError('ASSEMBLY_FULL_BEFORE_SNAPSHOT_NOT_VERIFIED')
        if verify_geometry_before is not None:
            proof=verify_geometry_before(api,current)
            if not isinstance(proof,dict) or not str(proof.get('status','')).endswith('PASS'):
                raise ValueError('ASSEMBLY_GEOMETRY_PREFLIGHT_NOT_VERIFIED')
            baseline['geometry']=proof
        return dict(status='NATIVE_ASSEMBLY_PARAMETER_PREFLIGHT_PASS')
    def after(reply,prior):
        current=read_state(writer.api)
        if current['elementId']['guid'].lower()!=target or current['kind']!=state['kind'] or current['homeStory']!=state['homeStory']:raise ValueError('ASSEMBLY_IDENTITY_TYPE_STORY_CHANGED')
        if state['kind'] not in {'CurtainWall','Railing','Shell'} and current.get('rootElementId',{}).get('guid','').lower()!=root.lower():raise ValueError('ASSEMBLY_COMPONENT_ROOT_CHANGED')
        for name,expected in ticket['parameters']['changes'].items():
            if name=='profileCoordinates':
                envelope=router.read(writer.api,router.prepare(command(router,'GetNativeEnvelopeMemoV1'),dict(elements=[dict(elementId=state['elementId'])])),True)
                shape=next(x for x in envelope['elements'][0]['shellShapes'] if x['slot']==0)
                actual=[{k:p[k] for k in ('x','y')} for p in shape['polygon']['coordinates']]
            elif name in {'referenceCoordinates','curtainWallContourCoordinates'}:
                memo=current['memo'];polygon=memo['referencePath'] if name=='referenceCoordinates' else memo['curtainWallContours'][0]['polygon']
                actual=[{k:p[k] for k in ('x','y')} for p in polygon['coordinates']]
            elif name in {'primaryPatternDistances','secondaryPatternDistances'}:
                actual=current['memo']['primaryPattern' if name.startswith('primary') else 'secondaryPattern']['distances']
            elif name in current['attributes']:actual=current['attributes'][name]['attributeId']
            else:actual=current['values'][name]
            if isinstance(expected,(float,int)) and not isinstance(expected,bool):
                if not math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-7):raise ValueError('ASSEMBLY_PARAMETER_READBACK_MISMATCH:'+name)
            elif isinstance(expected,dict) and 'guid' in expected:
                if actual.get('guid','').lower()!=expected['guid'].lower():raise ValueError('ASSEMBLY_ATTRIBUTE_IDENTITY_MISMATCH:'+name)
            elif isinstance(expected,list):
                def equal(a,b):
                    if isinstance(b,dict):return isinstance(a,dict) and set(a)==set(b) and all(equal(a[k],v) for k,v in b.items())
                    if isinstance(b,list):return isinstance(a,list) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
                    return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7) if isinstance(b,(float,int)) and not isinstance(b,bool) else a==b
                if not equal(actual,expected):raise ValueError('ASSEMBLY_MEMO_READBACK_MISMATCH:'+name)
            elif actual!=expected:raise ValueError('ASSEMBLY_PARAMETER_READBACK_MISMATCH:'+name)
        children=members(writer.api)
        if children!=baseline['children']:raise ValueError('ASSEMBLY_UNEXPECTED_CHILD_GUID_CHANGE_RECONCILE_NO_RETRY')
        geometry=verify_geometry(writer.api,state,current,baseline['children'],children)
        if not isinstance(geometry,dict) or not str(geometry.get('status','')).endswith('_PASS'):
            raise ValueError('ASSEMBLY_RESULTANT_GEOMETRY_NOT_VERIFIED')
        material_proof=verify_materials(writer.api,state,current)
        if not isinstance(material_proof,dict) or not str(material_proof.get('status','')).endswith('_PASS'):
            raise ValueError('ASSEMBLY_TYPED_MATERIAL_RETENTION_NOT_VERIFIED')
        other_proofs={}
        for name,fn in [('gdlParameters',verify_gdl),('nativeOwnership',verify_ownership),('dependentChanges',verify_dependent_changes)]:
            proof=fn(writer.api,state,current)
            if not isinstance(proof,dict) or not str(proof.get('status','')).endswith('_PASS'):raise ValueError('ASSEMBLY_ACCEPTANCE_AREA_NOT_VERIFIED:'+name)
            other_proofs[name]=proof
        return dict(status='NATIVE_ASSEMBLY_PARAMETERS_READBACK_PASS',rootGUID=root,targetGUID=target,
                    addedChildGUIDs=sorted(children-baseline['children']),removedChildGUIDs=sorted(baseline['children']-children),
                    currentStateSHA256=digest(current),physicalGeometry=geometry,materialAssignments=material_proof,acceptance=other_proofs,childGUIDs='EXACT_NATIVE_MEMBERSHIP_RETAINED',association='NOT_VERIFIED',engineering='NOT_VERIFIED')
    return router.execute(writer,scene_id,ticket,affected,retained_signatures,saved_sha256,authorization,'MODEL',after,before)


def prepare_existing_gdl_edit(router,element_guid,parameter_rows,changes):
    """Validate current parameter types/rank; reuse SetGDLParametersOfElements.

    No dictionary interpreter, implicit reshape, type conversion or execution.
    The SDK remains authoritative on parameter locks and dependent scripts.
    """
    rows={}
    for row in parameter_rows:
        if row['name'] in rows:raise ValueError('AMBIGUOUS_GDL_PARAMETER_NAME')
        rows[row['name']]=row
    parameters=[];dimensions=[]
    for name,value in changes.items():
        row=rows.get(name)
        if not row or 'value' not in row or row['type'] in {'Dictionary','UNKNOWN','Title','Separator'}:raise ValueError('GDL_PARAMETER_NOT_SUPPORTED_OR_NO_VALUE')
        if row.get('isLocked') is True or gdl_parameter_disabled(row):raise ValueError('GDL_PARAMETER_LOCKED_OR_DISABLED')
        old=row['value'];array=isinstance(old,list)
        if array!=isinstance(value,list):raise ValueError('GDL_SCALAR_ARRAY_RANK_CHANGE_NOT_SUPPORTED')
        outgoing=copy.deepcopy(value)
        if array:
            d1,d2=row.get('dimension1'),row.get('dimension2')
            if not isinstance(d1,int) or not isinstance(d2,int) or d1<=0 or d2<=0 or len(old)!=d1*d2:raise ValueError('GDL_DIMENSION_OR_CARDINALITY_MISMATCH')
            if value and all(isinstance(v,list) for v in value):
                if len(value)!=d1 or any(len(v)!=d2 for v in value):raise ValueError('GDL_DIMENSION_OR_CARDINALITY_MISMATCH')
                value=[v for row_values in value for v in row_values]
            if len(value)!=len(old) or any(isinstance(v,list) for v in value):raise ValueError('GDL_DIMENSION_OR_CARDINALITY_MISMATCH')
            # GetGDL serializes row-major arrays flat. SetGDL interprets a flat
            # list as Nx1, so reconstruct the declared matrix before routing.
            outgoing=[copy.deepcopy(value[i*d2:(i+1)*d2]) for i in range(d1)] if d2>1 else copy.deepcopy(value)
            dimensions.append(dict(name=name,dimension1=d1,dimension2=d2,serialization='ROW_MAJOR_MATRIX' if d2>1 else 'ONE_DIMENSIONAL',rankPreserved=True))
        source=old if array else [old];wanted=value if array else [value]
        for actual,expected in zip(wanted,source):
            if isinstance(expected,bool):valid=isinstance(actual,bool)
            elif isinstance(expected,int):valid=isinstance(actual,int) and not isinstance(actual,bool)
            elif isinstance(expected,float):valid=isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isfinite(actual)
            elif isinstance(expected,str):valid=isinstance(actual,str)
            else:valid=False
            if not valid:raise ValueError('GDL_PARAMETER_TYPE_MISMATCH')
        parameters.append(dict(name=name,value=outgoing))
    if not parameters:raise ValueError('EXPLICIT_GDL_PARAMETER_CHANGES_REQUIRED')
    ticket=router.prepare(command(router,'SetGDLParametersOfElements'),dict(elementsWithGDLParameters=[dict(elementId=dict(guid=element_guid),gdlParameters=parameters)]))
    return dict(schema='APA_EXISTING_GDL_EDIT_PREVIEW_V1',ticket=ticket,sourceParametersSHA256=digest(parameter_rows),sourceParameters=copy.deepcopy(parameter_rows),dimensions=dimensions,
                authority='CURRENT_PLACED_PARAMETER_TYPES_NOT_WRITE_OR_EDITABILITY_ACCEPTANCE',executionPermission=False,nativeModelWrites=0)


def readback_existing_gdl_edit(router,api,preview,phase='after'):
    """Read current placed definitions/values; never invoke the existing setter.

    Before phase refuses drift or newly locked fields. After phase requires
    exact type/rank and requested values, reports script-dependent other changes
    without scheduling any dependent native write. Unsupported definitions stay
    raw facts; Dictionary/Title/Separator are never interpreted as settable.
    """
    if phase not in {'before','after'}:raise ValueError('GDL_READBACK_PHASE_REQUIRED')
    ticket=preview['ticket'];router.validate(ticket)
    if ticket['command']!=command(router,'SetGDLParametersOfElements'):raise ValueError('EXISTING_GDL_SETTER_TICKET_REQUIRED')
    source=preview['sourceParameters']
    if digest(source)!=preview['sourceParametersSHA256']:raise ValueError('GDL_PREVIEW_PARAMETER_SNAPSHOT_DRIFT')
    targets=ticket['parameters']['elementsWithGDLParameters']
    if len(targets)!=1:raise ValueError('EXACTLY_ONE_GDL_READBACK_TARGET_REQUIRED')
    requested=targets[0];reply=router.read(api,router.prepare(command(router,'GetGDLParametersOfElements'),dict(elements=[dict(elementId=requested['elementId'])])),True)
    groups=reply.get('gdlParametersOfElements',[])
    if len(groups)!=1 or 'error' in groups[0]:raise ValueError('GDL_NATIVE_READBACK_CARDINALITY_OR_ERROR')
    rows=groups[0]['parameters'];old={p['name']:p for p in source};new={p['name']:p for p in rows}
    if len(old)!=len(source) or len(new)!=len(rows):raise ValueError('GDL_AMBIGUOUS_PARAMETER_DEFINITIONS')
    if phase=='before' and digest(rows)!=preview['sourceParametersSHA256']:raise ValueError('GDL_CURRENT_PLACED_PARAMETER_STATE_CHANGED')
    for change in requested['gdlParameters']:
        name=change['name'];before,after=old.get(name),new.get(name)
        if not before or not after or any(before.get(k)!=after.get(k) for k in ['index','type','dimension1','dimension2']):raise ValueError('GDL_NATIVE_TYPE_OR_DIMENSION_CHANGED')
        if phase=='before' and (after.get('isLocked') is True or gdl_parameter_disabled(after)):raise ValueError('GDL_CURRENT_PARAMETER_LOCKED')
        expected=before['value'] if phase=='before' else change['value']
        if isinstance(expected,list) and expected and all(isinstance(v,list) for v in expected):expected=[v for row in expected for v in row]
        if after.get('value')!=expected:raise ValueError('GDL_NATIVE_REQUESTED_VALUE_NOT_CONFIRMED:'+name)
    requested_names={p['name'] for p in requested['gdlParameters']};dependent=sorted(name for name in set(old)|set(new) if name not in requested_names and old.get(name)!=new.get(name))
    return dict(status='NATIVE_GDL_PARAMETER_'+phase.upper()+'_READBACK_PASS',elementId=requested['elementId'],requestedParameters=len(requested_names),scriptDependentChangedParameterNames=dependent,currentParametersSHA256=digest(rows),nativeModelWrites=0,automaticDependentWrites=False,engineering='NOT_VERIFIED')


def recovery_journal_status(journal_path,target_guids,reconciliation_proofs):
    """Read the existing ledger; never reopen/retry/reset an UNKNOWN scene.

    Caller supplies independently verified proof bytes for exact scene IDs.
    A matching proof hash explains an old outcome; it does not grant a write.
    """
    import sqlite3
    import re
    from pathlib import Path
    wanted={g.lower() for g in target_guids};blocked=[];reconciled=[];unscoped=[]
    with sqlite3.connect(Path(journal_path).resolve().as_uri()+'?mode=ro',uri=True) as db:
        for sid,state,raw,output in db.execute('SELECT s.scene_id,s.state,s.result,t.output FROM scenes s JOIN steps t ON s.scene_id=t.scene_id WHERE s.state NOT IN (\'PASS\',\'COMPLETE\')'):
            data=json.loads(output);result=json.loads(raw);intent=result.get('intent',data.get('intent',{}))
            text=json.dumps(intent.get('parameters',{}),sort_keys=True).lower() if intent else (output+' '+raw).lower()
            relevant=any(g in text for g in wanted)
            if not relevant:
                if not intent and not re.search(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',text):unscoped.append(sid)
                continue
            proof=reconciliation_proofs.get(sid);receipt=result.get('independentReconciliation',{})
            if proof is not None and hashlib.sha256(proof).hexdigest()==receipt.get('proofSHA256'):
                fact=json.loads(proof)
                if fact.get('sceneId',fact.get('originalSceneId'))==sid and fact.get('nativeWritesDuringReconciliation')==0 and 'RECONCILED' in fact.get('status','') and 'NO_EFFECT' in fact.get('status',''):
                    reconciled.append(sid);continue
            blocked.append(dict(sceneId=sid,state=state))
    return dict(status='RECOVERY_TARGET_JOURNAL_'+('BLOCKED' if blocked else 'NOT_VERIFIED' if unscoped else 'PASS'),unresolved=blocked,legacyUnscopedSceneIds=sorted(set(unscoped)),reconciledSceneIds=sorted(set(reconciled)),journalModified=False,executionPermission=False)


def prepare_railing_material_recovery(router,*,project_identity,saved_sha256,generated_object_guid,root_guid,owner_guid,placed_parameters,material_attributes,expected_material_guid,baseline_signatures,affected_guids,journal_status,owner_state=None):
    """Exact recovery intent plus lazy native reads, with no mutation ticket.

    The nested Object setter is proven unsupported. The public subelement memo
    route is documented but unresolved on AC29; do not invent a supported writer
    from enum names, raw parameter presence, or a Disabled/locked discrepancy.
    """
    import re
    if not isinstance(saved_sha256,str) or not re.fullmatch('[0-9a-f]{64}',saved_sha256):raise ValueError('RECOVERY_CURRENT_SAVED_SHA256_REQUIRED')
    ids={g.lower() for g in affected_guids};all_ids={g.lower() for g in baseline_signatures};target=generated_object_guid.lower();root=root_guid.lower()
    if not {target,root}<=ids or not ids<=all_ids:raise ValueError('RECOVERY_EXPLICIT_ROOT_AND_GENERATED_SCOPE_REQUIRED')
    wanted=expected_material_guid.lower();attrs=[x for x in material_attributes['attributes'] if x['attributeId']['guid'].lower()==wanted]
    if len(attrs)!=1 or not isinstance(attrs[0]['index'],int) or attrs[0]['index']<=0:raise ValueError('RECOVERY_ORIGINAL_BUILDING_MATERIAL_GUID_NOT_UNIQUE')
    definitions={p['name']:p for p in placed_parameters}
    if len(definitions)!=len(placed_parameters):raise ValueError('RECOVERY_AMBIGUOUS_PLACED_PARAMETERS')
    changes=[]
    for name in ['bmatRail','bmatFixing']:
        p=definitions.get(name)
        if not p or p['type']!='BuildingMaterial' or not isinstance(p.get('value'),int) or isinstance(p['value'],bool):raise ValueError('RECOVERY_TYPED_SCALAR_BUILDING_MATERIAL_REQUIRED')
        current=[a for a in material_attributes['attributes'] if a['index']==p['value']]
        if len(current)!=1:raise ValueError('RECOVERY_CURRENT_MATERIAL_IDENTITY_AMBIGUOUS')
        changes.append(dict(name=name,currentIndex=p['value'],currentAttributeId=current[0]['attributeId'],expectedIndex=attrs[0]['index'],expectedAttributeId=attrs[0]['attributeId'],disabled=gdl_parameter_disabled(p),isLocked=p.get('isLocked'),directWriteAllowed=False))
    reads=[router.prepare(command(router,'GetNativeAssemblyEditStateV1'),dict(elements=[dict(elementId=dict(guid=generated_object_guid))]))]
    missing=['PUBLIC_OWNER_ADD_PARS_WRITE_NOT_QUALIFIED','BMATFIXING_CONTROLLING_RULE_NOT_VERIFIED']
    if journal_status['status']!='RECOVERY_TARGET_JOURNAL_PASS':missing.append('RECOVERY_JOURNAL_SCOPE_NOT_FULLY_VERIFIED')
    if owner_state is None:missing.append('CURRENT_OWNER_COMPONENT_MEMO_AND_ROOT_STAMPS_NOT_READ')
    else:
        if owner_state['elementId']['guid'].lower()!=target or owner_state.get('rootElementId',{}).get('guid','').lower()!=root:raise ValueError('RECOVERY_NATIVE_OBJECT_ROOT_MISMATCH')
        owner=owner_state.get('ownerRecovery',{})
        if owner.get('ownerComponentId',{}).get('guid','').lower()!=owner_guid.lower():raise ValueError('RECOVERY_NATIVE_OWNER_MISMATCH')
        if not owner.get('ownerFoundInRootRailMemo') or not owner.get('rootRailMemoBounded'):missing.append('OWNER_NOT_QUALIFIED_IN_ROOT_RAIL_MEMO')
        # GetMemo stores flags; GetActParameters evaluates scripts and may add
        # Disabled/Child. A difference does not authorize bypassing active flags.
        for field in ['generatedObjectMaterials','ownerComponentMaterials']:
            memo=owner.get(field,{})
            if memo.get('memoQueryError')!=0 or memo.get('boundsStatus')!='BOUNDED_NATIVE_MEMO':missing.append('OWNER_TYPED_MATERIAL_MEMO_NOT_VERIFIED:'+field)
            entries={p.get('name'):p for p in memo.get('parameters',[])}
            for change in changes:
                entry=entries.get(change['name'],{})
                if entry.get('valueIndex')!=change['currentIndex'] or entry.get('attributeId',{}).get('guid','').lower()!=change['currentAttributeId']['guid'].lower():missing.append('OWNER_MATERIAL_VALUE_OR_IDENTITY_MISMATCH:'+field+':'+change['name'])
                change.setdefault('storedMemoFlags',{})[field]=entry.get('flags')
        missing.append('STORED_MEMO_FLAGS_DO_NOT_OVERRIDE_ACTIVE_SCRIPT_DISABLED_STATE')
        if owner.get('objectLibraryPartIndex'):
            reads.append(router.prepare(command(router,'GetNativeLibraryPartDefaultsV1'),dict(libraryPartIndices=[owner['objectLibraryPartIndex']],includeParameterScripts=True)))
    result=dict(schema='APA_RAILING_MATERIAL_RECOVERY_PREVIEW_V1',status='BLOCKED',reasons=missing,projectIdentity=copy.deepcopy(project_identity),savedSHA256=saved_sha256,generatedObjectId=dict(guid=generated_object_guid),rootElementId=dict(guid=root_guid),ownerComponentId=dict(guid=owner_guid),ownerStateSHA256=digest(owner_state) if owner_state is not None else None,requestedChanges=changes,placedParametersSHA256=digest(placed_parameters),baselineSignaturesSHA256=digest(baseline_signatures),affectedGUIDs=sorted(ids),retainedGUIDs=sorted(all_ids-ids),journalStatus=copy.deepcopy(journal_status),readTickets=reads,mutationTicket=None,nativeModelWrites=0,executionPermission=False,executor='Existing DynamicCommands / SceneWriter / SQLite only',geometryPolicy='NO_GEOMETRY_EDIT_NO_DELETE_CREATE_NO_UNDO',disabledPolicy='NEVER_WRITE_DISABLED_PARAMETER_WITHOUT_A_SUPPORTED_NATIVE_CONTRACT',propagation='NOT_INFERRED_FROM_PARAMETER_NAME_OR_SAME_VALUE')
    result['previewHash']=digest(result);return result
