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


def dependency_inputs(*, components=None, openings=None, drawings=None, view_ids=(), memberships=(), navigator_bindings=None, layout_bindings=(), attributes=None, envelopes=None, ifc_ids=None):
    nodes, edges, evidence, omitted = set(), set(), [], []

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

    # Indices are project-local and type-specific. Resolve only a unique native
    # header in this capture; neither names nor positive numbers prove identity.
    attribute_index = {}
    for kind, reply in (attributes or {}).items():
        if kind not in {'BuildingMaterial', 'Surface', 'Composite'}:
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

    for row in (ifc_ids or {}).get('elementIFCIds', []):
        source, identity = guid(row.get('elementId')), row.get('ifcId')
        if source and isinstance(identity, str) and identity.strip() and 'error' not in row:
            edge(source, 'IFC:' + identity, 'NATIVE_IFC_IDENTITY_NOT_EXPORT_ACCEPTANCE')
        else:
            omitted.append('IFC_IDENTITY_MISSING_OR_NATIVE_ERROR')

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
                relationshipEvidence=evidence, omitted=omitted,
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
