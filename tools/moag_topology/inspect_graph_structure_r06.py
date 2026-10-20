#!/usr/bin/env python3
"""МОАГ R06 structural projections: source association != traversable access.

This module does not assign XY, exact Z, walls, decks or metric book values.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import assemble_evidence_graph_r06 as assembly

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"
DIRECT_R04 = {
    "door_to", "stairs_to", "internally_connected", "connects_vertical",
    "single_locked_door_to", "biometric_door_to",
    "pressure_sealed_access_to", "steps_down_to",
}
DIRECT_R03 = {
    "DOOR_LEADS_TO", "DIRECT_PASSAGE_TO", "LEADS_UP_TO",
    "CONNECTS_FLOOR_TO", "CONNECTS_FLOOR_TO_UPPER_ROOM",
    "CONNECTS_UPPER_TO_LOWER",
}
DIRECT_R05 = {"DOOR_TO_OTHER_ROOM", "CONNECTS_VIA_PORTAL"}
DIRECT_R06 = {"LOCAL_STAIR_ACCESS", "LOCAL_STAIR_IN_HANGAR",
              "LOCAL_STAIR_FROM_GALLERY",
              "AIRLOCK_GATE_BETWEEN_HANGAR_AND_CHAMBER"}
VOLUME_ROLES = {"LEVEL_ENVELOPE_AREA_PROJECT_SCENARIO",
                "VERTICAL_CORE_SECTION", "VOID_CROSS_SECTION_NOT_FLOOR",
                "SHAFT_PATH_SECTION", "SHAFT_GROUP_NO_FLOOR_ADDITIVITY"}
NONADDITIVE_ROLES = {
    "AGGREGATE_UNION_NOT_ADDITIVE", "COMPLEX_UNION_NOT_ADDITIVE",
    "ALIAS_LEVEL_NO_DOUBLE_COUNT", "MULTIFLOOR_ZONE_AGGREGATE",
    "EQUIPMENT_WITHIN_HOST", "FURNITURE_WITHIN_HOST",
    "VEHICLE_ENVELOPE_NOT_STATION_FLOOR", "LOGICAL_NO_GEOMETRY",
} | VOLUME_ROLES


def project(graph, fragments, bounds, r06):
    """Produce independent evidence, access, metric and vertical projections."""
    physical = graph["indexed_source_entities"] + graph["indexed_r03_entities"] + fragments["physical_entities"]
    known = {x["id"]: x for x in physical}
    profiles = {p["id"]: p for p in bounds["profiles"]}
    effective = r06["area_volume"]["per_index"]
    assert set(profiles) == set(known) == set(effective), "R06_INDEX_MISMATCH"
    source_r04 = {x["id"]: x for x in graph["source_relationships"]}
    source_r03 = {x["id"]: x for x in graph["derived_r03_relationships"]}
    source_r05 = {x["id"]: x for x in fragments["typed_edges"]}
    spatial_r06 = json.loads(assembly.BRIDGES.read_text(encoding="utf-8"))
    source_r06 = {x["id"]: x for x in spatial_r06["typed_edges"]}
    clearance = json.loads(
        (SYNTH / "qualitative_vehicle_clearance_r06.json").read_text(encoding="utf-8"))
    if clearance.get("schema") != "APA-MOAG-QUALITATIVE-VEHICLE-CLEARANCE-R06/0.1":
        raise ValueError("BAD_QUALITATIVE_CLEARANCE_SCHEMA")
    reviewed_page = clearance["reviewed_source"]["page_id"]
    pages = json.loads((BASE / "v2/pages/B2.json").read_text(encoding="utf-8"))
    if (reviewed_page != "B2-015" or
            pages["pages"][14]["status"] != "REVIEWED_FULL_PAGE" or
            clearance["reviewed_source"]["url"] != pages["pages"][14]["url"]):
        raise ValueError("UNREVIEWED_CLEARANCE_PAGE")
    for condition in clearance["constraints"]:
        if (condition["architectural_entity_id"] not in known or
                condition["minimum_clearance_m"] is not None or
                condition["upper_clearance_m"] is not None or
                condition["station"] != "MOAG"):
            raise ValueError("UNSOURCED_CLEARANCE_OR_PREMATURE_METRIC")
    typed, access = [], []
    for e in r06["typed_evidence_edges"]:
        kind, direct = "UNCLASSIFIED", False
        eid = e["id"]
        if eid in source_r04:
            rel = source_r04[eid]["relation"]
            cls = source_r04[eid]["semantic_class"]
            direct = (rel in DIRECT_R04 and
                      source_r04[eid]["binding_status"] == "PROVISIONAL_SOURCE_RELATION" and
                      e["connects_evidence_graph"] and
                      cls != "PROXIMITY_NOT_SHAPE_PROOF")
            kind = ("DIRECT_ACCESS_OR_GATE" if direct else
                    "NONLOCAL_ROUTE" if cls == "ROUTE_REACHABILITY_NOT_DIRECT_DOOR" else
                    "CONTAINMENT_OR_MEMBERSHIP" if cls == "FUNCTIONAL_CONTAINMENT_NOT_WALL_GEOMETRY" else
                    "PROXIMITY_NOT_ADJACENT" if cls == "PROXIMITY_NOT_SHAPE_PROOF" else
                    "QUALITATIVE_RELATION")
        elif eid in source_r03:
            rel = source_r03[eid]["relation"]
            direct = (rel in DIRECT_R03 and
                      source_r03[eid]["evidence_state"] == "DIRECT_TEXT")
            kind = ("DIRECT_ACCESS_OR_GATE" if direct else
                    "INTERLEVEL_SPAN_NOT_ACCESS" if rel == "SPANS_GLOBAL_LEVEL" else
                    "VISUAL_OVERLOOK_NOT_ACCESS" if rel == "OVERLOOKS" else
                    "INTERIOR_CONTAINMENT" if rel in ("HAS_INTERNAL_UPPER_ROOM",
                        "HAS_UPPER_GALLERY", "ELEVATED_WITHIN", "CONTAINS_EQUIPMENT") else
                    "QUALITATIVE_RELATION")
        elif eid in source_r05:
            rel = source_r05[eid]["relation"]
            direct = rel in DIRECT_R05
            kind = ("DIRECT_ACCESS_OR_GATE" if direct else
                    "INTERIOR_CONTAINMENT" if rel in ("CONTAINS_SPACE",
                       "CONTAINS_EQUIPMENT") else "QUALITATIVE_RELATION")
        elif eid in source_r06:
            rel = source_r06[eid]["relation"]
            direct = rel in DIRECT_R06
            kind = ("DIRECT_ACCESS_OR_GATE" if direct else
                    "EQUIPMENT_CONTAINMENT" if rel in (
                        "EQUIPMENT_INSIDE_WORKSHOP", "VEHICLE_STORED_IN_HANGAR")
                    else "HISTORICAL_FUNCTION_NOT_PASSAGE"
                    if rel == "HISTORIC_CONTROLLER_OF_CARGO_HANGAR_COMPLEX"
                    else "SPATIAL_CONTEXT_NOT_DIRECT_PASSAGE"
                    if rel in ("SPACESUIT_ALCOVE_BY_CARGO_HALL",
                               "CARGO_HALL_FACES_PRODUCTION_GATE")
                    else "NONLOCAL_ROUTE")
        elif e["type"] == "ROUTE_VISITS_INDEX":
            kind = "ROUTE_OBSERVATION_ANCHOR"
        elif e["type"] == "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR":
            kind = "ORDERED_ROUTE_STEPS_NOT_ADJACENT_ROOMS"
        elif e["type"] == "EXTERIOR_OR_OTHER_VEHICLE_EVENT_NOT_INTERNAL_PASSAGE":
            kind = "EXTERNAL_VEHICLE_EVENT_NOT_STATION_LINK"
        else:
            raise ValueError("UNKNOWN_EVIDENCE_RELATION: " + eid)
        # Nonconnecting evidence (inference, proximity, visibility, spans)
        # must never be smuggled into the traversable graph.
        if not e["connects_evidence_graph"]:
            direct = False
        rec = {"edge_id": eid, "from": e["from"], "to": e["to"],
               "relation_class": kind, "source_ids": e["source_ids"],
               "physically_traversable_connection_asserted": direct,
               "metric_geometry_proven": False}
        typed.append(rec)
        if direct:
            if rec["from"] not in known or rec["to"] not in known:
                raise ValueError("DIRECT_LINK_NOT_BETWEEN_INDEXED_OBJECTS")
            access.append(rec)
    adj = defaultdict(list)
    for e in access:
        a, b = e["from"], e["to"]
        adj[a].append((b, e)); adj[b].append((a, e))
    visited, components = set(), []
    for x in sorted(known):
        if x in visited:
            continue
        q = [x]
        visited.add(x)
        members = []
        while q:
            n = q.pop()
            members.append(n)
            for dest, _ in adj[n]:
                if dest not in visited:
                    visited.add(dest)
                    q.append(dest)
        components.append(sorted(members))
    locations = {x["id"]: x for x in r06["nodes"] if x["layer"] == "PHYSICAL_INDEX"}
    # The R04 source concept and R03 expanded entity may describe the
    # same physical floor. Until identity/extent is settled, prohibit BOTH
    # records from being independently accumulated as additive plan area.
    candidate_crosswalks = []
    crosswalk_by_index = {}
    for old in graph["indexed_source_entities"]:
        to = old.get("promoted_physical_entity_id")
        if not to:
            continue
        if to not in known or old["id"] not in known:
            raise ValueError("CROSSWALK_UNKNOWN_INDEX")
        verdict = old.get("promotion_verdict")
        crosswalk = {
            "source_concept_id": old["id"],
            "refined_index_id": to,
            "source_page_ids": old.get("source_ids", []),
            "identity_status": verdict,
            "independent_floor_area_sum_permitted": False,
            "geometry_extent_equivalence_proven": False,
            "review_action": ("CHECK_GLOBAL_ENTITY_IDENTITY" if
                              verdict == "REVIEW_SOURCE_IDENTITY_BEFORE_BINDING"
                              else "RESOLVE_PROVISIONAL_REFERENT_EXTENT")
        }
        candidate_crosswalks.append(crosswalk)
        crosswalk_by_index.setdefault(old["id"], []).append(to)
        crosswalk_by_index.setdefault(to, []).append(old["id"])
    area_profiles = []
    for key in sorted(known):
        p, e = profiles[key], effective[key]
        role = p["area_role"]
        area_profiles.append({
            "physical_index_id": key, "kind": known[key]["kind"],
            "global_level_domain": locations[key]["possible_global_levels"],
            "area_role": role, "source_ids": (
                known[key].get("source_ids") or known[key].get("source_observation_ids") or []),
            "footprint_range_m2": [e["min_area_m2"], e["max_area_m2"]]
                                  if "min_area_m2" in e else None,
            "usable_floor_area_range_m2": e.get("usable_floor_area_range_m2"),
            "clear_volume_bounding_prism_range_m3": e.get("clear_volume_bounds_m3"),
            "local_floor_factor": e.get("local_story_factor_range"),
            "scenario_not_text_measurement": True,
            "book_derived_numeric_limits": {
                "footprint_area_m2": None,
                "usable_floor_area_m2": None,
                "clear_volume_m3": None,
                "note": "Reviewed source IDs establish presence/function, not numerical metrics"
            },
            "editable_project_bounds": {
                "footprint_area_m2": [e["min_area_m2"], e["max_area_m2"]]
                                       if "min_area_m2" in e else None,
                "usable_floor_area_m2": e.get("usable_floor_area_range_m2"),
                "clear_bounding_prism_m3": e.get("clear_volume_bounds_m3")
            },
            "not_additive_by_default": role in NONADDITIVE_ROLES or key in crosswalk_by_index,
            "candidate_same_referent_index_ids": crosswalk_by_index.get(key, []),
            "requires_crosswalk_reconciliation_before_sum": key in crosswalk_by_index,
            "geometry_proven": False,
        })
    # Multipliers may already budget partial extra floors. A separately
    # indexed control-room/mezzanine cannot be naively added to that same
    # host's upper-floor allowance without explicit non-overlap geometry.
    local_overlap_reviews = []
    multipliers = bounds.get("local_floor_area_multipliers", {})
    for link in graph["derived_r03_relationships"]:
        if link["relation"] not in ("HAS_INTERNAL_UPPER_ROOM",
                                  "HAS_UPPER_GALLERY", "ELEVATED_WITHIN"):
            continue
        host, child = link["from"], link["to"]
        if link["relation"] == "ELEVATED_WITHIN":
            host, child = child, host
        ratio = multipliers.get(host)
        if ratio and ratio["max"] > 1:
            local_overlap_reviews.append({
                "host_id": host, "local_floor_entity_id": child,
                "source_observation_ids": link["source_observation_ids"],
                "host_local_floor_factor_max": ratio["max"],
                "status": "POTENTIAL_DOUBLE_COUNT_WITH_HOST_MULTIPLIER",
                "rule": "NEVER_SUM_HOST_MULTIPLIER_AND_CHILD_FLOOR_UNLESS_DISJOINT_FLOOR_GEOMETRY_PROVEN",
                "additional_global_storey_created": False
            })
    spans = [r for r in typed if r["relation_class"] == "INTERLEVEL_SPAN_NOT_ACCESS"]
    budget = r06["area_volume"]["counts"]
    return {
        "schema": "APA-MOAG-STRUCTURAL-PROJECTIONS-R06/0.1",
        "status": "NON_METRIC_EVIDENCE_MODEL_WITH_REVIEW_DEBT",
        "physical_index_count": len(known),
        "evidence_relations": typed,
        "evidence_relation_classes": dict(sorted(Counter(x["relation_class"] for x in typed).items())),
        "direct_access_graph": {
            "note": "Only explicit doors/stairs/direct passages: no inferred routes via containment, overlays, proximity or unobserved steps",
            "edges": access, "components": sorted(components, key=lambda x:(-len(x),x[0])),
            "component_count": len(components),
            "isolated_indices": sorted(x[0] for x in components if len(x) == 1),
            "geometry_proven": False
        },
        "interlevel_span_without_access": spans,
        "source_qualitative_vehicle_clearance": {
            "page_id": reviewed_page,
            "inequalities": clearance["constraints"],
            "unverified_metric_dimensions": True,
            "exclusion_rules": clearance["avoid_false_inferences"]
        },
        "local_upper_floor_double_count_review": local_overlap_reviews,
        "spatial_area_volume_profiles": area_profiles,
        "source_concept_to_refined_object_accounting_guards": candidate_crosswalks,
        "area_and_volume_accounting": {
            "profile_count": len(area_profiles),
            "area_bearing": budget["with_area"],
            "failed_interval_checks": budget["fails"],
            "source_model_separates": ["FOOTPRINT", "USABLE_FLOOR", "CLEAR_VOLUME"],
            "never_sum_all_profiles": True,
            "disjoint_budget_results": r06["area_volume"].get("level_allocation_budgets", []),
            "note": "Global disks, local galleries, shafts, vehicles and aggregate groups are not independent floors; all quantities are editable scenarios"
        },
        "gates": {"geometry_approved": False, "archicad_write": False,
                  "walking_route_proven_for_entire_station": False,
                  "metric_coordinates_known": False}
    }


def trace_direct_access(projected, a, b):
    """Shortest *explicit* edge chain, without assuming gate is currently open."""
    graph = defaultdict(list)
    ids = {p["physical_index_id"] for p in projected["spatial_area_volume_profiles"]}
    if a not in ids or b not in ids:
        raise ValueError("UNKNOWN_ACCESS_INDEX")
    for e in projected["direct_access_graph"]["edges"]:
        graph[e["from"]].append((e["to"], e))
        graph[e["to"]].append((e["from"], e))
    prior = {a: None}
    queue = deque([a])
    while queue and b not in prior:
        node = queue.popleft()
        for nxt, edge in sorted(graph[node], key=lambda t:t[1]["edge_id"]):
            if nxt not in prior:
                prior[nxt] = (node, edge)
                queue.append(nxt)
    if b not in prior:
        return {"status": "NO_PROVEN_DIRECT_ACCESS_CHAIN", "edge_chain": []}
    chain = []
    cur = b
    while cur != a:
        prev, edge = prior[cur]
        chain.append({"from": prev, "to": cur,
                      "edge_id": edge["edge_id"],
                      "source_ids": edge["source_ids"]})
        cur = prev
    chain.reverse()
    return {"status": "EXPLICIT_ACCESS_CHAIN_WITHOUT_METRIC_GEOMETRY",
            "edge_chain": chain, "gate_operational_state_proven": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path)
    p.add_argument("--between", nargs=2, metavar=("A", "B"))
    args = p.parse_args()
    read = lambda name: json.loads((SYNTH / name).read_text(encoding="utf-8"))
    graph = read("full_indexed_parametric_graph_r04.json")
    fragments = read("progressive_fragments_r05.json")
    bounds = read("area_volume_bounds_r05.json")
    routes = json.loads((BASE / "v2/character_routes.json").read_text(encoding="utf-8"))
    result = project(graph, fragments, bounds,
                     assembly.assemble(graph, fragments, routes, bounds))
    if args.between:
        result["requested_explicit_access_chain"] = trace_direct_access(result, *args.between)
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
