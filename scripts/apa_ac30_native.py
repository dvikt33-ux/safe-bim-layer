"""Guarded AC30 project and acceptance jobs over the shared SceneWriter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from uuid import uuid4

from jsonschema import ValidationError

import apa_ac30_wall_preflight as WALL
import apa_ac30_project as PROJECT
from apa_ac29_reusable_native_copy import GuardedSaveTransport
from apa_ac29_save_isolation import (
    ScratchWriteLease, confirm_project_closed, copy_exclusive, preserve_guarded_save,
    require, reservation_owner_exited, sha256, write_new_json,
)
from apa_r03_mailbox import listener, open_test_port
import archicad_bim_documentation as DOC
import archicad_connected_components as GEOMETRY
from archicad_native_api import native_command
from archicad_native_stair_connection import prepare_ac30_stair, read_ac30_stair
import archicad_project_accelerator as APA
from archicad_tapir_catalog import load_for_runtime
from archicad_tapir_profile import exact_file
from apa_release import read_json


RUN = APA.RUN
SCHEMA = 'APA_AC30_NATIVE_JOB_V1'
RUNTIME = {'archicadVersion': 30, 'tapirVersion': '2.0.0'}
QUERY_READS = frozenset({
    'GetFavoritesByType', 'Get3DGeometryOfElements', 'GetGroupsOfElements',
    'GetElementsOfGroups', 'GetSuspendGroupsMode', 'GetDetailsOfElements',
    'GetSubelementsOfHierarchicalElements',
})
PROJECT_INVENTORY_READS = frozenset({
    'GetNavigatorItemTree', 'GetDatabaseIdFromNavigatorItemId', 'GetLibraryPartScripts',
})
POLICIES = {
    'CreateStairs': ('CREATE', 'MODEL', 'ExtendedElementCommands.cpp'),
    'CreateWalls': ('CREATE', 'MODEL', 'ExtendedElementCommands.cpp'),
    'CreateSlabs': ('CREATE', 'MODEL', 'ElementCreationCommands.cpp'),
    'CreateDoors': ('CREATE', 'MODEL', 'ExtendedElementCommands.cpp'),
    'CreateWindows': ('CREATE', 'MODEL', 'ExtendedElementCommands.cpp'),
    'ModifyWindows': ('MODIFY', 'MODEL', 'ExtendedElementCommands.cpp'),
    'ModifyWalls': ('MODIFY', 'MODEL', 'ExtendedElementCommands.cpp'),
    'SetSuspendGroupsMode': ('MODIFY', 'PROJECT', 'ElementGroupingCommands.cpp'),
    'SaveProject': ('TRANSACTION', 'PROJECT', 'ProjectCommands.cpp'),
}


def stage(args):
    job = args.job.absolute()
    source, addon = (exact_file(str(p.absolute())) for p in (args.source, args.addon))
    require(source.suffix.lower() == '.pln' and addon.suffix.lower() == '.apx'
            and sha256(source) == args.source_sha and sha256(addon) == args.addon_sha,
            'AC30_FIXTURE_OR_APX_BYTES_MISMATCH')
    require(re.fullmatch(r'[a-f0-9]{40}', args.source_revision)
            and re.fullmatch(r'[a-f0-9]{64}', args.build_identity), 'AC30_APX_STAMP_REQUIRED')
    binary = addon.read_bytes()
    require(all(value.encode('ascii') in binary for value in (args.source_revision, args.build_identity)),
            'AC30_APX_STAMP_NOT_IN_PINNED_FILE')
    router, catalog_sha = load_for_runtime({}, RUNTIME)
    if args.action == 'stage-stair':
        from apa_project_design import compile_design

        intent = exact_file(str(args.design.absolute()))
        report = compile_design(read_json(intent))
        variant = next((row for row in report['variants'] if row['id'] == args.variant), None)
        require(variant is not None and 'candidate' in variant, 'AC30_VALID_DESIGN_VARIANT_REQUIRED')
        recipe = prepare_ac30_stair(variant['candidate'], args.requirement, router.catalog)
        recipe.update(kind='stair', design=str(intent), designSha256=sha256(intent), variant=args.variant)
    elif args.action in {'stage-project', 'stage-update'}:
        intent = exact_file(str(args.design.absolute()))
        current = read_json(intent)
        recipe = PROJECT.design_recipe(current, args.variant, router)
        if args.action == 'stage-update':
            previous = Job(args.prior_job)
            accepted = previous.accepted_project()
            require(previous.project == source and previous.recipe['variant'] == args.variant,
                    'AC30_UPDATE_REQUIRES_EXACT_ACCEPTED_SOURCE_AND_VARIANT')
            recipe = PROJECT.update_recipe(previous, accepted, recipe, current, source)
        else:
            require(recipe['projectMode'] == 'GENERATE_FROM_ZERO', 'AC30_PROJECT_CREATE_REQUIRES_NEW_PROJECT_BRIEF')
            recipe['kind'] = 'project'
        recipe.update(design=str(intent), designSha256=sha256(intent))
    else:
        candidate = read_json(args.candidate)
        require(candidate['originalSha256'] == args.source_sha, 'AC30_WALL_CANDIDATE_SOURCE_DRIFT')
        wall, group = (candidate[key].lower() for key in ('wallGuid', 'groupGuid'))
        before, after = (candidate[key] for key in ('observedBaselineHeight', 'candidateHeight'))
        require(RUN._GUID.fullmatch(wall) and RUN._GUID.fullmatch(group)
                and RUN.close(before, before) and RUN.close(after, after)
                and min(before, after) > 0 and not RUN.close(before, after), 'AC30_WALL_SCOPE_INVALID')
        recipe = dict(kind='wall', wall=wall, group=group, before=before, after=after)
        router.prepare('ModifyWalls', wall_parameters(recipe))
    require(job.resolve() == job and job.parent.is_dir(), 'AC30_JOB_DIRECTORY_MUST_BE_NEW_AND_LOCAL')
    job.mkdir()
    (job / 'model').mkdir()
    project = job / 'model' / ('APA-AC30-' + recipe['kind'] + '-test.pln')
    copy_exclusive(source, project)
    require(sha256(project) == sha256(source) == args.source_sha, 'AC30_TEST_COPY_BYTES_MISMATCH')
    manifest = dict(schema=SCHEMA, project=str(project), source=str(source), initialSha256=args.source_sha,
                    addon=str(addon), addonSha256=args.addon_sha, sourceRevision=args.source_revision,
                    buildIdentity=args.build_identity, archicadBuild=args.build, catalogSha256=catalog_sha,
                    recipe=recipe)
    write_new_json(job / 'job.json', manifest)
    return dict(status='STAGED', job=str(job), project=str(project), nativeWrites=0,
                executionPermission=False, manifestSha256=sha256(job / 'job.json'))


def wall_parameters(recipe):
    return {'wallsWithDetails': [{'elementId': {'guid': recipe['wall']}, 'height': recipe['after']}]}


def capture(api, *, verify_empty=None):
    guids = APA.inventory_guids(api)
    options = {'verify_empty': verify_empty} if verify_empty is not None else {}
    model = DOC.capture_full_model(api, guids, **options)
    require(not model.get('unresolvedBodyOwners'), 'AC30_NATIVE_BREP_OWNER_UNVERIFIED')
    signatures = GEOMETRY.retained_geometry_signatures(model, guids)
    return model, signatures


class Job:
    def __init__(self, path):
        self.path = path.resolve(strict=True)
        self.manifest_path = exact_file(str(self.path / 'job.json'))
        self.manifest_sha = sha256(self.manifest_path)
        m = self.manifest = read_json(self.manifest_path)
        self.recipe = m['recipe']
        self.kind = self.recipe['kind']
        self.project = exact_file(m['project'])
        self.source = exact_file(m['source'])
        self.addon = exact_file(m['addon'])
        require(m['schema'] == SCHEMA and self.kind in {'stair', 'wall', 'project', 'update'}
                and self.project == self.path / 'model' / f'APA-AC30-{self.kind}-test.pln'
                and self.project != self.source, 'AC30_EXACT_JOB_COPY_REQUIRED')
        self.disk_sha = m['initialSha256']
        self.lease = None
        self.verification_directory = self.path
        self.verification_project = self.project
        self.router, catalog_sha = load_for_runtime({}, RUNTIME)
        require(m['catalogSha256'] == catalog_sha, 'AC30_JOB_CATALOG_DRIFT')
        if self.kind == 'project':
            self.writes = {step['command'] for step in self.recipe['graph']['operations']}
            require(self.writes <= PROJECT.CREATES, 'AC30_PROJECT_MUTATION_NOT_APPROVED')
        elif self.kind == 'update':
            require(self.recipe['change']['command'] == 'ModifyWindows', 'AC30_UPDATE_MUTATION_NOT_APPROVED')
            self.writes = {'ModifyWindows'}
        else:
            self.writes = {'CreateStairs'} if self.kind == 'stair' else {'ModifyWalls', 'SetSuspendGroupsMode'}
        self.writes.add('SaveProject')
        for command in sorted(self.writes):
            kind, impact, file = POLICIES[command]
            revision = self.router.catalog['_metadata']['binding']['sourceRevision']
            self.router.review_policy(command, kind, impact, {
                'source': f'Tapir {revision}:archicad-addon/Sources/{file}',
                'sha256': self.router.contract_hash(command),
            })

    def check_files(self):
        m = self.manifest
        require(sha256(self.manifest_path) == self.manifest_sha
                and sha256(self.source) == m['initialSha256']
                and sha256(self.verification_project) == self.disk_sha
                and sha256(self.addon) == m['addonSha256'],
                'AC30_JOB_OR_PROTECTED_FILE_CHANGED')

    def connect(self, phase, execute=False):
        require(self.verification_project == self.project or (phase == 'reopen' and not execute),
                'AC30_SAVED_COPY_IS_READ_ONLY')
        self.check_files()
        self.port = open_test_port(self.verification_project)
        require(self.port is not None, 'AC30_EXACT_TEST_PLN_NOT_OPEN_OR_API_UNAVAILABLE')
        self.identity = listener(self.port, addon=self.addon)
        trace = self.verification_directory / (phase + '-' + uuid4().hex)
        trace.mkdir()
        native = lambda command, params: native_command(self.port, command, params, timeout=75,
                                                         max_response=64 * 1024 * 1024)
        self.api = APA.EvidenceAPI(native, trace, execute=execute)
        self.api.allowed |= QUERY_READS | {'API.IsAddOnCommandAvailable'}
        if self.kind == 'project':
            self.api.allowed |= PROJECT_INVENTORY_READS
        self.binding = self.guard()
        return self.binding

    def guard(self):
        self.check_files()
        if self.lease is not None:
            self.lease.verify()
            require(sha256(self.path / 'preflight.json') == self.approval_sha, 'AC30_APPROVAL_DRIFT')
        require(listener(self.port, addon=self.addon) == self.identity, 'AC30_JOB_LISTENER_CHANGED')
        info = self.api('GetProjectInfo', {})
        product = self.api('API.GetProductInfo', {})
        addon = self.api('GetAddOnVersion', {})
        runtime = self.api('GetAPARuntimeInfoV1', {})
        m = self.manifest
        target = self.verification_project
        require(info.get('projectPath') == str(target) and info.get('projectName') == target.stem
                and info.get('isTeamwork') is False and info.get('isUntitled') is False,
                'AC30_EXACT_JOB_COPY_NOT_OPEN')
        require(product.get('version') == 30 and product.get('buildNumber') == m['archicadBuild']
                and addon.get('version') == '2.0.0' and runtime.get('sdkMajor') == 30
                and runtime.get('contract') == 'APA_NATIVE_RUNTIME_IDENTITY_V1'
                and runtime.get('developerId') == 826567491 and runtime.get('localId') == 368333322
                and runtime.get('nativeModelWrites') == 0 and runtime.get('sourceRevision') == m['sourceRevision']
                and runtime.get('buildIdentity') == m['buildIdentity'], 'AC30_WRONG_LOADED_TAPIR_APX')
        stories = self.api('GetStories', {})['stories']
        indices = [row['index'] for row in stories]
        require(len(set(indices)) == len(indices)
                and all(type(row['index']) is int and type(row['floorId']) is int
                        and RUN.close(row['level'], row['level']) for row in stories),
                'AC30_NATIVE_STORIES_INVALID')
        return dict(path=str(target), name=target.stem, port=self.port, **RUNTIME,
                    archicadBuild=product['buildNumber'], addonSha256=m['addonSha256'], runtime=runtime,
                    listener=self.identity, stories=sorted(stories, key=lambda row: row['index']))

    def read(self, command, parameters=None):
        require(command in QUERY_READS, 'AC30_JOB_READ_COMMAND_NOT_ALLOWED')
        args = {} if parameters is None else parameters
        self.router.prepare(command, args)
        return self.router.validate_result(command, self.api(command, args))

    def probe(self):
        commands = {'GetProjectInfo', 'GetStories', 'GetAddOnVersion', 'GetAllElements', 'GetDetailsOfElements'}
        commands |= self.writes
        if self.kind in {'stair', 'project', 'update'}:
            commands |= {'GetFavoritesByType', 'Get3DBoundingBoxes', 'Get3DGeometryOfElements',
                         'GetSubelementsOfHierarchicalElements'}
            if self.kind in {'project', 'update'}:
                commands.add('GetAttributesByType')
        else:
            commands |= {'GetGroupsOfElements', 'GetElementsOfGroups', 'GetSuspendGroupsMode'}
        for command in sorted(commands):
            self.router.probe_runtime(self.api, command)
        for command in ('GetAPARuntimeInfoV1', 'GetModelDumpV1'):
            available = self.api('API.IsAddOnCommandAvailable', {'addOnCommandId': {
                'commandNamespace': 'TapirCommand', 'commandName': command}}).get('available')
            require(available is True, 'AC30_REQUIRED_APA_COMMAND_NOT_REGISTERED: ' + command)

    def stair_story_indices(self):
        data = self.recipe['operation']['params']['stairsData'][0]
        expected = (data['zCoordinate'], data['zCoordinate'] + data['totalHeight'])
        pairs = [[row['index'] for row in self.binding['stories'] if RUN.close(row['level'], z)] for z in expected]
        require(all(len(indices) == 1 for indices in pairs), 'AC30_STAIR_REQUIRES_BOTH_EXACT_STORY_LEVELS')
        lower, upper = [indices[0] for indices in pairs]
        indices = [row['index'] for row in self.binding['stories']]
        require(indices.index(upper) - indices.index(lower) == 1, 'AC30_STAIR_REQUIRES_ADJACENT_STORIES')
        return [lower, upper]

    def wall_facts(self, height, model):
        w = self.recipe
        fact = WALL.read_grouped_wall(self.read, w['wall'], w['group'], height)
        members = self.read('GetElementsOfGroups', {'groups': [{'groupId': {'guid': w['group']}}]})['elementsOfGroups']
        require(len(members) == 1, 'AC30_GROUP_EXACT_MEMBERSHIP_REQUIRED')
        ids = sorted(row['elementId']['guid'].lower() for row in members[0]['elements'])
        require(w['wall'] in ids and len(ids) == len(set(ids)), 'AC30_GROUP_EXACT_MEMBERSHIP_REQUIRED')
        row = next((row for row in model['elements'] if row['guid'].lower() == w['wall']), None)
        require(row is not None and row['type'] == 'Wall', 'AC30_WALL_NATIVE_IDENTITY_REQUIRED')
        z = [vertex[2] for body in row['bodies'] for vertex in body['vertices']]
        require(z and RUN.close(max(z) - min(z), height), 'AC30_WALL_BREP_HEIGHT_MISMATCH')
        return dict(fact, groupMembers=ids, zMin=min(z), zMax=max(z), floorIndex=row['homeStory'])

    def baseline(self):
        require(self.guard() == self.binding, 'AC30_JOB_BINDING_DRIFT')
        verify_empty = PROJECT.verify_empty_model if self.kind == 'project' else None
        model, signatures = capture(self.api, verify_empty=verify_empty)
        if self.kind == 'wall':
            facts = self.wall_facts(self.recipe['before'], model)
        elif self.kind in {'project', 'update'}:
            require(sha256(self.recipe['design']) == self.recipe['designSha256'], 'AC30_PROJECT_DESIGN_SOURCE_DRIFT')
            current = PROJECT.design_recipe(read_json(self.recipe['design']), self.recipe['variant'], self.router)
            require(all(self.recipe[key] == value for key, value in current.items()),
                    'AC30_STAGED_PROJECT_PLAN_DRIFT')
            facts = PROJECT.bind_design(self.recipe, self.binding['stories'], self.api, self.router)
            if self.recipe['stairPlans']:
                favorites = self.read('GetFavoritesByType', {'elementType': 'Stair'})['favorites']
                require(all(step['params']['stairsData'][0]['favoriteName'] in favorites
                            for step in facts['graph']['operations'] if step['command'] == 'CreateStairs'),
                        'AC30_STAIR_FAVORITE_MISSING_IN_TEST_PLN')
            if self.kind == 'project':
                box = self.recipe['envelope']
                facts['spatialScan'] = RUN.scan_for_existing_geometry(self.api, box['xMin'], box['yMin'], box)
                if 'verifiedEmptyModel' in model:
                    facts['verifiedEmptyModel'] = model['verifiedEmptyModel']
            else:
                require(RUN.digest(signatures) == self.recipe['sourceSignaturesSha256'],
                        'AC30_UPDATE_COPY_DIFFERS_FROM_ACCEPTED_MODEL')
                PROJECT.verify_design(self, {'graph': self.recipe['beforeGraph']}, model,
                                      self.recipe['operationGuids'])
                self.router.prepare(self.recipe['change']['command'], self.recipe['change']['parameters'])
                facts['change'] = self.recipe['change']
                facts['affectedGuids'] = self.recipe['affectedGuids']
        else:
            data = self.recipe['operation']['params']['stairsData'][0]
            native_indices = self.stair_story_indices()
            x0, y0, x1, y1 = self.recipe['flightBounds']
            before, after = self.recipe['landingDepthsM']
            envelope = {'xMin': x0, 'yMin': y0 - before, 'xMax': x1, 'yMax': y1 + after,
                        'zMin': data['zCoordinate'], 'zMax': data['zCoordinate'] + data['totalHeight']}
            require(data['favoriteName'] in self.read('GetFavoritesByType', {'elementType': 'Stair'})['favorites'],
                    'AC30_STAIR_FAVORITE_MISSING_IN_TEST_PLN')
            spatial = RUN.scan_for_existing_geometry(self.api, x0, y0, envelope)
            facts = {'storyIndices': native_indices, 'placementEnvelope': envelope,
                     'favoriteName': data['favoriteName'], 'spatialScan': spatial}
        require(self.guard() == self.binding, 'AC30_JOB_BINDING_DRIFT')
        return {'signatures': signatures, 'facts': facts}

    def preflight(self):
        self.unattempted()
        require(not (self.path / 'preflight.json').exists(), 'AC30_PREFLIGHT_ALREADY_EXISTS')
        self.connect('preflight')
        self.probe()
        baseline = self.baseline()
        record = dict(status='READY_FOR_EXPLICIT_TEST_RUN', manifestSha256=self.manifest_sha,
                      binding=self.binding, baseline=baseline, recipe=self.recipe,
                      modelWrites=self.api.write_attempts, executionPermission=False)
        require(record['modelWrites'] == 0, 'AC30_PREFLIGHT_MUST_BE_READ_ONLY')
        path = self.path / 'preflight.json'
        write_new_json(path, record)
        return dict(status=record['status'], preflight=str(path), confirmSha256=sha256(path),
                    target=self.binding['path'], port=self.port, facts=baseline['facts'],
                    elementCount=len(baseline['signatures']), modelWrites=0, executionPermission=False)

    def unattempted(self):
        require(not any((self.path / n).exists() for n in ('attempted.json', 'scene-v1-attempts.sqlite3'))
                and not self.project.with_name(self.project.name + '.apa-write.lock').exists(),
                'AC30_EXISTING_ATTEMPT_RECONCILE_WITH_READBACK_NO_REPLAY')

    def scene_id(self, scene):
        return 'AC30-' + self.manifest_sha[:20] + '-' + scene

    def dispatch(self, scene, command, params, affected, signatures, verify, before):
        return self.router.execute(self.writer, self.scene_id(scene),
                                   self.router.prepare(command, params), affected,
                                   signatures, self.disk_sha, self.authorization,
                                   POLICIES[command][1], verify, verify_before=before)

    def accept_stair(self, reply, baseline):
        guid = RUN.created_guid(reply).lower()
        result = read_ac30_stair(self.read, guid, self.recipe, baseline['facts']['storyIndices'])
        model, signatures = capture(self.api)
        known = set(baseline['signatures'])
        added = set(signatures) - known
        members = {guid, *result['childGuids']}
        owned = members | {row['guid'].lower() for row in model['elements']
                           if (row.get('relationships', {}).get('hostGuid') or '').lower() in members}
        require(guid in added and added <= owned
                and all(signatures.get(g) == value for g, value in baseline['signatures'].items()),
                'AC30_STAIR_ADDED_GUIDS_OR_RETAINED_BREP_UNVERIFIED')
        return dict(result, addedGuids=sorted(added), signaturesSha256=RUN.digest(signatures))

    def group_mode(self):
        mode = self.read('GetSuspendGroupsMode')['suspendGroups']
        require(type(mode) is bool, 'AC30_GROUP_MODE_UNKNOWN')
        return mode

    def set_group_mode(self, suffix, value, expected, signatures):
        def check_mode(mode):
            require(self.group_mode() is mode, 'AC30_GROUP_MODE_CHANGED')
            return {'status': 'AC30_GROUP_MODE_READBACK_PASS', 'suspendGroups': mode}

        result = self.dispatch(suffix, 'SetSuspendGroupsMode', {'suspendGroups': value}, [],
                               signatures, lambda *_: check_mode(value), lambda _: check_mode(expected))
        require(result['status'] == 'PASS', 'AC30_GROUP_MODE_UNVERIFIED_RECONCILE_NO_REPLAY')

    def modify_wall(self, baseline):
        wall = self.recipe['wall']
        retained = {g: value for g, value in baseline['signatures'].items() if g != wall}
        facts = baseline['facts']
        original_mode = facts['suspendGroupsBefore']

        def check_wall(height):
            model, current = capture(self.api)
            measured = self.wall_facts(height, model)
            require(set(current) == set(baseline['signatures']) and measured['groupMembers'] == facts['groupMembers']
                    and measured['floorIndex'] == facts['floorIndex'] and RUN.close(measured['zMin'], facts['zMin'])
                    and measured['suspendGroupsBefore'] is True, 'AC30_WALL_GEOMETRY_OR_GROUP_DRIFT')
            return dict(measured, status='AC30_GROUPED_WALL_READBACK_PASS', signaturesSha256=RUN.digest(current))

        try:
            if not original_mode:
                self.set_group_mode('Suspend', True, False, baseline['signatures'])
            result = self.dispatch('Wall', 'ModifyWalls', wall_parameters(self.recipe), [wall], retained,
                                   lambda *_: check_wall(self.recipe['after']),
                                   lambda _: check_wall(self.recipe['before']))
        finally:
            require(self.guard() == self.binding, 'AC30_GROUP_RESTORE_REQUIRES_SAME_PROJECT_AND_PROCESS')
            if self.group_mode() is not original_mode:
                _, observed = capture(self.api)
                self.set_group_mode('Restore', original_mode, not original_mode, observed)
        require(result['status'] == 'PASS', 'AC30_WALL_OUTCOME_UNKNOWN_NO_REPLAY')
        return dict(result['readback'], restoredSuspendGroups=original_mode)

    def execute(self, confirmation):
        approval_path = self.path / 'preflight.json'
        require(sha256(approval_path) == confirmation, 'AC30_EXACT_LOCAL_PREFLIGHT_CONFIRMATION_REQUIRED')
        approval = read_json(approval_path)
        require(approval.get('status') == 'READY_FOR_EXPLICIT_TEST_RUN'
                and approval.get('manifestSha256') == self.manifest_sha
                and approval.get('recipe') == self.recipe, 'AC30_PREFLIGHT_MANIFEST_OR_RECIPE_DRIFT')
        if (self.path / 'saved.json').exists():
            return dict(self.saved(), status='ALREADY_APPLIED', newNativeWrites=0)
        self.unattempted()
        self.connect('execute', execute=True)
        self.probe()
        baseline = self.baseline()
        require(self.binding == approval['binding'] and baseline == approval['baseline'],
                'AC30_APPROVED_LISTENER_OR_BASELINE_DRIFT')
        require(sha256(approval_path) == confirmation, 'AC30_PREFLIGHT_CHANGED_DURING_READBACK')
        self.authorization = 'LOCAL_OPERATOR_PREFLIGHT_SHA256:' + confirmation
        self.approval_sha = confirmation
        self.lease = ScratchWriteLease(self.project, self.path, self.disk_sha)
        self.lease.acquire()
        write_new_json(self.path / 'attempted.json', {'confirmSha256': confirmation, 'automaticReplay': False})
        self.writer = RUN.SceneWriter(self.api, self.path / 'scene-v1-attempts.sqlite3',
                                      dynamic_project_guard=self.guard)
        if self.kind == 'wall':
            proof = self.modify_wall(baseline)
        elif self.kind == 'project':
            proof = PROJECT.execute_design(self, baseline, capture)
        elif self.kind == 'update':
            proof = PROJECT.execute_update(self, baseline, capture)
        else:
            step = self.recipe['operation']
            params = json.loads(RUN.canonical(step['params']))
            params['stairsData'][0]['floorIndex'] = baseline['facts']['storyIndices'][0]
            result = self.dispatch('Stair', step['command'], params, [], baseline['signatures'],
                                   lambda reply, _: self.accept_stair(reply, baseline),
                                   lambda _: {'status': 'AC30_STAIR_BASELINE_PASS'}
                                   if self.baseline() == baseline else None)
            require(result['status'] == 'PASS', 'AC30_STAIR_OUTCOME_UNKNOWN_NO_REPLAY')
            proof = result['readback']
        return self.save(proof)

    def save(self, proof):
        model, signatures = capture(self.api)
        require(RUN.digest(signatures) == proof['signaturesSha256'], 'AC30_VERIFIED_RESULT_CHANGED_BEFORE_SAVE')
        PROJECT.check_template_markers(model, proof.get('templateMarkerSignatures', {}))

        def rebind(port, path, name, saved_sha, authorization):
            self.disk_sha = saved_sha

        guard = GuardedSaveTransport(self.api.transport, rebind, self.project, self.source,
                                     lambda: sha256(self.project), lambda: sha256(self.source),
                                     self.project.stem, self.port, self.authorization)
        self.api.transport = guard
        guard.enable_after_verified_copy()

        def before(api):
            self.lease.verify()
            current_model, current_signatures = capture(api)
            require(current_signatures == signatures, 'AC30_FINAL_BREP_CHANGED_BEFORE_SAVE')
            PROJECT.check_template_markers(current_model, proof.get('templateMarkerSignatures', {}))
            if self.kind == 'wall':
                require(self.group_mode() is proof['restoredSuspendGroups'], 'AC30_GROUP_MODE_CHANGED_BEFORE_SAVE')
            return {'status': 'AC30_FINAL_BREP_PASS'}

        def after(reply, _):
            self.lease.verify()
            require(reply == {'success': True} and guard.new_saved_sha == self.disk_sha,
                    'AC30_NATIVE_SAVE_UNCONFIRMED')
            snapshot = preserve_guarded_save(self.project, self.path / 'guarded-save.snapshot', self.disk_sha,
                                              {self.source: self.manifest['initialSha256']})
            write_new_json(self.path / 'snapshot.json', snapshot)
            return {'status': 'AC30_SAVED_BYTES_PASS', 'savedSha256': self.disk_sha}

        saved = self.dispatch('Save', 'SaveProject', {}, [], signatures, after, before)
        require(saved['status'] == 'PASS' and self.api.calls['SaveProject'] == 1,
                'AC30_SAVE_OUTCOME_UNKNOWN_NO_REPLAY')
        record = dict(status='SAVED_PENDING_REAL_REOPEN', manifestSha256=self.manifest_sha,
                      binding=self.binding, savedSha256=self.disk_sha, signatures=signatures,
                      operationReadback=proof, nativeSaveCalls=1,
                      snapshotSha256=sha256(self.path / 'snapshot.json'))
        write_new_json(self.path / 'saved.json', record)
        return record

    def sealed_save(self):
        record = read_json(self.path / 'saved.json')
        snapshot = read_json(self.path / 'snapshot.json')
        require(record['status'] == 'SAVED_PENDING_REAL_REOPEN' and record['nativeSaveCalls'] == 1
                and record['manifestSha256'] == self.manifest_sha
                and sha256(self.path / 'snapshot.json') == record['snapshotSha256']
                and snapshot['savedSHA256'] == record['savedSha256']
                and sha256(self.path / 'guarded-save.snapshot') == record['savedSha256'],
                'AC30_SAVED_PERSISTENCE_EVIDENCE_DRIFT')
        return record, snapshot

    def saved(self):
        record, _ = self.sealed_save()
        self.disk_sha = record['savedSha256']
        self.check_files()
        return record

    def confirm_closed(self, saved):
        pinned = saved['binding']['listener']
        port = pinned['port']
        if not reservation_owner_exited(pinned['pid']):
            require(listener(port, addon=self.addon) == pinned, 'AC30_CLOSE_PROCESS_IDENTITY_DRIFT')
            confirm_project_closed(lambda command, params: native_command(port, command, params))
        return self.close_receipt(saved)

    def close_receipt(self, saved):
        return dict(status='AC30_REAL_CLOSE_CONFIRMED', listener=saved['binding']['listener'],
                    savedReceiptSha256=sha256(self.path / 'saved.json'), nativeWrites=0)

    def closed(self):
        record = self.confirm_closed(self.saved())
        write_new_json(self.path / 'closed.json', record)
        return record

    def reopen_copy_lineage(self):
        saved, snapshot = self.sealed_save()
        preflight = self.path / 'preflight.json'
        approval = read_json(preflight)
        approval_sha = sha256(preflight)
        attempted = self.path / 'attempted.json'
        guarded = self.path / 'guarded-save.snapshot'
        require(approval.get('status') == 'READY_FOR_EXPLICIT_TEST_RUN'
                and approval.get('manifestSha256') == self.manifest_sha
                and approval.get('executionPermission') is False
                and approval.get('binding') == saved['binding']
                and read_json(attempted) == {'confirmSha256': approval_sha, 'automaticReplay': False}
                and saved['binding']['path'] == str(self.project)
                and saved['operationReadback']['signaturesSha256'] == RUN.digest(saved['signatures']),
                'AC30_SAVED_COPY_ATTEMPT_OR_APPROVAL_DRIFT')
        require(snapshot.get('schema') == 'APA_SAVE_EXACT_SNAPSHOT_V1'
                and snapshot.get('status') == 'BYTE_EXACT_GUARDED_SAVE_SNAPSHOT_CAPTURED'
                and snapshot.get('snapshot') == str(guarded)
                and snapshot.get('source') == str(self.project)
                and snapshot.get('snapshotSHA256') == saved['savedSha256']
                and snapshot.get('protectedSHA256') == {str(self.source): self.manifest['initialSha256']}
                and sha256(self.source) == self.manifest['initialSha256']
                and sha256(self.addon) == self.manifest['addonSha256'],
                'AC30_SAVED_COPY_PROTECTED_PROVENANCE_DRIFT')
        return saved, {
            'sourceJob': str(self.path), 'manifestSha256': self.manifest_sha,
            'preflightSha256': approval_sha, 'attemptReceiptSha256': sha256(attempted),
            'savedReceiptSha256': sha256(self.path / 'saved.json'),
            'snapshotReceiptSha256': saved['snapshotSha256'], 'savedSha256': saved['savedSha256'],
            'ledgerSha256': sha256(self.path / 'scene-v1-attempts.sqlite3'),
        }

    def stage_reopen_copy(self, directory):
        target = directory.resolve()
        require(target.parent.is_dir() and not target.exists() and not target.is_relative_to(self.path),
                'AC30_SAVED_COPY_REQUIRES_FRESH_DIRECTORY_OUTSIDE_JOB')
        saved, lineage = self.reopen_copy_lineage()
        close = self.confirm_closed(saved)
        original_sha = sha256(self.project)
        target.mkdir(exist_ok=False)
        project = target / self.project.name
        copy_exclusive(self.path / 'guarded-save.snapshot', project)
        require(sha256(project) == saved['savedSha256'] and sha256(self.project) == original_sha
                and self.reopen_copy_lineage()[1] == lineage, 'AC30_SAVED_COPY_SOURCE_OR_BYTES_DRIFT')
        record = dict(schema='APA_AC30_SAVED_REOPEN_COPY_V1', lineage=lineage, sourceClose=close,
                      sourceProjectSha256AtStage=original_sha, verificationProject=str(project),
                      automaticReplay=False, modelWrites=0)
        write_new_json(target / 'reopen-copy.json', record)
        return dict(record, status='SAVED_COPY_READY_FOR_REOPEN')

    def load_reopen_copy(self, directory):
        target = directory.resolve(strict=True)
        require(not target.is_relative_to(self.path), 'AC30_SAVED_COPY_REQUIRES_DIRECTORY_OUTSIDE_JOB')
        saved, lineage = self.reopen_copy_lineage()
        receipt_file = exact_file(str(target / 'reopen-copy.json'))
        proof = read_json(receipt_file)
        project = exact_file(str(target / self.project.name))
        require(proof.get('schema') == 'APA_AC30_SAVED_REOPEN_COPY_V1'
                and proof.get('lineage') == lineage and proof.get('sourceClose') == self.close_receipt(saved)
                and proof.get('verificationProject') == str(project)
                and proof.get('automaticReplay') is False and proof.get('modelWrites') == 0,
                'AC30_SAVED_COPY_RECEIPT_DRIFT')
        self.verification_directory = target
        self.verification_project = project
        self.disk_sha = lineage['savedSha256']
        self.check_files()
        return saved, {'verificationProject': str(project), 'copyReceiptSha256': sha256(receipt_file),
                       'savedReceiptSha256': lineage['savedReceiptSha256']}

    def verify_reopen_copy(self, directory):
        saved, source = self.load_reopen_copy(directory)
        return self.verify_reopened(saved, source)

    def reopened(self):
        saved = self.saved()
        closed = read_json(self.path / 'closed.json')
        require(closed == self.close_receipt(saved),
                'AC30_MATCHING_CLOSE_EVIDENCE_REQUIRED')
        return self.verify_reopened(saved)

    def verify_reopened(self, saved, source=None):
        receipt = self.verification_directory / 'reopened.json'
        require(not receipt.exists(), 'AC30_REOPEN_RECEIPT_ALREADY_EXISTS')
        now = self.connect('reopen')
        self.probe()
        expected = dict(saved['binding'], path=str(self.verification_project))
        stable = ('path', 'name', 'runtime', 'archicadBuild', 'stories', 'addonSha256')
        require(all(now[key] == expected[key] for key in stable), 'AC30_REOPEN_RUNTIME_OR_STORIES_DRIFT')
        model, signatures = capture(self.api)
        require(signatures == saved['signatures'], 'AC30_REOPEN_GUID_OR_BREP_DRIFT')
        previous = saved['operationReadback']
        if self.kind == 'stair':
            result = read_ac30_stair(self.read, previous['guid'], self.recipe, self.stair_story_indices())
            require(result == {k: v for k, v in previous.items() if k not in {'addedGuids', 'signaturesSha256'}},
                    'AC30_REOPEN_STAIR_DRIFT')
        elif self.kind in {'project', 'update'}:
            PROJECT.check_template_markers(model, previous.get('templateMarkerSignatures', {}))
            PROJECT.verify_design(self, {'graph': previous['boundGraph']}, model, previous['operationGuids'])
            result = previous
        else:
            result = self.wall_facts(self.recipe['after'], model)
            require(all(result[key] == previous[key] for key in ('wallGuid', 'groupMembers', 'actualHeight', 'zMin', 'zMax')),
                    'AC30_REOPEN_WALL_DRIFT')
        require(self.guard() == now and self.api.write_attempts == 0, 'AC30_REOPEN_NOT_READ_ONLY')
        record = dict(status='SAVE_REOPEN_VERIFIED', savedSha256=self.disk_sha, verifiedElementCount=len(signatures),
                      signaturesSha256=RUN.digest(signatures), operationReadback=result, verificationNativeWrites=0)
        if self.kind in {'project', 'update'}:
            guids = sorted(result['operationGuids'].values())
            details = {guid: RUN.requested_details(self.api, guid) for guid in guids}
            record['bimSnapshot'] = DOC.make_snapshot(model, guids, details)
            if self.kind == 'update':
                record['documentationChange'] = DOC.compare_versions(self.recipe['previousDocumentation'],
                                                                     record['bimSnapshot'])
            require(self.guard() == now and self.api.write_attempts == 0, 'AC30_DOCUMENTATION_CAPTURE_DRIFT')
        if source is not None:
            require(self.load_reopen_copy(self.verification_directory)[1] == source,
                    'AC30_SAVED_COPY_RECEIPT_DRIFT')
            record.update(source, status='SAVE_REOPEN_COPY_VERIFIED', verificationBinding=now)
        write_new_json(receipt, record)
        return record

    def accepted_project(self, reopen_copy=None):
        require(self.kind in {'project', 'update'}, 'AC30_PROJECT_JOB_REQUIRED')
        if reopen_copy is None:
            saved = self.saved()
            closed = read_json(self.path / 'closed.json')
            require(closed == self.close_receipt(saved), 'AC30_PROJECT_ACCEPTANCE_EVIDENCE_MISMATCH')
            status, lineage = 'SAVE_REOPEN_VERIFIED', {}
        else:
            saved, lineage = self.load_reopen_copy(reopen_copy)
            status = 'SAVE_REOPEN_COPY_VERIFIED'
        reopened = read_json(self.verification_directory / 'reopened.json')
        require(reopened.get('status') == status
                and all(reopened.get(key) == value for key, value in lineage.items())
                and reopened.get('savedSha256') == saved['savedSha256']
                and reopened.get('signaturesSha256') == RUN.digest(saved['signatures'])
                and reopened.get('verificationNativeWrites') == 0
                and reopened.get('operationReadback') == saved['operationReadback'],
                'AC30_PROJECT_ACCEPTANCE_EVIDENCE_MISMATCH')
        selected = set(saved['operationReadback']['operationGuids'].values())
        snapshot = reopened['bimSnapshot']
        require({row['guid']: row['bodySignature'] for row in snapshot['elements']}
                == {guid: saved['signatures'][guid] for guid in selected}
                and snapshot['modelVersion'] == RUN.digest({
                    'stories': snapshot['stories'],
                    'elementSignatures': {guid: saved['signatures'][guid] for guid in selected},
                }), 'AC30_PROJECT_BIM_SNAPSHOT_DRIFT')
        return reopened

    def documentation(self, output, story=None, *, reopen_copy=None):
        target = output.resolve()
        require(target.parent.is_dir() and not target.exists()
                and not target.is_relative_to(self.path), 'AC30_DOCUMENTATION_REQUIRES_NEW_OUTPUT_OUTSIDE_JOB')
        accepted = self.accepted_project(reopen_copy)
        snapshot = accepted['bimSnapshot']
        occupied = sorted({row['storyIndex'] for row in snapshot['elements']})
        require(story is None or story in occupied, 'AC30_DOCUMENTATION_STORY_OUTSIDE_MODEL')
        stories = occupied if story is None else [story]
        package = DOC.bundle(snapshot, stories[0])
        package['plansByStory'] = {str(i): DOC.bundle(snapshot, i)['plan'] for i in stories}
        package['savedPlnSha256'] = accepted['savedSha256']
        package['reopenedReceiptSha256'] = sha256(self.verification_directory / 'reopened.json')
        package['operationGuids'] = accepted['operationReadback']['operationGuids']
        if reopen_copy is not None:
            package['verificationProject'] = accepted['verificationProject']
        if self.kind == 'update':
            package['documentationChange'] = accepted['documentationChange']
        DOC.write_package(package, target)
        result = dict(status='REOPENED_ASSEMBLY_DOCUMENTATION_WRITTEN', modelVersion=package['modelVersion'],
                      savedPlnSha256=package['savedPlnSha256'],
                      reopenedReceiptSha256=package['reopenedReceiptSha256'],
                      stories=stories, elements=len(snapshot['elements']), nativeViews='NOT_TESTED',
                      publisherPdf='NOT_TESTED', files={p.name: sha256(p) for p in target.iterdir()})
        if reopen_copy is not None:
            result.update(verificationProject=accepted['verificationProject'], sourceJob=str(self.path),
                          savedReceiptSha256=accepted['savedReceiptSha256'])
        write_new_json(target / 'receipt.json', result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    authoring = ('stage-stair', 'stage-wall', 'stage-project', 'stage-update')
    reopen_copy = ('stage-reopen-copy', 'verify-reopen-copy')
    for action in (*authoring, 'preflight', 'execute', 'verify-closed', 'verify-reopen', *reopen_copy):
        sub = commands.add_parser(action)
        sub.add_argument('--job', type=Path, required=True)
        if action in authoring:
            for name in ('source', 'addon'):
                sub.add_argument('--' + name, type=Path, required=True)
                sub.add_argument('--' + name + '-sha', required=True)
            sub.add_argument('--source-revision', required=True)
            sub.add_argument('--build-identity', required=True)
            sub.add_argument('--build', type=int, required=True)
        if action in {'stage-stair', 'stage-project', 'stage-update'}:
            sub.add_argument('--design', type=Path, required=True)
            sub.add_argument('--variant', required=True)
        if action == 'stage-stair':
            sub.add_argument('--requirement', required=True)
        if action == 'stage-update':
            sub.add_argument('--prior-job', type=Path, required=True)
        if action == 'stage-wall':
            sub.add_argument('--candidate', type=Path, required=True)
        if action == 'execute':
            sub.add_argument('--confirm-preflight', required=True)
        if action in reopen_copy:
            sub.add_argument('--copy', type=Path, required=True, help='Каталог точной копии сохранения')
    args = parser.parse_args(argv)
    try:
        if args.action in authoring:
            result = stage(args)
        else:
            job = Job(args.job)
            if args.action == 'execute':
                result = job.execute(args.confirm_preflight)
            elif args.action == 'stage-reopen-copy':
                result = job.stage_reopen_copy(args.copy)
            elif args.action == 'verify-reopen-copy':
                result = job.verify_reopen_copy(args.copy)
            else:
                result = {'preflight': job.preflight, 'verify-closed': job.closed,
                          'verify-reopen': job.reopened}[args.action]()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, ValidationError) as exc:
        status = 'RECONCILIATION_REQUIRED' if (args.job / 'attempted.json').exists() else 'BLOCKED'
        print(json.dumps(dict(status=status, reason=str(exc), automaticReplay=False), ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
