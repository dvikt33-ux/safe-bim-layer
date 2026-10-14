"""One source-bound native Stair/Slab-void recipe, using the existing writer."""
import copy,hashlib,math
from pathlib import Path
import xml.etree.ElementTree as ET
import archicad_project_accelerator as A
import archicad_authored_extension as E
import archicad_connected_components as C
RUN=A.RUN


def compatible_native_step_counts(height, going, rules):
    """Native configured limits only; no building-code or engineering verdict."""
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (height,going)):
        raise ValueError('NATIVE_STAIR_EXPLICIT_FINITE_DIMENSIONS_REQUIRED')
    fields=[('ruleMin','ruleMax'),('treadDepthMin','treadDepthMax'),('riserHeightMin','riserHeightMax')]
    for low,high in fields:
        for name in (low,high):
            if type(rules.get(name+'Applied')) is not bool or type(rules.get(name+'Value')) not in (int,float) or not math.isfinite(rules[name+'Value']) or rules[name+'Value']<=0:
                raise ValueError('NATIVE_STAIR_CONFIGURED_RULE_SOURCE_INCOMPLETE')
        if rules[low+'Applied'] and rules[high+'Applied'] and rules[low+'Value']>rules[high+'Value']:
            raise ValueError('NATIVE_STAIR_CONFIGURED_RULE_SOURCE_INCONSISTENT')
    def within(value,low,high):
        return (not rules[low+'Applied'] or value>=rules[low+'Value']-1e-8) and (not rules[high+'Applied'] or value<=rules[high+'Value']+1e-8)
    if not within(going,'treadDepthMin','treadDepthMax'):return []
    return [n for n in range(2,201) if within(height/n,'riserHeightMin','riserHeightMax') and within(2*height/n+going,'ruleMin','ruleMax')]


def prepare_source_dimension_example(api, source, native_state, data, schema_path):
    """One explicit native Stair graph; never silently alter count or dimensions.

    The caller supplies the independently captured native rule snapshot and
    complete test parameters. Normal identity/free-space/journal/retained checks
    still precede execution through the existing SceneWriter.
    """
    if hashlib.sha256(Path(source['sourcePath']).read_bytes()).hexdigest()!=source['sourceSHA256']:
        raise ValueError('NATIVE_STAIR_SOURCE_CHANGED_BEFORE_PLAN')
    source_guid=native_state.get('elementId',{}).get('guid','')
    if native_state.get('contract')!='APA_NATIVE_STAIR_GEOMETRY_V1' or native_state.get('nativeType')!='Stair' or not RUN._GUID.fullmatch(source_guid):
        raise ValueError('NATIVE_STAIR_TYPED_RULE_SNAPSHOT_REQUIRED')
    if data.get('favoriteName')!=source['favoriteName'] or source['favoriteName'] not in api('GetFavoritesByType',{'elementType':'Stair'}).get('favorites',[]):
        raise ValueError('NATIVE_STAIR_SOURCE_FAVORITE_UNAVAILABLE')
    params={'stairsData':[copy.deepcopy(data)]}
    # The ordinary scope validator checks every required field and H=N*R.
    E.model_operation_scope('CreateStairs',params,'source-validation',[],[source_guid],'explicit source test')
    if not RUN.close(data['flightWidth'],source['values']['FlightWidth']) or not RUN.close(data['treadDepth'],source['values']['TreadDepth']):
        raise ValueError('NATIVE_STAIR_FAVORITE_SOURCE_WIDTH_OR_GOING_CHANGED')
    counts=compatible_native_step_counts(data['totalHeight'],data['treadDepth'],native_state['rules'])
    if data['stepNum'] not in counts:
        raise ValueError('NATIVE_STAIR_REQUEST_INCOMPATIBLE_WITH_CONFIGURED_RULES_NO_SILENT_CHANGE')
    stories=api('GetStories',{})['stories'];lower=next((r for r in stories if r['index']==data['floorIndex']),None)
    if lower is None or not RUN.close(lower['level'],data['zCoordinate']):
        raise ValueError('NATIVE_STAIR_EXACT_LOWER_STORY_REQUIRED')
    upper=next((r for r in stories if RUN.close(r['level'],data['zCoordinate']+data['totalHeight'])),None)
    if upper is None:raise ValueError('NATIVE_STAIR_EXACT_UPPER_STORY_REQUIRED')
    a,b=data['baseLinePoints']
    if not RUN.close(a['x'],b['x']) or b['y']<=a['y']:
        raise ValueError('NATIVE_STAIR_EXAMPLE_REQUIRES_SOURCE_STRAIGHT_POSITIVE_Y_FRAME')
    length=math.hypot(b['x']-a['x'],b['y']-a['y'])
    if not RUN.close(length,data['stepNum']*data['treadDepth']):
        raise ValueError('NATIVE_STAIR_TEST_REQUIRES_EXPLICIT_FULL_WALKING_LINE')
    graph={'operations':[dict(id='source-native-stair-example',command='CreateStairs',params=params,after=[])]}
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(schema_path),graph,runtime_version=RUN.EXPECTED_TAPIR)
    if checked['status']!='PLAN_VALIDATED_OFFLINE':raise ValueError('NATIVE_STAIR_SOURCE_GRAPH_INVALID')
    recipe=dict(schema='APA_NATIVE_STAIR_SOURCE_DIMENSION_EXAMPLE_V1',source=copy.deepcopy(source),nativeRuleSnapshot=copy.deepcopy(native_state),parameters=params,graph=graph,graphPlanHash=checked['sourcePlanHash'],lowerStory=lower,upperStory=upper,compatibleCounts=counts,dimensionPolicy='EXPLICIT_TEST_COUNT_AND_HEIGHT_SOURCE_FAVOURITE_WIDTH_GOING_NO_SILENT_CORRECTION',physicalConnection='NOT_VERIFIED_DETACHED_EXAMPLE',engineeringAcceptance='NOT_VERIFIED')
    recipe['sourceHash']=RUN.digest(recipe)
    return recipe


def favorite_dimensions(xml_path,favorite_name):
    raw=Path(xml_path).read_bytes();root=ET.fromstring(raw)
    stair=root.find('.//StairDefault')
    if root.tag!='Favorites' or stair is None:raise ValueError('NATIVE_STAIR_FAVORITE_SOURCE_REQUIRED')
    def number(tag):
        nodes=stair.findall(tag)
        if len(nodes)!=1:raise ValueError('NATIVE_STAIR_SOURCE_FIELD_MISSING:'+tag)
        value=float(nodes[0].text)
        if not math.isfinite(value) or value<=0:raise ValueError('NATIVE_STAIR_SOURCE_DIMENSION_INVALID')
        return value
    values={tag:number(tag) for tag in ['FlightWidth','StepNum','RiserHeight','TreadDepth','TotalHeight']}
    if values['StepNum']!=int(values['StepNum']) or abs(values['StepNum']*values['RiserHeight']-values['TotalHeight'])>1e-6:
        raise ValueError('NATIVE_STAIR_FAVORITE_DIMENSIONS_INCONSISTENT')
    return dict(favoriteName=favorite_name,sourceSHA256=hashlib.sha256(raw).hexdigest(),sourcePath=str(Path(xml_path).resolve()),values=values,
        exportAcceptance='MAIN_XML_PARSED; RELATED_GDL_EXPORT_SEPARATELY_QUALIFIED',engineeringAcceptance='NOT_VERIFIED')


def audit_stair_inventory(native, inventory, retained, stair_guid, child_guids):
    """Explain actual native inventory without inventing hidden Stair ownership.

    Bodyless Objects are still elements. Native object.owner is an owner
    reference, not automatically a host or proof of ancestry to this Stair.
    An unresolved delta stays NOT_VERIFIED and never permits a Create replay.
    """
    ids={g.lower() for g in inventory};baseline={g.lower() for g in retained}
    members={stair_guid.lower(),*(g.lower() for g in child_guids)}
    if baseline & members or not baseline|members <= ids:
        raise ValueError('NATIVE_STAIR_RETAINED_OR_MEMBER_INVENTORY_MISMATCH')
    rows={e['guid'].lower():e for e in native['elements']}
    if not ids <= rows.keys():raise ValueError('NATIVE_STAIR_INVENTORY_NOT_FULLY_READ_BACK')
    if C.retained_geometry_signatures(native,list(retained))!=retained:
        raise ValueError('NATIVE_STAIR_RETAINED_GEOMETRY_CHANGED')
    extra=[]
    for guid in sorted(ids-baseline-members):
        row=rows[guid];relation=row.get('relationships',{})
        owner=relation.get('ownerGuid','').lower()
        resolved=row['type']=='Object' and relation.get('nativeField')=='object.owner' and owner in members
        extra.append(dict(guid=guid,nativeType=row['type'],bodyCount=len(row['bodies']),
            ownerGuid=owner or None,ownership='NATIVE_OWNER_IN_STAIR_MEMBERS' if resolved else 'NOT_VERIFIED'))
    unresolved=[r['guid'] for r in extra if r['ownership']=='NOT_VERIFIED']
    return dict(status='NOT_VERIFIED' if unresolved else 'NATIVE_STAIR_INVENTORY_PASS',
        retainedCount=len(baseline),nativeMemberCount=len(members),inventoryCount=len(ids),
        additionalElements=extra,unresolvedGuids=unresolved,automaticRetry=False,
        dimensionAcceptanceIndependent=True)


def prepare(api,plan,created,source):
    E.verify_model(api,plan,created)
    favs=api('GetFavoritesByType',{'elementType':'Stair'}).get('favorites',[])
    if source['favoriteName'] not in favs:raise ValueError('NATIVE_STAIR_FAVORITE_NO_LONGER_AVAILABLE')
    stories=plan['storyBindings'];lower,upper=stories[:2]
    height=upper['level']-lower['level'];v=source['values'];steps=int(v['StepNum'])
    outline=plan['envelope'];ops={s['id']:s for s in plan['graph']['operations']}
    partitions=[next(iter(op['params'].values()))[0] for sid,op in ops.items()
        if op['command']=='CreateWalls' and sid.startswith('test-partition-') and created[sid]['floorIndex']==lower['nativeIndex']]
    if len(partitions)!=1:raise ValueError('STAIROFFSET_REQUIRES_VERIFIED_PARTITION_BAY')
    partition=partitions[0];xwall=partition['begCoordinate']['x']
    if partition['endCoordinate']['x']!=xwall:raise ValueError('STAIR_TEST_REQUIRES_STRAIGHT_Y_PARTITION')
    external=[next(iter(op['params'].values()))[0] for op in ops.values() if op['command']=='CreateWalls']
    thick=max(d['thickness'] for d in external)
    xmin=outline['xMin']+thick/2;xmax=xwall-partition['thickness']/2
    ymin=outline['yMin']+thick/2;ymax=outline['yMax']-thick/2
    length=(steps-1)*v['TreadDepth'];width=v['FlightWidth']
    if width>=xmax-xmin or length+v['TreadDepth']>=ymax-ymin:
        raise ValueError('SOURCE_STAIR_DOES_NOT_FIT_ACTUAL_BAY')
    x=(xmin+xmax)/2;y=(ymin+ymax-length)/2
    data=dict(favoriteName=source['favoriteName'],baseLinePoints=[{'x':x,'y':y},{'x':x,'y':y+length}],
        zCoordinate=lower['level'],floorIndex=lower['nativeIndex'],totalHeight=height,
        flightWidth=width,stepNum=steps,riserHeight=height/steps,treadDepth=v['TreadDepth'],finishVisible=False)
    graph=copy.deepcopy(plan['graph']);graph['operations'].append(dict(id='native-stair-connection',command='CreateStairs',
        params={'stairsData':[data]},after=['native-slab-level-1','native-slab-level-2']))
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(RUN.DEFAULT_SCENE_SCHEMA),graph,runtime_version=RUN.EXPECTED_TAPIR)
    if checked['status']!='PLAN_VALIDATED_OFFLINE':raise ValueError('STAIR_BIM_GRAPH_INVALID')
    from archicad_native_spatial_structure import template_reference_signatures
    baseline=A.inventory_guids(api);templates=template_reference_signatures(api,
        sorted(set(baseline)-{v['guid'].lower() for v in created.values()}))
    return dict(schema='APA_NATIVE_STAIR_CONNECTION_V1',source=source,parameters={'stairsData':[data]},
        baselineInventory=baseline,templateSignatures=templates,
        graph=graph,graphPlanHash=checked['sourcePlanHash'],lowerStory=lower,upperStory=upper,
        lowerSlabGuid=created['native-slab-level-1']['guid'],upperSlabGuid=created['native-slab-level-2']['guid'],
        plan=plan,created=created,sourceDimensions='EXPORTED_NATIVE_FAVORITE; RISE_FROM_REAL_STORIES',
        holePolicy='MEASURED_NATIVE_STAIR_FOOTPRINT_NO_INVENTED_CLEARANCE',engineeringAcceptance='NOT_VERIFIED')


def read_native_stair(api,guid,expected):
    info=RUN.requested_details(api,guid)
    if info['type']!='Stair' or info['floorIndex']!=expected['floorIndex']:
        raise ValueError('NATIVE_STAIR_TYPE_OR_FLOOR_MISMATCH')
    parts=api('GetSubelementsOfHierarchicalElements',{'elements':[{'elementId':{'guid':guid}}]})['subelements'][0]
    children=sorted({item['elementId']['guid'].lower() for values in parts.values() if isinstance(values,list) for item in values})
    native=C.G.normalize_dump(api('GetModelDumpV1',{}));rows={e['guid'].lower():e for e in native['elements']}
    members={guid.lower(),*children};body_rows=[rows[g] for g in members if g in rows]
    points=[p for row in body_rows for b in row['bodies'] for p in b['vertices']]
    if not points:raise ValueError('NATIVE_STAIR_HAS_NO_OWNED_ACTUAL_BODIES')
    bounds={axis+suffix:fn(p[i] for p in points) for i,axis in enumerate('xyz') for suffix,fn in [('Min',min),('Max',max)]}
    if abs(bounds['zMax']-(expected['zCoordinate']+expected['totalHeight']))>1e-5:
        raise ValueError('NATIVE_STAIR_TOP_DOES_NOT_REACH_ACTUAL_UPPER_STORY')
    if abs((bounds['xMax']-bounds['xMin'])-expected['flightWidth'])>1e-5:
        raise ValueError('NATIVE_STAIR_ACTUAL_FLIGHT_WIDTH_MISMATCH')
    names=['Stair_DefaultGoing','Stair_DefaultRiserHeight','Stair_FlightWidth','Stair_WalkingLineLength']
    ids=api('API.GetPropertyIds',{'properties':[{'type':'BuiltIn','nonLocalizedName':n} for n in names]})['properties']
    values=api('API.GetPropertyValuesOfElements',{'elements':[{'elementId':{'guid':guid}}],'properties':ids})['propertyValuesForElements'][0]['propertyValues']
    numeric={}
    for name,value in zip(names,values):
        p=value.get('propertyValue',{})
        if p.get('status')!='normal' or type(p.get('value')) not in (int,float):
            raise ValueError('PRECISE_NATIVE_STAIR_DIMENSION_UNAVAILABLE')
        numeric[name]=p['value']
    if not RUN.close(numeric['Stair_FlightWidth'],expected['flightWidth']) or not RUN.close(numeric['Stair_DefaultRiserHeight'],expected['riserHeight']):
        raise ValueError('PRECISE_NATIVE_STAIR_WIDTH_OR_RISER_MISMATCH')
    matches=RUN.close(numeric['Stair_DefaultGoing'],expected['treadDepth'])
    return dict(status='NATIVE_STAIR_OWNED_GEOMETRY_PASS',guid=guid,childGuids=children,
        nativePartCounts={k:len(v) for k,v in parts.items() if isinstance(v,list)},bounds=bounds,
        actualBodyCount=sum(len(row['bodies']) for row in body_rows),nativeType='Stair',
        typedStairParameters='OFFICIAL_PRECISE_BUILTIN_PROPERTIES_AND_NATIVE_MEMO_BREP',
        actualNumericProperties=numeric,requestedGoing=expected['treadDepth'],
        requestedGoingAcceptance='PASS' if matches else 'NOT_VERIFIED_NATIVE_SOLVER_CHANGED_GOING',
        engineeringAcceptance='NOT_VERIFIED')


def hole_from_native_stair(proof,slab_details):
    if slab_details['details'].get('holes'):raise ValueError('STAIR_VOID_CANNOT_DISCARD_EXISTING_SLAB_HOLES')
    b=proof['bounds'];points=[dict(x=b['xMin'],y=b['yMin']),dict(x=b['xMax'],y=b['yMin']),
        dict(x=b['xMax'],y=b['yMax']),dict(x=b['xMin'],y=b['yMax'])]
    from shapely.geometry import Polygon
    outline=slab_details['details'].get('polygonOutline')
    if not outline or not Polygon([(p['x'],p['y']) for p in outline]).contains(Polygon([(p['x'],p['y']) for p in points])):
        raise ValueError('ACTUAL_STAIR_FOOTPRINT_IS_NOT_INSIDE_UPPER_SLAB')
    return points


def verify_slab_void(before,actual,points):
    """Native memo can rotate rings, repeat endpoints and quantize coordinates."""
    if before['floorIndex']!=actual['floorIndex']:raise ValueError('STAIR_VOID_SLAB_FLOOR_CHANGED')
    old=before['details'];new=actual['details'];holes=new.get('holes',[])
    if len(holes)!=1:raise ValueError('STAIR_VOID_NATIVE_HOLE_COUNT_MISMATCH')
    ring=holes[0].get('polygonOutline',holes[0].get('polygonCoordinates'))
    if not RUN.compare_polygon(points,ring):raise ValueError('STAIR_VOID_ACTUAL_HOLE_CONTOUR_MISMATCH')
    outer=list(old['polygonOutline'])
    if RUN.close(outer[0]['x'],outer[-1]['x']) and RUN.close(outer[0]['y'],outer[-1]['y']):outer.pop()
    if not RUN.compare_polygon(outer,new.get('polygonOutline')):
        raise ValueError('STAIR_VOID_OUTER_SLAB_CONTOUR_CHANGED')
    for key in ['thickness','zCoordinate']:
        if not RUN.close(old[key],new.get(key)):raise ValueError('STAIR_VOID_SLAB_DIMENSIONS_CHANGED')
    if old['buildingMaterialId']!=new.get('buildingMaterialId'):
        raise ValueError('STAIR_VOID_SLAB_MATERIAL_CHANGED')
    return dict(status='NATIVE_SLAB_VOID_CONTOUR_READBACK_PASS',nativeHoleCount=1,
        outerContourPreserved=True,materialPreserved=True,floorPreserved=True,
        coordinateComparison='NATIVE_RING_CYCLIC_ORIENTATION_AND_ENDPOINT_NORMALIZATION_1E-6')


def connection_readback(api,stair_guid,expected,lower_slab,upper_slab):
    proof=read_native_stair(api,stair_guid,expected)
    native=C.G.normalize_dump(api('GetModelDumpV1',{}));rows={e['guid'].lower():e for e in native['elements']}
    members={stair_guid.lower(),*proof['childGuids']};physical={g for g in members if g in rows and rows[g]['bodies']}
    owners={g:stair_guid.lower() for g in physical}
    owners.update({lower_slab.lower():lower_slab.lower(),upper_slab.lower():upper_slab.lower()})
    contacts=C.G.shared_surfaces(rows,owners)
    upper_contacts=[r for r in contacts if set(r['guids'])=={stair_guid.lower(),upper_slab.lower()}]
    lower_contacts=[r for r in contacts if set(r['guids'])=={stair_guid.lower(),lower_slab.lower()}]
    collisions=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':g}} for g in physical],
        'elementsGroup2':[{'elementId':{'guid':upper_slab}}],
        'settings':{'volumeTolerance':1e-8,'performSurfaceCheck':False,'surfaceTolerance':1e-8}})
    if collisions.get('collisions')!=[]:raise ValueError('NATIVE_STAIR_STILL_INTERSECTS_UPPER_SLAB')
    if not upper_contacts:raise ValueError('NATIVE_STAIR_UPPER_SLAB_PHYSICAL_CONTACT_NOT_VERIFIED')
    base=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':g}} for g in physical],
        'elementsGroup2':[{'elementId':{'guid':lower_slab}}],
        'settings':{'volumeTolerance':1e-8,'performSurfaceCheck':False,'surfaceTolerance':1e-8}})
    return dict(status='NATIVE_STAIR_SLAB_CONNECTION_GEOMETRY_PASS',stair=proof,
        physicalBodyOwnerGuids=sorted(physical),upperSlabPhysicalContacts=upper_contacts,
        lowerSlabSurfaceContacts=lower_contacts,upperSlabVolumeCollisions=[],
        lowerSlabVolumeCollisions=base['collisions'],
        baseIntersectionPolicy='EXPLICIT_TEST_STRUCTURAL_FOOTING_EMBEDDING; NOT_LOAD_CAPACITY_ACCEPTANCE',
        engineeringAcceptance='NOT_VERIFIED',sourceGoingAcceptance=proof['requestedGoingAcceptance'])


def verify_connected_model(api,building_plan,created,stair_guid,stair_data,connection,output):
    """Attach actual Stair/Slab contacts to the existing native building graph."""
    import networkx as nx
    original=C.G.run(api,building_plan,created,A.inventory_guids(api),output)
    if original['nativeVolumeIntersectionPairs']:raise ValueError('BUILDING_HAS_NEW_UNPLANNED_VOLUME_COLLISIONS')
    graph=nx.Graph()
    graph.add_nodes_from(v['guid'].lower() for v in created.values())
    for edge in original['graphEdges']:graph.add_edge(*edge['guids'])
    graph.add_node(stair_guid.lower())
    for edge in connection['upperSlabPhysicalContacts']+connection['lowerSlabSurfaceContacts']:
        graph.add_edge(*edge['guids'])
    components=[sorted(v) for v in nx.connected_components(graph)]
    if len(components)!=1 or len(components[0])!=len(created)+1:
        raise ValueError('NATIVE_STAIR_BUILDING_IS_NOT_ONE_CONNECTED_PHYSICAL_COMPONENT')
    return dict(status='NATIVE_BUILDING_WITH_STAIR_CONNECTED_GEOMETRY_PASS',primaryElementCount=len(created)+1,
        physicalComponents=components,buildingGeometry=original,stairConnection=connection,
        sourceDimensionAcceptance=connection['sourceGoingAcceptance'],engineeringAcceptance='NOT_VERIFIED')


def execute(writer,recipe,run_id,saved_sha256):
    """Two qualified operations on the same SceneWriter; never replay a packet."""
    source=recipe['source']
    if hashlib.sha256(Path(source['sourcePath']).read_bytes()).hexdigest()!=source['sourceSHA256']:
        raise ValueError('NATIVE_STAIR_SOURCE_CHANGED_BEFORE_WRITE')
    if A.inventory_guids(writer.api)!=recipe['baselineInventory']:
        raise ValueError('NATIVE_STAIR_CREATION_BASELINE_CHANGED_OR_ALREADY_CREATED')
    old=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
    signatures=C.retained_geometry_signatures(old,recipe['baselineInventory'])
    data=recipe['parameters']['stairsData'][0]
    def before_create(api):
        if source['favoriteName'] not in api('GetFavoritesByType',{'elementType':'Stair'})['favorites']:
            raise ValueError('NATIVE_STAIR_SOURCE_FAVORITE_UNAVAILABLE')
    def after_create(reply,*_):
        guid=RUN.created_guid(reply);proof=read_native_stair(writer.api,guid,data)
        actual=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
        if C.retained_geometry_signatures(actual,recipe['baselineInventory'])!=signatures:
            raise ValueError('NATIVE_STAIR_CREATE_CHANGED_EXISTING_ELEMENTS')
        return proof
    created=E.execute_model_operation(writer,run_id+'-create','CreateStairs',recipe['parameters'],
        RUN.digest(recipe),[v['guid'] for v in recipe['created'].values()],recipe['templateSignatures'],
        after_create,'Explicit source-bound native Stair recipe',saved_sha256,owned_before_check=before_create)
    if created['status']!='PASS':return dict(status='PARTIAL_OR_UNKNOWN_OUTCOME',creation=created,automaticRetry=False)
    guid=created['createdGuid'];stair=created['readback'];upper=recipe['upperSlabGuid']
    slab_before=RUN.requested_details(writer.api,upper);points=hole_from_native_stair(stair,slab_before)
    inventory=A.inventory_guids(writer.api);native=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
    retained=C.retained_geometry_signatures(native,[g for g in inventory if g!=upper.lower()])
    params={'slabsWithDetails':[{'elementId':{'guid':upper},'holes':[{'polygonCoordinates':points}]}]}
    def before_hole(api):
        if RUN.requested_details(api,upper)['details'].get('holes'):
            raise ValueError('NATIVE_STAIR_VOID_ALREADY_EXISTS_OR_CHANGED')
    def after_hole(*_):
        contour=verify_slab_void(slab_before,RUN.requested_details(writer.api,upper),points)
        contact=connection_readback(writer.api,guid,data,recipe['lowerSlabGuid'],upper)
        return dict(status='NATIVE_STAIR_VOID_CONTACT_READBACK_PASS',contour=contour,connection=contact)
    void=E.execute_model_operation(writer,run_id+'-void','ModifySlabs',params,
        RUN.digest([recipe['graphPlanHash'],params,stair]),[upper],retained,after_hole,
        'Explicit measured native Stair footprint void',saved_sha256,owned_before_check=before_hole)
    if void['status']!='PASS':return dict(status='PARTIAL_OR_UNKNOWN_OUTCOME',creation=created,void=void,automaticRetry=False)
    contact=void['readback']['connection'];matches=contact['sourceGoingAcceptance']=='PASS'
    graph=copy.deepcopy(recipe['graph'])
    upper_op=next(op for op in graph['operations'] if op['id']=='native-slab-level-2')
    upper_op['params']['slabsData'][0]['holes']=params['slabsWithDetails'][0]['holes']
    return dict(status='NATIVE_STAIR_CONNECTION_PASS' if matches else 'NATIVE_STAIR_CONNECTION_PARTIAL',
        geometryStatus='LIVE_PASS',sourceDimensionsStatus=contact['sourceGoingAcceptance'],
        creation=created,void=void,graph=graph,stairGuid=guid,automaticRetry=False,
        engineeringAcceptance='NOT_VERIFIED')
