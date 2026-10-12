"""Thin native Opening/SEO/roof-trim adapters over retained writer contracts."""
import math
import copy
import archicad_connected_components as C


def element_body(api,guid):
    dump=C.G.normalize_dump(api('GetModelDumpV1',{}))
    rows=[e for e in dump['elements'] if e['guid'].lower()==guid.lower()]
    if len(rows)!=1 or not rows[0].get('bodies'):raise ValueError('NATIVE_BODY_NOT_READABLE')
    return {'guid':guid.lower(),'native':rows[0],'bounds':C.ROOF.bounds(rows[0]),
        'geometryHash':C.RUN.digest(C.ROOF.geometry_signature(rows[0])),'units':dump['units'],
        'faceSurfaceGuids':C.ROOF.face_material_guids(rows[0],dump)}


def opening_hole_bounds(host,expected):
    """Bounded rectangular horizontal-wall specimen; reject ambiguous holes.

    Geometry comes from native inner face contours, never an invented body for
    provider's unsupported generic Opening details.
    """
    candidates=[]
    for body in host['native']['bodies']:
        for face in body['faces']:
            for hole in face.get('holes',[]):
                points=[body['vertices'][i] for i in hole]
                bounds=[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
                width=max(bounds[0][1]-bounds[0][0],bounds[1][1]-bounds[1][0])
                height=bounds[2][1]-bounds[2][0]
                if len(points)==4 and C.RUN.close(width,expected['width']) and C.RUN.close(height,expected['height']):
                    candidates.append(bounds)
    if len(candidates)!=2:raise ValueError('OPENING_HOLE_GEOMETRY_AMBIGUOUS')
    bounds=[[min(b[i][0] for b in candidates),max(b[i][1] for b in candidates)] for i in range(3)]
    point=expected['basePoint']
    if not C.RUN.close((bounds[0][0]+bounds[0][1])/2,point['x']) or not C.RUN.close((bounds[1][0]+bounds[1][1])/2,point['y']) or not C.RUN.close(bounds[2][0],point['z']):
        raise ValueError('OPENING_HOLE_POSITION_MISMATCH')
    return bounds


def opening_readback(api,guid,host_guid,before_host,expected=None):
    connected=api('GetConnectedElements',{'elements':[{'elementId':{'guid':host_guid}}],'connectedElementType':'Opening'})
    host=element_body(api,host_guid);row=C.RUN.requested_details(api,guid)
    # Keep the exact native hosting response for strict identity recognition.
    def guids(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k=='guid' and isinstance(x,str):yield x.lower()
                else:yield from guids(x)
        elif isinstance(v,list):
            for x in v:yield from guids(x)
    if guid.lower() not in set(guids(connected)):raise ValueError('OPENING_NATIVE_HOST_LINK_NOT_VERIFIED')
    if host['geometryHash']==before_host['geometryHash']:raise ValueError('OPENING_HOST_NATIVE_BODY_NOT_CHANGED')
    result={'status':'NATIVE_OPENING_HOST_AND_BODY_CHANGE_PASS','guid':guid,'hostGuid':host_guid,
        'homeStory':row.get('floorIndex'),'genericType':row.get('type'),'genericDetails':row.get('details'),
        'connectedElements':connected,'beforeHostBodyHash':before_host['geometryHash'],'afterHost':host,
        'engineeringAcceptance':'NOT_VERIFIED'}
    if expected is not None:result.update(nativeHoleBoundsMeters=opening_hole_bounds(host,expected),geometryAuthority='TWO_ACTUAL_NATIVE_HOST_INNER_FACE_CONTOURS')
    return result


def seo_readback(api,target,operator,before,expected_bounds):
    if len(expected_bounds)!=3 or any(len(axis)!=2 or axis[0]>=axis[1] for axis in expected_bounds):
        raise ValueError('SEO_EXPECTS_THREE_AXIS_INTERVALS')
    links=api('GetSolidElementLinks',{'elements':[{'elementId':{'guid':target}}]}).get('solidLinks',[])
    if len(links)!=1:raise ValueError('SEO_LINK_READBACK_CARDINALITY')
    rows=links[0]['solidLinksWithTheGivenTarget']
    if not any(r['operatorId']['guid'].lower()==operator.lower() and r['operation']=='Subtraction' for r in rows):raise ValueError('SEO_OPERATOR_RELATION_NOT_VERIFIED')
    after=element_body(api,target)
    if after['geometryHash']==before['geometryHash']:raise ValueError('SEO_NATIVE_BODY_NOT_CHANGED')
    if any(not C.RUN.close(a,b) for x,y in zip(after['bounds'],expected_bounds) for a,b in zip(x,y)):raise ValueError('SEO_NATIVE_BOUNDS_MISMATCH')
    return {'status':'SEO_SUBTRACTION_NATIVE_LINK_AND_BREP_PASS','targetGuid':target,'operatorGuid':operator,
        'linkReadback':links,'beforeBodyHash':before['geometryHash'],'after':after,'engineeringAcceptance':'NOT_VERIFIED'}


def provider_scope(catalog):
    return {k:('SCHEMA_AVAILABLE_REQUIRES_NATIVE_READBACK' if k in catalog['commands'] else 'UNSUPPORTED_INSTALLED_PROVIDER')
        for k in ['CreateShells','ModifyShells','CreateOpenings','ModifyOpenings','CreateSolidElementLinks','RemoveSolidElementLinks']}


def roof_trim_readback(api,wall_guid,roof_guid,before_wall,expected_area):
    """Native relation plus actual shared surfaces, independently read.

    Caller must distinguish underside bearing from a perimeter abutment.
    A positive area alone never proves the intended bearing configuration.
    """
    rows=api('GetElementTrims',{'elements':[{'elementId':{'guid':wall_guid}},{'elementId':{'guid':roof_guid}}]}).get('elementTrims')
    if (not isinstance(rows,list) or len(rows)!=2 or 'error' in rows[1] or
            not any(r.get('elementId',{}).get('guid','').lower()==wall_guid.lower() for r in rows[1].get('trims',[]))):
        raise ValueError('ROOF_TRIM_NATIVE_OPERATOR_RELATION_NOT_PROVEN')
    reciprocal=any(r.get('elementId',{}).get('guid','').lower()==roof_guid.lower() and r.get('trimType')=='KeepInside' for r in rows[0].get('trimmedBy',[]))
    # Installed provider discards the valid target-side trimming list when its
    # second SDK call (GetTrimmedElements on Wall) is inapplicable. Keep that
    # metadata gap explicit; actual operator relation and BREP remain factual.
    known_target_gap=rows[0].get('error',{}).get('message')=='Failed to read the elements this element trims.'
    if not reciprocal and not known_target_gap:raise ValueError('ROOF_TRIM_TARGET_RELATION_UNEXPLAINED')
    wall=element_body(api,wall_guid);roof=element_body(api,roof_guid)
    if wall['native']['type']!='Wall' or roof['native']['type']!='Roof':raise ValueError('ROOF_TRIM_REQUIRES_NATIVE_WALL_ROOF')
    if wall['geometryHash']==before_wall['geometryHash']:raise ValueError('ROOF_TRIM_WALL_BODY_NOT_CHANGED')
    bodies={wall_guid.lower():wall['native'],roof_guid.lower():roof['native']}
    contacts=C.G.shared_surfaces(bodies,{g:g for g in bodies});area=sum(r['sharedAreaSquareMeters'] for r in contacts)
    if not C.RUN.close(area,expected_area,1e-6):raise ValueError('ROOF_TRIM_ACTUAL_CONTACT_SURFACE_MISMATCH:'+str(area))
    collision=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':wall_guid}}],
        'elementsGroup2':[{'elementId':{'guid':roof_guid}}]})
    if collision.get('collisions')!=[]:raise ValueError('ROOF_TRIM_NATIVE_VOLUME_INTERSECTION')
    return {'status':'NATIVE_WALL_ROOF_TRIM_LINK_AND_CONTACT_PASS','nativeTools':['Wall','Roof'],
        'wallGuid':wall_guid,'roofGuid':roof_guid,'nativeTrimRelations':rows,'sharedAreaSquareMeters':area,
        'reciprocalTrimMetadata':'PASS' if reciprocal else 'NOT_VERIFIED_INSTALLED_PROVIDER_TARGET_ROW_ERROR',
        'beforeWallBodyHash':before_wall['geometryHash'],'wall':wall,'roof':roof,'volumeCollisions':collision,
        'scope':'Bounded geometric interface in separate native specimen; original building gaps remain unchanged',
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED','fixingsAndBearingDesign':'NOT_VERIFIED'}


def prepare_roof_trim_specimen(api,source,context,native,wall_guid,roof_guid):
    """One isolated Wall/Roof interface using measured existing dimensions.

    This exercises supported trimming without editing the accepted building.
    No new load path, fastening scheme or manufacturer approval is supplied.
    """
    bodies={e['guid'].lower():e for e in native['elements']}
    wall=bodies[wall_guid.lower()];roof=bodies[roof_guid.lower()]
    wr=C.RUN.requested_details(api,wall_guid);rr=C.RUN.requested_details(api,roof_guid)
    w=wr['details'];r=rr['details'];wb=C.ROOF.bounds(wall);rb=C.ROOF.bounds(roof)
    if (wr['type']!='Wall' or rr['type']!='Roof' or wr['floorIndex']!=rr['floorIndex'] or
            w['structureType']!='Basic' or r['structureType']!='Basic' or r['roofClass']!='SinglePlane' or
            w['begCoordinate']['x']!=w['endCoordinate']['x'] or w['arcAngle']!=0 or r['holes']):
        raise ValueError('ROOF_TRIM_SPECIMEN_SOURCE_GEOMETRY_UNSUPPORTED')
    width=r['polygonOutline'][1]['x']-r['polygonOutline'][0]['x']
    if width<=0:raise ValueError('ROOF_TRIM_SPECIMEN_ROOF_AXIS_UNSUPPORTED')
    max_x=max(C.ROOF.bounds(e)[0][1] for e in native['elements'] if e.get('bodies'))
    dx=max_x+width-rb[0][0]
    def point(p):return {'x':p['x']+dx,'y':p['y']}
    roof_data={'floorIndex':rr['floorIndex'],'level':r['zCoordinate'],'thickness':r['thickness'],
        'structureType':'Basic','buildingMaterialId':r['buildingMaterialId'],'angle':r['angle'],
        'polygonCoordinates':[point(p) for p in r['polygonOutline']],
        'pivotLine':{'begCoordinate':point(r['pivotLine']['begin']),'endCoordinate':point(r['pivotLine']['end'])}}
    x=(rb[0][0]+rb[0][1])/2+dx
    wall_data={'floorIndex':wr['floorIndex'],'zCoordinate':w['bottomOffset'],
        'begCoordinate':{'x':x,'y':wb[1][0]},'endCoordinate':{'x':x,'y':wb[1][1]},
        'height':rb[2][1]-wb[2][0],'thickness':w['begThickness'],'offset':0.,
        'referenceLineLocation':'Center','structureType':'Basic','buildingMaterialId':w['buildingMaterialId']}
    binding={'sourceWallGuid':wall_guid,'sourceRoofGuid':roof_guid,
        'sourceBodies':[{'guid':e['guid'],'geometryHash':C.RUN.digest(C.ROOF.geometry_signature(e)),
            'materialBindings':e['materialBindings'],'homeStory':e['homeStory']} for e in [wall,roof]],
        'placementAuthority':'Separate native specimen beyond actual maximum model X by one measured roof span; wall at copied roof center',
        'dimensionAuthority':'Actual wall thickness and resultant span, roof pitch/thickness/polygon, wall base and roof highest vertex',
        'sourceInterface':'Published49-pair west-upper-wall/roof gap; original model is preserved',
        'expectedAreaSquareMeters':(wb[1][1]-wb[1][0])*wall_data['thickness']/math.cos(r['angle']),
        'fullConstructionSolution':'NOT_VERIFIED','engineeringAcceptance':'ENGINEERING_NOT_VERIFIED'}
    plan=C.bind_plan(source,[{'id':'native-trim-specimen-roof','command':'CreateRoofs','params':{'roofsData':[roof_data]}},
        {'id':'native-trim-specimen-wall','command':'CreateWalls','params':{'wallsData':[wall_data]},'after':['native-trim-specimen-roof']}],
        ['roof','wall'],{'sourceRoofTrimBinding':binding})
    return {'status':'OFFLINE_NATIVE_ROOF_TRIM_SPECIMEN_PREPARED','binding':binding,'plan':plan,'nativeWrites':0}


def verify_roof_trim_source(api,binding):
    for expected in binding['sourceBodies']:
        e=element_body(api,expected['guid'])['native']
        if (C.RUN.digest(C.ROOF.geometry_signature(e))!=expected['geometryHash'] or
                e['materialBindings']!=expected['materialBindings'] or e['homeStory']!=expected['homeStory']):
            raise ValueError('ROOF_TRIM_SOURCE_INVALIDATED')
    return {'status':'ROOF_TRIM_SOURCE_BINDING_PASS'}


def roof_underside_plane(roof):
    """Lower of two actual parallel principal roof faces, independent of Trim."""
    if roof.get('type')!='Roof':raise ValueError('UNDERSIDE_REQUIRES_NATIVE_ROOF')
    faces=list(C.G.planar_faces(roof))
    if not faces:raise ValueError('ROOF_PRINCIPAL_FACES_MISSING')
    principal=max(faces,key=lambda f:f['area'])
    normal=principal['normal']
    if abs(normal[2])<.5:raise ValueError('ROOF_UNDERSIDE_SLOPE_UNSUPPORTED')
    sign=1 if normal[2]>0 else -1
    normal=[v*sign for v in normal]
    distances={round(f['distance']*sign,6) for f in faces
        if all(C.RUN.close(a,b,1e-6) for a,b in zip(f['normal'],principal['normal']))}
    if len(distances)!=2:raise ValueError('ROOF_PARALLEL_PRINCIPAL_PLANES_AMBIGUOUS')
    return {'normal':normal,'distance':min(distances),'authority':'ACTUAL_NATIVE_LOWER_PRINCIPAL_FACE_PLANE'}


def underside_contact_geometry(wall,roof,expected_area,expected_plane=None):
    if wall.get('type')!='Wall' or wall.get('homeStory')!=roof.get('homeStory'):
        raise ValueError('UNDERSIDE_REQUIRES_NATIVE_WALL_ROOF_SAME_STORY')
    plane=roof_underside_plane(roof)
    if expected_plane is not None and (not all(C.RUN.close(a,b,1e-6) for a,b in zip(plane['normal'],expected_plane['normal'])) or
            not C.RUN.close(plane['distance'],expected_plane['distance'],1e-6)):
        raise ValueError('ROOF_UNDERSIDE_PINNED_PLANE_CHANGED')
    n,d=plane['normal'],plane['distance']
    if any(sum(n[k]*v[k] for k in range(3))>d+1e-6 for body in wall['bodies'] for v in body['vertices']):
        raise ValueError('WALL_EXTENDS_ABOVE_ROOF_UNDERSIDE')
    selected={}
    indices={}
    for key,native in [('wall',wall),('roof',roof)]:
        selected[key]=copy.deepcopy(native);accepted=[]
        for f in C.G.planar_faces(native):
            if all(abs(sum(n[k]*v[k] for k in range(3))-d)<=1e-6 for v in f['points']):
                accepted.append((f['bodyIndex'],f['faceIndex']))
        for bi,body in enumerate(selected[key]['bodies']):
            body['faces']=[face for fi,face in enumerate(body['faces']) if (bi,fi) in accepted]
        indices[key]=accepted
    contact=C.G.shared_surfaces(selected,{g:g for g in selected})
    area=sum(c['sharedAreaSquareMeters'] for c in contact)
    if type(expected_area) not in (int,float) or expected_area<=0 or not C.RUN.close(area,expected_area,1e-6):
        raise ValueError('ROOF_ACTUAL_UNDERSIDE_CONTACT_AREA_MISMATCH:'+str(area))
    return {'status':'ACTUAL_NATIVE_ROOF_UNDERSIDE_FACE_CONTACT_PASS','plane':plane,
        'sharedAreaSquareMeters':area,'actualFaceIndices':indices,
        'wallEntirelyBelowUnderside':True,'holesPreservedInContactCheck':True}


def wall_roof_underside_gap(wall,roof):
    """Measure a flat native wall cap against the actual sloped roof underside."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    if wall.get('type')!='Wall' or wall.get('homeStory')!=roof.get('homeStory'):
        raise ValueError('GAP_REQUIRES_NATIVE_WALL_ROOF_SAME_STORY')
    plane=roof_underside_plane(roof);n,d=plane['normal'],plane['distance']
    caps=[f for f in C.G.planar_faces(wall) if abs(abs(f['normal'][2])-1)<1e-6]
    if not caps:raise ValueError('GAP_FLAT_WALL_CAP_UNAVAILABLE')
    top=max(f['points'][0][2] for f in caps)
    def polygons(native,predicate):
        result=[]
        for f in C.G.planar_faces(native):
            if not predicate(f):continue
            body=native['bodies'][f['bodyIndex']];face=body['faces'][f['faceIndex']]
            rings=[[[body['vertices'][i][k] for k in (0,1)] for i in ring] for ring in face['contours']]
            result.append(Polygon(rings[0],rings[1:]))
        return unary_union(result)
    cap=polygons(wall,lambda f:all(abs(v[2]-top)<1e-6 for v in f['points']))
    underside=polygons(roof,lambda f:all(abs(sum(n[k]*v[k] for k in range(3))-d)<1e-6 for v in f['points']))
    overlap=cap.intersection(underside)
    if overlap.area<=1e-8:raise ValueError('GAP_NO_ACTUAL_PROJECTED_FACE_OVERLAP')
    parts=[overlap] if overlap.geom_type=='Polygon' else [g for g in overlap.geoms if g.geom_type=='Polygon']
    gaps=[(d-n[0]*x-n[1]*y)/n[2]-top for part in parts for x,y in part.exterior.coords]
    return {'status':'ACTUAL_NATIVE_UNDERSIDE_GAP_MEASURED','minimumVerticalGapMeters':min(gaps),
        'maximumVerticalGapMeters':max(gaps),'projectedOverlapAreaSquareMeters':overlap.area,
        'wallTopAbsoluteZ':top,'roofUndersidePlane':plane,'authority':'ACTUAL_NATIVE_FACE_OVERLAP; not bounding-box separation',
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED'}


def prepare_roof_underside_specimen(api,source,context,native,wall_guid,roof_guid):
    """Reuse the native specimen recipe; one SEO replaces the unsuitable Trim."""
    part=prepare_roof_trim_specimen(api,source,context,native,wall_guid,roof_guid)
    operations=copy.deepcopy(part['plan']['graph']['operations'])
    ids={'native-trim-specimen-roof':'native-underside-roof','native-trim-specimen-wall':'native-underside-wall'}
    for op in operations:
        op['id']=ids[op['id']]
        if 'after' in op:op['after']=[ids[x] for x in op['after']]
    roof=next(e for e in native['elements'] if e['guid'].lower()==roof_guid.lower())
    plane=roof_underside_plane(roof)
    row=C.RUN.requested_details(api,roof_guid)['details']
    dx=operations[0]['params']['roofsData'][0]['pivotLine']['begCoordinate']['x']-row['pivotLine']['begin']['x']
    plane['distance']+=plane['normal'][0]*dx
    binding=copy.deepcopy(part['binding'])
    binding.update(expectedUndersidePlane=plane,operation='SubtractionUpwards',
        linkFlags={'inheritOperatorAttributes':False,'skipPolygonHoles':True},
        nativeOperationReason='Ignore operator polygon holes during upward subtraction; preserve actual roof thickness/material and accepted specimen',
        noTrimRequired=True)
    plan=C.bind_plan(source,operations,['roof','wall'],{'sourceRoofTrimBinding':binding})
    return {'status':'OFFLINE_NATIVE_UNDERSIDE_SPECIMEN_PREPARED','binding':binding,'plan':plan,'nativeWrites':0}


def roof_bearing_seo_readback(api,wall_guid,roof_guid,before_wall,expected_area,expected_plane=None):
    links=api('GetSolidElementLinks',{'elements':[{'elementId':{'guid':wall_guid}}]}).get('solidLinks',[])
    matches=[r for entry in links for r in entry.get('solidLinksWithTheGivenTarget',[])
        if r.get('operatorId',{}).get('guid','').lower()==roof_guid.lower() and r.get('operation')=='SubtractionUpwards']
    if len(links)!=1 or len(matches)!=1:raise ValueError('ROOF_BEARING_SEO_LINK_NOT_PROVEN')
    flags=matches[0].get('linkFlags')
    if not isinstance(flags,dict) or set(flags)!={'inheritOperatorAttributes','skipPolygonHoles'} or any(type(v) is not bool for v in flags.values()):
        raise ValueError('ROOF_BEARING_SEO_LINK_NOT_PROVEN')
    wall=element_body(api,wall_guid);roof=element_body(api,roof_guid)
    if wall['geometryHash']==before_wall['geometryHash']:raise ValueError('ROOF_BEARING_NATIVE_WALL_BODY_NOT_CHANGED')
    contact=underside_contact_geometry(wall['native'],roof['native'],expected_area,expected_plane)
    collision=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':wall_guid}}],
        'elementsGroup2':[{'elementId':{'guid':roof_guid}}]})
    if collision.get('collisions')!=[]:raise ValueError('ROOF_BEARING_NATIVE_VOLUME_INTERSECTION')
    return {'status':'NATIVE_WALL_ROOF_UNDERSIDE_SEO_CONTACT_PASS','solidLinks':links,
        'undersideContact':contact,'wall':wall,'roof':roof,'volumeCollisions':collision,
        'requestedLinkFlags':{'inheritOperatorAttributes':False,'skipPolygonHoles':True},
        'nativeFlagReadback':'PASS' if flags=={'inheritOperatorAttributes':False,'skipPolygonHoles':True} else 'NOT_VERIFIED_REQUEST_READBACK_DIFFERENCE',
        'geometryAuthority':'ACTUAL_NATIVE_LOWER_FACE_CONTACT_AND_CHANGED_WALL_BODY; flag equality is not inferred',
        'operation':'SubtractionUpwards','scope':'Separate native Wall/Roof actual underside contact; original building gaps unchanged',
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED'}
