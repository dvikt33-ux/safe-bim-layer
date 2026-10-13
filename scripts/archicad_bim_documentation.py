"""Associative documentation over native databases and the shared BIM snapshot.

No renderer, normative engine, transport or second writer. Geometry quantities
reuse the connected IFC adapter. Native views and CSV facts remain distinct.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import archicad_connected_components as C
from archicad_connected_ifc import native_body_quantities

RUN = C.RUN
DOCUMENT_COMMANDS = frozenset({'CreateSections', 'CreateInteriorElevations', 'CreateViewsInViewMap',
    'ChangeWindow', 'RebuildView', 'CreateWalls', 'SaveProject', 'OpenProject',
    'MoveElements', 'CreateAssociativeDimensionsOnSection', 'CreateLayout', 'CreateDrawings', 'PublishPublisherSet','SetViewSettings','UpdateDrawings'})
SPECIAL_DOCUMENT_COMMANDS = frozenset({'SaveProject', 'OpenProject', 'PublishPublisherSet'})
SLOTS = {'CreateSections': 'sectionsData', 'CreateInteriorElevations': 'interiorElevationsData', 'CreateViewsInViewMap': 'viewsData',
         'CreateWalls': 'wallsData', 'MoveElements': 'elementsWithMoveVectors',
         'CreateAssociativeDimensionsOnSection': 'dimensionsData', 'CreateLayout': 'layoutsData',
         'CreateDrawings': 'drawingsData','SetViewSettings':'navigatorItemIdsWithViewSettings','UpdateDrawings':'elements'}


def flatten(tree):
    node = tree.get('navigatorItemTree', tree)
    yield node
    for child in node.get('children', []):
        yield from flatten(child.get('navigatorItem', child))


def item_guid(item):
    return item['navigatorItemId']['guid'].lower()


def source_view(tree, kind, story_index=None):
    rows = [r for r in flatten(tree) if r.get('type') == kind and
            (story_index is None or r.get('prefix') == str(story_index))]
    if not rows:
        raise ValueError('NATIVE_VIEWPOINT_NOT_AVAILABLE: ' + kind)
    return rows[0]


def operation_scope(command, parameters, source_hash, retained_guids,
                    test_guids=(), authorization_ref=None):
    """Exact operation scope for the existing SceneWriter, never permission by name."""
    if not authorization_ref:
        raise ValueError('DOCUMENTATION_EXPLICIT_OPERATION_SCOPE_REQUIRED')
    scope = {'schema': 'APA_NATIVE_DOCUMENTATION_OPERATION_V1',
        'command': command, 'parameters': parameters, 'sourceHash': source_hash,
        'retainedGuids': sorted(g.lower() for g in retained_guids),
        'testGuids': sorted(g.lower() for g in test_guids),
        'authorizationRef': authorization_ref}
    scope['scopeHash'] = RUN.digest(scope)
    qualify_operation(scope, command, parameters, source_hash)
    return scope


def qualify_operation(scope, command, parameters, source_hash):
    if (scope.get('schema') != 'APA_NATIVE_DOCUMENTATION_OPERATION_V1' or
            not scope.get('authorizationRef') or scope.get('command') != command or
            scope.get('parameters') != parameters or scope.get('sourceHash') != source_hash or
            scope.get('scopeHash') != RUN.digest({k: v for k, v in scope.items() if k != 'scopeHash'}) or
            not scope.get('retainedGuids')):
        raise ValueError('DOCUMENTATION_OPERATION_SCOPE_MISMATCH')
    if command not in DOCUMENT_COMMANDS | {'ModifyWalls'}:
        raise ValueError('DOCUMENTATION_UNQUALIFIED_COMMAND')
    if command in SLOTS:
        rows = parameters.get(SLOTS[command])
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError('DOCUMENTATION_ONE_NATIVE_TARGET_REQUIRED')
    if command == 'ModifyWalls':
        rows = parameters.get('wallsWithDetails')
        if (set(parameters) != {'wallsWithDetails'} or not isinstance(rows, list) or len(rows) != 1 or
                set(rows[0]) != {'elementId', 'height'} or
                rows[0]['elementId']['guid'].lower() not in scope.get('testGuids', []) or
                rows[0]['elementId']['guid'].lower() in scope['retainedGuids'] or
                type(rows[0]['height']) not in (float, int) or not math.isfinite(rows[0]['height']) or rows[0]['height'] <= 0):
            raise ValueError('DOCUMENTATION_ONLY_NEW_TEST_WALL_HEIGHT_ALLOWED')
    if command == 'ChangeWindow' and set(parameters) != {'navigatorItemId'}:
        raise ValueError('DOCUMENTATION_EXACT_NATIVE_VIEW_ID_REQUIRED')
    if command == 'RebuildView' and parameters != {'regenerate': True}:
        raise ValueError('DOCUMENTATION_EXPLICIT_REGENERATION_REQUIRED')
    if command == 'SaveProject' and parameters != {}:
        raise ValueError('DOCUMENTATION_SAVE_CURRENT_PROJECT_ONLY')
    if command == 'OpenProject' and (set(parameters) != {'projectFilePath'} or
            not isinstance(parameters['projectFilePath'], str)):
        raise ValueError('DOCUMENTATION_OPEN_EXACT_BOUND_SAVED_PROJECT_ONLY')
    if command == 'MoveElements':
        row=parameters['elementsWithMoveVectors'][0]
        vector=row.get('moveVector',{})
        guid=row.get('elementId',{}).get('guid','').lower()
        copy_source=row.get('copy') is True and guid in scope['retainedGuids']
        new_test_target=row.get('copy') is False and guid in scope['testGuids'] and guid not in scope['retainedGuids']
        if (set(row)!={'elementId','moveVector','copy'} or not (copy_source or new_test_target) or
                set(vector)!={'x','y','z'} or vector['z']!=0 or
                any(type(v) not in (int,float) or not math.isfinite(v) for v in vector.values())):
            raise ValueError('DOCUMENTATION_COPY_ONLY_NO_EXISTING_ELEMENT_MOVE')
    if command == 'PublishPublisherSet':
        from pathlib import PureWindowsPath
        selected=parameters.get('selectedNavigatorItemIds')
        output=parameters.get('outputPath','')
        if (set(parameters)!={'publisherSetName','outputPath','selectedNavigatorItemIds'} or
                not isinstance(selected,list) or not 1<=len(selected)<=4 or
                not isinstance(output,str) or output.startswith(('\\\\','//')) or
                not (Path(output).is_absolute() or PureWindowsPath(output).is_absolute())):
            raise ValueError('DOCUMENTATION_EXPLICIT_LOCAL_SELECTED_PUBLICATION_REQUIRED')
    if command=='CreateLayout':
        row=parameters['layoutsData'][0]
        if not (row.get('masterLayoutName') or row.get('masterNavigatorItemId')):
            raise ValueError('DOCUMENTATION_LAYOUT_REQUIRES_EXPLICIT_MASTER')
    if command=='SetViewSettings':
        row=parameters['navigatorItemIdsWithViewSettings'][0];guid=row.get('navigatorItemId',{}).get('guid','').lower();settings=row.get('viewSettings',{});zoom=settings.get('zoom',{})
        if (guid not in scope['testGuids'] or guid in scope['retainedGuids'] or
                set(settings)!={'drawingScale','saveZoom','ignoreSavedZoom','zoom'} or
                settings['saveZoom'] is not True or settings['ignoreSavedZoom'] is not False or
                type(settings['drawingScale']) not in (int,float) or settings['drawingScale']<=0 or
                set(zoom)!={'xMin','yMin','xMax','yMax'} or
                any(type(v) not in (int,float) or not math.isfinite(v) for v in zoom.values()) or
                zoom['xMin']>=zoom['xMax'] or zoom['yMin']>=zoom['yMax']):
            raise ValueError('DOCUMENTATION_ONLY_NEW_VIEW_SCALE_AND_FRAME_ALLOWED')
    if command=='UpdateDrawings':
        guid=parameters['elements'][0].get('elementId',{}).get('guid','').lower()
        if guid not in scope['testGuids'] or guid in scope['retainedGuids']:
            raise ValueError('DOCUMENTATION_ONLY_NEW_DRAWING_UPDATE_ALLOWED')


def native_response(command, reply):
    if command in {'ChangeWindow', 'RebuildView', 'SaveProject', 'OpenProject'}:
        if reply != {'success': True}:
            raise ValueError('DOCUMENTATION_NATIVE_SUCCESS_NOT_CONFIRMED')
    elif command in {'CreateWalls', 'CreateSections', 'CreateInteriorElevations', 'CreateDrawings', 'CreateAssociativeDimensionsOnSection'}:
        return RUN.created_guid(reply)
    elif command=='CreateLayout':
        rows=reply.get('databases',[])
        if len(rows)!=1 or 'error' in rows[0] or not RUN._GUID.fullmatch(rows[0].get('databaseId',{}).get('guid','')):
            raise ValueError('DOCUMENTATION_NATIVE_LAYOUT_NOT_CONFIRMED')
        return rows[0]['databaseId']['guid'].lower()
    elif command in {'MoveElements','SetViewSettings'}:
        if reply!={'executionResults':[{'success':True}]}:
            raise ValueError('DOCUMENTATION_NATIVE_COPY_NOT_CONFIRMED')
    elif command=='UpdateDrawings':
        if reply!={'success':True}:raise ValueError('DOCUMENTATION_NATIVE_DRAWING_UPDATE_NOT_CONFIRMED')
    elif command=='PublishPublisherSet':
        # SDK returns an empty object on success. Independent file readback is
        # mandatory in execute_operation; a successful command alone proves no PDF.
        if reply!={}:raise ValueError('DOCUMENTATION_PUBLISH_NATIVE_REJECTED')
    elif command == 'CreateViewsInViewMap':
        rows = reply.get('navigatorItems')
        if not isinstance(rows, list) or len(rows) != 1 or 'error' in rows[0]:
            raise ValueError('DOCUMENTATION_NATIVE_VIEW_NOT_CONFIRMED')
        guid = rows[0].get('navigatorItemId', {}).get('guid')
        if not isinstance(guid, str) or not RUN._GUID.fullmatch(guid):
            raise ValueError('DOCUMENTATION_NATIVE_VIEW_ID_INVALID')
        return guid.lower()


def execute_operation(writer, scene_id, command, parameters, source_hash,
                      retained_signatures, verify_after, authorization_ref,
                      test_guids=(), saved_sha256=None, activate_navigator_id=None,
                      expected_window=None):
    """Documentation adapter delegates every intent to the same SceneWriter ledger.

    The caller supplies an independent, operation-specific native readback.
    Retained BREP, materials, relationships and stories are checked before and
    after. Unknown outcomes remain in the original journal and cannot replay.
    """
    scope = operation_scope(command, parameters, source_hash, retained_signatures,
                            test_guids, authorization_ref)
    preflight = {'sourcePlanHash': source_hash, 'binding': writer.guarded_binding(),
        'integrationBindings': {'dependencies': {'documentationOperation': scope}}}
    intent = {'sceneId': scene_id, 'sourcePlanHash': source_hash, 'command': command,
              'parameters': parameters, 'target': preflight['binding']}

    def retained():
        native = capture_full_model(writer.api, retained_signatures)
        if command=='MoveElements' and parameters['elementsWithMoveVectors'][0]['copy']:
            source=parameters['elementsWithMoveVectors'][0]['elementId']['guid'].lower()
            if next((e['type'] for e in native['elements'] if e['guid'].lower()==source),None)!='Elevation':
                raise ValueError('DOCUMENTATION_NATIVE_ELEVATION_COPY_SOURCE_REQUIRED')
        actual = C.retained_geometry_signatures(native, sorted(retained_signatures))
        if actual != retained_signatures:
            raise ValueError('DOCUMENTATION_RETAINED_MODEL_CHANGED')
        return {'status': 'RETAINED_NATIVE_MODEL_PASS', 'count': len(actual),
                'signatureHash': RUN.digest(actual)}

    def before():
        if saved_sha256 is None:
            raise ValueError('DOCUMENTATION_SAVED_FILE_HASH_REQUIRED')
        import hashlib
        if hashlib.sha256(Path(preflight['binding']['path']).read_bytes()).hexdigest() != saved_sha256:
            raise ValueError('DOCUMENTATION_SAVED_FILE_HASH_CHANGED')
        if command == 'PublishPublisherSet':
            output = Path(parameters['outputPath'])
            if output.is_symlink() or (output.exists() and
                    (not output.is_dir() or any(output.iterdir()))):
                raise ValueError('DOCUMENTATION_EXPORT_REQUIRES_NEW_EMPTY_DIRECTORY')
        try:
            proof=retained()
        except ValueError as exc:
            if str(exc)!='DOCUMENTATION_LAYOUT_MODEL_WINDOW_REQUIRED':raise
            proof=restore_model_window(writer,scene_id+'-db-before',source_hash,
                retained_signatures,authorization_ref,saved_sha256)
        if activate_navigator_id is not None:
            if expected_window not in {'FloorPlan', 'Section', 'Elevation', 'InteriorElevation', 'Layout'}:
                raise ValueError('DOCUMENTATION_EXPLICIT_WINDOW_BINDING_REQUIRED')
            nav_params = {'navigatorItemId': {'guid': activate_navigator_id}}
            nav_scope = operation_scope('ChangeWindow', nav_params, source_hash,
                retained_signatures, test_guids, authorization_ref)
            nav_pre = {**preflight, 'integrationBindings': {'dependencies': {'documentationOperation': nav_scope}}}
            nav_id = scene_id + '-view'
            nav_intent = {'sceneId': nav_id, 'sourcePlanHash': source_hash,
                'command': 'ChangeWindow', 'parameters': nav_params, 'target': preflight['binding']}
            def verify_window(*_):
                window = writer.api('GetCurrentWindowType', {})
                if window.get('currentWindowType') != expected_window:
                    raise ValueError('DOCUMENTATION_NATIVE_WINDOW_MISMATCH')
                return {'status': 'NATIVE_DOCUMENTATION_WINDOW_PASS', 'window': window,
                    'geometryProofImmediatelyBeforeNavigation': dict(proof)}
            activated = writer.execute_bound_operation(nav_pre, nav_id, 'ChangeWindow', nav_params,
                RUN.digest(nav_intent), lambda: proof, verify_window)
            if activated['status'] != 'PASS':
                raise ValueError('DOCUMENTATION_WINDOW_ACTIVATION_NOT_CONFIRMED')
            proof['windowActivation'] = {k: activated[k] for k in
                ('sceneId', 'status', 'operationHash', 'readback')}
        if command in {'CreateSections', 'CreateInteriorElevations', 'CreateWalls', 'ModifyWalls'}:
            if writer.api('GetCurrentWindowType', {}).get('currentWindowType') != 'FloorPlan':
                raise ValueError('DOCUMENTATION_MODEL_WRITE_REQUIRES_NATIVE_FLOOR_PLAN')
        return proof

    def after(reply, prior):
        proof = verify_after(reply, prior)
        if not isinstance(proof, dict) or not str(proof.get('status', '')).endswith('PASS'):
            raise ValueError('DOCUMENTATION_NATIVE_READBACK_REQUIRED')
        try:
            retained_proof=retained()
        except ValueError as exc:
            if str(exc)!='DOCUMENTATION_LAYOUT_MODEL_WINDOW_REQUIRED':raise
            retained_proof=restore_model_window(writer,scene_id+'-db-after',source_hash,
                retained_signatures,authorization_ref,saved_sha256)
        return {**proof, 'retained': retained_proof}

    return writer.execute_bound_operation(preflight, scene_id, command, parameters,
        RUN.digest(intent), before, after)


def capture_full_model(api, retained_guids):
    """Installed dump first enumerates the active DB, then opens/regenerates 3D.

    A section/elevation DB can omit nonspatial floor-plan GUIDs on the first
    read. Re-read only this read operation once after the native 3D switch.
    Never cache missing identities or repeat Create/Modify as reconciliation.
    Callers must activate their target database AFTER this geometry barrier.
    """
    selected = {g.lower() for g in retained_guids}
    raw=api('GetModelDumpV1', {})
    if raw.get('error')=={'code':-2130313109,'message':'ShowAllIn3D'}:
        raise ValueError('DOCUMENTATION_LAYOUT_MODEL_WINDOW_REQUIRED')
    if 'error' in raw:raise ValueError('DOCUMENTATION_NATIVE_DUMP_REJECTED')
    native=C.G.normalize_dump(raw)
    if not selected <= {e['guid'].lower() for e in native['elements']}:
        native = C.G.normalize_dump(api('GetModelDumpV1', {}))
    if not selected <= {e['guid'].lower() for e in native['elements']}:
        raise ValueError('DOCUMENTATION_COMPLETE_NATIVE_INVENTORY_UNAVAILABLE')
    return native


def restore_model_window(writer,scene_id,source_hash,retained_signatures,authorization_ref,saved_sha256):
    """View-only recovery via the existing journal, then full native proof.

    Installed ShowAllIn3D rejects Layout. This changes only the active window;
    identity/saved bytes precede the call. No Create/Modify/Publish replay.
    """
    import hashlib
    if writer.api('GetCurrentWindowType',{})!={'currentWindowType':'Layout'}:
        raise ValueError('DOCUMENTATION_MODEL_WINDOW_RECOVERY_NOT_LAYOUT')
    floor=source_view(writer.api('GetNavigatorItemTree',{'navigatorMapId':'ProjectMap'}),'StoryItem',0)
    params={'navigatorItemId':floor['navigatorItemId']};hash_ref=RUN.digest([source_hash,'LAYOUT_MODEL_WINDOW_RECOVERY',scene_id])
    scope=operation_scope('ChangeWindow',params,hash_ref,retained_signatures,authorization_ref=authorization_ref)
    preflight={'sourcePlanHash':hash_ref,'binding':writer.guarded_binding(),'integrationBindings':{'dependencies':{'documentationOperation':scope}}}
    intent={'sceneId':scene_id,'sourcePlanHash':hash_ref,'command':'ChangeWindow','parameters':params,'target':preflight['binding']}
    def before():
        if hashlib.sha256(Path(preflight['binding']['path']).read_bytes()).hexdigest()!=saved_sha256:
            raise ValueError('DOCUMENTATION_SAVED_FILE_HASH_CHANGED')
        return {'status':'VIEW_ONLY_RECOVERY_IDENTITY_AND_SAVED_BYTES_CHECKED','modelGeometryWrite':False}
    def after(reply,_):
        if writer.api('GetCurrentWindowType',{})!={'currentWindowType':'FloorPlan'}:raise ValueError('DOCUMENTATION_FLOOR_WINDOW_RECOVERY_FAILED')
        native=capture_full_model(writer.api,retained_signatures);actual=C.retained_geometry_signatures(native,sorted(retained_signatures))
        if actual!=retained_signatures:raise ValueError('DOCUMENTATION_RETAINED_MODEL_CHANGED')
        return {'status':'NATIVE_MODEL_DATABASE_RECOVERY_PASS','count':len(actual),'signatureHash':RUN.digest(actual)}
    result=writer.execute_bound_operation(preflight,scene_id,'ChangeWindow',params,RUN.digest(intent),before,after)
    if result['status']!='PASS':raise ValueError('DOCUMENTATION_MODEL_WINDOW_RECOVERY_UNVERIFIED')
    return result['readback']


def make_snapshot(native, guids, details=None):
    """One immutable version for plan facts, vertical facts and specifications."""
    selected = {g.lower() for g in guids}
    if not selected or len(selected) != len(guids):
        raise ValueError('DOCUMENTATION_UNIQUE_NONEMPTY_GUID_SCOPE_REQUIRED')
    elements = {e['guid'].lower(): e for e in native['elements']}
    if not selected <= elements.keys():
        raise ValueError('DOCUMENTATION_NATIVE_GUID_MISSING')
    signatures = C.retained_geometry_signatures(native, sorted(selected))
    stories = {s['index']: s for s in native['stories']}
    facts = []
    for guid in sorted(selected):
        e = elements[guid]
        if e.get('homeStory') not in stories:
            raise ValueError('DOCUMENTATION_NATIVE_STORY_MISSING')
        story = stories[e['homeStory']]
        coordinates = [v for b in e.get('bodies', []) for v in b['vertices']]
        actual_bounds = [[min(v[k] for v in coordinates), max(v[k] for v in coordinates)]
                         for k in range(3)] if coordinates else None
        d = (details or {}).get(guid, {})
        facts.append({'guid': guid, 'nativeType': e['type'], 'count': 1,
            'storyIndex': e['homeStory'], 'storyElevationMeters': story['elevation'],
            'referenceGeometry': e.get('placement', {}).get('referenceGeometry', {}),
            'resultantBoundsMeters': actual_bounds,
            'materials': e.get('materialBindings', {}), 'relationships': e.get('relationships', {}),
            'quantities': native_body_quantities(e),
            'floorPlanPolygons': d.get('floorPlanPolygons', []),
            'floorPlanStatus': 'NATIVE_CUT_FILL_AVAILABLE' if d.get('floorPlanPolygons') else 'NATIVE_CUT_FILL_NOT_AVAILABLE',
            'nativeDetails': d.get('details', {}), 'bodySignature': signatures[guid]})
    payload = {'schema': 'APA_BIM_DOCUMENTATION_SNAPSHOT_V1', 'units': 'meters',
               'stories': native['stories'], 'elements': facts}
    # Database-dependent cut fills and view settings must not masquerade as a
    # model edit. Version the source BREP and stories, independently of the UI.
    return {**payload, 'modelVersion': RUN.digest({'stories': native['stories'],
        'elementSignatures': signatures})}


def bundle(snapshot, plan_story, native_views=None):
    """Prepare facts; attach only actual native database readbacks as native views."""
    elements = snapshot['elements']
    if plan_story not in {s['index'] for s in snapshot['stories']}:
        raise ValueError('DOCUMENTATION_PLAN_STORY_MISSING')
    version = snapshot['modelVersion']
    schedules = {}
    for kind in sorted({e['nativeType'] for e in elements}):
        rows = [e for e in elements if e['nativeType'] == kind]
        schedules[kind] = {'status': 'BIM_FACTS_SPECIFICATION', 'modelVersion': version,
            'count': len(rows), 'rows': rows,
            'quantityAuthority': 'Existing IFC planar resultant BREP adapter; no gross box volumes',
            'nativeInteractiveScheduleRows': 'NOT_VERIFIED_NO_INSTALLED_ROW_READ_OR_CONFIGURE_CONTRACT'}
    return {'schema': 'APA_BIM_DOCUMENTATION_PACKAGE_V1', 'modelVersion': version,
        'plan': {'status': 'BIM_FACTS_WITH_NATIVE_CUT_FILLS', 'modelVersion': version,
            'storyIndex': plan_story, 'elements': [e for e in elements if e['storyIndex'] == plan_story]},
        'verticalGeometry': {'status': 'PREPARED_ACTUAL_3D_FACTS_NOT_A_NATIVE_DRAWING',
            'modelVersion': version, 'elements': elements},
        'specifications': schedules, 'nativeViews': native_views or {},
        'normativeAcceptance': 'NOT_PERFORMED'}


def compare_versions(before, after):
    left = {e['guid']: e for e in before['elements']}
    right = {e['guid']: e for e in after['elements']}
    changed = sorted(g for g in left.keys() & right.keys() if left[g] != right[g])
    return {'status': 'BIM_FACTS_UPDATED' if before['modelVersion'] != after['modelVersion'] else 'BIM_FACTS_UNCHANGED',
        'beforeVersion': before['modelVersion'], 'afterVersion': after['modelVersion'],
        'changedGuids': changed,
        'changedNativeModelGuids': sorted(g for g in left.keys() & right.keys()
            if left[g]['bodySignature'] != right[g]['bodySignature']),
        'changedDrawingFactGuids': sorted(g for g in left.keys() & right.keys()
            if left[g]['floorPlanPolygons'] != right[g]['floorPlanPolygons']),
        'addedGuids': sorted(right.keys() - left.keys()),
        'removedGuids': sorted(left.keys() - right.keys()),
        'nativeDrawingRegeneration': 'REQUIRES_NATIVE_REBUILD_AND_INDEPENDENT_READBACK'}


def read_database(api, guid):
    rows = api('GetDatabaseIdFromNavigatorItemId',
        {'navigatorItemIds': [{'navigatorItemId': {'guid': guid}}]}).get('databases')
    if not isinstance(rows, list) or len(rows) != 1 or 'error' in rows[0]:
        raise ValueError('DOCUMENTATION_NATIVE_DATABASE_UNAVAILABLE')
    return rows[0]


def create_view(writer, scene_id, source_guid, name, source_hash,
                retained_signatures, authorization_ref, saved_sha256):
    """Save an associative view of the existing native database, never 2D copies."""
    database = read_database(writer.api, source_guid)
    params = {'viewsData': [{'navigatorItemId': {'guid': source_guid}, 'name': name}]}
    def verify(reply, _):
        guid = native_response('CreateViewsInViewMap', reply)
        tree = writer.api('GetNavigatorItemTree', {'navigatorMapId': 'PublicViewMap'})
        rows = [r for r in flatten(tree) if item_guid(r) == guid]
        actual = read_database(writer.api, guid)
        if len(rows) != 1 or actual != database:
            raise ValueError('DOCUMENTATION_VIEW_SOURCE_DATABASE_MISMATCH')
        return {'status': 'NATIVE_ASSOCIATIVE_VIEW_PASS', 'view': rows[0],
                'database': actual, 'sourceDatabase': database}
    return execute_operation(writer, scene_id, 'CreateViewsInViewMap', params,
        source_hash, retained_signatures, verify, authorization_ref, saved_sha256=saved_sha256)


def create_viewpoint(writer, scene_id, command, data, floor_navigator_guid,
                     source_hash, retained_signatures, authorization_ref, saved_sha256):
    if command not in {'CreateSections', 'CreateInteriorElevations'}:
        raise ValueError('DOCUMENTATION_UNSUPPORTED_VIEWPOINT_CREATOR')
    kind = 'SectionItem' if command == 'CreateSections' else 'InteriorElevationItem'
    before = {item_guid(r) for r in flatten(writer.api('GetNavigatorItemTree', {'navigatorMapId': 'ProjectMap'}))}
    def verify(reply, _):
        guid = native_response(command, reply)
        rows = [r for r in flatten(writer.api('GetNavigatorItemTree', {'navigatorMapId': 'ProjectMap'}))
            if r.get('type') == kind and item_guid(r) not in before and not r.get('children')]
        if len(rows) != 1:
            raise ValueError('DOCUMENTATION_NEW_VIEWPOINT_NOT_UNIQUE')
        return {'status': 'NATIVE_DOCUMENTATION_VIEWPOINT_PASS', 'markerGuid': guid,
            'viewpoint': rows[0], 'database': read_database(writer.api, item_guid(rows[0])),
            'cutLineMemoReadback': 'NOT_VERIFIED_NO_INSTALLED_CONTRACT'}
    return execute_operation(writer, scene_id, command, {SLOTS[command]: [data]},
        source_hash, retained_signatures, verify, authorization_ref,
        saved_sha256=saved_sha256, activate_navigator_id=floor_navigator_guid, expected_window='FloorPlan')


def refresh_package(writer, run_id, floor_view_guid, plan_story, guids, views,
                    retained_signatures, authorization_ref, saved_sha256):
    """Rebuild native vertical databases and refresh one shared model package.

    Caller provides already approved view IDs and exact building membership.
    Existing SceneWriter serializes all native operations, including navigation.
    New run IDs are required; never automatically replay an unknown result.
    """
    native = capture_full_model(writer.api, retained_signatures)
    guids = [g.lower() for g in guids]
    bundle(make_snapshot(native, guids), plan_story)  # Validate membership/story before writes.
    selected_signatures = C.retained_geometry_signatures(native, guids)
    all_signatures = {**retained_signatures, **selected_signatures}
    source_hash = RUN.digest(all_signatures)
    native_views = {}
    for label, view in views.items():
        if view['windowType'] not in {'Section', 'Elevation', 'InteriorElevation'}:
            raise ValueError('DOCUMENTATION_EXPLICIT_VERTICAL_NATIVE_WINDOW_REQUIRED')
        def verify(_, prior, v=view):
            database = read_database(writer.api, v['guid'])
            rb = writer.api('GetSectionElements', {'databases': [database]})
            if not isinstance(rb.get('sectionElements'), list) or any(
                    r.get('success') is not True for r in rb.get('executionResultForDatabases', [])):
                raise ValueError('DOCUMENTATION_NATIVE_OWNER_READBACK_UNAVAILABLE')
            return {'status': 'NATIVE_DATABASE_REGENERATION_PASS', 'database': database, 'readback': rb}
        result = execute_operation(writer, run_id + '-' + label, 'RebuildView', {'regenerate': True},
            source_hash, all_signatures, verify, authorization_ref, saved_sha256=saved_sha256,
            activate_navigator_id=view['guid'], expected_window=view['windowType'])
        if result['status'] != 'PASS':
            raise ValueError('DOCUMENTATION_REGENERATION_UNKNOWN_OUTCOME_STOP')
        rb = result['readback']
        owners = {r['ownerElementId']['guid'].lower() for r in rb['readback']['sectionElements']}
        native_views[label] = {**view, **rb, 'selectedModelOwnerGuids': sorted(owners & set(guids)),
            'coverage': 'NATIVE_SELECTED_GEOMETRY_PRESENT' if owners & set(guids) else 'NATIVE_VIEW_EMPTY_OR_OUTSIDE_SELECTED_BUILDING',
            'verticalDrawingCoordinates': 'NOT_VERIFIED_NO_INSTALLED_2D_PRIMITIVE_EXPORT_CONTRACT'}
    captured = {}
    def floor_readback(_, prior):
        if (writer.api('GetCurrentWindowType', {}).get('currentWindowType') != 'FloorPlan' or
                writer.api('GetStories', {}).get('actStory') != plan_story):
            raise ValueError('DOCUMENTATION_NATIVE_FLOOR_STORY_MISMATCH')
        raw = writer.api('GetDetailsOfElements', {'elements': [{'elementId': {'guid': g}} for g in guids],
            'fields': ['type', 'floorIndex', 'details', 'floorPlanPolygons']}).get('detailsOfElements')
        if not isinstance(raw, list) or len(raw) != len(guids) or any('error' in r for r in raw):
            raise ValueError('DOCUMENTATION_NATIVE_FLOOR_FACTS_INCOMPLETE')
        snapshot = make_snapshot(native, guids, dict(zip(guids, raw)))
        for value in native_views.values(): value['modelVersion'] = snapshot['modelVersion']
        captured['snapshot'] = snapshot
        captured['package'] = bundle(snapshot, plan_story, native_views)
        return {'status': 'NATIVE_FLOOR_FACTS_PASS', 'modelVersion': snapshot['modelVersion'],
                'nativeCutFillCount': sum(bool(r.get('floorPlanPolygons')) for r in raw)}
    result = execute_operation(writer, run_id + '-floor', 'ChangeWindow',
        {'navigatorItemId': {'guid': floor_view_guid}}, source_hash, all_signatures,
        floor_readback, authorization_ref, saved_sha256=saved_sha256)
    if result['status'] != 'PASS':
        raise ValueError('DOCUMENTATION_FLOOR_CAPTURE_UNKNOWN_OUTCOME_STOP')
    return {**captured, 'status': 'NATIVE_DOCUMENTATION_DATA_REFRESH_PASS',
        'floorReadback': result['readback']}


def write_package(package, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'documentation.json').write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    for kind, spec in package['specifications'].items():
        with (output / (kind + '.csv')).open('w', encoding='utf-8-sig', newline='') as f:
            columns = ['guid', 'nativeType', 'count', 'storyIndex', 'storyElevationMeters',
                'referenceGeometry', 'resultantBoundsMeters', 'materials', 'relationships',
                'quantities', 'modelVersion']
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in spec['rows']:
                writer.writerow({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row.get(k), (dict, list))
                    else package['modelVersion'] if k == 'modelVersion' else row.get(k) for k in columns})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-dump', type=Path, required=True)
    p.add_argument('--guids', type=Path, required=True, help='JSON list of native GUIDs; no inferred building membership')
    p.add_argument('--story', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    native = C.G.normalize_dump(json.loads(args.native_dump.read_text(encoding='utf8')))
    selected = json.loads(args.guids.read_text(encoding='utf8'))
    package = bundle(make_snapshot(native, selected), args.story)
    write_package(package, args.output)
    print(json.dumps({'status': 'DOCUMENTATION_FACTS_WRITTEN', 'modelVersion': package['modelVersion'],
        'nativeViewsCreated': 0, 'specifications': {k: s['count'] for k, s in package['specifications'].items()}}))


if __name__ == '__main__':
    main()
