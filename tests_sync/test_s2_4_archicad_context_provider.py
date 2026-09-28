"""S2.4 Archicad context provider. Offline only; no Archicad or PLN access."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from sync_bridge.archicad_context_provider import (
    ARCHICAD_CONTEXT_PROVIDER_STATUS,
    MAX_SELECTED_ELEMENTS,
    READ_COMMAND_ALLOWLIST,
    AllowlistedReadTransport,
    ArchicadContextProvider,
    ContextProviderError,
)
from sync_bridge.context import ContextService
from sync_bridge.identity import canonical_hash
from sync_bridge.store import BridgeStore
from tests_sync.closing import ClosingDirectory


GUID_WALL = 'B6eF0001-0000-0000-0000-000000000001'
GUID_OPENING = '{A0A00002-0000-0000-0000-000000000002}'
GUID_STAIR = 'C0C00003-0000-0000-0000-000000000003'


def request(request_id='R1', generation=1):
    return {
        'requestId': request_id,
        'instanceId': 'AC-A',
        'logicalProjectId': 'P1',
        'requestedScope': 'selection',
        'generation': generation,
    }


def wire(payload):
    return {'result': {'addOnCommandResponse': copy.deepcopy(payload)}}


class FakeReadTransport:
    def __init__(self, *, selected=None, details=None, stories=None, binding=None,
                 project_infos=None, failures=None, malformed=None):
        self.calls = []
        self.selected = list(selected if selected is not None else [GUID_WALL])
        self.details = copy.deepcopy(details or {
            GUID_WALL: {
                'type': 'Wall',
                'details': {'begCoordinate': {'x': 0.0, 'y': 0.0}, 'height': 3.0},
            },
        })
        self.stories = copy.deepcopy(stories or {
            'actStory': 1,
            'stories': [
                {'index': 1, 'name': 'First', 'level': 3.0},
                {'index': 0, 'name': 'Ground', 'level': 0.0},
            ],
        })
        self.binding_value = copy.deepcopy(binding or {
            'instanceId': 'AC-A',
            'logicalProjectId': 'P1',
            'applicationVersion': '29.0',
        })
        self.project_infos = copy.deepcopy(project_infos or [{
            'isUntitled': False,
            'isTeamwork': False,
            'projectPath': r'C:\Users\private-user\Projects\Secret.pln',
            'projectName': 'Secret',
        }])
        self.project_info_count = 0
        self.failures = failures or {}
        self.malformed = malformed or {}

    def binding(self):
        return copy.deepcopy(self.binding_value)

    def call(self, command, params):
        self.calls.append((command, copy.deepcopy(params)))
        if command in self.failures:
            raise self.failures[command]
        if command in self.malformed:
            return copy.deepcopy(self.malformed[command])
        if command == 'GetAddOnVersion':
            return wire({'version': '1.5.9'})
        if command == 'GetProjectInfo':
            index = min(self.project_info_count, len(self.project_infos) - 1)
            self.project_info_count += 1
            return wire(self.project_infos[index])
        if command == 'GetStories':
            return wire(self.stories)
        if command == 'GetSelectedElements':
            return wire({'elements': [
                {'elementId': {'guid': guid}} for guid in self.selected
            ]})
        if command == 'GetDetailsOfElements':
            guid = params['elements'][0]['elementId']['guid']
            return wire({'detailsOfElements': [copy.deepcopy(self.details[guid])]})
        raise AssertionError(f'unexpected fake command: {command}')


def capture(fake, *, max_selection=MAX_SELECTED_ELEMENTS):
    return ArchicadContextProvider(fake, max_selection=max_selection).capture(request())


class ArchicadContextProviderTests(unittest.TestCase):
    def test_real_provider_adapter_produces_deterministic_selection_snapshot(self):
        fake = FakeReadTransport()
        snapshot = capture(fake)
        self.assertEqual(snapshot['source'], 'archicad')
        self.assertEqual(snapshot['selection']['count'], 1)
        self.assertEqual(snapshot, capture(FakeReadTransport()))
        self.assertEqual(ARCHICAD_CONTEXT_PROVIDER_STATUS, 'IMPLEMENTED_NOT_LIVE_VERIFIED')

    def test_stories_are_sorted_by_factual_story_index(self):
        snapshot = capture(FakeReadTransport())
        self.assertEqual([story['index'] for story in snapshot['stories']], [0, 1])
        self.assertEqual([story['elevation'] for story in snapshot['stories']], [0.0, 3.0])

    def test_current_story_resolves_against_captured_stories(self):
        snapshot = capture(FakeReadTransport())
        self.assertEqual(snapshot['currentStory'], {
            'index': 1, 'name': 'First', 'elevation': 3.0})

    def test_unresolved_current_story_is_explicit_not_fabricated(self):
        fake = FakeReadTransport(stories={
            'actStory': 99,
            'stories': [{'index': 0, 'name': 'Ground', 'level': 0.0}],
        })
        current = capture(fake)['currentStory']
        self.assertEqual(current['status'], 'UNRESOLVED')
        self.assertEqual(current['index'], 99)

    def test_selected_guids_are_preserved_exactly(self):
        fake = FakeReadTransport(
            selected=[GUID_OPENING],
            details={GUID_OPENING: {'type': 'Opening', 'details': {'error': 'unsupported'}}},
        )
        self.assertEqual(capture(fake)['selection']['elements'][0]['guid'], GUID_OPENING)

    def test_selection_is_deterministic_regardless_of_api_return_order(self):
        details = {
            GUID_WALL: {'type': 'Wall', 'details': {'height': 3.0}},
            GUID_OPENING: {'type': 'Opening', 'details': {'error': 'unsupported'}},
        }
        first = capture(FakeReadTransport(
            selected=[GUID_WALL, GUID_OPENING], details=details))
        second = capture(FakeReadTransport(
            selected=[GUID_OPENING, GUID_WALL], details=details))
        self.assertEqual(first, second)
        self.assertEqual(
            [item['guid'] for item in first['selection']['elements']],
            sorted([GUID_WALL, GUID_OPENING], key=lambda value: (value.casefold(), value)))

    def test_same_semantic_state_has_same_s2_3_root_hash(self):
        details = {
            GUID_WALL: {'type': 'Wall', 'details': {'height': 3.0}},
            GUID_OPENING: {'type': 'Opening', 'details': {'error': 'unsupported'}},
        }
        providers = [
            ArchicadContextProvider(FakeReadTransport(
                selected=[GUID_WALL, GUID_OPENING], details=details)),
            ArchicadContextProvider(FakeReadTransport(
                selected=[GUID_OPENING, GUID_WALL], details=details)),
        ]
        hashes = []
        with ClosingDirectory() as directory:
            for index, provider in enumerate(providers):
                store = BridgeStore(Path(directory) / f'root-{index}.sqlite3')
                service = ContextService(store, lambda: '2026-09-29T00:00:00+00:00', provider)
                hashes.append(service.request(request())['rootHash'])
                store.close()
        self.assertEqual(hashes[0], hashes[1])

    def test_zero_selection_is_valid_and_empty(self):
        snapshot = capture(FakeReadTransport(selected=[]))
        self.assertEqual(snapshot['selection'], {'count': 0, 'elements': []})

    def test_selection_over_limit_fails_without_truncation_or_detail_reads(self):
        fake = FakeReadTransport(selected=[GUID_WALL, GUID_OPENING, GUID_STAIR])
        with self.assertRaises(ContextProviderError) as caught:
            capture(fake, max_selection=2)
        self.assertEqual(caught.exception.code, 'SELECTION_TOO_LARGE')
        self.assertNotIn('GetDetailsOfElements', [command for command, _ in fake.calls])

    def test_opening_details_are_explicitly_unsupported(self):
        fake = FakeReadTransport(
            selected=[GUID_OPENING],
            details={GUID_OPENING: {'type': 'Opening', 'details': {'width': 1.0}}},
        )
        element = capture(fake)['selection']['elements'][0]
        self.assertEqual(element['detailsStatus'], 'UNSUPPORTED')
        self.assertIsNone(element['details'])

    def test_stair_details_are_explicitly_unsupported(self):
        fake = FakeReadTransport(
            selected=[GUID_STAIR],
            details={GUID_STAIR: {'type': 'Stair', 'details': {'risers': 10}}},
        )
        element = capture(fake)['selection']['elements'][0]
        self.assertEqual(element['detailsStatus'], 'UNSUPPORTED')
        self.assertIsNone(element['details'])

    def test_beam_unreliable_dimensions_are_not_exposed_as_verified(self):
        guid = 'BEAM-1'
        fake = FakeReadTransport(
            selected=[guid],
            details={guid: {'type': 'Beam', 'details': {
                'profileId': {'guid': 'PROFILE'}, 'width': 0.4, 'height': 0.8,
                'isWidthAndHeightLinked': False, 'level': 0.0,
            }}},
        )
        element = capture(fake)['selection']['elements'][0]
        self.assertEqual(element['detailsStatus'], 'PARTIAL')
        self.assertNotIn('width', element['details'])
        self.assertNotIn('height', element['details'])

    def test_morph_closed_solid_semantics_are_not_inferred(self):
        guid = 'MORPH-1'
        fake = FakeReadTransport(
            selected=[guid],
            details={guid: {'type': 'Morph', 'details': {
                'surface': 'Surface', 'body': {'isClosed': False, 'vertices': []},
            }}},
        )
        element = capture(fake)['selection']['elements'][0]
        self.assertEqual(element['detailsStatus'], 'PARTIAL')
        self.assertNotIn('isClosed', element['details']['body'])

    def test_multiplane_roof_per_edge_gable_semantics_are_not_invented(self):
        guid = 'ROOF-1'
        fake = FakeReadTransport(
            selected=[guid],
            details={guid: {'type': 'Roof', 'details': {
                'roofClass': 'MultiPlane', 'polygonOutline': [],
                'gableEdges': [{'edge': 1, 'kind': 'Gable'}],
            }}},
        )
        element = capture(fake)['selection']['elements'][0]
        self.assertEqual(element['detailsStatus'], 'PARTIAL')
        self.assertNotIn('gableEdges', element['details'])

    def test_unsupported_element_does_not_invalidate_supported_element(self):
        details = {
            GUID_WALL: {'type': 'Wall', 'details': {'height': 3.0}},
            GUID_OPENING: {'type': 'Opening', 'details': {'error': 'unsupported'}},
            GUID_STAIR: {'type': 'Stair', 'details': {'error': 'unsupported'}},
        }
        snapshot = capture(FakeReadTransport(
            selected=[GUID_STAIR, GUID_WALL, GUID_OPENING], details=details))
        by_type = {item['type']: item for item in snapshot['selection']['elements']}
        self.assertEqual(snapshot['selection']['count'], 3)
        self.assertEqual(by_type['Wall']['detailsStatus'], 'SUPPORTED')
        self.assertEqual(by_type['Opening']['detailsStatus'], 'UNSUPPORTED')
        self.assertEqual(by_type['Stair']['detailsStatus'], 'UNSUPPORTED')

    def test_transport_failure_does_not_become_empty_valid_snapshot(self):
        fake = FakeReadTransport(failures={
            'GetSelectedElements': ConnectionError('offline'),
        })
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'transport.sqlite3')
            service = ContextService(
                store, lambda: '2026-09-29T00:00:00+00:00',
                ArchicadContextProvider(fake))
            with self.assertRaises(ContextProviderError) as caught:
                service.request(request())
            self.assertEqual(caught.exception.code, 'ARCHICAD_NOT_AVAILABLE')
            row = store.context_request('R1')
            self.assertIsNone(row['response'])
            self.assertEqual(row['state'], 'CAPTURING')
            self.assertEqual(store.pending_outbox(), [])
            store.close()

    def test_transport_error_is_distinct_from_archicad_unavailable(self):
        fake = FakeReadTransport(failures={'GetStories': TimeoutError('timeout')})
        with self.assertRaises(ContextProviderError) as caught:
            capture(fake)
        self.assertEqual(caught.exception.code, 'TRANSPORT_ERROR')

    def test_malformed_read_response_fails_closed(self):
        fake = FakeReadTransport(malformed={'GetSelectedElements': {
            'result': {'wrong': []},
        }})
        with self.assertRaises(ContextProviderError) as caught:
            capture(fake)
        self.assertEqual(caught.exception.code, 'INVALID_RESPONSE')

    def test_wrong_instance_is_blocked_before_transport(self):
        fake = FakeReadTransport(binding={
            'instanceId': 'AC-B', 'logicalProjectId': 'P1',
        })
        with self.assertRaises(ContextProviderError) as caught:
            capture(fake)
        self.assertEqual(caught.exception.code, 'PROJECT_MISMATCH')
        self.assertEqual(fake.calls, [])

    def test_wrong_logical_project_is_blocked_before_transport(self):
        fake = FakeReadTransport(binding={
            'instanceId': 'AC-A', 'logicalProjectId': 'P2',
        })
        with self.assertRaises(ContextProviderError) as caught:
            capture(fake)
        self.assertEqual(caught.exception.code, 'PROJECT_MISMATCH')
        self.assertEqual(fake.calls, [])

    def test_project_switch_during_capture_is_blocked(self):
        first = {
            'isUntitled': False, 'isTeamwork': False,
            'projectPath': r'C:\Projects\A.pln', 'projectName': 'A',
        }
        second = first | {'projectPath': r'C:\Projects\B.pln', 'projectName': 'B'}
        fake = FakeReadTransport(project_infos=[first, second])
        with self.assertRaises(ContextProviderError) as caught:
            capture(fake)
        self.assertEqual(caught.exception.code, 'PROJECT_MISMATCH')

    def test_mutation_command_is_rejected_before_transport(self):
        fake = FakeReadTransport()
        fence = AllowlistedReadTransport(fake)
        with self.assertRaises(ContextProviderError) as caught:
            fence.dispatch('CreateWalls', {'wallsData': []})
        self.assertEqual(caught.exception.code, 'UNSUPPORTED_CAPABILITY')
        self.assertEqual(fake.calls, [])
        self.assertTrue(all(command.startswith('Get') for command in READ_COMMAND_ALLOWLIST))

    def test_provider_has_no_remote_publication_authority(self):
        provider = ArchicadContextProvider(FakeReadTransport())
        capture(provider._reads._transport)
        names = set(vars(provider))
        self.assertTrue(names.isdisjoint({'github', 'mailbox', 'outbox', 'publisher'}))

    def test_provider_has_no_bridge_store_completion_authority(self):
        provider = ArchicadContextProvider(FakeReadTransport())
        self.assertNotIn('store', vars(provider))
        self.assertFalse(hasattr(provider, 'commit_context_ready'))
        self.assertFalse(hasattr(provider, 'complete_request'))

    def test_s2_3_duplicate_and_restart_semantics_remain_unchanged(self):
        with ClosingDirectory() as directory:
            path = Path(directory) / 'restart.sqlite3'
            fake = FakeReadTransport()
            first_store = BridgeStore(path)
            first = ContextService(
                first_store, lambda: '2026-09-29T00:00:00+00:00',
                ArchicadContextProvider(fake))
            ready = first.request(request())
            call_count = len(fake.calls)
            first_store.close()

            refusing = FakeReadTransport(failures={
                'GetAddOnVersion': AssertionError('duplicate recaptured'),
            })
            second_store = BridgeStore(path)
            second = ContextService(
                second_store, lambda: '2026-09-30T00:00:00+00:00',
                ArchicadContextProvider(refusing))
            replay = second.request(request())
            self.assertEqual(replay, ready)
            self.assertEqual(refusing.calls, [])
            self.assertGreater(call_count, 0)
            second_store.close()

    def test_s2_3_generation_monotonicity_remains_unchanged(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'generation.sqlite3')
            fake = FakeReadTransport()
            service = ContextService(
                store, lambda: '2026-09-29T00:00:00+00:00',
                ArchicadContextProvider(fake))
            service.request(request('R2', generation=2))
            before = len(fake.calls)
            stale = service.request(request('R1', generation=1))
            self.assertEqual(stale['kind'], 'IGNORED_STALE')
            self.assertEqual(len(fake.calls), before)
            store.close()

    def test_s2_3_capture_revision_conflict_remains_unchanged(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'revision.sqlite3')
            service = ContextService(
                store, lambda: '2026-09-29T00:00:00+00:00',
                ArchicadContextProvider(FakeReadTransport()))
            service.fault_after_provider_returned = lambda: service.mark_changed('AC-A', 'P1')
            rejected = service.request(request())
            self.assertEqual(rejected['kind'], 'CAPTURE_REVISION_CONFLICT')
            self.assertIsNone(store.context_request('R1')['response'])
            self.assertEqual(store.pending_outbox(), [])
            store.close()

    def test_synthetic_provider_still_passes_original_interface(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'synthetic.sqlite3')
            service = ContextService(store, lambda: '2026-09-29T00:00:00+00:00')
            ready = service.request(request())
            self.assertEqual(ready['payload']['source'], 'synthetic')
            self.assertEqual(ready['rootHash'], canonical_hash(ready['payload']))
            store.close()

    def test_snapshot_never_publishes_local_project_path(self):
        snapshot = capture(FakeReadTransport())
        serialized = repr(snapshot)
        self.assertNotIn('private-user', serialized)
        self.assertNotIn('Secret.pln', serialized)
        self.assertEqual(snapshot['project'], {'logicalProjectId': 'P1'})


if __name__ == '__main__':
    unittest.main()
