"""Strict read contracts shared by execution and read-only reconciliation.

Tapir details.id is a human element ID, NOT its GUID. Identity is established by
one-GUID-per-request reads; optional echoed GUIDs must agree. No zip truncation.
"""
import math
import uuid


class VerificationError(RuntimeError):
    pass


def guid_key(value):
    if not isinstance(value, str) or not value.strip():
        raise VerificationError('GUID required')
    try:
        return uuid.UUID(value.strip()).hex
    except ValueError:
        # Opaque identifiers remain useful for offline fake backends. Real UUID
        # spellings (braces, case, hyphenless) always share one identity key.
        return value.casefold()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise VerificationError(f'finite number required: {value!r}')
    return float(value)


def equal(a, b):
    if isinstance(b, (int, float)) and not isinstance(b, bool):
        return math.isclose(number(a), number(b), rel_tol=0, abs_tol=1e-6)
    return a == b


def response_items(response):
    if not isinstance(response, dict) or response.get('success') is False or 'error' in response:
        raise VerificationError('invalid/error API response')
    result = response.get('result')
    if not isinstance(result, dict) or 'error' in result:
        raise VerificationError('missing/error result')
    value = result.get('addOnCommandResponse')
    if not isinstance(value, dict) or 'error' in value or value.get('success') is False:
        raise VerificationError('missing/error addOnCommandResponse')
    return value


def element_guids(response, expected_count=None):
    rows = response_items(response).get('elements')
    if not isinstance(rows, list):
        raise VerificationError('elements array required')
    guids = []
    for row in rows:
        if not isinstance(row, dict) or 'error' in row or not isinstance(row.get('elementId'), dict):
            raise VerificationError('element identity/error')
        guid = row['elementId'].get('guid')
        if not isinstance(guid, str) or not guid.strip():
            raise VerificationError('GUID required')
        guids.append(guid)
    if len({guid_key(g) for g in guids}) != len(guids):
        raise VerificationError('duplicate GUID')
    if expected_count is not None and len(guids) != expected_count:
        raise VerificationError('incomplete creation response')
    return guids


def verify_details(prepared, guids, details):
    expected = prepared['expected']
    if len(guids) != len(expected) or len(details) != len(expected) or not guids:
        raise VerificationError('incomplete read-back')
    if len({guid_key(g) for g in guids}) != len(guids):
        raise VerificationError('duplicate identity')
    for guid, row, spec in zip(guids, details, expected):
        if not isinstance(row, dict) or row.get('verifiedGuid') != guid:
            raise VerificationError('read-back identity not bound to request')
        if row.get('type') != prepared['type'] or not equal(row.get('floorIndex'), prepared['floorIndex']):
            raise VerificationError('wrong type/floorIndex')
        actual = row.get('details')
        if not isinstance(actual, dict):
            raise VerificationError('details object required')
        for key, value in spec.items():
            if key not in actual or not equal(actual[key], value):
                raise VerificationError(f'read-back mismatch: {key}')
        if prepared['type'] == 'Wall':
            # Explicit contract: zCoordinate is story-relative, never absolute.
            bottom = prepared['storyElevation'] + number(actual['zCoordinate'])
            top = bottom + number(actual['height'])
        elif prepared['type'] == 'Slab':
            reference = prepared['storyElevation'] + number(actual['level'])
            top = reference + number(actual['offsetFromTop'])
            bottom = top - number(actual['thickness'])
            if not equal(actual['zCoordinate'], reference):
                raise VerificationError('slab absolute reference Z mismatch')
        else:
            continue
        fp = prepared['expectedZFingerprint']
        if not equal(bottom, fp['expected_bottom']) or not equal(top, fp['expected_top']):
            raise VerificationError('absolute bottom/top mismatch')
    return True
