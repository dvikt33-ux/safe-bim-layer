#!/usr/bin/env python3
"""МОАГ R08: hypothesis overlays preserve uncertainty, never change R07 truth."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import assemble_evidence_graph_r06 as assembly
import inspect_graph_structure_r06 as structure
import unified_evidence_graph_r07 as unified

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"
PROPOSALS = SYNTH / "spatial_hypotheses_r08.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def build(graph, fragments, bounds, routes, *, proposals=None):
    proposals = proposals if proposals is not None else read(PROPOSALS)
    if proposals.get("schema") != "APA-MOAG-HYPOTHESIS-PROPOSALS-R08/0.1":
        raise ValueError("HYPOTHESIS_SCHEMA_INVALID")
    if any(proposals["gates"].values()):
        raise ValueError("HYPOTHESIS_GATE_CANNOT_AUTHORIZE_GEOMETRY")
    assembled = assembly.assemble(graph, fragments, routes, bounds)
    projected = structure.project(graph, fragments, bounds, assembled)
    base = unified.build(graph, fragments, bounds, routes,
                         assembled=assembled, structural=projected)
    original_nodes = base["nodes"]
    original_edges = base["edges"]
    nodes = [dict(n) for n in original_nodes]
    edges = [dict(e) for e in original_edges]
    index = {x["id"]: x for x in original_nodes}
    existing_ids = {x["id"] for x in original_edges}
    components = base["component_membership_not_rooms_or_geometry"]
    if len(components) != len(index):
        raise ValueError("BASE_GRAPH_NOT_EXHAUSTIVE")
    source_observations = {x["id"]: x for x in graph["observations"]}
    excluded_sources = set(assembled["quarantined_foreign_station_source_observations"])
    excluded_indices = set(assembled["quarantined_foreign_station_candidate_indices"])
    physical = (graph["indexed_source_entities"] +
                graph["indexed_r03_entities"] + fragments["physical_entities"])
    physical_by_id = {x["id"]: x for x in physical}
    if len(physical_by_id) != 197:
        raise ValueError("PHYSICAL_INDEX_MISMATCH")
    prohibited_pairs = {
        frozenset((x["a"], x["b"]))
        for x in graph["permanent_identity_exclusions"]
    }
    prohibited_pairs.update(
        frozenset((x["from"], x["to"]))
        for x in fragments["typed_edges"]
        if x["relation"] == "NOT_SAME_AS"
    )
    def check_sources(sources):
        if not sources:
            raise ValueError("HYPOTHESIS_MISSING_SOURCE")
        for sid in sources:
            if sid in excluded_sources:
                raise ValueError("HYPOTHESIS_USES_FOREIGN_STATION_SOURCE")
            if sid.startswith("P-"):
                item = source_observations.get(sid)
                if not item or item["station"] != "MOAG" or item["evidence_class"] != "DIRECT_TEXT":
                    raise ValueError("HYPOTHESIS_SOURCE_NOT_PRIMARY_MOAG")
            elif not (sid.startswith(("B1-", "B2-", "B3-", "B4-", "LR-B1-", "LR-B2-",
                                      "LR-B3-", "LR-B4-"))):
                raise ValueError("HYPOTHESIS_SOURCE_ID_INVALID")

    def add_hypothesis_edge(id, a, b, sources, hypothesis_type, group, reason):
        if id in existing_ids or a not in index or b not in index or a == b:
            raise ValueError("DUPLICATE_OR_DANGLING_HYPOTHESIS_EDGE")
        check_sources(sources)
        existing_ids.add(id)
        edge = {
            "id": id, "from": a, "to": b,
            "layer": "R08_HYPOTHESIS_NOT_A_PHYSICAL_LINK",
            "source_ids": list(dict.fromkeys(sources)),
            "hypothesis_type": hypothesis_type, "choice_group": group,
            "reason": reason,
            "source_supports": "EXISTENCE_AND_CONTEXT_NOT_THIS_EXACT_PLACEMENT",
            "confidence": "ANALOGY_OR_FUNCTIONAL_PLAUSIBILITY_NOT_BOOK_PROOF",
            "joins_approved_evidence_component": False,
            "proves_direct_access": False,
            "metric_geometry_proven": False,
            "geometry_approved": False,
            "requires_new_primary_evidence": True
        }
        edges.append(edge)
        return edge

    isolates = {
        x["physical_index_id"]
        for x in assembled["unconnected_index_source_review_queue"]
        if x["spatial_inventory_role"] ==
        "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE"
    }
    groups = []
    covered = set()
    potential_cross_component_choices = 0
    for item in proposals["isolation_candidate_groups"]:
        target = item["target_index_id"]
        alternatives = item["possible_anchors"]
        sources = item["source_observation_or_page_ids"]
        if (target not in isolates or target in covered or not alternatives or
                len(set(alternatives)) != len(alternatives) or
                item["model_status"] != "HYPOTHESIS_ONLY" or
                any(item[k] for k in ("geometry_approved", "identity_approved",
                                      "access_approved"))):
            raise ValueError("HYPOTHESIS_TARGET_NOT_ISOLATED_OR_ALREADY_RESOLVED")
        covered.add(target)
        check_sources(sources)
        target_ref = physical_by_id[target]
        source_ref = set(target_ref.get("source_ids", [])) | set(
            target_ref.get("source_observation_ids", []))
        if not source_ref.intersection(sources):
            raise ValueError("TARGET_EXISTENCE_NOT_SOURCE_REFERENCED")
        choices = []
        for i, a in enumerate(alternatives, 1):
            if (a not in physical_by_id or a in excluded_indices or
                    a == target or frozenset((target, a)) in prohibited_pairs):
                raise ValueError("HYPOTHESIS_CONTRADICTS_NEGATIVE_IDENTITY")
            levels = sorted(set(index[target]["possible_global_levels"]) &
                            set(index[a]["possible_global_levels"]))
            if not levels:
                raise ValueError("HYPOTHESIS_DISJOINT_GLOBAL_LEVELS")
            edge = add_hypothesis_edge(
                "R08-PLACE:" + target + ":" + str(i),
                target, a, sources, item["group"], target, item["rationale"])
            if components[target] != components[a]:
                potential_cross_component_choices += 1
            choices.append({
                "edge_id": edge["id"], "candidate_anchor_id": a,
                "compatible_global_levels": levels,
                "would_bridge_distinct_proven_components_if_verified":
                    components[target] != components[a],
                "proves_connection": False
            })
        groups.append({
            "target_index_id": target, "known_to_exist": True,
            "exact_location_known": False, "source_ids": sources,
            "alternatives_exclusive_or_neither": True,
            "unlocated_option_always_allowed": True,
            "hypothesis_type": item["group"],
            "placement_choices": choices,
            "counterevidence_check": item["contraindication"],
            "review_status": "REQUIRES_PRIMARY_PAGE_OR_ROUTE_BRIDGE",
            "no_geometry_authorized": True})
    if covered != isolates:
        raise ValueError("NOT_ALL_UNLOCATED_FIXED_INDICES_PRESERVED:" +
                         repr(sorted(isolates - covered)))

    # The 18 explicit narrative cuts are NOT the only unknown pathways:
    # ordered route observations also leave the geometry of 306 traversed
    # intervals unlocated. Preserve them without claiming 306 physical halls.
    observed_transitions_with_unknown_geometry = [
        {
            "id": e["id"], "from_occurrence": e["from"],
            "to_occurrence": e["to"], "source_ids": e["source_ids"],
            "route_order_witnessed": True,
            "direct_door_or_same_corridor_proven": False,
            "intermediate_geometry_unknown": True,
            "number_of_intervening_physical_elements_inferred": False
        }
        for e in original_edges
        if e["id"].startswith("STEP::") and e["layer"] == "OBSERVED_TRAJECTORY"
    ]
    if len(observed_transitions_with_unknown_geometry) != (
            assembled["counts"]["source_backed_edges_by_class"][
                "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR"]):
        raise ValueError("ORDERED_ROUTE_UNCERTAINTY_NOT_FULLY_PRESERVED")
    unresolved_route_slots = []
    for gap in assembled["narrative_gaps"]:
        key = gap["route_id"] + ":" + gap["from"] + ":" + gap["to"]
        slot_id = "R08-UNKNOWN-TRANSIT:" + key
        a = "ROUTE::" + gap["route_id"] + "::" + gap["from"]
        b = "ROUTE::" + gap["route_id"] + "::" + gap["to"]
        left = index[a]["possible_global_levels"]
        right = index[b]["possible_global_levels"]
        possible = sorted(set(left) | set(right))
        cross_level = not bool(set(left) & set(right))
        virtual = {
            "id": slot_id, "layer": "HYPOTHETICAL_UNKNOWN_ROUTE_SEGMENT",
            "source_ids": gap["source_pages"],
            "possible_global_levels": possible,
            "not_a_separate_room": True,
            "physical_element_count_inferred": False,
            "presence_of_missing_route_information_proven": True,
            "specific_corridor_or_staircase_proven": False,
            "coordinates_known": False
        }
        if slot_id in index:
            raise ValueError("DUPLICATE_UNKNOWN_TRANSIT_SLOT")
        nodes.append(virtual)
        index[slot_id] = virtual
        for end, label in ((a, "LEFT"), (b, "RIGHT")):
            add_hypothesis_edge(
                "R08-GAP:" + key + ":" + label,
                end, slot_id, gap["source_pages"],
                "UNSPECIFIED_TRANSIT_SEGMENT_NOT_A_NEW_ROOM", key,
                "Narrative boundary only; no certain intervening corridor")
        unresolved_route_slots.append({
            "id": slot_id,
            "boundary_route_nodes": [a, b],
            "source_pages": gap["source_pages"],
            "possible_global_levels": possible,
            "interlevel_transition_might_be_required": cross_level,
            "alternative_explanations": (
                ["UNKNOWN_VERTICAL_TRANSIT_OR_INTERVENING_STOP",
                 "NARRATIVE_CUT_WITH_DIFFERENT_LEVELS"]
                if cross_level else
                ["UNLOCATED_CORRIDOR_OR_HATCH_OR_PASSAGE",
                 "NARRATIVE_CUT_OR_UNRECORDED_DETOUR"]),
            "no_direct_passage_concluded": True,
            "not_counted_as_physical_room": True
        })

    pattern_reviews = []
    for pattern in proposals["analogical_patterns"]:
        refs = pattern["references"]
        if not refs or len(set(refs)) != len(refs):
            raise ValueError("PATTERN_NEEDS_DISTINCT_REFERENCES")
        if any(x not in physical_by_id or x in excluded_indices for x in refs):
            raise ValueError("PATTERN_REFERENCES_UNVERIFIED_STATION")
        check_sources(pattern["source_context"])
        if pattern["produces_graph_edges"] or pattern["fixes_xy_z"]:
            raise ValueError("SYMMETRY_CANNOT_PROVE_METRIC_TOPOLOGY")
        pattern_reviews.append({
            **pattern, "status": "OPTIONAL_COMPOSITIONAL_SCENARIO_NOT_A_SOURCE_FACT",
            "physical_component_merges": 0,
            "global_decks_added": 0})

    if len({e["id"] for e in edges}) != len(edges):
        raise ValueError("DUPLICATED_GRAPH_EDGE_IDS")
    if any(e["joins_approved_evidence_component"] or
           e["proves_direct_access"] or e["metric_geometry_proven"]
           for e in edges[len(original_edges):]):
        raise ValueError("HYPOTHESIS_INCORRECTLY_PROMOTED")
    if [e for e in edges[:len(original_edges)]] != original_edges:
        raise ValueError("R07_APPROVED_EDGES_MUTATED")
    if nodes[:len(original_nodes)] != original_nodes:
        raise ValueError("R07_SOURCE_NODES_MUTATED")
    return {
        "schema": "APA-MOAG-UNCERTAINTY-PRESERVING-GRAPH-R08/0.1",
        "status": "ONE_GRAPH_WITH_SEPARATE_UNPROVEN_SPATIAL_PLACEMENTS",
        "nodes": nodes, "edges": edges,
        "inventory": {
            "approved_r07_node_count": len(original_nodes),
            "approved_r07_edge_count": len(original_edges),
            "new_unknown_route_placeholders_not_new_rooms": len(unresolved_route_slots),
            "unlocated_fixed_object_groups": len(groups),
            "alternative_placement_edges": sum(len(x["placement_choices"]) for x in groups),
            "candidate_intercomponent_choices_not_actual_merges":
                potential_cross_component_choices,
            "route_gap_candidate_edges": len(unresolved_route_slots) * 2,
            "ordered_route_transitions_with_unlocated_path_geometry":
                len(observed_transitions_with_unknown_geometry),
            "optional_compositional_pattern_scenarios": len(pattern_reviews),
            "total_nodes_including_nonphysical_placeholders": len(nodes),
            "total_relations_including_unapproved_scenarios": len(edges),
            "approved_qualitative_physical_components":
                base["inventory"]["qualitative_components_with_physical_indices"],
            "approved_explicit_access_edges": base["inventory"]["direct_access_edges"],
            "still_unknown_route_gaps": len(unresolved_route_slots),
            "area_profiles_preserved": len(projected["spatial_area_volume_profiles"]),
            "proven_metric_xy_indices": 0
        },
        "isolated_object_placement_hypotheses": groups,
        "unknown_route_segments": unresolved_route_slots,
        "witnessed_route_transitions_without_direct_door_geometry":
            observed_transitions_with_unknown_geometry,
        "nonbinding_symmetry_and_analogy_scenarios": pattern_reviews,
        "current_proven_qualitative_component_membership":
            base["component_membership_not_rooms_or_geometry"],
        "area_volume_profiles_not_summed_or_promoted":
            projected["spatial_area_volume_profiles"],
        "gates": {
            "one_master_graph_schema": True, "hypothesis_edges_are_nonconnecting": True,
            "placement_hypotheses_fix_global_decks": False,
            "symmetry_measured_or_proven": False,
            "bim_geometry_authorized": False,
            "archicad_write": False
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
    text = json.dumps(build(g, f, b, r), indent=2,
                      ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")

if __name__ == "__main__":
    main()
