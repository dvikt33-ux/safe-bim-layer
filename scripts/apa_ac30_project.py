"""Bind an authored APA design to the existing DynamicCommands workflow."""
from __future__ import annotations

from copy import deepcopy

from apa_ac29_save_isolation import require, sha256
from apa_release import read_json
import archicad_project_accelerator as APA
from archicad_native_stair_connection import prepare_ac30_stair, read_ac30_stair
from apa_project_design import changes_between, compile_design_for_tapir2
from archicad_authored_extension import plan_parameter_operations


RUN = APA.RUN
CREATES = {'CreateWalls', 'CreateSlabs', 'CreateDoors', 'CreateWindows', 'CreateStairs'}


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


def bind_design(recipe, native_stories, read, router):
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

    names = {recipe['slabMaterial'], *recipe['wallMaterials'].values()}
    materials = {name: RUN.resolve_basic_slab_material(read, name) for name in sorted(names)}
    for step in graph['operations']:
        params, = next(iter(step['params'].values()))
        if 'floorIndex' in params:
            params['floorIndex'] = story_map[params['floorIndex']]
        if step['command'] == 'CreateSlabs':
            params.update(structureType='Basic', buildingMaterialId={'guid': materials[recipe['slabMaterial']]})
        if step['id'] in recipe['wallMaterials']:
            params['buildingMaterialId'] = {'guid': materials[recipe['wallMaterials'][step['id']]]}

    checked = APA.SCENE.GRAPH.compile_graph(router.catalog, graph, runtime_version='2.0.0')
    require(checked['status'] == 'PLAN_VALIDATED_OFFLINE', 'AC30_BOUND_PROJECT_GRAPH_INVALID')
    native_graph = deepcopy(graph)
    for step in native_graph['operations']:
        if step['command'] in {'CreateDoors', 'CreateWindows'}:
            params, = next(iter(step['params'].values()))
            parent = params['ownerWallId']['guid']['$createdGuid']
            params['ownerWallId']['guid'] = {'$result': {'step': parent, 'pointer': '/elements/0/elementId/guid'}}
    return dict(graph=graph, workflow=router.prepare_workflow(native_graph), storyIndices=list(story_map.values()),
                materials=materials, boundGraphSha256=checked['sourcePlanHash'])


def read_created(job, step, params, guid, model):
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
    material = row.get('buildingMaterialId', {}).get('guid')
    RUN.verify_readback(step['command'], params, RUN.requested_details(job.api, guid), owner_guid=owner,
                        expected_floor=floor, expected_slab_material_guid=material,
                        expected_story_level=story_level, slab_level_is_absolute=True)
    require(any(body['vertices'] for body in element['bodies']), 'AC30_PROJECT_CREATED_BREP_MISSING:' + guid)
    return set()


def verify_design(job, facts, model, guids):
    bound = {step['id']: {'guid': guids[step['id']], 'kind': APA.SCENE.GRAPH.CREATES[step['command']]}
             for step in facts['graph']['operations']}
    for step in facts['graph']['operations']:
        read_created(job, step, RUN.resolve_params(step, bound), guids[step['id']], model)


def execute_design(job, baseline, capture):
    facts = baseline['facts']
    original = baseline['signatures']
    owned = set()
    created = {}
    steps = {step['id']: step for step in facts['graph']['operations']}
    stories = [{'nativeIndex': s['index'], 'level': s['level']} for s in job.binding['stories']]

    def scopes(step, ticket, results):
        params = ticket['parameters']

        def before(api):
            # A preceding create may affect native joins. Check the host of a
            # new opening immediately before dispatch as well as at creation.
            if step['command'] in {'CreateDoors', 'CreateWindows'}:
                RUN.check_previous_wall(api, steps[step['id']], dict(created, __plan__=facts['graph']), stories)
            return {'status': 'AC30_PROJECT_STEP_SCOPE_PASS'}

        def after(reply, _):
            guid = RUN.created_guid(reply).lower()
            live, signatures = capture(job.api)
            new = set(signatures) - original.keys() - owned
            require(guid in new and (set(original) | owned) <= signatures.keys(),
                    'AC30_PROJECT_CREATED_GUID_OR_PRIOR_SCOPE_DRIFT')
            children = read_created(job, step, params, guid, live)
            require(new <= {guid, *children}, 'AC30_PROJECT_UNEXPLAINED_NATIVE_GUIDS')
            created[step['id']] = {'guid': guid, 'kind': APA.SCENE.GRAPH.CREATES[step['command']]}
            owned.update(new)
            return dict(status='AC30_PROJECT_STEP_READBACK_PASS', guid=guid, addedGuids=sorted(new))

        return dict(scene_id=job.scene_id('Project-' + RUN.digest(step['id'])[:12]), affected=sorted(owned),
                    retained_signatures=original, saved_sha256=job.disk_sha, authorization=job.authorization,
                    impact='MODEL', verify_before=before, verify_after=after)

    result = job.router.run_workflow(job.api, facts['workflow'], writer=job.writer, scopes=scopes)
    require(result['status'] == 'WORKFLOW_CALLABLE_VERIFIED', 'AC30_PROJECT_UNKNOWN_OUTCOME_NO_REPLAY')
    model, signatures = capture(job.api)
    require(set(signatures) == set(original) | owned
            and all(signatures[guid] == value for guid, value in original.items()),
            'AC30_PROJECT_BASELINE_DRIFT_BEFORE_SAVE')
    guids = {sid: row['guid'] for sid, row in created.items()}
    verify_design(job, facts, model, guids)
    return dict(status='AC30_PROJECT_NATIVE_READBACK_PASS', operationGuids=guids, addedGuids=sorted(owned),
                boundGraph=facts['graph'], signaturesSha256=RUN.digest(signatures))


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
