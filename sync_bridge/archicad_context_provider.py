"""Bounded, read-only Archicad context capture for the S2.3 state machine.

The provider owns no durable state and has no publishing or completion
authority.  Its transport is injected so the same command fence is exercised
by production adapters and offline tests.
"""
from __future__ import annotations

import re
from copy import deepcopy

from sync_bridge.identity import canonical_hash


ARCHICAD_CONTEXT_PROVIDER_STATUS = 'IMPLEMENTED_NOT_LIVE_VERIFIED'
MAX_SELECTED_ELEMENTS = 500

# This is deliberately narrower than a generic Tapir read surface.  A command
# that is absent here is rejected before the injected transport is called.
READ_COMMAND_ALLOWLIST = frozenset({
    'GetAddOnVersion',
    'GetProjectInfo',
    'GetStories',
    'GetSelectedElements',
    'GetDetailsOfElements',
})

_UNSUPPORTED_DETAIL_TYPES = frozenset({'Opening', 'Stair'})
_WINDOWS_PATH = re.compile(r'^[A-Za-z]:[\\/]|^\\\\')
_SENSITIVE_KEYS = frozenset({
    'authorization', 'credential', 'credentials', 'filepath', 'hostname',
    'localpath', 'machinename', 'password', 'projectlocation', 'projectpath',
    'tempdir', 'temppath', 'token', 'username',
})


class ContextProviderError(RuntimeError):
    """A deterministic capture failure with a machine-readable status."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class AllowlistedReadTransport:
    """The provider's only path to Archicad/Tapir."""

    def __init__(self, transport):
        self._transport = transport

    def dispatch(self, command: str, params: dict) -> dict:
        if command not in READ_COMMAND_ALLOWLIST:
            raise ContextProviderError(
                'UNSUPPORTED_CAPABILITY',
                f'command {command!r} is not in the context read allowlist')
        call = getattr(self._transport, 'call', None)
        if not callable(call):
            raise ContextProviderError(
                'ARCHICAD_NOT_AVAILABLE', 'injected read transport has no callable call()')
        try:
            response = call(command, deepcopy(params))
        except ContextProviderError:
            raise
        except ConnectionError as exc:
            raise ContextProviderError(
                'ARCHICAD_NOT_AVAILABLE', f'Archicad is not available during {command}') from exc
        except (TimeoutError, OSError) as exc:
            raise ContextProviderError(
                'TRANSPORT_ERROR', f'read transport failed during {command}') from exc
        except Exception as exc:
            raise ContextProviderError(
                'TRANSPORT_ERROR', f'unexpected read transport failure during {command}') from exc
        return _unwrap_response(command, response)


class ArchicadContextProvider:
    """Capture selection-scoped evidence without any Archicad mutation."""

    def __init__(self, transport, binding_reader=None, *, max_selection=MAX_SELECTED_ELEMENTS):
        if isinstance(max_selection, bool) or not isinstance(max_selection, int) or max_selection <= 0:
            raise ValueError('max_selection must be a positive integer')
        self._reads = AllowlistedReadTransport(transport)
        self._binding_reader = binding_reader or getattr(transport, 'binding', None)
        self.max_selection = max_selection

    def capture(self, request: dict) -> dict:
        instance_id, project_id = _request_identity(request)
        if request.get('requestedScope') != 'selection':
            raise ContextProviderError(
                'UNSUPPORTED_CAPABILITY', 'only requestedScope=selection is supported')

        first_binding = self._require_binding(instance_id, project_id)
        addon = self._reads.dispatch('GetAddOnVersion', {})
        tapir_version = _required_string(addon, 'version', 'GetAddOnVersion')

        first_project = self._reads.dispatch('GetProjectInfo', {})
        project_fingerprint = _project_fingerprint(first_project)
        stories_payload = self._reads.dispatch('GetStories', {})
        stories, current_story = _stories(stories_payload)

        selection_payload = self._reads.dispatch('GetSelectedElements', {})
        guids = _selected_guids(selection_payload)
        if len(guids) > self.max_selection:
            raise ContextProviderError(
                'SELECTION_TOO_LARGE',
                f'selection contains {len(guids)} elements; maximum is {self.max_selection}')

        elements = [self._selected_element(guid) for guid in sorted(guids, key=_guid_sort_key)]

        # Re-read both facts after the potentially long singleton details pass.
        # Neither local paths nor the fingerprint are included in the snapshot.
        final_project = self._reads.dispatch('GetProjectInfo', {})
        if _project_fingerprint(final_project) != project_fingerprint:
            raise ContextProviderError('PROJECT_MISMATCH', 'open Archicad project changed during capture')
        final_binding = self._require_binding(instance_id, project_id)
        if _binding_identity(final_binding) != _binding_identity(first_binding):
            raise ContextProviderError('PROJECT_MISMATCH', 'Archicad binding changed during capture')

        snapshot = {
            'source': 'archicad',
            'instanceId': instance_id,
            'logicalProjectId': project_id,
            'application': {
                'name': 'Archicad',
                'version': _optional_string(first_binding.get('applicationVersion')),
                'tapirVersion': tapir_version,
            },
            'project': {'logicalProjectId': project_id},
            'stories': stories,
            'currentStory': current_story,
            'selection': {'count': len(elements), 'elements': elements},
        }
        try:
            canonical_hash(snapshot)
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ContextProviderError(
                'INVALID_RESPONSE', 'Archicad response is not canonical JSON data') from exc
        return snapshot

    def _selected_element(self, guid: str) -> dict:
        payload = self._reads.dispatch(
            'GetDetailsOfElements',
            {'elements': [{'elementId': {'guid': guid}}]},
        )
        rows = payload.get('detailsOfElements')
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise ContextProviderError(
                'INVALID_RESPONSE', 'GetDetailsOfElements must return one object for one GUID')
        row = rows[0]
        element_type = _required_string(row, 'type', 'GetDetailsOfElements')
        result = {'guid': guid, 'type': element_type}

        if element_type in _UNSUPPORTED_DETAIL_TYPES:
            result.update({
                'detailsStatus': 'UNSUPPORTED',
                'details': None,
                'detailsReason': 'DETAILED_VERIFIER_UNSUPPORTED',
            })
            return result

        raw_details = row.get('details')
        if not isinstance(raw_details, dict):
            raise ContextProviderError(
                'INVALID_RESPONSE', 'GetDetailsOfElements returned no details object')
        if isinstance(raw_details.get('error'), str):
            result.update({
                'detailsStatus': 'UNSUPPORTED',
                'details': None,
                'detailsReason': 'TAPIR_DETAILS_UNSUPPORTED',
            })
            return result

        try:
            details = _privacy_copy(raw_details)
        except _SensitiveDetail:
            result.update({
                'detailsStatus': 'UNSUPPORTED',
                'details': None,
                'detailsReason': 'PRIVACY_FILTER',
            })
            return result

        partial = False
        if element_type == 'Beam':
            for key in ('width', 'height', 'isWidthAndHeightLinked'):
                partial = details.pop(key, None) is not None or partial
        elif element_type == 'Morph':
            details, partial = _drop_matching_keys(details, lambda key: key == 'isClosed')
        elif (element_type == 'Roof'
              and isinstance(details.get('roofClass'), str)
              and details['roofClass'] == 'MultiPlane'):
            details, partial = _drop_matching_keys(
                details, lambda key: 'gable' in key.casefold())

        result['detailsStatus'] = 'PARTIAL' if partial else 'SUPPORTED'
        result['details'] = details
        if partial:
            result['detailsReason'] = 'UNVERIFIED_FIELDS_OMITTED'
        return result

    def _require_binding(self, instance_id: str, project_id: str) -> dict:
        if not callable(self._binding_reader):
            raise ContextProviderError(
                'ARCHICAD_NOT_AVAILABLE', 'no Archicad binding reader was injected')
        try:
            binding = self._binding_reader()
        except ContextProviderError:
            raise
        except Exception as exc:
            raise ContextProviderError(
                'ARCHICAD_NOT_AVAILABLE', 'Archicad binding cannot be read') from exc
        if not isinstance(binding, dict):
            raise ContextProviderError('INVALID_RESPONSE', 'Archicad binding must be an object')
        if binding.get('instanceId') != instance_id or binding.get('logicalProjectId') != project_id:
            raise ContextProviderError(
                'PROJECT_MISMATCH', 'requested instance/project is not the bound Archicad context')
        return binding


def _unwrap_response(command: str, response) -> dict:
    if not isinstance(response, dict):
        raise ContextProviderError('INVALID_RESPONSE', f'{command} returned a non-object response')
    if 'error' in response:
        _raise_api_error(command, response['error'])
    if 'result' not in response:
        return response
    result = response.get('result')
    if not isinstance(result, dict):
        raise ContextProviderError('INVALID_RESPONSE', f'{command} returned malformed result')
    payload = result.get('addOnCommandResponse')
    if not isinstance(payload, dict):
        raise ContextProviderError(
            'INVALID_RESPONSE', f'{command} returned no addOnCommandResponse object')
    if 'error' in payload:
        _raise_api_error(command, payload['error'])
    return payload


def _raise_api_error(command: str, error) -> None:
    text = str(error)
    lowered = text.casefold()
    if 'unsupported' in lowered or 'not implemented' in lowered:
        code = 'UNSUPPORTED_CAPABILITY'
    else:
        code = 'TRANSPORT_ERROR'
    raise ContextProviderError(code, f'{command} failed: {text}')


def _request_identity(request: dict) -> tuple[str, str]:
    if not isinstance(request, dict):
        raise ContextProviderError('INVALID_RESPONSE', 'capture request must be an object')
    instance_id = request.get('instanceId')
    project_id = request.get('logicalProjectId')
    if not isinstance(instance_id, str) or not instance_id.strip():
        raise ContextProviderError('PROJECT_MISMATCH', 'request has no instanceId')
    if not isinstance(project_id, str) or not project_id.strip():
        raise ContextProviderError('PROJECT_MISMATCH', 'request has no logicalProjectId')
    return instance_id, project_id


def _project_fingerprint(payload: dict) -> dict:
    for field in ('isUntitled', 'isTeamwork'):
        if not isinstance(payload.get(field), bool):
            raise ContextProviderError(
                'INVALID_RESPONSE', f'GetProjectInfo returned invalid {field}')
    identity = {
        'isUntitled': payload['isUntitled'],
        'isTeamwork': payload['isTeamwork'],
    }
    for field in ('projectPath', 'projectLocation', 'projectName'):
        value = payload.get(field)
        if value is not None and not isinstance(value, str):
            raise ContextProviderError(
                'INVALID_RESPONSE', f'GetProjectInfo returned invalid {field}')
        identity[field] = value
    return identity


def _stories(payload: dict) -> tuple[list[dict], dict]:
    raw = payload.get('stories')
    if not isinstance(raw, list):
        raise ContextProviderError('INVALID_RESPONSE', 'GetStories returned no stories array')
    stories = []
    indexes = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ContextProviderError('INVALID_RESPONSE', 'GetStories returned a non-object story')
        index = item.get('index')
        name = item.get('name')
        elevation = item.get('level', item.get('elevation'))
        if isinstance(index, bool) or not isinstance(index, int):
            raise ContextProviderError('INVALID_RESPONSE', 'story index must be an integer')
        if index in indexes:
            raise ContextProviderError('INVALID_RESPONSE', 'duplicate story index')
        if not isinstance(name, str):
            raise ContextProviderError('INVALID_RESPONSE', 'story name must be a string')
        if isinstance(elevation, bool) or not isinstance(elevation, (int, float)):
            raise ContextProviderError('INVALID_RESPONSE', 'story elevation must be numeric')
        elevation = float(elevation)
        if not (-float('inf') < elevation < float('inf')):
            raise ContextProviderError('INVALID_RESPONSE', 'story elevation must be finite')
        indexes.add(index)
        stories.append({'index': index, 'name': name, 'elevation': elevation})
    stories.sort(key=lambda story: story['index'])

    active = payload.get('actStory')
    if isinstance(active, bool) or not isinstance(active, int):
        current = {
            'status': 'UNRESOLVED',
            'reason': 'CURRENT_STORY_NOT_REPORTED',
        }
    else:
        current = next((deepcopy(story) for story in stories if story['index'] == active), None)
        if current is None:
            current = {
                'status': 'UNRESOLVED',
                'index': active,
                'reason': 'CURRENT_STORY_NOT_IN_CAPTURED_STORIES',
            }
    return stories, current


def _selected_guids(payload: dict) -> list[str]:
    rows = payload.get('elements')
    if not isinstance(rows, list):
        raise ContextProviderError(
            'INVALID_RESPONSE', 'GetSelectedElements returned no elements array')
    guids = []
    seen = set()
    for row in rows:
        guid = row.get('elementId', {}).get('guid') if isinstance(row, dict) else None
        if not isinstance(guid, str) or not guid:
            raise ContextProviderError('INVALID_RESPONSE', 'selected element has no exact GUID')
        key = guid.casefold()
        if key in seen:
            raise ContextProviderError('INVALID_RESPONSE', 'selection contains a duplicate GUID')
        seen.add(key)
        guids.append(guid)
    return guids


def _guid_sort_key(guid: str) -> tuple[str, str]:
    return guid.casefold(), guid


def _required_string(payload: dict, field: str, command: str) -> str:
    value = payload.get(field) if isinstance(payload, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise ContextProviderError(
            'INVALID_RESPONSE', f'{command} returned invalid {field}')
    return value


def _optional_string(value):
    return value if isinstance(value, str) and value.strip() else None


def _binding_identity(binding: dict) -> tuple[str, str]:
    return binding.get('instanceId'), binding.get('logicalProjectId')


class _SensitiveDetail(ValueError):
    pass


def _privacy_copy(value, key=''):
    normalized = re.sub(r'[^a-z0-9]', '', key.casefold())
    if normalized in _SENSITIVE_KEYS:
        raise _SensitiveDetail(key)
    if isinstance(value, str):
        lowered = value.casefold()
        if _WINDOWS_PATH.search(value) or '\\users\\' in lowered or '/users/' in lowered:
            raise _SensitiveDetail(key)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [_privacy_copy(item) for item in value]
    if isinstance(value, dict):
        return {item_key: _privacy_copy(item_value, item_key)
                for item_key, item_value in value.items()}
    raise ContextProviderError('INVALID_RESPONSE', 'element details contain non-JSON data')


def _drop_matching_keys(value, predicate):
    removed = False
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if predicate(key):
                removed = True
                continue
            cleaned, child_removed = _drop_matching_keys(item, predicate)
            result[key] = cleaned
            removed = removed or child_removed
        return result, removed
    if isinstance(value, list):
        result = []
        for item in value:
            cleaned, child_removed = _drop_matching_keys(item, predicate)
            result.append(cleaned)
            removed = removed or child_removed
        return result, removed
    return value, False
