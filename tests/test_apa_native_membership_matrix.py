"""128 hierarchical native-assembly relationship variations; no Archicad transport."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_native_dependency_flow import dependency_inputs
from archicad_local_modules import dependency_impact


def ident(value):
    return {"guid": value}


@pytest.mark.parametrize("case", range(128))
def test_native_component_membership_parent_root_matrix(case):
    parent, root = f"P_{case}", f"ROOT_{case}"
    count = 1 + ((case * 7) % 6)
    children = [f"PART_{case}_{i}" for i in range(count)]
    parent_ok, root_ok = bool(case & 1), bool(case & 2)
    rows = [
        dict(elementId=ident(ch), parentElementId=ident(parent),
             rootElementId=ident(root), parentQueryError=0 if parent_ok else -1,
             rootQueryError=0 if root_ok else -1,
             declaredOwnerId=ident(root if case & 16 else parent))
        for ch in children
    ]
    if case & 64:
        rows.append(dict(elementId=ident(f"UNBOUND_{case}"), parentQueryError=-1,
                         rootQueryError=-1))
    memberships = [dict(parentElementId=ident(parent),
                        subelements={"panels": [dict(elementId=ident(ch)) for ch in children]})]
    if case & 8:
        memberships.append(dict(parentElementId=ident("NOT_VERIFIED"),
                                subelements={"error": {"code": -1}}))
    if case & 32:
        memberships.append(dict(parentElementId=ident(root), subelements={"frames": []}))
    result = dependency_inputs(memberships=memberships, components={"elements": rows})
    expected_edges = {(parent, ch) for ch in children}
    if root_ok:
        expected_edges |= {(root, ch) for ch in children}
    assert {tuple(edge) for edge in result["edges"]} == expected_edges
    expected_nodes = {parent, *children}
    if root_ok or case & 32:
        expected_nodes.add(root)
    if case & 64:
        expected_nodes.add(f"UNBOUND_{case}")
    assert set(result["nodes"]) == expected_nodes
    assert len(result["relationshipEvidence"]) == len(expected_edges)
    assert result["omitted"].count("MEMBERSHIP_PARENT_OR_NATIVE_RESULT_MISSING") == bool(case & 8)
    assert result["omitted"].count("DECLARED_OWNER_DIFFERS_FROM_PARENT_NO_INFERRED_EDGE") == (
        count if parent_ok and case & 16 else 0
    )
    impact = dependency_impact(result["nodes"], result["edges"], [parent])
    assert impact["status"] == "DAG"
    assert set(impact["affected"]) == {parent, *children}
    assert impact["executionAllowed"] is False
