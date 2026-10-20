#!/usr/bin/env python3
"""МОАГ R09: reconcile both R08 hypothesis registers without losing an unknown feature.

Endpoint-equivalent hypotheses are cross-referenced, never counted as
independent spatial evidence. Composed edges remain nonbinding; source
topology and area calculations are strictly unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import hypothesis_overlay_r08 as r08a
import hypothetical_structure_r08 as r08b

SYNTH = r08a.SYNTH
BASE = r08a.BASE


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pair(x):
    return frozenset((x["from"], x["to"]))


def build(graph, fragments, bounds, routes, *, left=None, right=None):
    left = left or r08a.build(graph, fragments, bounds, routes)
    right = right or r08b.build(graph, fragments, bounds, routes)
    original_nodes = left["unified_evidence_graph"]["nodes"]
    original_edges = left["unified_evidence_graph"]["edges"]
    nproof = len(original_nodes)
    eproof = len(original_edges)

    # Both derived R08 constructions MUST originate from precisely the same
    # R07 proof graph; merely having the same counts is insufficient.
    if (right["nodes"][:nproof] != original_nodes or
            right["edges"][:eproof] != original_edges):
        raise ValueError("R08_PROVEN_GRAPHS_DIVERGED")
    if left["composed_graph"]["nodes"][:nproof] != original_nodes or (
            left["composed_graph"]["edges"][:eproof] != original_edges):
        raise ValueError("R08_PRIMARY_PROVEN_PREFIX_MUTATED")
    if set(x["id"] for x in right["nodes"][nproof:]) & {
            x["id"] for x in original_nodes}:
        raise ValueError("SECOND_R08_UNKNOWN_SLOT_IS_A_PROVEN_ROOM")

    # The two builders have different IDs for each unobserved interval.
    # One canonical placeholder is retained with both legacy IDs as aliases.
    route_gaps_a = {}
    for x in left["unknown_transits"]:
        key = (x["route_id"], *x["between"])
        if key in route_gaps_a:
            raise ValueError("DUPLICATED_PRIMARY_ROUTE_GAP")
        route_gaps_a[key] = x
    route_gaps_b = {}
    for x in right["unknown_route_segments"]:
        ends = x["boundary_route_nodes"]
        if len(ends) != 2 or not ends[0].startswith("ROUTE::") or (
                not ends[1].startswith("ROUTE::")):
            raise ValueError("INVALID_SECONDARY_ROUTE_GAP")
        a = ends[0].split("::")
        b = ends[1].split("::")
        if len(a) != 3 or len(b) != 3 or a[1] != b[1]:
            raise ValueError("CROSS_ROUTE_GAP_CONFLATED")
        key = (a[1], a[2], b[2])
        if key in route_gaps_b:
            raise ValueError("DUPLICATED_SECONDARY_ROUTE_GAP")
        route_gaps_b[key] = x
    if set(route_gaps_a) != set(route_gaps_b):
        raise ValueError("DIFFERENT_UNOBSERVED_ROUTE_BOUNDARIES")
    gap_aliases = []
    for key, x in route_gaps_a.items():
        y = route_gaps_b[key]
        if (set(x["source_pages"]) != set(y["source_pages"]) or
                set(x["candidate_level_domain"]) != set(y["possible_global_levels"])):
            raise ValueError("R08_ROUTE_GAP_PROVENANCE_OR_LEVEL_CONFLICT")
        gap_aliases.append({
            "route_id": key[0], "step_ids": list(key[1:]),
            "canonical_hypothetical_node_id": x["hypothetical_node_id"],
            "secondary_register_alias": y["id"],
            "same_missing_information_not_two_physical_corridors": True,
            "no_intermediate_room_count_proven": True
        })

    nodes = list(left["composed_graph"]["nodes"])
    edges = list(left["composed_graph"]["edges"])
    node_ids = {x["id"] for x in nodes}
    edge_ids = {x["id"] for x in edges}
    original_node_ids = {x["id"] for x in original_nodes}
    if len(node_ids) != len(nodes) or len(edge_ids) != len(edges):
        raise ValueError("PRIMARY_R08_DUPLICATE_IDS")

    variants = [x for x in left["hypothetical_edges"]
                if x["layer"] == "HYPOTHETICAL_SYMMETRY_OR_FUNCTIONAL_LAYOUT"]
    variants_by_pair = {}
    for x in variants:
        variants_by_pair.setdefault(pair(x), []).append(x)
    placement_edges_b = [
        x for x in right["edges"][eproof:]
        if x["id"].startswith("R08-PLACE:")
    ]
    if len(placement_edges_b) != right["inventory"]["alternative_placement_edges"]:
        raise ValueError("SECONDARY_R08_PLACEMENTS_NOT_EXHAUSTIVE")
    source_ids_a = {x["id"] for x in variants}
    canonical_choices = []
    equivalent_choices = []
    crosswalk_map = {}
    for x in placement_edges_b:
        if x["from"] not in original_node_ids or x["to"] not in original_node_ids:
            raise ValueError("PLACEMENT_DOES_NOT_REFERENCE_KNOWN_ELEMENT")
        if (x["joins_approved_evidence_component"] or x["proves_direct_access"] or
                x["metric_geometry_proven"]):
            raise ValueError("SECONDARY_PROPOSAL_PROMOTED_TO_PHYSICAL_EVIDENCE")
        overlaps = variants_by_pair.get(pair(x), [])
        if overlaps:
            # Same potential index pair but potentially *different* reason
            # and semantic spatial pattern; no declaration of identical proof.
            canonical_ids = sorted(y["id"] for y in overlaps)
            equivalent_choices.append({
                "secondary_option_id": x["id"],
                "already_visible_in_primary_variant_ids": canonical_ids,
                "same_pair_only_not_equivalent_spatial_hypothesis": True,
                "original_reason": x["reason"],
                "original_source_ids": x["source_ids"],
                "source_reconciliation_required": True
            })
            crosswalk_map[x["id"]] = canonical_ids
        else:
            if x["id"] in edge_ids:
                raise ValueError("ALTERNATIVE_OPTION_EDGE_ID_COLLISION")
            x = dict(x)
            x["model_status"] = "OPTION_NOT_SELECTED_NOT_PROVEN"
            x["duplicate_source_register"] = "R08_PLACEMENT_OPTION"
            x["connects_proven_components"] = False
            x["direct_access_proven"] = False
            x["not_a_direct_door"] = True
            edge_ids.add(x["id"])
            edges.append(x)
            canonical_choices.append(x)
            crosswalk_map[x["id"]] = [x["id"]]

    groups = []
    for item in right["isolated_object_placement_hypotheses"]:
        ids = [choice["edge_id"] for choice in item["placement_choices"]]
        if len(ids) != 2 or len(set(ids)) != 2:
            raise ValueError("PLACEMENT_GROUP_CHOICES_NOT_EXCLUSIVE_PAIR")
        if not item["unlocated_option_always_allowed"]:
            raise ValueError("UNLOCATED_PLACEHOLDER_MUST_REMAIN_AVAILABLE")
        groups.append({
            "target_index_id": item["target_index_id"],
            "source_ids": item["source_ids"],
            "source_model": "R08_ISOLATED_STATIONARY_OBJECT",
            "not_selected": True,
            "none_of_the_above_is_allowed": True,
            "original_option_ids": ids,
            "canonical_edge_ids": [crosswalk_map[x] for x in ids],
            "counterevidence_check": item["counterevidence_check"]
        })
    isolated = {x["index_id"] for x in left["unlocated_fixed_stational_elements"]}
    if {x["target_index_id"] for x in groups} != isolated:
        raise ValueError("ISOLATED_FIXED_OBJECT_COVERAGE_CONFLICT")

    core_edges = edges[:eproof]
    if core_edges != original_edges or nodes[:nproof] != original_nodes:
        raise ValueError("R09_INADVERTENTLY_CHANGED_SOURCE_EVIDENCE")
    hypothesis_edges = edges[eproof:]
    if any(x.get("joins_approved_evidence_component", False) or
           x.get("proves_direct_access", False) or
           x.get("direct_access_proven", False) or
           x.get("connects_proven_components", False) or
           x.get("metric_geometry_proven", True)
           for x in hypothesis_edges):
        raise ValueError("R09_SOFT_EDGE_ESCAPED_TO_EVIDENCE_GRAPH")
    if len({x["id"] for x in edges}) != len(edges):
        raise ValueError("R09_DUPLICATE_GRAPH_EDGE")

    return {
        "schema": "APA-MOAG-RECONCILED-HYPOTHESIS-OVERLAY-R09/0.1",
        "status": "ONE_MASTER_GRAPH_WITH_NONBINDING_ALTERNATIVES",
        "nodes": nodes, "edges": edges,
        "source_invariants": {
            "proven_nodes": nproof, "proven_edges": eproof,
            "proven_components": left["counts"]["proven_components_unchanged"],
            "approved_direct_access": left["unified_evidence_graph"][
                "proven_direct_access_edges"],
            "preserves_R07_exact_nodes_and_edges": True
        },
        "gap_placeholders": gap_aliases,
        "unlocated_fixed_element_options": groups,
        "all_197_unlocated_index_provenance": left[
            "entire_unplaced_index_register"],
        "witnessed_route_steps_with_unresolved_intermediate_geometry": right[
            "witnessed_route_transitions_without_direct_door_geometry"],
        "conceptual_symmetry_and_nonsymmetry_patterns": right[
            "nonbinding_symmetry_and_analogy_scenarios"],
        "layout_alternative_groups": left["mutually_alternative_layout_groups"],
        "overlapping_proposals_kept_as_cross_references": equivalent_choices,
        "additional_soft_placement_edges": canonical_choices,
        "quantities": {
            "total_vertices": len(nodes), "total_typed_edges": len(edges),
            "hypothetical_vertices": len(nodes) - nproof,
            "hypothetical_edges": len(hypothesis_edges),
            "primary_layout_variant_count": len(variants),
            "secondary_placement_variant_count": len(placement_edges_b),
            "cross_referenced_same_endpoint_candidates": len(equivalent_choices),
            "distinct_secondary_placement_edges_added": len(canonical_choices),
            "fixed_objects_with_multiple_options": len(groups),
            "unknown_route_gaps_reconciled": len(gap_aliases),
            "observed_transitions_still_without_direct_geometry": len(
                right["witnessed_route_transitions_without_direct_door_geometry"]),
            "unselected_compositional_patterns": len(right[
                "nonbinding_symmetry_and_analogy_scenarios"]),
            "edge_layers": dict(sorted(Counter(
                x["layer"] for x in hypothesis_edges).items()))
        },
        "gates": {
            "R07_unchanged": True,
            "hypothesis_may_merge_evidence_components": False,
            "hints_are_not_metric_coordinates": True,
            "unobserved_route_gap_is_not_confirmed_corridor": True,
            "symmetry_is_never_mandatory": True,
            "hypothetical_global_extra_decks": False,
            "archicad_write": False,
            "BIM_release_approved": False
        }
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    g = read(SYNTH / "full_indexed_parametric_graph_r04.json")
    f = read(SYNTH / "progressive_fragments_r05.json")
    b = read(SYNTH / "area_volume_bounds_r05.json")
    r = read(BASE / "v2/character_routes.json")
    out = build(g, f, b, r)
    text = json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
