"""128 Navigator/Drawing identity, map, deleted-view and ambiguous ownership cases."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_native_dependency_flow import dependency_inputs


def ident(value):
    return {"guid": value}


@pytest.mark.parametrize("mask", range(128))
def test_drawing_navigator_sources_never_become_physical_guids(mask):
    view, drawing, db = f"VIEW_{mask}", f"DRAW_{mask}", f"DB_{mask}"
    layout, source = f"LAYOUT_{mask}", f"REF_{mask}"
    match = bool(mask & 1) and bool(mask & 2)
    items = [dict(navigatorItemId=ident(view), requestedMap="PublicViewMap",
                  identityMatchesRequest=bool(mask & 1),
                  mapMatchesRequest=bool(mask & 2), sourceGuid=ident(source))]
    if mask & 32:
        items.append(dict(navigatorItemId=ident(view), requestedMap="OtherViewMap",
                          identityMatchesRequest=True, mapMatchesRequest=True,
                          sourceGuid=ident(f"REF_OTHER_{mask}")))
    layouts = [dict(databaseId=ident(db), navigatorItemId=ident(layout))]
    if mask & 64:
        layouts.append(dict(databaseId=ident(db), navigatorItemId=ident(f"LAYOUT_ALT_{mask}")))
    result = dependency_inputs(
        navigator_bindings={"items": items}, layout_bindings=layouts,
        view_ids=[view] if mask & 16 else [],
        drawings={"drawings": [dict(elementId=ident(drawing), databaseId=ident(db),
             databaseQualified=bool(mask & 8), linkGuid=ident(view),
             viewDeleted=not bool(mask & 4))]})
    expected = set()
    primary = "NAVIGATOR:PUBLICVIEWMAP:" + view
    alternate = "NAVIGATOR:OTHERVIEWMAP:" + view
    if match:
        expected.add(("NAVIGATOR_SOURCE_REFERENCE:" + source, primary))
    if mask & 32:
        expected.add(("NAVIGATOR_SOURCE_REFERENCE:REF_OTHER_" + str(mask), alternate))
    if mask & 8 and not mask & 64:
        expected.add((drawing, "NAVIGATOR:LAYOUTBOOK:" + layout))
    # A single verified OtherViewMap entry may be the only resolved source.
    # An explicit trusted view ID takes precedence; two inferred maps are ambiguous.
    resolved_source = None
    if mask & 16:
        resolved_source = primary
    elif match and not mask & 32:
        resolved_source = primary
    elif not match and mask & 32:
        resolved_source = alternate
    if mask & 4 and resolved_source:
        expected.add((resolved_source, drawing))
    assert {tuple(edge) for edge in result["edges"]} == expected
    assert len(result["relationshipEvidence"]) == len(expected)
    assert result["omitted"].count(
        "DRAWING_SOURCE_NOT_IN_CAPTURED_OR_EXPLICITLY_RESOLVED_NAVIGATOR"
    ) == (not bool(mask & 4 and resolved_source))
    assert source not in result["nodes"]     # source reference is namespaced
    assert view not in result["nodes"]       # navigator identity is namespaced
    assert drawing in result["nodes"]
