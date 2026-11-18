"""Bind an authored APA design to the existing DynamicCommands workflow."""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
import math

from apa_ac29_save_isolation import require, sha256
from apa_release import read_json
import archicad_bim_documentation as DOC
from archicad_connected_components import retained_geometry_signatures
import archicad_project_accelerator as APA
from apa_room_layout import resolve_zone_categories, verify_native_zone, verify_wall_body
from archicad_native_stair_connection import prepare_ac30_stair, read_ac30_stair
from archicad_strategy_discovery import source_data_hash
from apa_project_design import changes_between, compile_design_for_tapir2
from archicad_authored_extension import plan_parameter_operations


RUN = APA.RUN
WALL_ATTRIBUTE_READS = frozenset({'GetLayerOfElementDefaults', 'GetLayers', 'GetBuildingMaterials'})
CREATES = {'CreateWalls', 'CreateSlabs', 'CreateDoors', 'CreateWindows', 'CreateStairs'}
# Native main ID, subtype ID and revision ID of the built-in Elevation and Story markers.
_TEMPLATE_MARKERS = {
    '6a08ba99-6c84-4b6e-aa5a-c0caedc741a6': (
        '9fabbd06-d663-4519-809e-76e90e5a6ba5', 'f7b4967a-9e62-4392-b8dd-e93f566630f7'),
    '19225d34-ba38-44fe-baf2-94d57b069fc9': (
        '7a407b90-c976-40db-acd5-8c3142c93727', 'e96fc2e9-c3ab-4218-8265-dcddda27b34c'),
}


def verify_empty_model(api, native, selected):
    """Prove the floor-plan inventory without relying on 3D view filters."""
    require(type(native['nativeBodySlots']) is int and native['nativeBodySlots'] == 0
            and not native['unresolvedBodyOwners'], 'AC30_EMPTY_DUMP_UNVERIFIED')
    tree = api('GetNavigatorItemTree', {'navigatorMapId': 'ProjectMap'})
    story = DOC.source_view(tree, 'StoryItem')
    database = DOC.read_database(api, DOC.item_guid(story))
    require(RUN._GUID.fullmatch(database['databaseId']['guid']), 'AC30_EMPTY_FLOOR_DATABASE_UNVERIFIED')
    visible_inventory = set(APA.inventory_guids(api, database=database))
    full_inventory = APA.inventory_guids(api, database=database, include_sub_elements=True)
    nodes = {node['guid'].lower(): node for node in native['elements']}
    require(visible_inventory == selected and set(full_inventory) == nodes.keys(),
            'AC30_EMPTY_FLOOR_INVENTORY_MISMATCH')

    references = [{'elementId': {'guid': guid}} for guid in full_inventory]
    details = api('GetDetailsOfElements', {'elements': references})['detailsOfElements'] if references else []
    require(len(details) == len(references), 'AC30_EMPTY_ELEMENT_DETAILS_INCOMPLETE')
    roots, markers = set(), set()
    prototype_refs = {}
    for guid, detail in zip(full_inventory, details):
        node = nodes[guid]
        kind = node['type']
        require(detail.get('type') == kind and detail.get('floorIndex') == node['homeStory'],
                'AC30_EMPTY_ELEMENT_IDENTITY_UNVERIFIED: ' + guid)
        if kind in RUN._NONSPATIAL_TYPES:
            roots.add(guid)
            continue
        require(kind == 'Object', 'AC30_EMPTY_SPATIAL_ELEMENT_PRESENT: ' + guid)
        properties = detail['details']
        owner = (node['relationships'].get('ownerGuid') or '').lower()
        library = properties.get('libPart', {})
        part = library.get('ownUnID', {}).get('guid', '').lower()
        parent = library.get('parentUnID', {}).get('guid', '').lower()
        require(owner != '00000000-0000-0000-0000-000000000000' and RUN._GUID.fullmatch(owner)
                and owner == properties.get('ownerElementId', {}).get('guid', '').lower()
                and part in _TEMPLATE_MARKERS and parent == _TEMPLATE_MARKERS[part][0],
                'AC30_EMPTY_UNVERIFIED_LIBRARY_OBJECT: ' + guid)
        markers.add(guid)
        prototype_refs.setdefault(part, {'elementId': {'guid': guid}})
    require(roots == selected and markers == set(full_inventory) - selected,
            'AC30_EMPTY_FLOOR_CLASSIFICATION_MISMATCH')

    library_proof = []
    if prototype_refs:
        parts = api('GetLibraryPartScripts', {
            'libraryParts': list(prototype_refs.values()), 'scripts': ['3d'],
        })['libraryParts']
        require(len(parts) == len(prototype_refs), 'AC30_EMPTY_LIBRARY_SCRIPT_COVERAGE_INCOMPLETE')
        for part, row in zip(prototype_refs, parts):
            expected = '{' + part + '}-{' + _TEMPLATE_MARKERS[part][1] + '}'
            require(row.get('unID', '').lower() == expected
                    and row.get('scripts', {}).get('3d') == {'present': False},
                    'AC30_EMPTY_MARKER_REVISION_OR_3D_SCRIPT_UNVERIFIED: ' + part)
            library_proof.append({'libraryPartId': expected, 'has3DScript': False})
    return dict(status='AC30_EMPTY_FLOOR_PLAN_VERIFIED', database=database, nativeBodySlots=0,
                nativeElementCount=len(full_inventory), nonSpatialRootGuids=sorted(roots),
                libraryParts=library_proof, markerSignatures=retained_geometry_signatures(native, sorted(markers)))


def check_template_markers(model, expected):
    if expected:
        available = {row['guid'].lower() for row in model['elements']}
        require(expected.keys() <= available and retained_geometry_signatures(model, expected) == expected,
                'AC30_TEMPLATE_MARKER_READBACK_DRIFT')


def design_recipe(design, variant, router):
    report = compile_design_for_tapir2(design)
    brief = report['brief']
    chosen = next((row for row in report['variants'] if row['id'] == variant), None)
    require(chosen is not None and 'candidate' in chosen, 'AC30_PROJECT_VALID_VARIANT_REQUIRED')
    candidate = chosen['candidate']
    planned = chosen['tapir2Preview']
    graph = planned['graph']
    require(planned['compilation']['status'] == 'PLAN_VALIDATED_OFFLINE'
            and all(row['command'] in CREATES for row in graph['operations']),
            'AC30_PROJECT_GRAPH_CONTRACT_OR_ADAPTER_MISSING')
    require(not candidate.get('unresolvedWallCoordination') and not candidate.get('structuralFunctions'),
            'AC30_PROJECT_WALL_COORDINATION_OR_STRUCTURAL_ROLE_ADAPTER_REQUIRED')
    stairs = {link['stairOperationId']: prepare_ac30_stair(candidate, link['requirementId'], router.catalog)
              for link in candidate.get('stairConnections', []) if link['dimensionsMeetProjectLimits'] is True}
    require(set(candidate['requiredOpenIds']) <= {row['requirementId'] for row in stairs.values()}
            and {s['id'] for s in graph['operations'] if s['command'] == 'CreateStairs'} == stairs.keys(),
            'AC30_PROJECT_REQUIRED_DESIGN_CHECKS_OPEN')

    # Include physical thickness and cantilevered slabs in the approved placement envelope.
    levels = [row['level'] for row in brief['stories']]
    points = []
    for operation in graph['operations']:
        params, = next(iter(operation['params'].values()))
        match operation['command']:
            case 'CreateWalls':
                base = levels[params['floorIndex']] + params['zCoordinate']
                for point in (params['begCoordinate'], params['endCoordinate']):
                    for side, z in ((-.5, base), (.5, base + params['height'])):
                        points.append((point['x'] + side * params['thickness'],
                                       point['y'] + side * params['thickness'], z))
            case 'CreateSlabs':
                for point in params['polygonCoordinates']:
                    points += [(point['x'], point['y'], params['level'] - params['thickness']),
                               (point['x'], point['y'], params['level'])]
            case 'CreateStairs':
                stair = stairs[operation['id']]
                x0, y0, x1, y1 = stair['flightBounds']
                before, after = stair['landingDepthsM']
                points += [(x0, y0 - before, params['zCoordinate']),
                           (x1, y1 + after, params['zCoordinate'] + params['totalHeight'])]
    require(points, 'AC30_PROJECT_ENVELOPE_UNAVAILABLE')
    envelope = {axis + suffix: fn(point[i] for point in points)
                for i, axis in enumerate('xyz') for suffix, fn in (('Min', min), ('Max', max))}
    return dict(projectId=brief['projectId'], projectMode=brief['mode'], targetProjectPath=brief.get('targetProjectPath'),
                stories=brief['stories'], graph=graph, stairPlans=stairs, envelope=envelope,
                sourcePlanHash=planned['compilation']['sourcePlanHash'], variant=variant,
                planChecks=candidate['requirements'],
                slabMaterial=candidate['slabBasicMaterialName'],
                wallMaterials={k: v['materialName'] for k, v in candidate.get('wallCseBindings', {}).items()})


def wall_attributes(read, router, material_guids, layer_guid=None):
    """Read real intersection settings and pin the layer and material IDs."""
    def checked(command, params):
        router.prepare(command, params)
        return router.validate_result(command, read(command, params))

    if layer_guid is None:
        defaults, = checked('GetLayerOfElementDefaults', {'elementTypes': ['Wall']})['layersOfElementDefaults']
        require(defaults.get('elementType') == 'Wall' and 'layerId' in defaults, 'LAYOUT_NATIVE_WALL_LAYER_UNAVAILABLE')
        layer_guid = defaults['layerId']['guid']
    layer, = checked('GetLayers', {'attributeIds': [{'attributeId': {'guid': layer_guid}}]})['layers']
    require(layer.get('attributeId', {}).get('guid', '').lower() == layer_guid.lower()
            and type(layer.get('index')) is int and type(layer.get('intersectionGroupNr')) is int
            and layer['intersectionGroupNr'] > 0 and layer.get('isHidden') is False and layer.get('isLocked') is False,
            'LAYOUT_WALL_LAYER_INTERSECTION_NOT_QUALIFIED')
    requested = sorted({guid.lower() for guid in material_guids})
    rows = checked('GetBuildingMaterials', {'attributeIds': [
        {'attributeId': {'guid': guid}} for guid in requested]})['buildingMaterials']
    priorities = {}
    for row in rows:
        guid = row.get('attributeId', {}).get('guid', '').lower()
        require(guid in requested and guid not in priorities and type(row.get('connPriority')) is int,
                'LAYOUT_NATIVE_BUILDING_MATERIAL_PRIORITY_UNAVAILABLE')
        priorities[guid] = dict(name=row['name'], priority=row['connPriority'])
    require(set(priorities) == set(requested), 'LAYOUT_NATIVE_BUILDING_MATERIALS_INCOMPLETE')
    return dict(layer=dict(guid=layer_guid.lower(), index=layer['index'], name=layer['name'],
                           intersectionGroup=layer['intersectionGroupNr']), materials=priorities)


def bind_design(recipe, native_stories, read, router, *, layer_guid=None):
    graph = deepcopy(recipe['graph'])
    story_map = {}
    for i, story in enumerate(recipe['stories']):
        candidates = [row for row in native_stories if RUN.close(row['level'], story['level'])]
        require(len(candidates) == 1, 'AC30_PROJECT_UNIQUE_NATIVE_STORY_REQUIRED:' + story['id'])
        match = candidates[0]
        if story.get('existingNativeIndex') is not None:
            require(match['index'] == story['existingNativeIndex'] and match['floorId'] == story['existingFloorId']
                    and match['name'] == story['existingNativeLabel'], 'AC30_PROJECT_PINNED_STORY_DRIFT')
        story_map[i] = match['index']

    names = {recipe['slabMaterial'], *recipe['wallMaterials'].values()} - {None}
    materials = {name: RUN.resolve_basic_slab_material(read, name) for name in sorted(names)}
    joins = wall_attributes(read, router, materials.values(), layer_guid) if 'wallJunctions' in recipe else None
    categories = {}
    if any(step['command'] == 'CreateZones' for step in graph['operations']):
        rows = read('GetAttributesByType', {'attributeType': 'ZoneCategory'})['attributes']
        categories = resolve_zone_categories(recipe, rows)
    for step in graph['operations']:
        params, = next(iter(step['params'].values()))
        if 'floorIndex' in params:
            params['floorIndex'] = story_map[params['floorIndex']]
        if step['command'] == 'CreateSlabs':
            params.update(structureType='Basic', buildingMaterialId={'guid': materials[recipe['slabMaterial']]})
        if step['id'] in recipe['wallMaterials']:
            params['buildingMaterialId'] = {'guid': materials[recipe['wallMaterials'][step['id']]]}
            if joins is not None:
                params['layerIndex'] = joins['layer']['index']
        if step['command'] == 'CreateZones':
            room_id = step['id'].split('-zone-', 1)[1]
            params['categoryAttributeId'] = {'guid': categories[room_id]['guid']}

    checked = APA.SCENE.GRAPH.compile_graph(router.catalog, graph, runtime_version='2.0.0')
    require(checked['status'] == 'PLAN_VALIDATED_OFFLINE', 'AC30_BOUND_PROJECT_GRAPH_INVALID')
    native_graph = deepcopy(graph)
    for step in native_graph['operations']:
        if step['command'] in {'CreateDoors', 'CreateWindows'}:
            params, = next(iter(step['params'].values()))
            parent = params['ownerWallId']['guid']['$createdGuid']
            params['ownerWallId']['guid'] = {'$result': {'step': parent, 'pointer': '/elements/0/elementId/guid'}}
    result = dict(graph=graph, workflow=router.prepare_workflow(native_graph), storyIndices=list(story_map.values()),
                  materials=materials, boundGraphSha256=checked['sourcePlanHash'])
    if categories:
        result['zoneCategories'] = categories
    if joins is not None:
        result['wallJunctionAttributes'] = joins
    return result


def select_layout_wall_workflow(facts, story_level, router, binding, evidence_ref):
    """Use discovery V2 on the already validated and model-bound Wall rows."""
    graph = deepcopy(facts['workflow']['graph'])
    walls = [step for step in graph['operations'] if step['command'] == 'CreateWalls']
    wall_ids = [step['id'] for step in walls]
    require(2 <= len(walls) <= 200 and all(set(step.get('after', [])) <= set(wall_ids) for step in walls),
            'LAYOUT_WALL_BATCH_HAS_EXTERNAL_DEPENDENCIES_OR_UNSUPPORTED_SIZE')
    targets = []
    for step in walls:
        row, = step['params']['wallsData']
        target = dict(type='Wall', familySignature=RUN.digest(row), storyIndex=row['floorIndex'],
                      storyElevation=story_level, anchor=dict(row['begCoordinate'], z=story_level + row['zCoordinate']),
                      sourceRef=evidence_ref + '#' + step['id'], nativeCreateData=row)
        target['sourceVerification'] = dict(status='SOURCE_VERIFIED', evidenceRef=target['sourceRef'],
                                             dataHash=source_data_hash(target))
        targets.append(target)
    require(router.registration.get('CreateWalls') is True, 'LAYOUT_WALL_COMMAND_NOT_RUNTIME_REGISTERED')
    selection = APA.prepare_auto_optimized_native_task(router, {
        'schemaVersion': 'apa-native-auto/2', 'request': 'Создать проектные стены R02',
        'existing': [], 'targets': targets, 'benchmarks': {},
    })
    selected = selection.get('selectedNativeTaskPreview')
    require(selected is not None and selection.get('nativeWritePermission') is False,
            'LAYOUT_WALL_DISCOVERY:' + selection['status'])
    batch, = selected['workflow']['graph']['operations']
    require(batch['command'] == 'CreateWalls' and batch['params']['wallsData'] ==
            [target['nativeCreateData'] for target in targets], 'LAYOUT_SELECTED_WALL_BATCH_CHANGED_INPUTS')

    indexes = {wall_id: i for i, wall_id in enumerate(wall_ids)}
    operations = [batch]
    for step in graph['operations']:
        if step['id'] in indexes:
            continue
        step['after'] = list(dict.fromkeys(batch['id'] if dep in indexes else dep
                                          for dep in step.get('after', [])))
        if step['command'] in {'CreateDoors', 'CreateWindows'}:
            row, = next(iter(step['params'].values()))
            host = row['ownerWallId']['guid']['$result']
            if host['step'] in indexes:
                host.update(step=batch['id'], pointer=f"/elements/{indexes[host['step']]}/elementId/guid")
        operations.append(step)
    workflow = router.prepare_workflow({'operations': operations})
    discovery = selection['discovery']
    receipt = dict(
        schema='APA_R02_WALL_STRATEGY_V1', requestSchema='apa-room-layout/1',
        source=evidence_ref, project=binding['path'], runtime=binding['runtime'],
        archicadBuild=binding['archicadBuild'], tapirVersion=binding['tapirVersion'],
        addonSha256=binding['addonSha256'], catalogueSha256=router.fingerprint,
        capabilities={name: {'cataloguePresent': name in router.catalog['commands'],
                             'registered': router.registration.get(name)}
                      for name in ('CreateWalls', 'MoveElements', 'CreateGroups', 'CreateHotlinkInstances')},
        wallContractSha256=router.contract_hash('CreateWalls'),
        selectedStrategyId=selection['selectedStrategyId'], method=selection['selectionMethod'],
        discoverySchema=discovery['schema'], catalogueCommandCount=discovery['catalogCommandCount'],
        calibrationStatus=selection['calibrationStatus'],
        candidates=[
            dict(command='CreateWalls', mode='ONE_WALL_PER_CALL', plannedNativeCalls=len(walls),
                 qualification='SAME_TYPED_GRAPH_VALIDATED', elapsedMs='NOT_MEASURED'),
            dict(command='CreateWalls', mode='WALLS_DATA_ARRAY', plannedNativeCalls=1,
                 qualification=selection['status'], elapsedMs='NOT_MEASURED'),
        ],
        rejected=discovery['rejectedStrategies'] + [
            dict(command='CreateGroups', reason='GROUPING_REQUIRES_EXISTING_MEMBERS_AND_DOES_NOT_CREATE_WALLS'),
            dict(command='CreateHotlinkInstances', reason='NO_QUALIFIED_DONOR_AND_EDITABLE_LOCAL_WALLS_REQUIRED'),
            dict(command='Rectangle Wall (GUI)', reason='NO_SEPARATE_REGISTERED_COMMAND_IN_CHECKED_CATALOGUE'),
        ],
        plannedWorkflowCalls=len(operations), previousSingleWorkflowCalls=len(graph['operations']),
        workflowSha256=workflow['sourcePlanHash'], targetWorkloadSha256=discovery['benchmarkWorkloadHash'],
        optimumStatus='OPTIMUM_NOT_PROVEN', elapsedMs='NOT_MEASURED',
        fallback='SEPARATE_REVIEW_BEFORE_DISPATCH_ONLY', automaticRetry=False,
        requiredEvidence=['AC30_BATCH_READBACK', 'SAVE_CLOSE_REOPEN', 'COMPARABLE_NATIVE_END_TO_END_TIMINGS'],
    )
    facts.update(workflow=workflow, wallStrategy=receipt, wallBatch={'step': batch['id'], 'members': wall_ids})


def read_created(job, step, params, guid, model, zone_facts=None):
    row, = next(iter(params.values()))
    nodes = {e['guid'].lower(): e for e in model['elements']}
    require(guid in nodes, 'AC30_PROJECT_CREATED_GUID_MISSING')
    element = nodes[guid]
    if step['command'] == 'CreateStairs':
        source = job.recipe['stairPlans'][step['id']]
        upper = [s['index'] for s in job.binding['stories']
                 if RUN.close(s['level'], row['zCoordinate'] + row['totalHeight'])]
        require(len(upper) == 1, 'AC30_PROJECT_STAIR_UPPER_STORY_DRIFT')
        proof = read_ac30_stair(job.read, guid, dict(source, operation=dict(step, params=params)),
                                [row['floorIndex'], upper[0]])
        return set(proof['childGuids'])
    owner = row.get('ownerWallId', {}).get('guid')
    floor = nodes[owner.lower()]['homeStory'] if owner else row['floorIndex']
    story_level = next((s['level'] for s in job.binding['stories'] if s['index'] == floor), None)
    require(story_level is not None and element['homeStory'] == floor, 'AC30_PROJECT_NATIVE_STORY_DRIFT')
    details = RUN.requested_details(job.api, guid)
    if step['command'] == 'CreateZones':
        require(element['type'] == 'Zone', 'LAYOUT_NATIVE_ZONE_TYPE_DRIFT')
        quantities, = job.read('GetQuantitiesOfElements', {'elements': [{'elementId': {'guid': guid}}]})[
            'quantitiesOfElements']
        measurement = verify_native_zone(row, details, quantities, story_level)
        room_id = step['id'].split('-zone-', 1)[1]
        require(measurement['measuredAreaM2'] + 1e-9 >= job.recipe['roomFacts'][room_id]['minAreaM2'],
                'LAYOUT_NATIVE_ROOM_MINIMUM_AREA')
        if zone_facts is not None:
            zone_facts[step['id']] = dict(measurement, guid=guid)
        return set()
    material = row.get('buildingMaterialId', {}).get('guid')
    RUN.verify_readback(step['command'], params, details, owner_guid=owner,
                        expected_floor=floor, expected_slab_material_guid=material,
                        expected_story_level=story_level, slab_level_is_absolute=True)
    require(any(body['vertices'] for body in element['bodies']), 'AC30_PROJECT_CREATED_BREP_MISSING:' + guid)
    if job.kind == 'layout' and step['command'] == 'CreateWalls':
        verify_wall_body(row, element, story_level + row['zCoordinate'], joined='wallJunctions' in job.recipe)
    return set()


def verify_design(job, facts, model, guids):
    bound = {step['id']: {'guid': guids[step['id']], 'kind': APA.SCENE.GRAPH.CREATES[step['command']]}
             for step in facts['graph']['operations']}
    zones = {}
    for step in facts['graph']['operations']:
        read_created(job, step, RUN.resolve_params(step, bound), guids[step['id']], model, zones)
    return zones


def editable_details(api, guids):
    ids = sorted(guids)
    proof = {}
    for offset in range(0, len(ids), 200):
        chunk = ids[offset:offset + 200]
        response = api('GetDetailsOfElements', {
            'elements': [{'elementId': {'guid': guid}} for guid in chunk],
            'fields': ['elementId', 'type', 'id', 'floorIndex', 'layerIndex', 'libraryPartUnId',
                       'infoString', 'details'],
        })
        rows = response.get('detailsOfElements') if isinstance(response, dict) else None
        require(isinstance(rows, list) and len(rows) == len(chunk), 'LAYOUT_RETAINED_DETAILS_INCOMPLETE')
        for guid, row in zip(chunk, rows):
            require(isinstance(row, dict) and not row.get('error') and isinstance(row.get('type'), str),
                    'LAYOUT_RETAINED_DETAILS_IDENTITY_DRIFT')
            identity = row.get('elementId')
            # GetDetailsOfElements can wrap its selected elementId in an ElementIdArrayItem.
            if isinstance(identity, dict) and identity.keys() == {'elementId'}:
                identity = identity['elementId']
            reported = identity['guid'] if isinstance(identity, dict) and identity.keys() == {'guid'} else None
            require(isinstance(reported, str) and RUN._GUID.fullmatch(reported)
                    and reported.lower() == guid.lower(), 'LAYOUT_RETAINED_DETAILS_IDENTITY_DRIFT')
            proof[guid] = dict(row, elementId={'guid': reported.lower()})
    return proof


def retained_details_digest(api, guids):
    """Fingerprint editable fields so geometry parity alone cannot pass retention."""
    return RUN.digest(editable_details(api, guids))


def wall_system_geometry(walls, native_by_step, joints, priorities, top, openings=()):
    """Verify actual BREP against the complete straight Basic Wall system."""
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union
    from archicad_authored_geometry import horizontal_caps, shared_surfaces

    tolerance = 0.001
    shafts = {}
    for sid, row in walls.items():
        line = [(row[k]['x'], row[k]['y']) for k in ('begCoordinate', 'endCoordinate')]
        shafts[sid] = LineString(line).buffer(row['thickness'] / 2, cap_style='flat')
    expected = unary_union(list(shafts.values())).difference(unary_union(list(openings)))
    measured = {sid: horizontal_caps(native_by_step[sid], top) for sid in walls}
    actual = unary_union(list(measured.values()))
    require(expected.difference(actual.buffer(tolerance)).is_empty, 'LAYOUT_WALL_JUNCTION_BREP_GAP')
    require(actual.difference(expected.buffer(tolerance)).is_empty, 'LAYOUT_WALL_JUNCTION_BREP_PROTRUSION')
    for a, b in combinations(measured.values(), 2):
        require(a.intersection(b).buffer(-tolerance / 2).is_empty, 'LAYOUT_WALL_JUNCTION_DOUBLE_BODY')
    contacts = shared_surfaces(native_by_step, {sid: sid for sid in walls}, vertical_only=True)
    areas = {tuple(c['guids']): c['sharedAreaSquareMeters'] for c in contacts}
    proofs = []
    for joint in joints:
        left, right = joint['walls']
        pair = ':' + left + ':' + right
        x, y = (p / 1000 for p in joint['pointMM'])
        core = shafts[left].intersection(shafts[right])
        require(core.area > 0 and core.buffer(tolerance).covers(Point(x, y)),
                'LAYOUT_WALL_JUNCTION_EXPECTED_CORE_MISSING' + pair)
        area = areas.get(tuple(sorted((left, right))), 0)
        require(area > tolerance ** 2, 'LAYOUT_WALL_JUNCTION_NO_SHARED_BREP_FACE' + pair)
        winner = None
        if priorities[left] != priorities[right]:
            winner = max((left, right), key=priorities.__getitem__)
            require(core.difference(measured[winner].buffer(tolerance)).is_empty,
                    'LAYOUT_WALL_JUNCTION_MATERIAL_PRIORITY_DRIFT' + pair)
        proofs.append(dict(joint, sharedAreaM2=area, materialPriorities=[priorities[left], priorities[right]],
                           higherPriorityWall=winner))
    return dict(status='WALL_JUNCTION_BREP_CHECK_PASS', toleranceMM=1, measuredCapZM=top, joints=proofs,
                expectedCapAreaM2=expected.area, actualCapAreaM2=actual.area,
                visualAndEngineeringAcceptance='PENDING_USER_NATIVE_TEST')


def verify_layout_wall_system(job, facts, model, guids, *, region='experiment', openings_created=True):
    settings = facts['wallJunctionAttributes']
    current = wall_attributes(job.api, job.router, settings['materials'], settings['layer']['guid'])
    require(current == settings, 'LAYOUT_WALL_INTERSECTION_ATTRIBUTES_CHANGED')
    graph = facts['graph']['operations']
    walls = {s['id']: s['params']['wallsData'][0] for s in graph if s['command'] == 'CreateWalls'}
    found = {e['guid'].lower(): e for e in model['elements']}
    entities = {sid: found[guids[sid]] for sid in walls}
    rows = editable_details(job.api, {guids[sid] for sid in walls})
    orders, priorities, tops = {}, {}, set()
    for sid, wall in walls.items():
        row = rows[guids[sid]]
        expected = wall['buildingMaterialId']['guid'].lower()
        details = row['details']
        require(row.get('layerIndex') == settings['layer']['index']
                and details.get('buildingMaterialId', {}).get('guid', '').lower() == expected
                and type(details.get('junctionSequence')) is int, 'LAYOUT_WALL_JUNCTION_ATTRIBUTE_READBACK_DRIFT')
        orders[sid] = details['junctionSequence']
        priorities[sid] = settings['materials'][expected]['priority']
        tops.add(job.recipe['stories'][0]['level'] + wall['zCoordinate'] + wall['height'])
    require(len(tops) == 1, 'LAYOUT_WALL_JUNCTION_REQUIRES_COMMON_TOP')
    openings = []
    if openings_created:
        from shapely.geometry import LineString

        for step in graph:
            if step['command'] != 'CreateDoors':
                continue
            door, = step['params']['doorsData']
            host = walls[door['ownerWallId']['guid']['$createdGuid']]
            if door['sillHeight'] + door['height'] < host['height'] - 1e-6:
                continue
            start, end = host['begCoordinate'], host['endCoordinate']
            length = math.hypot(end['x'] - start['x'], end['y'] - start['y'])
            offsets = (door['centerOffset'] - door['width'] / 2, door['centerOffset'] + door['width'] / 2)
            opening_axis = [tuple(start[k] + (end[k] - start[k]) * offset / length for k in 'xy')
                            for offset in offsets]
            openings.append(LineString(opening_axis).buffer(host['thickness'] / 2, cap_style='flat'))
    return dict(wall_system_geometry(walls, entities, job.recipe['wallJunctions'][region], priorities,
                                     next(iter(tops)), openings),
                junctionOrder=orders, attributes=settings)


def transferable_fields(row):
    # Position and host identity are proved separately against the translated
    # graph. Archicad generates new element identifiers for native copies.
    moved = {
        'Wall': {'begCoordinate', 'endCoordinate', 'polygonOutline'},
        'Door': {'ownerElementId'},
        'Zone': {'polygonOutline', 'referencePosition', 'stampPosition'},
    }
    return dict(type=row['type'], floorIndex=row.get('floorIndex'), layerIndex=row.get('layerIndex'),
                libraryPartUnId=row.get('libraryPartUnId'), infoString=row.get('infoString'),
                details={key: value for key, value in row['details'].items() if key not in moved[row['type']]})


def verify_layout_inclusion(job, saved, model, signatures):
    """Match a user-copied fragment by typed geometry, properties and new GUIDs."""
    old = saved['signatures']
    require(old.keys() <= signatures.keys() and all(signatures[guid] == sig for guid, sig in old.items()),
            'LAYOUT_INCLUSION_CHANGED_EXISTING_GEOMETRY')
    previous = saved['operationReadback']
    markers = previous.get('templateMarkerSignatures', {})
    details = editable_details(job.api, set(signatures) | markers.keys())
    require(RUN.digest({guid: details[guid] for guid in set(old) | markers.keys()})
            == previous['retainedDetailsAfterExperiment'],
            'LAYOUT_INCLUSION_CHANGED_EXISTING_PARAMETERS')
    verify_design(job, {'graph': previous['boundGraph']}, model, previous['operationGuids'])

    recipe = dict(job.recipe, graph=job.recipe['inclusionGraph'],
                  wallMaterials={name.replace('exp-', 'accept-', 1): value
                                 for name, value in job.recipe['wallMaterials'].items()})
    source_system = previous.get('wallSystem')
    layer_guid = source_system['attributes']['layer']['guid'] if source_system else None
    bound = bind_design(recipe, job.binding['stories'], job.api, job.router, layer_guid=layer_guid)
    steps = bound['graph']['operations']
    new = set(signatures) - old.keys()
    require(len(new) == len(steps), 'LAYOUT_INCLUSION_UNEXPECTED_GUID_COUNT')
    types = {row['guid'].lower(): row['type'] for row in model['elements']}
    created, remaining = {}, set(new)
    for step in steps:
        kind = APA.SCENE.GRAPH.CREATES[step['command']]
        params = RUN.resolve_params(step, created)
        matching = []
        for guid in sorted(remaining):
            if types[guid] != kind:
                continue
            try:
                read_created(job, step, params, guid, model)
            except ValueError:
                continue
            matching.append(guid)
        require(len(matching) == 1, 'LAYOUT_INCLUSION_MISSING_OR_AMBIGUOUS:' + step['id'])
        guid, = matching
        created[step['id']] = {'guid': guid, 'kind': kind}
        remaining.remove(guid)
    require(not remaining, 'LAYOUT_INCLUSION_UNEXPLAINED_GUIDS')
    operation_guids = {name: row['guid'] for name, row in created.items()}
    for name, guid in operation_guids.items():
        source = previous['operationGuids']['exp-' + name.removeprefix('accept-')]
        require(transferable_fields(details[guid]) == transferable_fields(details[source]),
                'LAYOUT_INCLUSION_EDITABLE_PARAMETERS_DRIFT:' + name)
    proof = dict(operationGuids=operation_guids, roomReadback=verify_design(job, bound, model, operation_guids),
                 retainedGuidCount=len(old), addedGuidCount=len(new), copyTranslationMM=job.recipe['copyTranslationMM'],
                 signaturesSha256=RUN.digest(signatures), savedOriginalSha256=saved['savedSha256'],
                 inclusionGraphSha256=recipe['inclusionGraphSha256'])
    if source_system:
        require(bound['wallJunctionAttributes'] == source_system['attributes'],
                'LAYOUT_WALL_INTERSECTION_ATTRIBUTES_CHANGED')
        proof['wallSystem'] = verify_layout_wall_system(job, bound, model, operation_guids, region='acceptance')
    return proof


def execute_design(job, baseline, capture):
    facts = baseline['facts']
    original = baseline['signatures']
    owned = set()
    created = {}
    steps = {step['id']: step for step in facts['graph']['operations']}
    batch = facts.get('wallBatch', {})
    stories = [{'nativeIndex': s['index'], 'level': s['level']} for s in job.binding['stories']]
    empty_proof = facts.get('verifiedEmptyModel')
    template_markers = empty_proof['markerSignatures'] if empty_proof else {}
    empty_rechecked = False

    def verify_before_first_create(api, native, selected):
        nonlocal empty_rechecked
        proof = verify_empty_model(api, native, selected)
        require(proof == empty_proof, 'AC30_APPROVED_EMPTY_FLOOR_PLAN_DRIFT')
        empty_rechecked = True
        return proof

    def scopes(step, ticket, results):
        params = ticket['parameters']
        is_batch = step['id'] == batch.get('step')

        def before(api):
            if empty_proof and not created:
                require(empty_rechecked, 'AC30_APPROVED_EMPTY_FLOOR_PLAN_DRIFT')
            # A preceding create may affect native joins. Check the host of a
            # new opening immediately before dispatch as well as at creation.
            if step['command'] in {'CreateDoors', 'CreateWindows'}:
                RUN.check_previous_wall(api, steps[step['id']], dict(created, __plan__=facts['graph']), stories)
            return {'status': 'AC30_PROJECT_STEP_SCOPE_PASS'}

        def after(reply, _):
            live, signatures = capture(job.api)
            check_template_markers(live, template_markers)
            new = set(signatures) - original.keys() - owned
            if is_batch:
                guids = [RUN.created_guid({'elements': [row]}).lower() for row in reply['elements']]
                require(new == set(guids) and (set(original) | owned) <= signatures.keys(),
                        'LAYOUT_BATCH_GUID_SCOPE_DRIFT')
                for sid, guid in zip(batch['members'], guids, strict=True):
                    item = steps[sid]
                    read_created(job, item, item['params'], guid, live)
                    created[sid] = {'guid': guid, 'kind': 'Wall'}
                if 'wallJunctions' in job.recipe:
                    verify_layout_wall_system(job, facts, live, {sid: row['guid'] for sid, row in created.items()},
                                              openings_created=False)
                owned.update(new)
                return dict(status='LAYOUT_WALL_BATCH_READBACK_PASS', addedGuids=sorted(new))
            guid = RUN.created_guid(reply).lower()
            require(guid in new and (set(original) | owned) <= signatures.keys(),
                    'AC30_PROJECT_CREATED_GUID_OR_PRIOR_SCOPE_DRIFT')
            children = read_created(job, step, params, guid, live)
            require(new <= {guid, *children}, 'AC30_PROJECT_UNEXPLAINED_NATIVE_GUIDS')
            created[step['id']] = {'guid': guid, 'kind': APA.SCENE.GRAPH.CREATES[step['command']]}
            owned.update(new)
            return dict(status='AC30_PROJECT_STEP_READBACK_PASS', guid=guid, addedGuids=sorted(new))

        return dict(scene_id=job.scene_id('Project-' + RUN.digest(step['id'])[:12]), affected=sorted(owned),
                    retained_signatures=original, saved_sha256=job.disk_sha, authorization=job.authorization,
                    impact='MODEL', verify_before=before, verify_after=after, batch=is_batch)

    result = job.router.run_workflow(job.api, facts['workflow'], writer=job.writer, scopes=scopes,
                                     verify_empty=verify_before_first_create if empty_proof else None)
    require(result['status'] == 'WORKFLOW_CALLABLE_VERIFIED', 'AC30_PROJECT_UNKNOWN_OUTCOME_NO_REPLAY')
    model, signatures = capture(job.api)
    require(set(signatures) == set(original) | owned
            and all(signatures[guid] == value for guid, value in original.items()),
            'AC30_PROJECT_BASELINE_DRIFT_BEFORE_SAVE')
    guids = {sid: row['guid'] for sid, row in created.items()}
    zones = verify_design(job, facts, model, guids)
    proof = dict(status='AC30_PROJECT_NATIVE_READBACK_PASS', operationGuids=guids, addedGuids=sorted(owned),
                 boundGraph=facts['graph'], signaturesSha256=RUN.digest(signatures),
                 templateMarkerSignatures=template_markers)
    if job.kind == 'layout':
        require(retained_details_digest(job.api, set(original) | template_markers.keys()) == facts['retainedDetailsSha256'],
                'LAYOUT_EXPERIMENT_CHANGED_EXISTING_PARAMETERS')
        proof.update(roomReadback=zones, zoneCategories=facts['zoneCategories'], regions=job.recipe['regions'],
                     routes=job.recipe['routes'],
                     roomDependencies=job.recipe['roomDependencies'], masonryChecks=job.recipe['masonryChecks'],
                     copyTranslationMM=job.recipe['copyTranslationMM'],
                     retainedDetailsAfterExperiment=retained_details_digest(job.api, set(signatures) | template_markers.keys()),
                     inclusionMode='USER_COPY_THEN_READBACK', normativeApplicability='NOT_VERIFIED')
        if batch:
            proof.update(wallStrategy=facts['wallStrategy'], executionTrace=result['trace'])
        if 'wallJunctions' in job.recipe:
            proof['wallSystem'] = verify_layout_wall_system(job, facts, model, guids)
    return proof


def update_recipe(previous, accepted, updated, new_design, source):
    old = previous.recipe
    require(sha256(old['design']) == old['designSha256'], 'AC30_ORIGINAL_BRIEF_CHANGED')
    impact = changes_between(read_json(old['design']), new_design, old['variant'])
    require(updated['stories'] == old['stories'] and updated['slabMaterial'] == old['slabMaterial']
            and updated['wallMaterials'] == old['wallMaterials']
            and updated['stairPlans'] == old['stairPlans'], 'AC30_UPDATE_REQUIRES_UNCHANGED_STORIES_AND_SYSTEMS')
    if updated['targetProjectPath']:
        require(updated['targetProjectPath'] == str(source), 'AC30_UPDATE_BRIEF_TARGET_DRIFT')
    created = {sid: {'guid': guid} for sid, guid in accepted['operationReadback']['operationGuids'].items()}
    edits = plan_parameter_operations(old['graph'], updated['graph'], created)
    require(len(edits) == 1 and edits[0]['command'] == 'ModifyWindows'
            and set(edits[0]['parameters']['windowsWithDetails'][0]) == {'elementId', 'width'},
            'AC30_UPDATE_CURRENT_SCOPE_ONE_EXISTING_WINDOW_WIDTH')
    change = edits[0]
    window = next(step for step in old['graph']['operations'] if step['id'] == change['id'])
    host = window['params']['windowsData'][0]['ownerWallId']['guid']['$createdGuid']
    updated.update(kind='update', change=change, impact=impact,
                   operationGuids={sid: entry['guid'] for sid, entry in created.items()},
                   affectedGuids=sorted([created[host]['guid'], created[change['id']]['guid']]),
                   sourceSignaturesSha256=accepted['signaturesSha256'],
                   beforeGraph=accepted['operationReadback']['boundGraph'],
                   previousDocumentation=accepted['bimSnapshot'])
    return updated


def execute_update(job, baseline, capture):
    recipe = job.recipe
    change = recipe['change']
    affected = recipe['affectedGuids']
    original = baseline['signatures']
    retained = {guid: signature for guid, signature in original.items() if guid not in affected}

    def before(api):
        live, signatures = capture(api)
        require(signatures == original, 'AC30_UPDATE_BASELINE_DRIFT')
        verify_design(job, {'graph': recipe['beforeGraph']}, live, recipe['operationGuids'])
        return {'status': 'AC30_UPDATE_BASELINE_PASS'}

    def after(reply, prior):
        status, = reply['executionResults']
        require(status.get('success') is True, 'AC30_UPDATE_UNCONFIRMED_BY_NATIVE')
        live, signatures = capture(job.api)
        require(set(signatures) == set(original) and all(signatures[g] == v for g, v in retained.items())
                and all(signatures[g] != original[g] for g in affected),
                'AC30_UPDATE_AFFECTED_OR_RETAINED_BREP_UNVERIFIED')
        facts = baseline['facts']
        verify_design(job, facts, live, recipe['operationGuids'])
        return dict(status='AC30_PROJECT_UPDATE_READBACK_PASS', operationGuids=recipe['operationGuids'],
                    addedGuids=[], modifiedGuids=affected, boundGraph=facts['graph'],
                    signaturesSha256=RUN.digest(signatures))

    result = job.dispatch('Update-Window', change['command'], change['parameters'], affected, retained, after, before)
    require(result['status'] == 'PASS', 'AC30_UPDATE_UNKNOWN_OUTCOME_NO_REPLAY')
    return result['readback']
