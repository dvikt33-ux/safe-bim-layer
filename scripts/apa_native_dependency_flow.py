"""Convert captured native relationships to the existing DependencyImpact input.

No transport, graph store, executor or model writes. Callers retain raw source
replies privately. Membership and parameter evidence stay separate from contact.
"""
import hashlib
import json


def dependency_inputs(*, components=None, openings=None, drawings=None, view_ids=(), memberships=(), navigator_bindings=None, layout_bindings=()):
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
