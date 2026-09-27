#!/usr/bin/env python3
"""Focused regression tests for the v1.3 compatibility shim."""
from __future__ import annotations

import pathlib
import sys
import uuid

HERE = pathlib.Path(__file__).resolve()
PROBES = HERE.parents[1] / "probes"
sys.path.insert(0, str(PROBES))

import backends as base  # noqa: E402
from backends_v13 import TapirBackendV13, TAPIR_READ_COMMANDS_V13  # noqa: E402


class FakeUtilities:
    def __init__(self):
        self.calls = []

    def GetBuiltInPropertyId(self, name):
        self.calls.append(("builtin", name))
        return ("builtin", name)

    def GetUserDefinedPropertyId(self, group, name):
        self.calls.append(("user", group, name))
        return ("user", group, name)

    def GetPropertyValuesDictionary(self, elements, pids):
        return {e: {pids[0]: "VALUE"} for e in elements}


class FakeTypes:
    class ElementId:
        def __init__(self, guid):
            self.guid = guid

        def __hash__(self):
            return hash(self.guid)

        def __eq__(self, other):
            return isinstance(other, FakeTypes.ElementId) and self.guid == other.guid

    class NormalStringPropertyValue:
        def __init__(self, value):
            self.value = value

    class ElementPropertyValue:
        def __init__(self, elementId, propertyId, propertyValue):
            self.elementId = elementId
            self.propertyId = propertyId
            self.propertyValue = propertyValue


class FakeCommands:
    def __init__(self):
        self.writes = []

    def SetPropertyValuesOfElements(self, items):
        self.writes.append(items)
        return []


class FakeConn:
    def __init__(self):
        self.utilities = FakeUtilities()
        self.types = FakeTypes()
        self.commands = FakeCommands()


def backend():
    b = TapirBackendV13(port=19723)
    b.conn = FakeConn()
    return b


def test_details_payload_and_response_key():
    b = backend()
    seen = {}

    def fake_tapir(name):
        assert name == "GetDetailsOfElements"

        def call(payload):
            seen["payload"] = payload
            return {
                "detailsOfElements": [
                    {
                        "type": "Wall",
                        "id": "W-TEST-001",
                        "floorIndex": 0,
                        "layerIndex": 1,
                        "details": {
                            "begCoordinate": {"x": 1.0, "y": 2.0},
                            "endCoordinate": {"x": 6.0, "y": 2.0},
                            "height": 3.0,
                            "thickness": 0.3,
                        },
                    }
                ]
            }

        return call

    b._tapir = fake_tapir
    guid = "A0159B37-5EA0-48BB-A8C4-4DDE446DAF61"
    raw = b.details_raw(guid)
    assert seen["payload"] == {"elements": [{"elementId": {"guid": guid}}]}
    assert raw["type"] == "Wall"


def test_property_resolution_and_read():
    b = backend()
    guid = "A0159B37-5EA0-48BB-A8C4-4DDE446DAF61"
    got = b.get_property_values({"kind": "builtin", "id": "General_ElementID"}, [guid])
    assert got == {guid: "VALUE"}
    assert ("builtin", "General_ElementID") in b.conn.utilities.calls

    pid = b.resolve_property_id(
        {"kind": "user", "group": "BIMEXEC", "name": "BIMEXEC_MARKER"}
    )
    assert pid == ("user", "BIMEXEC", "BIMEXEC_MARKER")


def test_property_write_shape():
    b = backend()
    guid = "A0159B37-5EA0-48BB-A8C4-4DDE446DAF61"
    b.set_property_value(
        guid, {"kind": "builtin", "id": "General_ElementID"}, "BX:PROBE:test"
    )
    assert len(b.conn.commands.writes) == 1
    item = b.conn.commands.writes[0][0]
    assert item.elementId.guid == uuid.UUID(guid)
    assert item.propertyId == ("builtin", "General_ElementID")
    assert item.propertyValue.value == "BX:PROBE:test"


def test_blank_story_name_fails_closed():
    b = backend()
    b._tapir = lambda name: lambda: {"stories": [
        {"index": 0, "name": "Ground", "level": 0.0},
        {"index": 1, "name": "", "level": 3.0},
    ]}
    stories = b.stories()
    assert stories[0]["name"] == "Ground"
    assert stories[1]["name"] is None


def test_no_fake_api_namespace_commands():
    assert TAPIR_READ_COMMANDS_V13
    assert all(not x.startswith("API.") for x in TAPIR_READ_COMMANDS_V13)


if __name__ == "__main__":
    tests = [
        test_details_payload_and_response_key,
        test_property_resolution_and_read,
        test_property_write_shape,
        test_blank_story_name_fails_closed,
        test_no_fake_api_namespace_commands,
    ]
    for test in tests:
        test()
        print("OK", test.__name__)
    print(f"{len(tests)}/{len(tests)} passed")
