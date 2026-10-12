"""Thin native Opening/SEO observations over retained dump and writer contracts."""
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
