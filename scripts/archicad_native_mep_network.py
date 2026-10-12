"""Native routing/physical-port graph; generic enumeration is advisory only."""
import math
import networkx as nx
import archicad_connected_components as C


def read_network(api,route_guids,system_guid,domain='Ventilation'):
    if not route_guids or len(set(g.lower() for g in route_guids))!=len(route_guids):raise ValueError('MEP_ROUTE_IDENTITIES_NOT_UNIQUE')
    routes=api('GetMEPRoutingElements',{'elements':[{'elementId':{'guid':g}} for g in route_guids]}).get('routingElements',[])
    if len(routes)!=len(route_guids) or any('error'in r for r in routes):raise ValueError('MEP_DEDICATED_ROUTE_READBACK_MISSING')
    graph=nx.Graph();owned=set();logical=[];segment_count=0
    for guid,route in zip(route_guids,routes):
        if route['domain']!=domain or C.attribute_guid(route['mepSystemId'])!=system_guid.lower():raise ValueError('MEP_NETWORK_SYSTEM_MISMATCH')
        nodes=route['nodes'];segments=route['segments'];line=route['polyline']
        segment_count+=len(segments)
        if len(nodes)!=len(line) or len(segments)!=len(nodes)-1:raise ValueError('MEP_NETWORK_NODE_SEGMENT_CARDINALITY')
        for node,p in zip(nodes,line):
            if not C.points_equal(p,node['position']):raise ValueError('MEP_NETWORK_NODE_POSITION_MISMATCH')
            gid=node['elementId']['guid'].lower();owned.add(gid);graph.add_node(gid,position=p)
        for i,segment in enumerate(segments):
            gid=segment['elementId']['guid'].lower();owned.add(gid)
            if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (segment['crossSectionWidth'],segment['crossSectionHeight'])):raise ValueError('MEP_NETWORK_SECTION_INVALID')
            graph.add_edge(nodes[i]['elementId']['guid'].lower(),nodes[i+1]['elementId']['guid'].lower(),guid=gid,
                width=segment['crossSectionWidth'],height=segment['crossSectionHeight'],shape=segment['crossSectionShape'])
        logical.append({'guid':guid,'details':route})
    systems=[s for s in api('GetMEPDistributionSystems',{}).get('distributionSystems',[]) if s['domain']==domain and C.attribute_guid(s['mepSystemId'])==system_guid.lower()]
    if not systems:raise ValueError('MEP_NETWORK_DISTRIBUTION_MISSING')
    # Native API reports a row per connected component, sharing one attribute.
    members=[r['elementId']['guid'].lower() for system in systems for r in system['elements']]
    if len(members)!=len(set(members)):raise ValueError('MEP_DISTRIBUTION_MEMBER_DUPLICATED')
    # Dedicated ports identify physical members even when GetMEPElements omits
    # them. No membership is inferred from an inventory delta alone.
    rows=api('GetMEPPorts',{'elements':[{'elementId':{'guid':g}} for g in members]}).get('elementPorts',[])
    if len(rows)!=len(members):raise ValueError('MEP_NETWORK_PHYSICAL_PORT_COVERAGE')
    physical=[];port_graph=nx.Graph();ports=[]
    for guid,row in zip(members,rows):
        if 'error'in row:raise ValueError('MEP_NETWORK_MEMBER_PORT_READ_ERROR')
        pp=row.get('ports',[])
        if not pp:continue
        physical.append(guid);port_graph.add_node(guid)
        for p in pp:
            if p['domain']!=domain or C.attribute_guid(p['mepSystemId'])!=system_guid.lower():raise ValueError('MEP_NETWORK_PORT_SYSTEM_MISMATCH')
            if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (p['width'],p['height'])):raise ValueError('MEP_NETWORK_PORT_SECTION_INVALID')
            ports.append({'ownerGuid':guid,**p})
    port_index={p['portId']:p for p in ports}
    if len(port_index)!=len(ports):raise ValueError('MEP_DUPLICATE_NATIVE_PORT_ID')
    for p in ports:
        if not p['isPhysicallyConnected']:continue
        peer=port_index.get(p.get('connectedPortId'))
        if (peer is None or not peer.get('isPhysicallyConnected') or peer.get('connectedPortId')!=p['portId'] or
            p.get('connectedElementId',{}).get('guid','').lower()!=peer['ownerGuid'] or
            peer.get('connectedElementId',{}).get('guid','').lower()!=p['ownerGuid']):
            raise ValueError('MEP_CONNECTED_PORT_NOT_RECIPROCAL_OR_OUTSIDE_SCOPE')
        if not C.points_equal(p['position'],peer['position']):raise ValueError('MEP_CONNECTED_PORT_POSITION_MISMATCH')
        if p['ownerGuid']==peer['ownerGuid']:raise ValueError('MEP_CONNECTED_PORT_SELF_OWNER')
        if p['shape']!=peer['shape'] or any(not C.RUN.close(p[k],peer[k]) for k in ('width','height')):
            raise ValueError('MEP_JOIN_PORT_SECTION_MISMATCH')
        if not C.RUN.close(sum(p['direction'][k]*peer['direction'][k] for k in ('x','y','z')),-1.):
            raise ValueError('MEP_CONNECTED_PORT_DIRECTION_MISMATCH')
        port_graph.add_edge(p['ownerGuid'],peer['ownerGuid'],position=p['position'])
    for i,p in enumerate(ports):
        for q in ports[i+1:]:
            if p['ownerGuid']==q['ownerGuid'] or not C.points_equal(p['position'],q['position']):continue
            if p['isPhysicallyConnected'] and q['isPhysicallyConnected']:
                if not C.RUN.close(p['width'],q['width']) or not C.RUN.close(p['height'],q['height']) or p['shape']!=q['shape']:
                    raise ValueError('MEP_JOIN_PORT_SECTION_MISMATCH')
                port_graph.add_edge(p['ownerGuid'],q['ownerGuid'],position=p['position'])
                if p.get('connectedPortId')!=q['portId']:raise ValueError('MEP_COINCIDENT_PORT_IS_NOT_LINKED_PEER')
                if not C.RUN.close(sum(p['direction'][k]*q['direction'][k] for k in ('x','y','z')),-1.):
                    raise ValueError('MEP_CONNECTED_PORT_DIRECTION_MISMATCH')
                junction=[gid for gid,v in graph.nodes(data=True) if C.points_equal(p['position'],v['position'])]
                if len(junction)==2:graph.add_edge(*junction,connection='RECIPROCAL_NATIVE_PHYSICAL_PORTS')
    # Split routes meet at the branch centre while the fitting's physical ports
    # lie away from that centre. Bind routes to actual collinear physical ducts,
    # then use reciprocal native connectivity through fittings as the authority.
    ownership=physical_route_members(logical,ports)
    if physical and nx.is_connected(port_graph):
        if all(ownership[g['guid'].lower()] for g in logical):
            for i,left in enumerate(logical):
                for right in logical[i+1:]:
                    for a in left['details']['nodes']:
                        for b in right['details']['nodes']:
                            if C.points_equal(a['position'],b['position']):
                                graph.add_edge(a['elementId']['guid'].lower(),b['elementId']['guid'].lower(),connection='NATIVE_BRANCH_PHYSICAL_GRAPH')
    return {'schema':'APA_NATIVE_MEP_NETWORK_V1','routes':logical,'routeGuids':route_guids,'ownedNodeSegmentGuids':sorted(owned),
        'physicalGuids':physical,'ports':ports,'routePhysicalMembers':ownership,'logicalConnected':nx.is_connected(graph),
        'physicalConnected':bool(physical) and nx.is_connected(port_graph),
        'physicalConnectionEdges':port_graph.number_of_edges(),'segmentCount':segment_count,'nodeCount':graph.number_of_nodes(),
        'openPorts':[p for p in ports if not p['isPhysicallyConnected']],
        'distributionComponentCount':len(systems),
        'genericEnumerationCount':len(api('GetMEPElements',{}).get('elements',[])),
        'nativeTopologyAuthority':'Dedicated routing + native system membership + physical port flags/section/positions',
        'engineeringAcceptance':'NOT_VERIFIED'}


def physical_route_members(routes,ports):
    """Native port segments contained in a logical polyline, including trims."""
    by_owner={}
    for p in ports:by_owner.setdefault(p['ownerGuid'],[]).append(p)
    result={}
    for route in routes:
        members=[];line=route['details']['polyline']
        for guid,pp in by_owner.items():
            if len(pp)!=2:continue  # A tee is a connection, not a duct segment.
            for a,b in zip(line,line[1:]):
                d=[b[k]-a[k] for k in ('x','y','z')];length2=sum(x*x for x in d)
                if length2<=1e-14:raise ValueError('MEP_ZERO_LENGTH_LOGICAL_SEGMENT')
                def contained(p):
                    v=[p[k]-a[k] for k in ('x','y','z')];t=sum(x*y for x,y in zip(v,d))/length2
                    return -1e-6<=t<=1+1e-6 and sum((x-t*y)**2 for x,y in zip(v,d))<1e-10
                if all(contained(p['position']) for p in pp):members.append(guid);break
        result[route['guid'].lower()]=sorted(members)
    assigned=[g for values in result.values() for g in values]
    if len(set(assigned))!=len(assigned):raise ValueError('MEP_PHYSICAL_ROUTE_OWNERSHIP_AMBIGUOUS')
    return result


def connection_intent(network,first_guid,second_guid):
    if first_guid.lower() not in {g.lower() for g in network['routeGuids']} or second_guid.lower() not in {g.lower() for g in network['routeGuids']}:
        raise ValueError('CONNECT_REQUIRES_VERIFIED_ROUTE_OWNERSHIP')
    if first_guid.lower()==second_guid.lower():raise ValueError('CONNECT_ROUTE_TO_SELF')
    if network['logicalConnected'] and network['physicalConnected']:
        return {'status':'ALREADY_NATIVE_CONNECTED','nativeWritesRequired':0}
    return {'status':'EXPLICIT_CONNECT_REQUIRED','command':'ConnectMEPElements','parameters':{
        'connectionsData':[{'routingElementId':{'guid':first_guid},'connectToId':{'guid':second_guid}}]}}
