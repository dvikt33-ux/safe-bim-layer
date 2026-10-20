#!/usr/bin/env python3
"""МОАГ R08: retain unlocated elements and plausible alternatives *without* graph union.

Unobserved route interval != a proven corridor. A possible annular or radial
organisation is a falsifiable model option, not an inference of symmetry.
The R07 proven 575-node / 761-edge graph is retained byte-for-byte in
its logical node/edge records. No Archicad execution or metric coordinates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import assemble_evidence_graph_r06 as r06
import unified_evidence_graph_r07 as r07

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"
OPTIONS = SYNTH / "hypothetical_placement_options_r08.json"
LEVEL_ANCHORS = {1: "M-STA-L1-001",
                 2: "M-STA-L2-001",
                 3: "M-STA-L3-001"}
STATIONARY = "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE"
WEAK_BASES = {
    "REPEATED_FUNCTION_ANALOGY", "RADIAL_SYMMETRY_CONCEPT_ONLY",
    "RING_AND_RADIAL_SYMMETRY_CONCEPT_ONLY",
    "CIRCULATION_TOPOLOGY_ALTERNATIVE",
    "LOCAL_RING_SYMMETRY_CONCEPT_ONLY",
    "NON_SYMMETRIC_ALTERNATIVE", "CIRCULAR_SERVICE_PATTERN_OPTION",
}
PROHIBITED = {
    "PROHIBITED_IDENTITY_MERGE", "PROHIBITED_IDENTITY_OR_INFERENCE",
    "REJECTED_INFERENCE_NOT_A_CONNECTION",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build(g, f, b, routes, *, master=None, source=None, option_file=None):
    master = master or r07.build(g, f, b, routes)
    source = source or r06.assemble(g, f, routes, b)
    option_file = option_file or read(OPTIONS)
    if option_file.get("schema") != "APA-MOAG-HYPOTHETICAL-PLACEMENT-OPTIONS-R08/0.1":
        raise ValueError("INVALID_R08_OPTION_SCHEMA")
    base_nodes = master["nodes"]
    base_edges = master["edges"]
    node = {n["id"]: n for n in base_nodes}
    if len(node) != len(base_nodes):
        raise ValueError("R07_NODES_NOT_UNIQUE")
    original_ids = set(node)
    original_edges = {e["id"] for e in base_edges}
    physical = {id for id, n in node.items() if n["layer"] == "PHYSICAL_INDEX"}
    quarantined = set(source["quarantined_foreign_station_candidate_indices"])
    documented = {x["id"]: x for x in g["observations"]}
    component = master["component_membership_not_rooms_or_geometry"]
    blocked_pairs = {
        frozenset((x["a"], x["b"]))
        for x in g["permanent_identity_exclusions"]
    }
    blocked_pairs.update(frozenset((e["from"], e["to"]))
                         for e in master["edges"]
                         if e["layer"] in PROHIBITED)
    if set(LEVEL_ANCHORS.values()) - physical:
        raise ValueError("GLOBAL_LEVEL_ANCHORS_MISSING")

    guessed_nodes = []
    guessed_edges = []
    issued = set(original_edges)
    node_ids = set(original_ids)
    def add_node(x):
        if x["id"] in node_ids:
            raise ValueError("DUPLICATED_R08_HYPOTHETICAL_NODE")
        node_ids.add(x["id"])
        guessed_nodes.append(x)

    def add_edge(e):
        if (e["id"] in issued or e["from"] not in node_ids or
                e["to"] not in node_ids or not e["source_ids"] or
                e["connects_proven_components"] is not False or
                e["direct_access_proven"] is not False or
                e["metric_geometry_proven"] is not False):
            raise ValueError("R08_HYPOTHESIS_PROMOTED_OR_INVALID")
        issued.add(e["id"])
        guessed_edges.append(e)

    # These are 18 observed *boundaries* of missing route detail, not
    # 18 proven architectural corridors or fresh room identities.
    unknown_transits = []
    for i, gap in enumerate(source["narrative_gaps"], 1):
        a = "ROUTE::" + gap["route_id"] + "::" + gap["from"]
        z = "ROUTE::" + gap["route_id"] + "::" + gap["to"]
        if a not in node or z not in node:
            raise ValueError("UNLOCATED_GAP_ENDPOINT")
        la = set(node[a]["possible_global_levels"])
        lz = set(node[z]["possible_global_levels"])
        intersection = la & lz
        crosses = not bool(intersection)
        candidate_domain = sorted(intersection if intersection else la | lz)
        hidden = f"H08-UNKNOWN-TRANSIT-{i:02d}"
        src = sorted(set(gap["source_pages"]))
        add_node({
            "id": hidden, "layer": "HYPOTHETICAL_UNOBSERVED_ROUTE_INTERVAL",
            "source_ids": src, "possible_global_levels": candidate_domain,
            "physical_corridor_exists_proven": False,
            "possible_in_narrative_ellipsis_without_new_room": True,
            "possible_change_of_global_level": crosses,
            "unmeasured_length": True, "not_a_separate_room": True,
            "absolute_XY": None, "absolute_Z": None
        })
        for side, endpoint in (("ENTRY", a), ("EXIT", z)):
            add_edge({
                "id": hidden + "::" + side, "from": endpoint, "to": hidden,
                "source_ids": src,
                "layer": "HYPOTHETICAL_GAP_SEGMENT_NOT_CONFIRMED_PATH",
                "model_status": "UNOBSERVED_ROUTE_BOUNDARY",
                "connects_proven_components": False,
                "direct_access_proven": False, "metric_geometry_proven": False,
                "may_be_vertical_transition": crosses,
                "asserts_construction_of_room_or_corridor": False,
                "rejection_test": "Find a page confirming a direct step with no hidden interval or identify the actual intermediate connection"
            })
        unknown_transits.append({
            "route_id": gap["route_id"], "between": [gap["from"], gap["to"]],
            "hypothetical_node_id": hidden,
            "source_pages": src, "candidate_level_domain": candidate_domain,
            "vertical_transition_unresolved": crosses,
            "missing_route_detail_is_not_proof_of_built_passage": True
        })

    # Placeholders link an *already indexed* room to a possible level
    # envelope. They express neither a direct entrance nor XY placement.
    unlocated_fixed = []
    for row in source["unconnected_index_source_review_queue"]:
        if row["spatial_inventory_role"] != STATIONARY:
            continue
        name = row["physical_index_id"]
        if name not in physical or name in quarantined:
            raise ValueError("INVALID_FIXED_UNLOCATED_SUBJECT")
        levels = node[name]["possible_global_levels"]
        if not levels or any(x not in LEVEL_ANCHORS for x in levels):
            raise ValueError("INVALID_GLOBAL_LEVEL_DOMAIN")
        links = []
        for lev in levels:
            anchor = LEVEL_ANCHORS[lev]
            linkid = f"H08-SCOPE::{name}::L{lev}"
            add_edge({
                "id": linkid, "from": name, "to": anchor,
                "source_ids": row["source_ids"],
                "layer": "HYPOTHETICAL_LOCATION_SCOPE_NOT_ACCESS",
                "model_status": "KNOWN_OR_CANDIDATE_GLOBAL_LEVEL_ONLY",
                "connects_proven_components": False,
                "direct_access_proven": False, "metric_geometry_proven": False,
                "asserts_floor_plate_or_xy": False,
                "rejection_test": "Locate a source with an incompatible global level or establish an exact local sector"
            })
            links.append(linkid)
        unlocated_fixed.append({
            "index_id": name, "name": row["name"],
            "kind": row["kind"], "documented_sources": row["source_ids"],
            "global_level_candidates": levels,
            "level_scope_link_ids": links,
            "unplaced_detail_preserved": True,
            "not_automatically_attached_to_any_access_edge": True
        })

    # Curated spatial patterns are *mutually alternative interpretations*
    # within a local sector. Similarity and ring terminology alone never
    # establish station-wide symmetry, axis directions or door counts.
    variants = []
    groups = []
    for gspec in option_file["alternative_groups"]:
        choices = gspec["options"]
        if len(choices) < 2:
            raise ValueError("SYMMETRY_OPTION_REQUIRES_ASYMMETRIC_ALTERNATIVE")
        members = []
        for opt in choices:
            a, z = opt["from"], opt["to"]
            if a not in physical or z not in physical or a in quarantined or z in quarantined:
                raise ValueError("HYPOTHESIS_UNKNOWN_OR_FOREIGN_STATION_ENDPOINT")
            if frozenset((a, z)) in blocked_pairs:
                raise ValueError("PROHIBITED_IDENTITY_AS_SPATIAL_HYPOTHESIS")
            if not set(node[a]["possible_global_levels"]) & set(
                    node[z]["possible_global_levels"]):
                raise ValueError("HYPOTHESIS_DISJOINT_LEVELS")
            if opt["basis"] not in WEAK_BASES:
                raise ValueError("UNRECOGNISED_HYPOTHESIS_BASIS")
            if (not opt["reason"] or not opt["falsifier"] or
                    opt["id"] in members):
                raise ValueError("HYPOTHESIS_UNFALSIFIABLE_OR_DUPLICATE")
            for sid in gspec["source_ids"]:
                if (sid not in documented or
                        documented[sid]["station"] != "MOAG"):
                    raise ValueError("HYPOTHESIS_SOURCE_NOT_MOAG")
            lev = sorted(set(node[a]["possible_global_levels"]) &
                         set(node[z]["possible_global_levels"]))
            add_edge({
                "id": opt["id"], "from": a, "to": z,
                "source_ids": gspec["source_ids"],
                "layer": "HYPOTHETICAL_SYMMETRY_OR_FUNCTIONAL_LAYOUT",
                "model_status": "OPTION_NOT_SELECTED_NOT_PROVEN",
                "relation": opt["relation"], "basis": opt["basis"],
                "possible_global_levels": lev,
                "reason": opt["reason"],
                "rejection_test": opt["falsifier"],
                "alternative_group": gspec["group_id"],
                "connects_proven_components": False,
                "direct_access_proven": False, "metric_geometry_proven": False,
                "would_bridge_qualitative_components":
                    component[a] != component[z],
                "does_not_assert_a_direct_door": True,
                "does_not_infer_new_global_deck": True,
            })
            members.append(opt["id"])
            variants.append({
                "id": opt["id"], "alternative_group": gspec["group_id"],
                "source_ids": gspec["source_ids"],
                "certainty": "SPECULATIVE_NOT_PRIMARY_TEXT_PROOF",
                "could_connect_proven_components_if_later_verified":
                    component[a] != component[z],
                "selected_as_reconstruction": False,
                "rejection_test": opt["falsifier"]
            })
        groups.append({
            "id": gspec["group_id"], "question": gspec["question"],
            "source_ids": gspec["source_ids"],
            "mutually_alternative_conceptual_models": members,
            "selected_variant": None,
            "applies_stationwide_symmetry": False
        })

    # R07 remains strictly immutable. Even *following* all speculative links
    # through a viz tool does not authorize union-find or geometric export.
    if (len(master["nodes"]) != len(base_nodes) or
            len(master["edges"]) != len(base_edges) or
            master["inventory"]["qualitative_components_with_physical_indices"] !=
            source["counts"]["after_routes_physical_components"]):
        raise ValueError("R08_CHANGED_PROVEN_EVIDENCE_GRAPH")
    layers = dict(sorted(Counter(x["layer"] for x in guessed_edges).items()))
    return {
        "schema": "APA-MOAG-HYPOTHESIS-OVERLAY-R08/0.1",
        "status": "CONDITIONAL_PLACEMENT_NOT_SOURCE_PROVEN_GEOMETRY",
        "unified_evidence_graph": {
            "schema": master["schema"],
            "nodes": base_nodes, "edges": base_edges,
            "proven_component_count": master["inventory"][
                "qualitative_components_with_physical_indices"],
            "proven_direct_access_edges": master["inventory"]["direct_access_edges"]
        },
        "hypothetical_nodes": guessed_nodes,
        "hypothetical_edges": guessed_edges,
        "composed_graph": {
            "nodes": base_nodes + guessed_nodes,
            "edges": base_edges + guessed_edges,
            "proven_index_ids": sorted(original_ids),
            "hypothetical_node_ids": sorted(x["id"] for x in guessed_nodes),
            "hypothetical_edge_ids": sorted(x["id"] for x in guessed_edges),
            "graph_unity_does_not_mean_spatial_connectivity": True,
            "traversable_evidence_must_filter_layer": "EXPLICIT_ACCESS",
            "all_hypothetical_edges_have_connects_proven_components_false": True
        },
        "merged_visualization_node_count": len(base_nodes) + len(guessed_nodes),
        "merged_visualization_relation_count": len(base_edges) + len(guessed_edges),
        "unknown_transits": unknown_transits,
        "unlocated_fixed_stational_elements": unlocated_fixed,
        "mutually_alternative_layout_groups": groups,
        "speculative_layout_variants": variants,
        "counts": {
            "proven_nodes_unchanged": len(base_nodes),
            "proven_edges_unchanged": len(base_edges),
            "proven_components_unchanged": master["inventory"][
                "qualitative_components_with_physical_indices"],
            "unknown_route_intervals_kept": len(unknown_transits),
            "unlocated_fixed_elements_kept": len(unlocated_fixed),
            "symmetry_and_nonsymmetry_option_groups": len(groups),
            "unselected_layout_options": len(variants),
            "hypothetical_nodes": len(guessed_nodes),
            "hypothetical_edges": len(guessed_edges),
            "hypothetical_relation_layers": layers
        },
        "gates": {
            "hypotheses_are_visually_inspectable": True,
            "hypotheses_can_change_proven_connectivity": False,
            "symmetry_assumed_as_fact": False,
            "all_undefined_routes_mapped_as_actual_corridors": False,
            "extra_global_decks_inferred": False,
            "book_metric_dimensions_fabricated": False,
            "Archicad_writes": False,
            "approved_BIM_geometry": False
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
    result = build(g, f, b, r)
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
