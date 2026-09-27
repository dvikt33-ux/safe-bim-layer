"""Tapir 1.5.9 write gate.

The only supported version probe is the read-only GetAddOnVersion command.
A missing, unparseable, or non-1.5.9 result blocks the physical write. This
module does not enable new primitives and does not invent a second handshake.
"""
from __future__ import annotations

from safe_bim_layer import SafeBIMError

SUPPORTED_TAPIR_VERSION = '1.5.9'
PHYSICAL_WRITE_PREFIXES = ('Create', 'Modify', 'Delete')


def is_physical_write(command) -> bool:
    return isinstance(command, str) and command.startswith(PHYSICAL_WRITE_PREFIXES)


def version_from_response(response):
    """Return the add-on version string, or None if the envelope is not usable."""
    if not isinstance(response, dict):
        return None
    result = response.get('result')
    if not isinstance(result, dict):
        return None
    addon = result.get('addOnCommandResponse')
    if not isinstance(addon, dict):
        return None
    version = addon.get('version')
    return version if isinstance(version, str) and version.strip() else None


def assert_tapir_write_allowed(client) -> str:
    """Read GetAddOnVersion. Raise before any physical write when it is not 1.5.9."""
    try:
        response = client.call('GetAddOnVersion', {})
    except SafeBIMError:
        raise
    except Exception as exc:
        raise SafeBIMError('Tapir 1.5.9 version unverifiable; physical writes blocked') from exc
    version = version_from_response(response)
    if version != SUPPORTED_TAPIR_VERSION:
        raise SafeBIMError(
            f'Tapir version {version!r} is not {SUPPORTED_TAPIR_VERSION}; physical writes blocked')
    return version
