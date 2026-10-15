"""Typed grouped reads over the public AC29 SDK, using the existing manifest.

Generate the quantity field switch from an explicit installed SDK header.
No SDK header or private path is copied into the product.
"""
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUANTITY_TYPES={'Wall':('API_WallQuantity','wall'),'Column':('API_ColumnQuantity','column'),
 'Beam':('API_BeamQuantity','beam'),'Slab':('API_SlabQuantity','slab'),
 'Roof':('API_RoofQuantity','roof'),'Shell':('API_ShellQuantity','shell'),
 'Morph':('API_MorphQuantity','morph'),'Zone':('API_ZoneAllQuantity','zone'),
 'CurtainWall':('API_CurtainWallQuantity','cw'),'CurtainWallFrame':('API_CWFrameQuantity','cwFrame'),
 'CurtainWallPanel':('API_CWPanelQuantity','cwPanel'),'Stair':('API_StairQuantity','stair'),
 'Railing':('API_RailingQuantity','railing')}

def contracts():
    from build_functional_module_manifest import obj,arr,S,N,I,B
    eid=obj({'guid':dict(S,minLength=1)})
    inputs=obj({'elements':arr(obj({'elementId':eid}),minItems=1,maxItems=32)})
    error=obj({'error':obj({'code':I,'message':S})})
    either=lambda row:dict(anyOf=[row,error])
    polygon=obj(dict(indexBase={'const':1},coordinateFrame=S,
        coordinates=arr(obj({'index':I,'x':N,'y':N})),contourEnds=arr(I),
        arcs=arr(obj({'beginIndex':I,'endIndex':I,'angle':N})),vertexIds=arr(I),edgeIds=arr(I)))
    header=dict(elementId=eid,nativeTypeId=I,homeStory=I)
    envelope=obj(dict(header,polygon=polygon,roofEdgeTypes=arr(I),roofClass=I,roofLevel=N,
        pivotPolygon=polygon,shellClass=I,shellShapes=arr(obj({'slot':I,'polygon':polygon,'bodyFlags':arr(obj({'allocationIndex':I,'generatesBody':B})),'bodyFlagIndexAuthority':S},['slot','polygon','bodyFlags','bodyFlagIndexAuthority'])),
        shellContours=arr(obj({'slot':I,'hole':B,'depth':N,'polygon':polygon,'planeTransform':arr(N,minItems=12,maxItems=12),'edgeData':arr(obj({'allocationIndex':I,'edgeTypeId':I,'sideTypeId':I,'sideAngleRadians':N,'surfaceOverridden':B,'surfaceIndex':I}))})),
        shellContourCountExpected=I,shellContourCountAllocated=I,
        edgeTrims=arr(obj({'memoIndex':I,'sideTypeId':I,'sideAngleRadians':N})),
        sideMaterials=arr(obj({'memoIndex':I,'overridden':B,'surfaceIndex':I})),
        pivotEdgeOverrides=arr(obj({'memoIndex':I,'pivotEdgeUniqueId':I,'segmentTypeId':I,
            'levels':arr(obj({'levelIndex':I,'angleRadians':N,'angleTypeId':I,'eavesOverhangMetres':N,'topSurfaceIndex':I,'bottomSurfaceIndex':I}))})),
        shellBasePlaneTransform=arr(N,minItems=12,maxItems=12),shellClassParameters=obj({'coordinateFrame':S,'class':S,'begin':obj({'x':N,'y':N,'z':N}),'extrusionVector':obj({'x':N,'y':N,'z':N}),'shapeDirection':obj({'x':N,'y':N}),
        'axisBase':obj({'matrix3x4':arr(N,minItems=12,maxItems=12)}),'plane1':obj({'matrix3x4':arr(N,minItems=12,maxItems=12)}),'plane2':obj({'matrix3x4':arr(N,minItems=12,maxItems=12)}),
        'slantAngleRadians':N,'shapePlaneTiltRadians':N,'beginPlaneTiltRadians':N,'endPlaneTiltRadians':N,'revolutionAngleRadians':N,'distortionAngleRadians':N,'beginAngleRadians':N,
        'distortionVector':obj({'x':N,'y':N}),'segmentTypeId':I,'segmentsByArc':I,'segmentsByCircle':I,'segmentedSurfaces':B,'morphingRuleId':I},['coordinateFrame','class']),serializationBoundary=S),
        list(header)+['polygon','roofEdgeTypes','serializationBoundary'])
    drawings=obj(dict(elementId=eid,navigatorItemId=eid,databaseQualified=B,databaseQueryError=I,databaseTypeId=I,databaseId=eid,databaseRestoreError=I,linkGuid=eid,linkTypeId=I,viewTypeId=I,contentTypeId=I,
        viewDeleted=B,externalPathPresent=B,updateStatus=I,statusQueryError=I,contentBoxQueryError=I,
        fullContentBox=obj({k:N for k in ['xMin','yMin','xMax','yMax']})),
        ['elementId','linkGuid','linkTypeId','viewTypeId','contentTypeId','viewDeleted','externalPathPresent','updateStatus','statusQueryError','contentBoxQueryError'])
    hotspots=obj(dict(header,hotspots=arr(obj({'neigId':I,'neigIndex':I,'x':N,'y':N,'z':N}))))
    quantities=obj(dict(header,metrics=dict(type='object',additionalProperties=N),
        composites=arr(obj({'volume':N,'projectedArea':N,'buildingMaterialIndex':I}))))
    defs={
      'GetNativeEnvelopeMemoV1':(inputs,obj({'nativeModelWrites':{'const':0},'authority':S,'elements':arr(either(envelope))}),
        'Roof/Slab/Shell parameter topology, pivot polygons and shell contours; edge trims, side material indices and bounded pivot level overrides; not resultant BREP.'),
      'GetNativeDrawingAssociationsV1':(obj({'elements':arr(obj({'elementId':eid,'databaseId':eid},['elementId']),minItems=1,maxItems=32)}),obj({'nativeModelWrites':{'const':0},'drawings':arr(either(drawings)),'databaseRestoreError':I},['nativeModelWrites','drawings']),
        'Native Drawing source-link GUID, update status and full content box; private external paths suppressed.'),
      'GetNativeElementHotspotsV1':(inputs,obj({'nativeModelWrites':{'const':0},'authority':S,'elements':arr(either(hotspots))}),
        'Native element hotspots and neighbor references with XYZ; not body vertices.'),
      'GetNativeElementQuantitiesV1':(obj(dict(inputs['properties'],minOpeningSize=dict(N,minimum=0))),
        obj({'nativeModelWrites':{'const':0},'authority':S,'minOpeningSize':N,'elements':arr(either(quantities))}),
        'Native quantity engine scalars and composite material quantities for thirteen tool types. Explicit minOpeningSize; SDK field semantics apply, not engineering acceptance.')}
    component=obj(dict(header,variationId=I,hierarchyKind=I,parentQueryError=I,rootQueryError=I,
        parentElementId=eid,rootElementId=eid,declaredOwnerId=eid,libraryPartGuid=eid,
        specificParametersSupported=B,parameters=dict(type='object',additionalProperties=N),flags=dict(type='object',additionalProperties=B)),
        list(header)+['variationId','parentQueryError','rootQueryError','hierarchyKind','specificParametersSupported','parameters','flags'])
    xyz=obj({'x':N,'y':N,'z':N})
    opening=obj(dict(elementId=eid,nativeTypeId=I,parentResolved=B,hostElementId=eid,cutElements=arr(eid),
        connectedOpenings=arr(eid),anchor=xyz,vectorX=xyz,vectorY=xyz,extrusionDirection=xyz,
        shapeTypeId=I,limitTypeId=I,constraintId=I,widthMetres=N,heightMetres=N,
        finiteBodyLengthMetres=N,startOffsetMetres=N,geometryBoundary=S),['elementId','nativeTypeId'])
    defs.update({
      'GetNativeComponentBindingsV1':(inputs,obj({'nativeModelWrites':{'const':0},'authority':S,'elements':arr(either(component))}),
        'Reuse existing membership query; add hierarchical parent/root, Stair child and Railing/CurtainWall component parameters. Supported subset explicit per row.'),
      'GetNativeOpeningConnectionsV1':(inputs,obj({'nativeModelWrites':{'const':0},'authority':S,'elements':arr(either(opening))}),
        'AC29 modern Generic Opening host, cut-element identities, extrusion parameters and local frame; host-to-opening query. No cut-body BREP claim.'),
      'GetNativeQuantityPreflightV1':(inputs,obj({'nativeModelWrites':{'const':0},'quantityEngineCalled':{'const':False},'quarantineRetained':{'const':True},
        'elements':arr(either(obj(dict(header,stage={'const':'PRE_ENGINE_ELEMENT_IDENTIFIED_NO_QUANTITY_CALL'},engineCallAllowed={'const':False}))))}),
        'Read element identity and type only before the quarantined quantity engine. Does not allocate quantities, construct masks or call engine.')})
    value=dict(anyOf=[S,N,B,arr(S),arr(N),arr(B)])
    parameter=obj({'name':S,'displayName':S,'index':I,'type':S,'nativeTypeId':I,'typeModifier':I,'dimension1':I,'dimension2':I,'flags':I,'valueStatus':S,'value':value},['name','displayName','index','type','nativeTypeId','typeModifier','dimension1','dimension2','flags','valueStatus'])
    nav=obj({'navigatorItemId':eid,'requestedMap':S,'actualMapId':I,'itemTypeId':I,'sourceGuid':eid,'databaseTypeId':I,'databaseId':eid,'homeStory':I,'isIndependent':B,'identityMatchesRequest':B,'mapMatchesRequest':B,'parentQueryError':I,'parentItemId':eid},['navigatorItemId','requestedMap','actualMapId','itemTypeId','sourceGuid','databaseTypeId','databaseId','homeStory','isIndependent','identityMatchesRequest','mapMatchesRequest','parentQueryError'])
    defs.update({
      'GetNativeLibraryPartDefaultsV1':(obj({'libraryPartIndices':arr(dict(I,minimum=1),minItems=1,maxItems=8,uniqueItems=True)}),obj({'nativeModelWrites':{'const':0},'authority':S,'parts':arr(either(obj({'libraryPartIndex':I,'defaultA':N,'defaultB':N,'parameterCount':I,'parameters':arr(parameter)})))}),
        'Read bounded library-part default parameter definitions without a placed instance or global parameter context. Reuse existing Tapir serializers; dictionary/oversize arrays explicitly omitted; SDK handles disposed.'),
      'GetNativeNavigatorBindingsV1':(obj({'items':arr(obj({'navigatorItemId':eid,'navigatorMapId':dict(S,enum=['PublicViewMap','ProjectMap','LayoutBook'])}),minItems=1,maxItems=32)}),obj({'nativeModelWrites':{'const':0},'items':arr(either(nav))}),
        'Resolve exact Navigator GUID in an explicit map, source GUID, database and parent without rebuilding/updating Drawing. Complements existing Navigator tree, no name matching.')})
    defs['CreateNativeAssemblyV1']=(obj({'kind':dict(S,enum=['CurtainWall','Railing','ExtrudedShell']),'origin':obj({'x':N,'y':N}),'homeStory':dict(I,minimum=-100,maximum=100),'relativeLevel':N,'length':dict(N,exclusiveMinimum=0,maximum=100),'height':dict(N,exclusiveMinimum=0,maximum=20),'extrusionDepth':dict(N,exclusiveMinimum=0,maximum=100)},['kind','origin','homeStory','relativeLevel','length','height']),
        either(obj({'nativeModelWrites':{'const':1},'nativeTypeId':I,'homeStory':I,'placementFrame':{'const':'HOME_STORY_RELATIVE_LEVEL'},'engineering':{'const':'NOT_VERIFIED'},'createdElements':arr(obj({'elementId':eid}),minItems=1,maxItems=1)})),
        'Native SDK defaults+Create for one straight CurtainWall/Railing or triangular-profile ExtrudedShell. Explicit geometry, preserved tool defaults; SceneWriter CREATE authorization/readback required. No Morph, quantity engine or custom geometry kernel.')
    rows={name:dict(version='29',category='Native SDK grouped read adapter',description=d,
        parameters=p,returns=r,availability='BUILD_CANDIDATE_NOT_RUNTIME_REGISTERED',
        implementationSource='archicad-addon/Sources/NativeExtendedModules.cpp') for name,(p,r,d) in defs.items()}
    rows['CreateNativeAssemblyV1'].update(operationKind='CREATE',impact='MODEL',implementationSource='archicad-addon/Sources/NativeAssemblyCommands.inc')
    rows['GetNativeLibraryPartDefaultsV1']['implementationSource']='archicad-addon/Sources/NativeLibraryDefaults.inc'
    rows['GetNativeElementQuantitiesV1'].update(
        executionBlocker='AC29_QUANTITY_ENGINE_ACCESS_VIOLATION_ROOT_CAUSE_NOT_VERIFIED_NO_REPLAY',
        description='QUARANTINED after an actual AC29 quantity query crash. Contract remains discoverable/preparable; APA dispatch and native entry refuse execution until independently diagnosed.')
    return rows

def write_schemas():
    source=ROOT/'archicad-addon/Sources/NativeExtendedSchemas.inc'
    lines=['// Generated by build_extended_module_contracts.py from code-owned schemas.']
    for name,row in contracts().items():
        for method,key in [('GetInputParametersSchema','parameters'),('GetRawResponseSchema','returns')]:
            lines.append(f'GS::Optional<GS::UniString> {name}Command::{method}() const {{return R"APA({json.dumps(row[key],separators=(",",":"))})APA";}}')
    source.write_text('\n'.join(lines)+'\n',encoding='utf8')

def write_quantity_fields(header):
    raw=Path(header).read_bytes();text=re.sub(r'/\*.*?\*/','',raw.decode('utf8'),flags=re.S);lines=[
        '// Generated scalar accessors from public Archicad 29 APIdefs_Elements.h.',
        '// SDK header SHA256 '+hashlib.sha256(raw).hexdigest(),
        '// Field names and meanings remain those of the SDK quantity engine.']
    count=0
    for tool,(struct,member) in QUANTITY_TYPES.items():
        match=re.search(r'struct\s+'+struct+r'\s*\{(.*?)\n\};',text,re.S)
        body=match.group(1) if match else dict((n,b) for b,n in re.findall(r'typedef\s+struct\s*\{(.*?)\}\s*(API_\w+)\s*;',text,re.S)).get(struct)
        if body is None:raise ValueError('SDK_QUANTITY_STRUCT_MISSING:'+struct)
        fields=[n for n in re.findall(r'\b(?:double|Int32|UInt32)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',body) if not n.startswith('filler')]
        if not fields:raise ValueError('SDK_QUANTITY_FIELDS_MISSING:'+struct)
        lines.append('case API_'+tool+'ID:')
        lines.extend(f' metrics.Add("{f}",static_cast<double>(values.{member}.{f}));' for f in fields)
        lines.append(' break;');count+=len(fields)
    (ROOT/'archicad-addon/Sources/NativeQuantityFields.inc').write_text('\n'.join(lines)+'\n',encoding='utf8')
    return dict(types=len(QUANTITY_TYPES),scalarAccessors=count)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--sdk-header',required=True);args=parser.parse_args()
    write_schemas();print(json.dumps(write_quantity_fields(args.sdk_header)))
