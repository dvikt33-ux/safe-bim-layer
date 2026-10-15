"""64 cross-domain dependency topologies: component, Opening, Navigator, Drawing."""
import sys
from pathlib import Path

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_native_dependency_flow import dependency_inputs
from archicad_local_modules import dependency_impact


def gid(n):
    return {"guid": n}


@pytest.mark.parametrize("mask", range(64))
def test_cross_domain_multi_capture_cycle_and_namespacing(mask):
    wall, opening_a, opening_b, frame, draw, view, layout, db = (
        f"WALL_{mask}", f"OPEN_A_{mask}", f"OPEN_B_{mask}",
        f"FRAME_{mask}", f"DRAW_{mask}", f"VIEW_{mask}",
        f"LAYOUT_{mask}", f"DB_{mask}")
    # Opening B hosted in A is a verified opening link, independent of physical BREP.
    opening_rows = [
        {"elementId": gid(opening_a), "parentResolved": True,
         "hostElementId": gid(wall), "connectedOpenings": [gid(opening_b)]},
        {"elementId": gid(opening_b), "parentResolved": bool(mask & 1),
         "hostElementId": gid(opening_a),
         "connectedOpenings": [gid(opening_a)] if mask & 2 else [],
         "cutElements": [gid(wall)] if mask & 4 else []}
    ]
    components = {"elements": [
        {"elementId": gid(frame), "parentQueryError": 0 if mask & 8 else -1,
         "parentElementId": gid(wall), "rootQueryError": -1}]}
    navigator = {"items": [{
        "navigatorItemId": gid(view), "requestedMap": "PublicViewMap",
        "identityMatchesRequest": bool(mask & 16),
        "mapMatchesRequest": True, "sourceGuid": gid(wall)}]}
    drawings = {"drawings": [{"elementId": gid(draw), "databaseId": gid(db),
                              "databaseQualified": True, "linkGuid": gid(view),
                              "viewDeleted": bool(mask & 32)}]}
    data = dependency_inputs(
        components=components, openings={"elements": opening_rows},
        navigator_bindings=navigator, drawings=drawings,
        layout_bindings=[{"databaseId": gid(db), "navigatorItemId": gid(layout)}])
    edges = {tuple(e) for e in data["edges"]}
    assert (wall, opening_a) in edges
    assert (opening_a, opening_b) in edges
    assert (draw, "NAVIGATOR:LAYOUTBOOK:" + layout) in edges
    assert ((wall, frame) in edges) == bool(mask & 8)
    assert (("NAVIGATOR_SOURCE_REFERENCE:" + wall,
             "NAVIGATOR:PUBLICVIEWMAP:" + view) in edges) == bool(mask & 16)
    has_link = bool(mask & 16) and not bool(mask & 32)
    assert (("NAVIGATOR:PUBLICVIEWMAP:" + view, draw) in edges) == has_link
    result = dependency_impact(data["nodes"], data["edges"], [wall])
    assert result["executionAllowed"] is False
    assert result["status"] == ("CYCLIC" if mask & 2 else "DAG")
    if result["status"] == "DAG":
        assert set(result["affected"]) >= {wall, opening_a, opening_b}
    # Navigator IDs must never coalesce with the physical native wall identifier.
    assert (("NAVIGATOR:PUBLICVIEWMAP:" + view) in data["nodes"]) == bool(mask & 16)
    assert (("NAVIGATOR_SOURCE_REFERENCE:" + wall) in data["nodes"]) == bool(mask & 16)
