"""Command classes for the Safe BIM mutation boundary.

A command is read-only only when it is on the explicit allowlist. Name prefixes
are not permission. A name absent from the pinned Tapir 1.5.9 snapshot is
UNKNOWN and must fail closed.
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path


class PolicyError(ValueError):
    """Fail-closed policy rejection. Not evidence that a write was sent."""


class CommandClass(str, Enum):
    READ_ONLY = 'READ_ONLY'
    SESSION_MUTATION = 'SESSION_MUTATION'
    MODEL_MUTATION = 'MODEL_MUTATION'
    ATTRIBUTE_MUTATION = 'ATTRIBUTE_MUTATION'
    UNKNOWN = 'UNKNOWN'


READ_ONLY_COMMANDS = frozenset({
    'GetAddOnVersion',
    'GetProjectInfo',
    'GetStories',
    'GetDetailsOfElements',
    'GetElementsByType',
    'GetNavigatorItemTree',
})

# Production may admit only these model commands, and only one item at a time.
ADMITTED_MODEL_COMMANDS = frozenset({
    'CreateWalls', 'CreateSlabs', 'CreateWindows', 'CreateDoors',
})

# Story activation is the only session mutation the runtime may perform,
# and only inside an admitted step. Open/Save stay denied.
ADMITTED_SESSION_COMMANDS = frozenset({'ChangeWindow'})

DENIED_FROM_NORMAL_EXECUTION = frozenset({
    'OpenProject', 'CloseProject', 'SaveProject', 'SaveAsModuleFile',
})

_EXPLICIT = {
    'OpenProject': CommandClass.SESSION_MUTATION,
    'CloseProject': CommandClass.SESSION_MUTATION,
    'ChangeWindow': CommandClass.SESSION_MUTATION,
    'SaveProject': CommandClass.SESSION_MUTATION,
    'SaveAsModuleFile': CommandClass.SESSION_MUTATION,
    'SetLibraries': CommandClass.ATTRIBUTE_MUTATION,
    'TrimElements': CommandClass.MODEL_MUTATION,
    'CreateWalls': CommandClass.MODEL_MUTATION,
    'CreateSlabs': CommandClass.MODEL_MUTATION,
    'CreateWindows': CommandClass.MODEL_MUTATION,
    'CreateDoors': CommandClass.MODEL_MUTATION,
    'ModifySlabs': CommandClass.MODEL_MUTATION,
    'DeleteElements': CommandClass.MODEL_MUTATION,
}

_CATEGORY_CLASS = {
    'Attribute Commands': CommandClass.ATTRIBUTE_MUTATION,
    'Element Commands': CommandClass.MODEL_MUTATION,
    'Element grouping Commands': CommandClass.MODEL_MUTATION,
    'Solid Element Operation Commands': CommandClass.MODEL_MUTATION,
    'MEP Commands': CommandClass.MODEL_MUTATION,
    'Project Commands': CommandClass.SESSION_MUTATION,
    'Application Commands': CommandClass.SESSION_MUTATION,
    'Teamwork Commands': CommandClass.SESSION_MUTATION,
    'Library Commands': CommandClass.ATTRIBUTE_MUTATION,
    'Navigator Commands': CommandClass.SESSION_MUTATION,
    'Property Commands': CommandClass.ATTRIBUTE_MUTATION,
    'Classification Commands': CommandClass.ATTRIBUTE_MUTATION,
    'Favorites Commands': CommandClass.ATTRIBUTE_MUTATION,
    'Issue Management Commands': CommandClass.SESSION_MUTATION,
    'Design Options Commands': CommandClass.SESSION_MUTATION,
}

_CREATE_ARRAY_FIELDS = {
    'CreateWalls': 'wallsData',
    'CreateSlabs': 'slabsData',
    'CreateWindows': 'windowsData',
    'CreateDoors': 'doorsData',
}

_SNAPSHOT_COMMANDS = None


def snapshot_commands():
    global _SNAPSHOT_COMMANDS
    if _SNAPSHOT_COMMANDS is None:
        path = Path(__file__).with_name('tapir-1.5.9.json')
        document = json.loads(path.read_text(encoding='utf-8'))
        _SNAPSHOT_COMMANDS = document.get('commands') or {}
    return _SNAPSHOT_COMMANDS


def classify(command) -> CommandClass:
    """Return the command class. Never treats an unknown name as read-only."""
    if not isinstance(command, str) or not command.strip():
        return CommandClass.UNKNOWN
    if command in READ_ONLY_COMMANDS:
        return CommandClass.READ_ONLY
    if command in _EXPLICIT:
        return _EXPLICIT[command]
    spec = snapshot_commands().get(command)
    if not isinstance(spec, dict):
        return CommandClass.UNKNOWN
    # Snapshot Get* commands are not reads unless allowlisted above.
    if command.startswith('Get'):
        return CommandClass.UNKNOWN
    return _CATEGORY_CLASS.get(spec.get('category'), CommandClass.UNKNOWN)


def is_mutation(command) -> bool:
    return classify(command) in {
        CommandClass.SESSION_MUTATION,
        CommandClass.MODEL_MUTATION,
        CommandClass.ATTRIBUTE_MUTATION,
    }


def schema_provider_version(schema):
    if not isinstance(schema, dict):
        return None
    meta = schema.get('_metadata')
    if not isinstance(meta, dict):
        return None
    version = meta.get('provider_version')
    return version if isinstance(version, str) and version.strip() else None


def assert_single_create_item(command, params):
    """Production Create* payloads are one element. Longer batches are denied."""
    field = _CREATE_ARRAY_FIELDS.get(command)
    if field is None:
        return
    rows = params.get(field) if isinstance(params, dict) else None
    if not isinstance(rows, list) or len(rows) != 1:
        raise PolicyError(f'{command} payload must contain exactly one {field} item')
