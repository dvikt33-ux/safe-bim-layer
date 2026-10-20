#!/usr/bin/env python3
"""МОАГ R07: one typed, source-auditable graph without false physical unification.

The graph is unified as a data structure, not as one connected floor plan.
Access, traversal observations, containment, aliases, prohibitions and unresolved
candidate bridges are distinct edge layers; only the R06 evidence solver can
approve a qualitative connected component. Never convert annotation edges to
walkable passages or metric geometry.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import assemble_evidence_graph_r06 as assembler
import inspect_graph_structure_r06 as projections

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build(graph, fragments, bounds, routes, assembled=None, structural=None,
          explicit=None):
    assembled = assembled or assembler.assemble(graph, fragments, routes, bounds)
    structural = structural or projections.project(graph, fragments, bounds, assembled)
    explicit = explicit or read(assembler.BRIDGES)

    nodes = assembled["nodes"]
    by_id = {x["id"]: x for x in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("DUPLICATE_MASTER_NODE")
    physical = {x["id"] for x in nodes if x["layer"] == "PHYSICAL_INDEX"}
    if len(physical) != 197:
        raise ValueError("MASTER_INDEX_GRAIN_CHANGED")

    component_index = {}
    for component in assembled["connected_evidence_components"]:
        for member in component["all_node_ids"]:
            if member in component_index:
                raise ValueError("COMPONENT_MULTIPLE_MEMBERSHIPS")
            component_index[member] = component["id"]
    if set(component_index) != set(by_id):
        raise ValueError("INCOMPLETE_COMPONENT_COVERAGE")

    evidence_semantics = {e["edge_id"]: e for e in structural["evidence_relations"]}
    edges = []
    ids = set()
    def add(edge_id, a, b, layer, source_ids, *, is_physical_union=False,
            is_direct_access=False, review=None, relation=None):
        if (edge_id in ids or a not in by_id or b not in by_id
                or not source_ids or is_direct_access and not is_physical_union):
            raise ValueError("INVALID_MASTER_EDGE:" + edge_id)
        ids.add(edge_id)
        edges.append({
            "id": edge_id, "from": a, "to": b, "layer": layer,
            "source_ids": sorted(set(source_ids)),
            "relation": relation,
            "joins_approved_evidence_component": bool(is_physical_union),
            "proves_direct_access": bool(is_direct_access),
            "metric_geometry_proven": False,
            "review_status": review
        })

    for e in assembled["typed_evidence_edges"]:
        semantics = evidence_semantics[e["id"]]
        direct = semantics["physically_traversable_connection_asserted"]
        if direct:
            layer = "EXPLICIT_ACCESS"
        elif e["type"] in ("ROUTE_VISITS_INDEX",
                           "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR"):
            layer = "OBSERVED_TRAJECTORY"
        elif e["connects_evidence_graph"]:
            layer = "SOURCE_QUALITATIVE_ASSOCIATION"
        else:
            layer = "NONCONNECTING_CONTEXT"
        add(e["id"], e["from"], e["to"], layer, e["source_ids"],
            is_physical_union=e["connects_evidence_graph"],
            is_direct_access=direct,
            relation=e.get("detail", {}).get("relation")
            if isinstance(e.get("detail"), dict) else None)

    # A source concept is a *referential proxy* for a refined object, never an
    # access route or a proof of equal planimetric extent.
    for p in structural["source_concept_to_refined_object_accounting_guards"]:
        add("ALIAS-CONTEXT:" + p["source_concept_id"],
            p["source_concept_id"], p["refined_index_id"],
            "REFERENT_CROSSWALK_NOT_PHYSICAL_IDENTITY",
            p["source_page_ids"],
            review=p["identity_status"], relation="CANDIDATE_REFERENT")
    for x in graph["permanent_identity_exclusions"]:
        add("PERMANENT-EXCLUSION:" + x["issue_id"], x["a"], x["b"],
            "PROHIBITED_IDENTITY_MERGE", x["evidence"],
            review=x["status"], relation="MUST_KEEP_DISTINCT")
    foreign = set(assembled["quarantined_foreign_station_candidate_indices"])
    for x in fragments["typed_edges"]:
        if x["relation"].startswith("NOT_"):
            layer = ("UNVERIFIED_STATION_PROVENANCE"
                     if x["from"] in foreign or x["to"] in foreign
                     else "PROHIBITED_IDENTITY_OR_INFERENCE")
            add("R05-NEGATIVE:" + x["id"], x["from"], x["to"], layer,
                x["source_ids"], review=x["certainty"],
                relation=x["relation"])

    resolved, rejected, candidates = [], [], []
    approved = {e["id"]: e for e in assembled["typed_evidence_edges"]}
    for h in explicit.get("deferred_hypotheses", []):
        if h.get("status", "").startswith("RESOLVED_"):
            adopted = approved.get(h.get("superseded_by"))
            if (not adopted or
                    {adopted["from"], adopted["to"]} !=
                    {h["from"], h["to"]} or
                    not adopted["connects_evidence_graph"]):
                raise ValueError("RESOLVED_HYPOTHESIS_MISSING_APPROVED_LINK")
            resolved.append({"hypothesis_id": h["id"],
                             "accepted_edge_id": h["superseded_by"],
                             "additional_source": h.get("additional_scene_source")})
            continue
        if h.get("status", "").startswith("REJECTED_"):
            rejected.append({"hypothesis_id": h["id"], "from": h["from"],
                             "to": h["to"], "reason": h["reason"],
                             "status": h["status"]})
            add("REJECTED:" + h["id"], h["from"], h["to"],
                "REJECTED_INFERENCE_NOT_A_CONNECTION", h["source_ids"],
                review=h["status"])
            continue
        a, b = h["from"], h["to"]
        if a not in physical or b not in physical or h["approved_as_connection"]:
            raise ValueError("INVALID_UNRESOLVED_HYPOTHESIS")
        endpoint_levels = [set(by_id[z]["possible_global_levels"]) for z in (a, b)]
        if not endpoint_levels[0] & endpoint_levels[1]:
            raise ValueError("CANDIDATE_DISJOINT_GLOBAL_LEVELS")
        candidates.append({
            "id": h["id"], "from": a, "to": b,
            "source_ids": h["source_ids"],
            "left_component": component_index[a],
            "right_component": component_index[b],
            "could_bridge_evidence_components":
                component_index[a] != component_index[b],
            "only_after_new_identity_or_route_proof": True,
            "status": "NOT_APPROVED_AS_GRAPH_CONNECTOR"})
        add("CANDIDATE:" + h["id"], a, b,
            "UNVERIFIED_CANDIDATE_NOT_A_CONNECTION", h["source_ids"],
            review="NEW_PRIMARY_EVIDENCE_REQUIRED")

    for gap in assembled["narrative_gaps"]:
        a = "ROUTE::" + gap["route_id"] + "::" + gap["from"]
        b = "ROUTE::" + gap["route_id"] + "::" + gap["to"]
        add("MISSING-TRANSIT:" + gap["route_id"] + "::" +
            gap["from"] + "::" + gap["to"], a, b,
            "DOCUMENTED_GAP_NO_ROUTE_LINK", gap["source_pages"],
            review="DO_NOT_ASSUME_ADJACENCY")

    # Each node belongs to the one master graph, even if its physical
    # connectivity component has no confirmed links.
    role_counts = Counter()
    for n in nodes:
        if n["layer"] == "PHYSICAL_INDEX":
            role_counts["PHYSICAL_INDEX"] += 1
        else:
            role_counts["ROUTE_OCCURRENCE"] += 1
    edge_classes = dict(sorted(Counter(x["layer"] for x in edges).items()))
    direct = [x for x in edges if x["proves_direct_access"]]
    physical_component_count = len({
        component_index[x] for x in physical})
    source_direct_count = len(structural["direct_access_graph"]["edges"])
    if len(direct) != source_direct_count:
        raise ValueError("ACCESS_COUNT_CONFLICT_WITH_STRUCTURAL_GRAPH")
    if (physical_component_count !=
            assembled["counts"]["after_routes_physical_components"]):
        raise ValueError("PHYSICAL_COMPONENT_COUNT_CONFLICT")
    if not all(not e["proves_direct_access"] and
               not e["joins_approved_evidence_component"]
               for e in edges if e["layer"] in (
                   "DOCUMENTED_GAP_NO_ROUTE_LINK",
                   "UNVERIFIED_CANDIDATE_NOT_A_CONNECTION",
                   "REJECTED_INFERENCE_NOT_A_CONNECTION",
                   "PROHIBITED_IDENTITY_OR_INFERENCE",
                   "PROHIBITED_IDENTITY_MERGE",
                   "REFERENT_CROSSWALK_NOT_PHYSICAL_IDENTITY")):
        raise ValueError("CONTEXT_OR_NEGATIVE_PROMOTED_TO_ACCESS")

    return {
        "schema": "APA-MOAG-UNIFIED-EVIDENCE-GRAPH-R07/0.1",
        "status": "ONE_INVENTORY_MULTIPLE_RELATION_LAYERS_NOT_A_CONTINUOUS_BIM_PLAN",
        "nodes": nodes, "edges": edges,
        "inventory": {
            "physical_or_conceptual_indices": len(physical),
            "route_occurrences": role_counts["ROUTE_OCCURRENCE"],
            "all_vertices": len(nodes), "all_typed_relations": len(edges),
            "relation_layers": edge_classes,
            "qualitative_components_with_physical_indices": physical_component_count,
            "isolated_physical_or_conceptual_indices":
                assembled["counts"]["isolated_physical_indices"],
            "direct_access_edges": len(direct),
            "direct_access_components":
                structural["direct_access_graph"]["component_count"],
            "source_alias_crosswalks": edge_classes.get(
                "REFERENT_CROSSWALK_NOT_PHYSICAL_IDENTITY", 0),
            "resolved_obsolete_hypotheses": len(resolved),
            "rejected_invalid_hypotheses": len(rejected),
            "open_connector_hypotheses": len(candidates),
            "narrative_gaps_not_joined": edge_classes.get(
                "DOCUMENTED_GAP_NO_ROUTE_LINK", 0)
        },
        "potential_connectors_for_new_primary_review": candidates,
        "resolved_obsolete_hypotheses": resolved,
        "rejected_invalid_hypotheses": rejected,
        "component_membership_not_rooms_or_geometry": component_index,
        "source_component_summary": [
            {"component_id": x["id"],
             "indexed_member_ids": x["physical_index_ids"],
             "route_steps": x["route_occurrence_count"],
             "no_verified_global_XY": True}
            for x in assembled["connected_evidence_components"]
            if x["physical_index_ids"]],
        "gates": {
            "all_graph_items_have_one_source_aware_model": True,
            "one_qualitative_spatial_component": physical_component_count == 1,
            "all_paths_walkable": False, "metric_XY_Z_proven": False,
            "local_mezzanines_equal_global_decks": False,
            "bim_authorized": False, "archicad_write": False
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    g = read(SYNTH / "full_indexed_parametric_graph_r04.json")
    f = read(SYNTH / "progressive_fragments_r05.json")
    b = read(SYNTH / "area_volume_bounds_r05.json")
    r = read(BASE / "v2/character_routes.json")
    output = build(g, f, b, r)
    payload = json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
