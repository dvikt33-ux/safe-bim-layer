"""128 real-shape synthetic Generic Opening host/linked opening combinations."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_native_dependency_flow import dependency_inputs


def ident(value):
    return {"guid": value}


@pytest.mark.parametrize("mask", range(128))
def test_opening_host_cut_and_reverse_edges_are_distinct(mask):
    opening, host = f"OPEN_{mask}", f"HOST_{mask}"
    linked, cut = f"LINK_{mask}", f"CUT_{mask}"
    connected = ([ident(linked)] if mask & 8 else [])
    if mask & 16:
        connected.append(ident(opening))  # self-edge must not be emitted
    if mask & 32:
        connected.append(ident(linked))   # duplicate must not be emitted
    cut_elements = ([ident(host)] if mask & 2 else []) + ([ident(cut)] if mask & 4 else [])
    items = [dict(elementId=ident(opening), hostElementId=ident(host),
                  parentResolved=bool(mask & 1), connectedOpenings=connected,
                  cutElements=cut_elements)]
    if mask & 64:
        items.append(dict(error={"code": -1}))
    result = dependency_inputs(openings={"elements": items})
    expected = set()
    if mask & 1 or mask & 2:
        expected.add((host, opening))
    if mask & 4:
        expected.add((cut, opening))
    if mask & 8 or mask & 32:
        expected.add((opening, linked))
    assert {tuple(v) for v in result["edges"]} == expected
    assert len(result["relationshipEvidence"]) == len(expected)
    assert set(result["nodes"]) == {opening} | {k for pair in expected for k in pair}
    assert result["omitted"].count("OPENING_ERROR_OR_ID_MISSING") == bool(mask & 64)
    assert all(a != b for a, b in result["edges"])
    assert result["authority"] == "CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT"
