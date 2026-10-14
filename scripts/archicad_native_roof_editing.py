"""Source-derived native Roof assemblies through the existing BIM Graph/writer."""
import copy,math
import archicad_project_accelerator as A
import archicad_building_shell as B
import archicad_connected_components as C


def qualify_operation(command,parameters,owned,retained):
    slot='roofsData' if command=='CreateRoofs' else 'roofsWithDetails'
    if set(parameters)!={slot} or not 1<=len(parameters[slot])<=(1 if command=='CreateRoofs' else 2):raise ValueError('ROOF_BOUNDED_EXPLICIT_OPERATION_REQUIRED')
    if len(parameters[slot])==2:
        ids=[row.get('elementId',{}).get('guid','').lower() for row in parameters[slot]]
        if len(set(ids))!=2:raise ValueError('ROOF_DUPLICATE_TARGET_IN_BATCH')
        for row in parameters[slot]:qualify_operation(command,{slot:[row]},owned,retained)
        return
    row=parameters[slot][0]
    allowed={'level','floorIndex','thickness','structureType','buildingMaterialId','compositeId','polygonArcs','holes','pivotLine','angle','eavesOverhang','levels'}
    allowed|={'sourceRoofId','polygonCoordinates'} if command=='CreateRoofs' else {'elementId','polygonOutline'}
    if not set(row)<=allowed:raise ValueError('ROOF_FIELDS_NOT_QUALIFIED')
    if command=='CreateRoofs':
        if not {'sourceRoofId','polygonCoordinates','holes','level','floorIndex'}<=row.keys():raise ValueError('ROOF_COMPLETE_SOURCE_REQUIRED')
        if row['sourceRoofId'].get('guid','').lower() not in owned|retained:raise ValueError('ROOF_SOURCE_OUTSIDE_VERIFIED_SCOPE')
    elif row.get('elementId',{}).get('guid','').lower() not in owned:
        raise ValueError('ROOF_EDIT_OUTSIDE_EXPERIMENT')
    for key in ['level','thickness','angle','eavesOverhang']:
        if key in row and (type(row[key]) not in (int,float) or not math.isfinite(row[key])):raise ValueError('ROOF_FINITE_DIMENSIONS_REQUIRED')
    if 'angle' in row and not 0<row['angle']<math.pi/2:raise ValueError('ROOF_SLOPE_OUT_OF_RANGE')
    if 'thickness' in row and row['thickness']<=0:raise ValueError('ROOF_POSITIVE_THICKNESS_REQUIRED')
    if 'floorIndex' in row and type(row['floorIndex']) is not int:raise ValueError('ROOF_EXACT_NATIVE_FLOOR_REQUIRED')
    contour=row.get('polygonCoordinates',row.get('polygonOutline'))
    if contour is not None:
        if 'holes' not in row:raise ValueError('ROOF_CONTOUR_REQUIRES_EXPLICIT_HOLES')
        B.source_floor_polygon(dict(polygonCoordinates=contour,holes=row['holes']))
    if 'pivotLine' in row:
        pivot=row['pivotLine']
        if set(pivot)!={'begCoordinate','endCoordinate'} or pivot['begCoordinate']==pivot['endCoordinate'] or any(set(p)!={'x','y'} or any(type(v) not in (int,float) or not math.isfinite(v) for v in p.values()) for p in pivot.values()):raise ValueError('ROOF_VALID_PIVOT_REQUIRED')
    if 'levels' in row:
        if not row['levels'] or any(set(level)!={'levelAngle','levelHeight'} or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in level.values()) or level['levelAngle']>=math.pi/2 for level in row['levels']):raise ValueError('ROOF_VALID_MULTI_PLANE_LEVELS_REQUIRED')


def rectangle_recipe(source_guid,source_details,x,y,width,depth,scheme,angle_degrees,overhang=0):
    """Explicit rectangular test/source parameters; SDK creates real geometry."""
    d=source_details['details']
    if source_details['type']!='Roof' or d['structureType'] not in {'Basic','Composite'}:raise ValueError('ROOF_NATIVE_SOURCE_STRUCTURE_REQUIRED')
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in [x,y,width,depth,angle_degrees,overhang]) or width<=depth or depth<=0 or not 0<angle_degrees<45 or overhang<0:raise ValueError('ROOF_RECTANGLE_WITH_REAL_RIDGE_REQUIRED')
    if scheme not in {'GABLE','HIP'}:raise ValueError('ROOF_SCHEME_NOT_SUPPORTED')
    if d.get('holes'):raise ValueError('ROOF_ASSEMBLY_HOLE_ROUTING_REQUIRES_EXPLICIT_SOURCE_CLIPPING')
    def ring(x0,y0,x1,y1):return [dict(x=a,y=b) for a,b in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
    common=dict(sourceRoofId=dict(guid=source_guid),level=d['zCoordinate'],floorIndex=source_details['floorIndex'],thickness=d['thickness'],structureType=d['structureType'],holes=[])
    key='buildingMaterialId' if d['structureType']=='Basic' else 'compositeId';common[key]=copy.deepcopy(d[key])
    angle=math.radians(angle_degrees);full=ring(x-overhang,y-overhang,x+width+overhang,y+depth+overhang)
    if scheme=='GABLE':
        mid=y+depth/2
        rows=[dict(common,polygonCoordinates=ring(x-overhang,y-overhang,x+width+overhang,mid),pivotLine=dict(begCoordinate=dict(x=x,y=y),endCoordinate=dict(x=x+width,y=y)),angle=angle),dict(common,polygonCoordinates=ring(x-overhang,mid,x+width+overhang,y+depth+overhang),pivotLine=dict(begCoordinate=dict(x=x+width,y=y+depth),endCoordinate=dict(x=x,y=y+depth)),angle=angle)]
    else:rows=[dict(common,polygonCoordinates=ring(x,y,x+width,y+depth),eavesOverhang=overhang,levels=[dict(levelAngle=angle,levelHeight=10.)])]
    return dict(schema='APA_NATIVE_ROOF_ASSEMBLY_V1',scheme=scheme,sourceGuid=source_guid,sourceDetails=copy.deepcopy(source_details),testParameters=dict(x=x,y=y,width=width,depth=depth,angleDegrees=angle_degrees,overhang=overhang),outerFootprint=full,roofsData=rows,expectedPlanes=2 if scheme=='GABLE' else 4,engineering='NOT_VERIFIED')


def compile_graph(recipe,schema_path):
    graph=dict(operations=[dict(id='roof-'+str(i),command='CreateRoofs',params=dict(roofsData=[row]),after=[]) for i,row in enumerate(recipe['roofsData'])])
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(schema_path),graph,runtime_version=A.RUN.EXPECTED_TAPIR)
    if checked['status']!='PLAN_VALIDATED_OFFLINE':raise ValueError('ROOF_GRAPH_SCHEMA_INVALID')
    return dict(graph=graph,planHash=checked['sourcePlanHash'])


def edit_assembly(writer,scene_id,old_recipe,guids,protected_signatures,authorization_ref,saved_sha256,**changes):
    """One existing writer call; no regeneration and no duplicate-on-repeat.

    The current assembly must match either the old ticket or the exact new
    one. Arbitrary drift is a reconciliation gate, not automatic repair.
    """
    if set(changes)-{'angle_degrees','width','depth','x','y','overhang'}:raise ValueError('ROOF_EDIT_FIELDS_NOT_SUPPORTED')
    # Repeated requests still require the same authorized project and baseline.
    # A matching shape in a different project is never an idempotence receipt.
    from pathlib import Path
    import hashlib
    binding=writer.guarded_binding()
    if hashlib.sha256(Path(binding['path']).read_bytes()).hexdigest()!=saved_sha256:
        raise ValueError('ROOF_SAVED_FILE_HASH_CHANGED')
    current=A.inventory_guids(writer.api)
    if set(current)!={g.lower() for g in protected_signatures}|{g.lower() for g in guids}:
        raise ValueError('ROOF_EXPERIMENT_INVENTORY_CHANGED')
    native=C.G.normalize_dump(writer.api('GetModelDumpV1',{}))
    if C.retained_geometry_signatures(native,list(protected_signatures))!=protected_signatures:
        raise ValueError('ROOF_RETAINED_GEOMETRY_CHANGED')
    data=old_recipe['testParameters'];args=dict(x=data['x'],y=data['y'],width=data['width'],depth=data['depth'],angle_degrees=data['angleDegrees'],overhang=data['overhang']);args.update(changes)
    updated=rectangle_recipe(old_recipe['sourceGuid'],old_recipe['sourceDetails'],scheme=old_recipe['scheme'],**args)
    try:
        actual=verify_assembly(writer.api,guids,updated)
    except ValueError:
        verify_assembly(writer.api,guids,old_recipe)
    else:
        return dict(status='ALREADY_APPLIED_READBACK_PASS',recipe=updated,readback=actual,nativeWrites=0,automaticRetry=False)
    rows=[]
    for guid,data in zip(guids,updated['roofsData']):
        row=dict(elementId=dict(guid=guid))
        if set(changes)=={'angle_degrees'}:
            row.update(angle=data['angle']) if updated['scheme']=='GABLE' else row.update(levels=copy.deepcopy(data['levels']))
        else:
            if 'angle_degrees' in changes:raise ValueError('ROOF_APPLY_SLOPE_AND_CONTOUR_AS_SEPARATE_JOURNALED_STEPS')
            row.update(polygonOutline=data['polygonCoordinates'],holes=copy.deepcopy(data['holes']))
            if updated['scheme']=='GABLE':row['pivotLine']=copy.deepcopy(data['pivotLine'])
            else:row['eavesOverhang']=data['eavesOverhang']
        rows.append(row)
    if len(rows)!=len(guids):raise ValueError('ROOF_GUID_TO_PLANE_BINDING_INCOMPLETE')
    from archicad_authored_extension import execute_model_operation
    result=execute_model_operation(writer,scene_id,'ModifyRoofs',dict(roofsWithDetails=rows),A.RUN.digest(updated),guids,protected_signatures,
        lambda *_:verify_assembly(writer.api,guids,updated),authorization_ref,saved_sha256)
    return dict(result,recipe=updated,parameters=dict(roofsWithDetails=rows),nativeWrites=1,automaticRetry=False)


def verify_assembly(api,guids,recipe):
    """Count/measure actual upper planes and their 3D boundary continuity."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    model=C.G.normalize_dump(api('GetModelDumpV1',{}));rows={e['guid'].lower():e for e in model['elements']}
    groups={};expected=math.radians(recipe['testParameters']['angleDegrees']);details=[]
    for guid in guids:
        info=A.RUN.requested_details(api,guid);d=info['details'];source=recipe['sourceDetails']['details']
        if info['type']!='Roof' or info['floorIndex']!=recipe['sourceDetails']['floorIndex'] or d['structureType']!=source['structureType'] or not A.RUN.close(d['thickness'],source['thickness']):raise ValueError('ROOF_NATIVE_TYPE_STORY_STRUCTURE_CHANGED')
        key='buildingMaterialId' if source['structureType']=='Basic' else 'compositeId'
        if d[key]!=source[key]:raise ValueError('ROOF_SOURCE_MATERIAL_CHANGED')
        if not A.RUN.close(d['zCoordinate'],source['zCoordinate']):raise ValueError('ROOF_EAVE_PIVOT_ELEVATION_CHANGED')
        if d['roofClass']!=('SinglePlane' if recipe['scheme']=='GABLE' else 'MultiPlane'):raise ValueError('ROOF_NATIVE_CLASS_MISMATCH')
        details.append(info)
        for face in C.G.planar_faces(rows[guid.lower()]):
            n=face['normal'];dist=face['distance']
            if abs(n[2])<1e-8:continue
            if n[2]<0:n=[-v for v in n];dist=-dist
            angle=math.atan2(math.hypot(n[0],n[1]),n[2])
            if abs(angle-expected)>1e-5:continue
            if face['drop']!=2:raise ValueError('ROOF_TOP_PROJECTION_NOT_AVAILABLE')
            direction=tuple(round(v/n[2],6) for v in n[:2]);intercept=dist/n[2]
            group=groups.get(direction)
            if group is None or intercept>group['intercept']+1e-5:groups[direction]=dict(normal=n,intercept=intercept,polygons=[face['polygon']],guid=guid.lower())
            elif abs(intercept-group['intercept'])<=1e-5:group['polygons'].append(face['polygon'])
    if len(groups)!=recipe['expectedPlanes']:raise ValueError('ROOF_ACTUAL_SLOPED_PLANE_COUNT_MISMATCH')
    planes=[]
    for group in groups.values():group['polygon']=unary_union(group.pop('polygons'));planes.append(group)
    target=Polygon([(p['x'],p['y']) for p in recipe['outerFootprint']]);union=unary_union([p['polygon'] for p in planes]);gap=union.symmetric_difference(target).area
    if gap>1e-5:raise ValueError('ROOF_ACTUAL_PLAN_FOOTPRINT_GAP_OR_OVERHANG_MISMATCH')
    joins=[]
    def z(p,x,y):return p['intercept']-(p['normal'][0]*x+p['normal'][1]*y)/p['normal'][2]
    for i,a in enumerate(planes):
        for b in planes[i+1:]:
            intersection=a['polygon'].boundary.intersection(b['polygon'].boundary)
            if intersection.length<1e-5:continue
            pieces=list(intersection.geoms) if hasattr(intersection,'geoms') else [intersection];segments=[]
            for part in pieces:
                if part.geom_type!='LineString' or part.length<1e-5:continue
                points=[]
                for x,y in part.coords:
                    if abs(z(a,x,y)-z(b,x,y))>1e-5:raise ValueError('ROOF_JOIN_3D_ELEVATION_GAP')
                    points.append([x,y,z(a,x,y)])
                segments.append(points)
            if segments:joins.append(dict(lengthXY=intersection.length,segmentsXYZ=segments))
    if len(joins)!=(1 if recipe['scheme']=='GABLE' else 5):raise ValueError('ROOF_ACTUAL_RIDGE_HIP_TOPOLOGY_MISMATCH')
    contacts=C.G.shared_surfaces(rows,{g.lower():g.lower() for g in guids}) if len(guids)>1 else []
    if recipe['scheme']=='GABLE' and not contacts:raise ValueError('ROOF_SOLID_SEAM_CONTACT_NOT_VERIFIED')
    return dict(status='NATIVE_ROOF_ASSEMBLY_GEOMETRY_PASS',scheme=recipe['scheme'],nativeElementCount=len(guids),actualSlopePlaneCount=len(planes),pitchDegrees=recipe['testParameters']['angleDegrees'],footprintGapAreaSquareMeters=gap,joins=joins,solidSeamContacts=contacts,nativeDetails=details,engineering='NOT_VERIFIED')
