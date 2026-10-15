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


def prepare_assembly_edit(router,state,changes):
    state,changes=copy.deepcopy(state),copy.deepcopy(changes)
    applicable=set(state['values'])|set(state['attributes'])
    if state['kind']=='Shell':applicable.add('profileCoordinates')
    if not changes or not set(changes)<=applicable:raise ValueError('ASSEMBLY_FIELD_NOT_APPLICABLE_TO_CAPTURED_STATE')
    params=dict(elementId=state['elementId'],expectedKind=state['kind'],expectedModificationStamp=state['modificationStamp'],changes=changes)
    ticket=router.prepare(command(router,'ModifyNativeAssemblyV1'),params)
    return dict(schema='APA_NATIVE_PARAMETER_EDIT_V1',state=state,stateHash=digest(state),ticket=ticket,
                executionPermission=False,executor='SceneWriter',nativeModelWrites=0,
                childGUIDPolicy='ROOT_TARGET_RETAINED_COMPONENTS_RECONCILED_INDEPENDENTLY',engineering='NOT_VERIFIED')


def execute_assembly_edit(router,writer,preview,*,scene_id,affected,retained_signatures,saved_sha256,authorization):
    """One intent. Fresh state before, independent state/membership after.

    Caller authorizes the isolated copy and complete affected root subtree.
    Existing router/SceneWriter enforce identity, retained bodies, SQLite
    intent-before-write and UNKNOWN_OUTCOME no-replay. No dependent writes.
    """
    import archicad_project_accelerator as A
    state=preview['state'];ticket=preview['ticket'];router.validate(ticket)
    if digest(state)!=preview['stateHash'] or ticket['parameters']!=dict(elementId=state['elementId'],expectedKind=state['kind'],expectedModificationStamp=state['modificationStamp'],changes=ticket['parameters']['changes']):
        raise ValueError('ASSEMBLY_PREVIEW_STATE_DRIFT')
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
            elif name in current['attributes']:actual=current['attributes'][name]['attributeId']
            else:actual=current['values'][name]
            if isinstance(expected,(float,int)) and not isinstance(expected,bool):
                if not math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-7):raise ValueError('ASSEMBLY_PARAMETER_READBACK_MISMATCH:'+name)
            elif isinstance(expected,dict) and 'guid' in expected:
                if actual.get('guid','').lower()!=expected['guid'].lower():raise ValueError('ASSEMBLY_ATTRIBUTE_IDENTITY_MISMATCH:'+name)
            elif actual!=expected:raise ValueError('ASSEMBLY_PARAMETER_READBACK_MISMATCH:'+name)
        children=members(writer.api)
        return dict(status='NATIVE_ASSEMBLY_PARAMETERS_READBACK_PASS',rootGUID=root,targetGUID=target,
                    addedChildGUIDs=sorted(children-baseline['children']),removedChildGUIDs=sorted(baseline['children']-children),
                    currentStateSHA256=digest(current),physicalGeometry='REQUIRES_SEPARATE_RESULTANT_BODY_ACCEPTANCE',association='NOT_VERIFIED',engineering='NOT_VERIFIED')
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
        if row.get('isLocked') is True or 'Disabled' in row.get('flags',[]):raise ValueError('GDL_PARAMETER_LOCKED_OR_DISABLED')
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
    return dict(schema='APA_EXISTING_GDL_EDIT_PREVIEW_V1',ticket=ticket,sourceParametersSHA256=digest(parameter_rows),dimensions=dimensions,
                authority='CURRENT_PLACED_PARAMETER_TYPES_NOT_WRITE_OR_EDITABILITY_ACCEPTANCE',executionPermission=False,nativeModelWrites=0)
