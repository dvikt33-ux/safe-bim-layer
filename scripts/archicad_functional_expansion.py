"""Reuse the accepted functional context for bounded native expansion.

Original bodies remain pinned; newly split routes are discovered through the
dedicated native query. No generic-enumeration completeness assumption.
"""
import archicad_functional_gaps as F
C=F.C;M=F.M


def preserve_baseline(api,baseline):
    context=baseline['shared']['context']
    if C.RUN.guarded_project(api,context['storyBindings'][0])!=context['binding']:
        raise ValueError('EXPANSION_TARGET_DRIFT')
    inventory=C.A.inventory_guids(api)
    if not set(baseline['geometry59']).issubset(inventory):raise ValueError('EXPANSION_BASELINE_GUID_REMOVED')
    native=C.G.normalize_dump(api('GetModelDumpV1',{}))
    if C.retained_geometry_signatures(native,sorted(baseline['geometry59']))!=baseline['geometry59']:
        raise ValueError('EXPANSION_BASELINE_GEOMETRY_DRIFT')
    return {'status':'BASELINE59_PRESERVED_PASS','inventory':inventory,'native':native}


def discover_network(api,baseline):
    inventory=C.A.inventory_guids(api)
    candidates=sorted(set(inventory)-set(baseline['geometry59'])|set(g.lower() for g in baseline['receipt']['routeGuids']))
    rows=api('GetMEPRoutingElements',{'elements':[{'elementId':{'guid':g}} for g in candidates]}).get('routingElements',[])
    if len(rows)!=len(candidates):raise ValueError('EXPANSION_ROUTING_DISCOVERY_CARDINALITY')
    routes=[g for g,r in zip(candidates,rows) if 'error' not in r and all(k in r for k in ('polyline','segments','nodes'))]
    return M.read_network(api,routes,baseline['receipt']['systemGuid'],scope_to_routes=True)


def expanded_context(api,baseline,new_primary=None):
    verified=preserve_baseline(api,baseline);native=verified['native']
    import copy
    context=copy.deepcopy(baseline['shared']['context']);context['inventory']=verified['inventory']
    geometry={e['guid'].lower():e for e in native['elements']}
    network=discover_network(api,baseline)
    for route in network['routes']:
        guid=route['guid'].lower();sid=next((sid for sid,e in context['elements'].items() if e['guid'].lower()==guid),'mep-'+guid)
        members=network['routePhysicalMembers'][guid]
        if not members:raise ValueError('EXPANSION_ROUTE_BODY_NOT_MAPPED')
        bodies=[geometry[g] for g in members]
        context['elements'][sid]={'guid':guid,'kind':'MEPRouting','floorIndex':C.RUN.requested_details(api,guid)['floorIndex'],
            'bounds':[C.ROOF.bounds(b) for b in bodies], 'physicalElementGuids':members,
            'materialBindings':{},'hostGuid':None,'geometryAuthority':'DEDICATED_ROUTE_PLUS_COLLINEAR_PHYSICAL_PORT_SEGMENTS'}
    route_parts={g for row in network['routePhysicalMembers'].values() for g in row}
    for guid in set(network['physicalGuids'])-route_parts:
        row=C.RUN.requested_details(api,guid);body=geometry.get(guid)
        if body is None:raise ValueError('EXPANSION_FITTING_BODY_MISSING')
        context['elements']['mep-physical-'+guid]={'guid':guid,'kind':'MEPComponent','floorIndex':row['floorIndex'],
            'bounds':[C.ROOF.bounds(body)],'materialBindings':body.get('materialBindings',{}),'hostGuid':None}
    for sid,value in (new_primary or {}).items():
        guid=value['guid'].lower();body=geometry[guid]
        context['elements'][sid]={**value,'bounds':[C.ROOF.bounds(body)],'materialBindings':body.get('materialBindings',{}),
            'hostGuid':value.get('hostGuid')}
    return context,native,network


def native_collision_check(api,context,network):
    reply=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':g}} for g in network['physicalGuids']],
        'elementsGroup2':[{'elementId':{'guid':e['guid']}} for e in context['elements'].values()
                          if not e['kind'].startswith('MEP') and e['kind']!='Opening']})
    if not isinstance(reply.get('collisions'),list) or reply['collisions']:raise ValueError('EXPANSION_NEW_NATIVE_COLLISION')
    return {'status':'NATIVE_MEP_ARCHITECTURAL_COLLISIONS_PASS','reply':reply}


def audit_actual_branch(network,native,architecture):
    """Expose fitting defaults/physical overshoot before declaring acceptance."""
    geometry={e['guid'].lower():e for e in native['elements']};branches=[]
    for guid in network['physicalGuids']:
        ports=[p for p in network['ports'] if p['ownerGuid']==guid]
        if len(ports)<3:continue
        body=geometry.get(guid)
        if not body:raise ValueError('BRANCH_ACTUAL_BODY_MISSING')
        bounds=C.ROOF.bounds(body);candidates=[]
        for sid,e in architecture['elements'].items():
            if e['kind'].startswith('MEP') or e['kind']=='Opening':continue
            if any(all(min(a[1],wall[1])-max(a[0],wall[0])>1e-7 for a,wall in zip(bounds,box)) for box in e['bounds']):candidates.append(sid)
        branches.append({'guid':guid,'portCount':len(ports),'connectedPortCount':sum(p['isPhysicallyConnected'] for p in ports),
            'boundsMeters':bounds,'architecturalAABBCandidates':candidates,'exactCollisionStatus':'NOT_VERIFIED',
            'status':'NATIVE_BRANCH_REQUIRES_FIT_OR_CONNECTION_REPAIR' if candidates or any(not p['isPhysicallyConnected'] for p in ports) else 'NATIVE_BRANCH_PORTS_CONNECTED_REQUIRES_EXACT_COLLISION_READBACK'})
    return {'status':'NATIVE_NETWORK_ACCEPTANCE_NOT_VERIFIED' if not network['physicalConnected'] or not network['logicalConnected'] or any(b['architecturalAABBCandidates'] for b in branches) else 'NATIVE_NETWORK_TOPOLOGY_ONLY_PASS',
        'branches':branches,'physicalConnected':network['physicalConnected'],'logicalConnected':network['logicalConnected'],
        'unmappedRoutes':[guid for guid,parts in network['routePhysicalMembers'].items() if not parts],
        'scope':'Actual captured native data; AABB is a conservative rejection screen, not exact collision proof'}


def guarded_parameter_read(api,guids):
    """Installed AC29/Tapir MEP GDL query crashed; use dedicated MEP reads."""
    for guid in guids:
        row=C.RUN.requested_details(api,guid)
        if row.get('type')=='Unknown':
            raise ValueError('GDL_PARAMETER_READ_REQUIRES_QUALIFIED_KNOWN_NATIVE_TYPE_USE_DEDICATED_MEP_API')
    return api('GetGDLParametersOfElements',{'elements':[{'elementId':{'guid':g}} for g in guids]})
