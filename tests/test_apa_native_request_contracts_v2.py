"""192 independent boundary cases against source-pinned SDK command input contracts.
No native transport, no runtime registration claim.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands

NAMES = [
    "GetNativeEnvelopeMemoV1",
    "GetNativeOpeningConnectionsV1",
    "GetNativeNavigatorBindingsV1",
    "GetNativeLibraryPartDefaultsV1",
    "CreateNativeAssemblyV1",
]


@pytest.fixture(scope="module")
def router():
    r = DynamicCommands(json.loads(
        (ROOT / "schemas/accelerator/mass-capabilities/commands.json").read_text(encoding="utf8")
    ))
    A.connect_functional_modules(r)
    return r


def original(index, case):
    if index in (0, 1):
        return {"elements": [{"elementId": {"guid": f"GUID-{case}-{i}"}} for i in range(1 + case % 3)]}
    if index == 2:
        return {"items": [{"navigatorItemId": {"guid": f"NAV-{case}-{i}"},
                            "navigatorMapId": ["PublicViewMap", "ProjectMap", "LayoutBook"][i % 3]}
                           for i in range(1 + case % 3)]}
    if index == 3:
        return {"libraryPartIndices": [case + i + 1 for i in range(1 + case % 3)]}
    return {"kind": ["CurtainWall", "Railing", "ExtrudedShell"][case % 3],
            "origin": {"x": (case % 13) - 6, "y": case * 0.125},
            "homeStory": (case % 41) - 20, "relativeLevel": case / 8,
            "length": 0.5 + (case % 55), "height": 0.3 + (case % 15),
            "extrusionDepth": 1 + case % 40}


@pytest.mark.parametrize("case", range(96))
def test_bounded_native_contract_positive_without_transport(router, case):
    index = case % 5
    cmd = "AddOn.TapirCommand." + NAMES[index]
    source = original(index, case)
    ticket = router.prepare(cmd, source)
    assert ticket["nativeWritePermission"] is False
    assert ticket["effect"] == ("CREATE" if index == 4 else "READ_ONLY")
    assert ticket["parameters"] == source
    assert router.validate(ticket) == ticket
    assert ticket["catalogHash"] == router.fingerprint


def mutate(index, source, mode):
    row = json.loads(json.dumps(source))
    required = {0: "elements", 1: "elements", 2: "items",
                3: "libraryPartIndices", 4: "kind"}[index]
    if mode == 0:
        row.pop(required)
    elif mode == 1:
        row["notInSchema"] = 1
    elif mode == 2:
        row[required] = None
    elif mode == 3:
        row[required] = "not-a-valid-value"
    elif mode == 4:
        if index == 4: row["origin"] = {"x": 1}
        else: row[required] = []
    elif mode == 5:
        if index == 4: row["length"] = 0
        else:
            first = row[required][0]
            row[required] = [first] * (9 if index == 3 else 33)
    elif mode == 6:
        if index == 4: row["homeStory"] = 101
        elif index == 3: row[required] = [0]
        elif index == 2: row["items"][0]["navigatorMapId"] = "UnknownMap"
        else: row["elements"][0]["elementId"]["guid"] = ""
    elif mode == 7:
        if index == 4: row["height"] = 21
        elif index == 3: row[required] = [1, 1]
        elif index == 2: row["items"][0]["extraField"] = True
        else: row["elements"][0]["elementId"]["extraField"] = True
    elif mode == 8:
        if index == 4: row["kind"] = "Shell"
        elif index == 3: row[required] = [False]
        elif index == 2: row["items"][0]["navigatorItemId"] = {"guid": ""}
        else: row["elements"][0]["elementId"] = {"guid": 14}
    elif mode == 9:
        if index == 4: row["origin"] = {"x": "bad", "y": 1}
        elif index == 3: row[required] = [1.5]
        else: row[required][0] = {}
    elif mode == 10:
        if index == 4: row["homeStory"] = -101
        elif index == 3: row[required] = [-1]
        else: row[required][0] = None
    elif mode == 11:
        if index == 4: row["extrusionDepth"] = -1
        elif index == 3: row[required] = ["1"]
        elif index == 2: row["items"][0]["navigatorMapId"] = 5
        else: row["elements"][0]["elementId"] = None
    else:
        raise AssertionError(mode)
    return row


@pytest.mark.parametrize("case", range(96))
def test_bounded_native_contract_invalid_rejected_before_transport(router, case):
    index = case % 5
    mode = (case // 5) % 12
    command = "AddOn.TapirCommand." + NAMES[index]
    payload = mutate(index, original(index, case), mode)
    with pytest.raises(Exception):
        router.prepare(command, payload)
    assert router.select(command)["runtimeRegistered"] is None
