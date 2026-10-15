"""Convert captured native relationships to the existing DependencyImpact input.

No transport, graph store, executor or model writes. Callers retain raw source
replies privately. Membership and parameter evidence stay separate from contact.
"""
import hashlib
import json


def capture_ifc_facts(api, router, element_ids):
    """Read current native IFC facts through source-reviewed dynamic contracts.

    Uses the existing IFC implementation. Runtime availability, project identity,
    schemas and per-command READ_ONLY policies remain enforced by the router.
    Values are the provider's strings; empty IDs and native errors stay explicit.
    This is not an IFC export or semantic compatibility acceptance.
    """
    ids = list(element_ids)
    if not 1 <= len(ids) <= 32 or len(set(ids)) != len(ids):
        raise ValueError('ONE_TO_32_UNIQUE_ELEMENT_IDS_REQUIRED')
    params = dict(elements=[dict(elementId=dict(guid=value)) for value in ids])
    result = {}
    for command in ('GetIFCIdsOfElements', 'GetIFCTypeOfElements', 'GetIFCPropertiesOfElements'):
        key = command if command in router.catalog['commands'] else 'AddOn.TapirCommand.' + command
        result[command] = router.read(api, router.prepare(key, params), reviewed_read_only=True)
    return dict(results=result, sourceSHA256=hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
                authority='CURRENT_NATIVE_IFC_ACCESSOR_NOT_EXPORT_ACCEPTANCE', nativeModelWrites=0)


def capture_mep_facts(api, router, element_ids=(), routing_ids=(), include_systems=True):
    """Reuse registered Tapir MEP reads; no native connection or preference edit."""
    def read(command, params):
        key=command if command in router.catalog['commands'] else 'AddOn.TapirCommand.'+command
        return router.read(api, router.prepare(key, params), reviewed_read_only=True)
    elements, routes = list(element_ids), list(routing_ids)
    if len(elements)>32 or len(routes)>32 or len(set(elements))!=len(elements) or len(set(routes))!=len(routes):
        raise ValueError('BOUNDED_UNIQUE_MEP_IDENTITIES_REQUIRED')
    out=dict(nativeModelWrites=0, portGroups=[], routingGroups=[], distributionSystems=[], authority='CURRENT_NATIVE_MEP_READ_NOT_GEOMETRIC_INTERSECTION_OR_ENGINEERING_ACCEPTANCE')
    for command, ids, key, result_key in [('GetMEPPorts',elements,'portGroups','elementPorts'),('GetMEPRoutingElements',routes,'routingGroups','routingElements')]:
        if not ids:continue
        reply=read(command,dict(elements=[dict(elementId=dict(guid=g)) for g in ids]))
        rows=reply[result_key]
        if len(rows)!=len(ids):raise ValueError('NATIVE_MEP_REQUEST_RESULT_CARDINALITY_MISMATCH')
        # Existing provider has one row per request in source-defined order.
        # Bind that order explicitly; never match names or array positions from
        # a different request. Raw native port IDs remain independent identities.
        out[key]=[dict(elementId=dict(guid=g),native=row,identityAuthority='SOURCE_ORDERED_REQUEST',requestOrdinal=i) for i,(g,row) in enumerate(zip(ids,rows))]
    if include_systems:out['distributionSystems']=read('GetMEPDistributionSystems',{})['distributionSystems']
    out['sourceSHA256']=hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
    return out


def dependency_inputs(*, components=None, openings=None, drawings=None, view_ids=(), memberships=(), navigator_bindings=None, layout_bindings=(), attributes=None, envelopes=None, ifc_ids=None, ifc_properties=None, gdl_parameters=(), mep=None, mep_topology=None, assembly_states=None):
    nodes, edges, evidence, omitted, connection_facts, property_facts, parameter_facts = set(), set(), [], [], [], [], []

    def guid(value):
        value = value.get('guid') if isinstance(value, dict) else None
        return value.upper() if isinstance(value, str) and value.strip() and value.replace('-','').strip('0') else None

    def edge(source, target, kind):
        if source and target and source != target:
            nodes.update((source, target))
            pair = (source, target)
            if pair not in edges:
                edges.add(pair)
                evidence.append(dict(source=source, target=target, kind=kind))

    def system_id(value):
        return guid(value.get('attributeId',value)) if isinstance(value,dict) else None

    ports={}
    for group in (mep or {}).get('portGroups',[]):
        owner=guid(group.get('elementId'));body=group.get('native',{})
        if not owner or group.get('identityAuthority')!='SOURCE_ORDERED_REQUEST' or 'error' in body:
            omitted.append('MEP_PORT_GROUP_IDENTITY_OR_RESULT_MISSING');continue
        for port in body.get('ports',[]):
            pid=guid({'guid':port.get('portId')})
            if not pid:omitted.append('MEP_PORT_ID_MISSING');continue
            key='MEP_PORT:'+pid
            if pid in ports and ports[pid]['owner']!=owner:raise ValueError('MEP_PORT_HAS_CONFLICTING_CAPTURED_OWNERS')
            ports[pid]=dict(owner=owner,native=port)
            edge(owner,key,'NATIVE_MEP_ELEMENT_PORT_MEMBERSHIP')
            sid=system_id(port.get('mepSystemId'))
            if sid:edge('ATTRIBUTE:MEPSYSTEM:'+sid,key,'NATIVE_MEP_PORT_SYSTEM_MEMBERSHIP')
    seen_connections=set()
    for pid,value in ports.items():
        port=value['native'];other=guid({'guid':port.get('connectedPortId')})
        if not other:continue
        pair=tuple(sorted((pid,other)))
        if pair in seen_connections:continue
        seen_connections.add(pair);peer=ports.get(other);reciprocal=bool(peer and guid({'guid':peer['native'].get('connectedPortId')})==pid)
        physical=bool(reciprocal and port.get('isPhysicallyConnected') is True and peer['native'].get('isPhysicallyConnected') is True)
        cid='MEP_CONNECTION:'+':'.join(pair)
        edge('MEP_PORT:'+pid,cid,'NATIVE_MEP_CONNECTION_ENDPOINT')
        if peer:edge('MEP_PORT:'+other,cid,'NATIVE_MEP_CONNECTION_ENDPOINT')
        connection_facts.append(dict(connection=cid,ports=list(pair),reciprocal=reciprocal,peerCaptured=peer is not None,physical=True if physical else None,nativePhysicalFlag=port.get('isPhysicallyConnected'),authority='BILATERAL_NATIVE_PORT_READ' if physical else 'SINGLE_SIDED_OR_LOGICAL_NATIVE_REFERENCE_NOT_PHYSICAL_PASS'))
    for system in (mep or {}).get('distributionSystems',[]):
        sid=system_id(system.get('mepSystemId'))
        if not sid:omitted.append('MEP_DISTRIBUTION_SYSTEM_ATTRIBUTE_MISSING');continue
        for item in system.get('elements',[]):edge('ATTRIBUTE:MEPSYSTEM:'+sid,guid(item.get('elementId')),'NATIVE_MEP_DISTRIBUTION_SYSTEM_MEMBERSHIP')
    for group in (mep or {}).get('routingGroups',[]):
        owner=guid(group.get('elementId'));body=group.get('native',{})
        if not owner or group.get('identityAuthority')!='SOURCE_ORDERED_REQUEST':continue
        sid=system_id(body.get('mepSystemId'))
        if sid:edge('ATTRIBUTE:MEPSYSTEM:'+sid,owner,'NATIVE_MEP_ROUTE_SYSTEM_MEMBERSHIP')
        for items,prefix,relation in [(body.get('segments',[]),'MEP_SEGMENT:','NATIVE_MEP_ROUTE_SEGMENT_MEMBERSHIP'),(body.get('nodes',[]),'MEP_NODE:','NATIVE_MEP_ROUTE_NODE_MEMBERSHIP')]:
            for item in items:
                child=guid(item.get('elementId'))
                if child:edge(owner,prefix+child,relation)
                else:omitted.append('MEP_ROUTE_CHILD_IDENTITY_MISSING')
    for row in (mep_topology or {}).get('elements',[]):
        identity=guid(row.get('elementId'));kind=row.get('kind')
        if not identity or 'error' in row:continue
        target=('MEP_SEGMENT:' if kind=='RoutingSegment' else 'MEP_NODE:' if kind=='RoutingNode' else '')+identity
        for field,prefix,relation in [('routingElementId','','NATIVE_MEP_ROUTE_OWNERSHIP'),('routingSegmentId','MEP_SEGMENT:','NATIVE_MEP_RIGID_SEGMENT_OWNER'),('routingNodeId','MEP_NODE:','NATIVE_MEP_FITTING_NODE_OWNER')]:
            owner=guid(row.get(field))
            if owner:edge(prefix+owner,target,relation)
        sid=guid(row.get('mepSystemId'))
        if sid:edge('ATTRIBUTE:MEPSYSTEM:'+sid,target,'NATIVE_MEP_TOPOLOGY_SYSTEM_MEMBERSHIP')
        preference=guid(row.get('preferenceTableId'))
        if preference:edge('MEP_PREFERENCE_TABLE:'+preference,target,'NATIVE_MEP_PARAMETER_PREFERENCE_DEPENDENCY')
        for field,prefix,relation in [('routingSegments','MEP_SEGMENT:','NATIVE_MEP_ROUTE_SEGMENT_MEMBERSHIP'),('routingNodes','MEP_NODE:','NATIVE_MEP_ROUTE_NODE_MEMBERSHIP'),('rigidSegments','','NATIVE_MEP_SEGMENT_RIGID_MEMBERSHIP'),('elbows','','NATIVE_MEP_NODE_ELBOW_MEMBERSHIP'),('transitions','','NATIVE_MEP_NODE_TRANSITION_MEMBERSHIP')]:
            for item in row.get(field,[]):
                child=guid(item)
                if child:edge(target,prefix+child,relation)
        for field in ['logicalBeginPortId','logicalEndPortId']:
            port=guid(row.get(field))
            if port:edge(target,'MEP_PORT:'+port,'NATIVE_MEP_ROUTE_LOGICAL_ENDPOINT_NOT_PHYSICAL_CONNECTION')
        for field in ['narrowerPortId','widerPortId']:
            port=guid(row.get(field))
            if port:edge(target,'MEP_PORT:'+port,'NATIVE_MEP_TRANSITION_PORT_MEMBERSHIP')
        for field in ['beginNodeId','endNodeId']:
            node=guid(row.get(field))
            if node:
                incidence='MEP_INCIDENCE:'+identity+':'+node
                edge(target,incidence,'NATIVE_MEP_SEGMENT_NODE_INCIDENCE');edge('MEP_NODE:'+node,incidence,'NATIVE_MEP_SEGMENT_NODE_INCIDENCE')

    for row in (assembly_states or {}).get('elements',[]):
        owner=guid(row.get('elementId'))
        if not owner or 'error' in row:omitted.append('ASSEMBLY_NATIVE_STATE_IDENTITY_OR_RESULT_MISSING');continue
        for name,value in row.get('values',{}).items():
            key='NATIVE_PARAMETER:'+owner+':'+name
            read_only=row.get('kind')=='CurtainWall' and name=='heightMetres'
            edge(owner,key,'NATIVE_READ_ONLY_DERIVED_PARAMETER_FACT') if read_only else edge(key,owner,'NATIVE_EDITABLE_PARAMETER_DEPENDENCY')
            parameter_facts.append(dict(node=key,value=value,editable=not read_only,authority='NATIVE_SDK_FIELD_NOT_PHYSICAL_CONTACT',runtimeWriteAcceptance='NOT_INFERRED_FROM_STATE_READ'))
        kinds={'buildingMaterialId':'BUILDINGMATERIAL','compositeId':'COMPOSITE','surfaceId':'SURFACE','outerSurfaceId':'SURFACE','innerSurfaceId':'SURFACE','cutSurfaceId':'SURFACE','topSurfaceId':'SURFACE','sideSurfaceId':'SURFACE','bottomSurfaceId':'SURFACE'}
        for name,item in row.get('attributes',{}).items():
            identity=guid(item.get('attributeId'));kind=kinds.get(name);flag=name.replace('SurfaceId','SurfaceOverridden')
            if flag in row.get('values',{}) and row['values'][flag] is not True:continue
            if name=='surfaceId' and row.get('values',{}).get('useOwnMaterial') is False:continue
            if identity and kind:edge('ATTRIBUTE:'+kind+':'+identity,owner,'NATIVE_APPLICABLE_EDIT_ATTRIBUTE_DEPENDENCY')
        memo=row.get('memo',{})
        if memo and row.get('memoReadError')==0:
            for name in ['referencePath','primaryPattern','secondaryPattern','curtainWallContours']:
                if name in memo:
                    key='NATIVE_PARAMETER:'+owner+':MEMO:'+name;edge(key,owner,'NATIVE_MEMO_PARAMETER_DEPENDENCY');parameter_facts.append(dict(node=key,authority='NATIVE_PARAMETER_MEMO_NOT_RESULTANT_BODY',editable=bool(row.get('memoEdits'))))
            for segment in memo.get('curtainWallSegments',[]):
                child=guid(segment.get('elementId'));declared=guid(segment.get('ownerId'))
                if declared==owner and child:edge(owner,child,'NATIVE_CW_MEMO_DECLARED_SEGMENT_OWNER')
                else:omitted.append('CW_MEMO_SEGMENT_OWNER_NOT_CONFIRMED')

    # Indices are project-local and type-specific. Resolve only a unique native
    # header in this capture; neither names nor positive numbers prove identity.
    attribute_index = {}
    for kind, reply in (attributes or {}).items():
        if kind not in {'BuildingMaterial', 'Surface', 'Composite', 'Profile'}:
            continue
        for item in reply.get('attributes', []):
            identity, index = guid(item.get('attributeId')), item.get('index')
            if identity and isinstance(index, int) and not isinstance(index, bool):
                attribute_index.setdefault((kind, index), set()).add('ATTRIBUTE:' + kind.upper() + ':' + identity)

    def attribute(kind, index, target, relation):
        candidates = attribute_index.get((kind, index), set())
        if target and len(candidates) == 1:
            edge(next(iter(candidates)), target, relation)
        else:
            omitted.append('ATTRIBUTE_INDEX_MISSING_OR_AMBIGUOUS:' + kind)

    for group in memberships:
        parent = guid(group.get('parentElementId'))
        body = group.get('subelements', {})
        if not parent or 'error' in body:
            omitted.append('MEMBERSHIP_PARENT_OR_NATIVE_RESULT_MISSING')
            continue
        nodes.add(parent)
        for items in body.values():
            if isinstance(items, list):
                for item in items:
                    edge(parent, guid(item.get('elementId')), 'NATIVE_HIERARCHICAL_MEMBERSHIP')

    for row in (components or {}).get('elements', []):
        child = guid(row.get('elementId'))
        if not child:
            omitted.append('COMPONENT_ERROR_OR_ID_MISSING')
            continue
        nodes.add(child)
        params, flags = row.get('parameters', {}), row.get('flags', {})
        # Panel material is explicit. Frame material applies only with the SDK
        # useOwnMaterial flag. Disabled surface overrides are not dependencies.
        if row.get('specificParametersSupported'):
            if 'buildingMaterialIndex' in params and ('useOwnMaterial' not in flags or flags['useOwnMaterial']):
                attribute('BuildingMaterial', params['buildingMaterialIndex'], child, 'NATIVE_COMPONENT_BUILDING_MATERIAL')
            for name, flag in [('outerSurfaceIndex','outerSurfaceOverridden'), ('innerSurfaceIndex','innerSurfaceOverridden'), ('cutSurfaceIndex','cutSurfaceOverridden')]:
                if flags.get(flag) is True and name in params:
                    attribute('Surface', params[name], child, 'NATIVE_COMPONENT_SURFACE_OVERRIDE')
            if flags.get('useOwnMaterial') is True and 'surfaceIndex' in params:
                attribute('Surface', params['surfaceIndex'], child, 'NATIVE_FRAME_OWN_SURFACE')
        if row.get('parentQueryError') == 0:
            edge(guid(row.get('parentElementId')), child, 'NATIVE_HIERARCHICAL_PARENT')
        if row.get('rootQueryError') == 0:
            edge(guid(row.get('rootElementId')), child, 'NATIVE_HIERARCHICAL_ROOT')
        declared = guid(row.get('declaredOwnerId'))
        if declared and row.get('parentQueryError') == 0 and declared != guid(row.get('parentElementId')):
            omitted.append('DECLARED_OWNER_DIFFERS_FROM_PARENT_NO_INFERRED_EDGE')

    for row in (openings or {}).get('elements', []):
        current = guid(row.get('elementId'))
        if not current:
            omitted.append('OPENING_ERROR_OR_ID_MISSING')
            continue
        nodes.add(current)
        if row.get('parentResolved'):
            edge(guid(row.get('hostElementId')), current, 'NATIVE_OPENING_HOST')
        for item in row.get('connectedOpenings', []):
            edge(current, guid(item), 'NATIVE_HOST_CONNECTED_OPENING')
        # Cut elements are native affected hosts, not proof of physical contact.
        for item in row.get('cutElements', []):
            edge(guid(item), current, 'NATIVE_OPENING_CUT_HOST')

    for row in (envelopes or {}).get('elements', []):
        target, base = guid(row.get('elementId')), row.get('shellBaseParameters', {})
        if base.get('buildingMaterialApplicable') is True:
            attribute('BuildingMaterial', base.get('buildingMaterialIndex'), target, 'NATIVE_ENVELOPE_BUILDING_MATERIAL')
        if base.get('compositeApplicable') is True:
            attribute('Composite', base.get('compositeIndex'), target, 'NATIVE_ENVELOPE_COMPOSITE')
        for item in base.get('surfaceOverrides', []):
            if item.get('overridden') is True:
                attribute('Surface', item.get('surfaceIndex'), target, 'NATIVE_ENVELOPE_SURFACE_OVERRIDE')

    ifc_by_native={}
    for row in (ifc_ids or {}).get('elementIFCIds', []):
        source, identity = guid(row.get('elementId')), row.get('ifcId')
        if source and isinstance(identity, str) and identity.strip() and 'error' not in row:
            ifc_by_native.setdefault(source,set()).add(identity)
            edge(source, 'IFC:' + identity, 'NATIVE_IFC_IDENTITY_NOT_EXPORT_ACCEPTANCE')
        else:
            omitted.append('IFC_IDENTITY_MISSING_OR_NATIVE_ERROR')

    for row in (ifc_properties or {}).get('elementIFCProperties',[]):
        identities=ifc_by_native.get(guid(row.get('elementId')),set())
        if len(identities)!=1 or 'error' in row:
            omitted.append('IFC_PROPERTY_NATIVE_IDENTITY_MISSING_OR_AMBIGUOUS');continue
        identity=next(iter(identities))
        for item in row.get('ifcProperties',[]):
            if not all(isinstance(item.get(k),str) for k in ('propertySetName','name','value')):
                omitted.append('IFC_PROPERTY_PROVIDER_STRING_CONTRACT_MISSING');continue
            label=json.dumps([item['propertySetName'],item['name']],ensure_ascii=False,separators=(',',':'))
            key='IFC_PROPERTY:'+identity+':'+hashlib.sha256(label.encode()).hexdigest()
            edge('IFC:'+identity,key,'NATIVE_IFC_PROPERTY_ACCESSOR_REFERENCE')
            property_facts.append(dict(node=key,propertySetName=item['propertySetName'],name=item['name'],value=item['value'],authority='PROVIDER_SERIALIZED_STRING_NOT_TYPED_IFC_EXPORT_ACCEPTANCE'))
    for binding in gdl_parameters:
        owner=guid(binding.get('elementId'));part=guid(binding.get('libraryPartId'))
        if not owner:omitted.append('GDL_PLACED_OWNER_IDENTITY_MISSING');continue
        if not part:omitted.append('GDL_LIBRARY_PART_IDENTITY_NOT_CAPTURED_NO_NAME_MATCH')
        for parameter in binding.get('parameters',[]):
            if not isinstance(parameter.get('name'),str) or not isinstance(parameter.get('index'),int):
                omitted.append('GDL_PARAMETER_IDENTITY_MISSING');continue
            label=json.dumps([parameter['index'],parameter['name']],ensure_ascii=False,separators=(',',':'))
            key='GDL_PARAMETER:'+owner+':'+hashlib.sha256(label.encode()).hexdigest()
            edge(key,owner,'NATIVE_PLACED_PARAMETER_DEPENDENCY')
            if part:edge('LIBRARY_PART:'+part,key,'NATIVE_LIBRARY_PARAMETER_DEFINITION')
            attribute_kind={'BuildingMaterial':'BuildingMaterial','Material':'Surface','Profile':'Profile'}.get(parameter.get('type'))
            if attribute_kind:
                values=parameter.get('value');values=values if isinstance(values,list) else [values]
                for value in values:
                    if isinstance(value,int) and not isinstance(value,bool):attribute(attribute_kind,value,key,'NATIVE_TYPED_GDL_ATTRIBUTE_PARAMETER')

    resolved = {}
    for row in (navigator_bindings or {}).get('items', []):
        if row.get('identityMatchesRequest') and row.get('mapMatchesRequest'):
            current = guid(row.get('navigatorItemId'))
            if current:
                key = 'NAVIGATOR:' + row['requestedMap'].upper() + ':' + current
                resolved.setdefault(current, set()).add(key)
                nodes.add(key)
                source = guid(row.get('sourceGuid'))
                # SDK sourceGuid is a source reference, not a physical element ID.
                if source:
                    edge('NAVIGATOR_SOURCE_REFERENCE:' + source, key, 'NATIVE_NAVIGATOR_SOURCE_REFERENCE')
    layouts = {}
    for row in layout_bindings:
        db, layout = guid(row.get('databaseId')), guid(row.get('navigatorItemId'))
        if db and layout:
            layouts.setdefault(db, set()).add('NAVIGATOR:LAYOUTBOOK:' + layout)
    known_views = {v.upper() for v in view_ids}
    for row in (drawings or {}).get('drawings', []):
        drawing = guid(row.get('elementId'))
        if not drawing:
            omitted.append('DRAWING_ERROR_OR_ID_MISSING')
            continue
        nodes.add(drawing)
        owners = layouts.get(guid(row.get('databaseId')), set())
        if row.get('databaseQualified') and len(owners) == 1:
            edge(drawing, next(iter(owners)), 'NATIVE_DRAWING_OWNING_LAYOUT')
        source = guid(row.get('linkGuid'))
        sources = resolved.get(source, set())
        if source in known_views:
            sources = {'NAVIGATOR:PUBLICVIEWMAP:' + source}
        if len(sources) == 1 and row.get('viewDeleted') is False:
            edge(next(iter(sources)), drawing, 'NATIVE_DRAWING_LINK_VERIFIED_IN_NAVIGATOR')
        else:
            omitted.append('DRAWING_SOURCE_NOT_IN_CAPTURED_OR_EXPLICITLY_RESOLVED_NAVIGATOR')
    return dict(nodes=sorted(nodes), edges=[list(e) for e in sorted(edges)],
                relationshipEvidence=evidence, omitted=omitted, connectionFacts=connection_facts, ifcPropertyFacts=property_facts, nativeParameterFacts=parameter_facts,
                authority='CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT')


def run(router, captured, changed):
    """Reuse BIM Graph and local dispatch; never author native operations."""
    import archicad_project_accelerator as A
    inputs = dependency_inputs(**captured)
    changed = [x.upper() for x in changed]
    if not set(changed) <= set(inputs['nodes']):
        raise ValueError('CHANGED_NODE_NOT_PRESENT_IN_NATIVE_RELATIONSHIPS')
    graph = dict(operations=[dict(id='impact', command='AddOn.APAAnalysis.DependencyImpact',
        params={k: inputs[k] for k in ('nodes', 'edges')} | dict(changed=changed))])
    answer = router.run_workflow(None, A.prepare_native_workflow(router, graph))
    return dict(inputs=inputs, result=answer['results']['impact'],
                sourceSHA256=hashlib.sha256(json.dumps(captured, sort_keys=True).encode()).hexdigest(),
                sourcePlanHash=answer['sourcePlanHash'], status=answer['status'],
                nativeModelWrites=0, executionPermission=False)
