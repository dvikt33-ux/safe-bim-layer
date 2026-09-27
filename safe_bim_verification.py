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


def wall_z_contract(story_index, story_elevation, absolute_bottom, height, structure_type='Basic'):
    """Split the two wall/plinth Z meanings that 14bc0d2 had collapsed.

    write_relative_z is the CreateWalls input when floorIndex is present:
    absolute_bottom - story_elevation. expected_readback_z is the value live
    Tapir wall GetDetails returns in zCoordinate: the absolute bottom, not the
    write offset. On story elevation 0 the two numbers coincide; that hid the bug.
    """
    if isinstance(story_index, bool) or not isinstance(story_index, int):
        raise VerificationError('integer story index required')
    if structure_type != 'Basic':
        raise VerificationError('wall/plinth vertical contract is Basic-only')
    elevation = number(story_elevation)
    bottom = number(absolute_bottom)
    wall_height = number(height)
    if wall_height <= 0:
        raise VerificationError('positive height required')
    relative = bottom - elevation
    top = bottom + wall_height
    return {
        'story_index': story_index,
        'floorIndex': story_index,
        'story_elevation': elevation,
        'write_relative_z': relative,
        'relative_offset': relative,
        'expected_readback_z': bottom,
        'expected_absolute_bottom_z': bottom,
        'expected_bottom': bottom,
        'expected_absolute_top_z': top,
        'expected_top': top,
        'height': wall_height,
        'structureType': structure_type,
    }


def assess_wall_vertical(fingerprint, floor_index, details):
    """Read-only geometry classification for one wall/plinth detail row.

    MATCH means the confirmed live vertical facts agree. It does not prove that
    a job, step, attempt, or receipt owns the element.
    """
    if not isinstance(fingerprint, dict) or not isinstance(details, dict):
        return {'geometry': 'MISMATCH', 'reasons': ['malformed'], 'ownershipProven': False}
    reasons = []
    z = height = None
    try:
        expected_floor = fingerprint['story_index'] if 'story_index' in fingerprint else fingerprint['floorIndex']
        if not equal(floor_index, expected_floor):
            reasons.append('floorIndex')
        if 'zCoordinate' not in details:
            reasons.append('zCoordinate')
        else:
            z = number(details['zCoordinate'])
            if 'expected_readback_z' in fingerprint:
                expected_z = fingerprint['expected_readback_z']
            elif 'expected_absolute_bottom_z' in fingerprint:
                expected_z = fingerprint['expected_absolute_bottom_z']
            else:
                expected_z = fingerprint['expected_bottom']
            # Compare to absolute bottom. Never add story elevation here: that
            # would accept the old write offset (-0.600) as bottom 3.900.
            if not equal(z, expected_z):
                reasons.append('zCoordinate')
        if 'height' not in details:
            reasons.append('height')
        else:
            height = number(details['height'])
            if not equal(height, fingerprint['height']):
                reasons.append('height')
        if details.get('structureType') != fingerprint.get('structureType', 'Basic'):
            reasons.append('structureType')
        expected_top = fingerprint.get('expected_absolute_top_z', fingerprint.get('expected_top'))
        if z is None or height is None or not equal(z + height, expected_top):
            reasons.append('top')
    except (VerificationError, KeyError) as exc:
        return {'geometry': 'MISMATCH', 'reasons': [type(exc).__name__], 'ownershipProven': False}
    return {
        'geometry': 'MATCH' if not reasons else 'MISMATCH',
        'reasons': reasons,
        'ownershipProven': False,
        'absolute_bottom': None if z is None or 'zCoordinate' in reasons else z,
        'absolute_top': None if z is None or height is None else z + height,
    }


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
            # Live wall GetDetails.zCoordinate is absolute bottom, not the
            # story-relative CreateWalls write offset stored beside it.
            assessment = assess_wall_vertical(prepared['expectedZFingerprint'], row.get('floorIndex'), actual)
            if assessment['geometry'] != 'MATCH':
                raise VerificationError('wall vertical read-back mismatch: ' + ','.join(assessment['reasons']))
            bottom = number(actual['zCoordinate'])
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
