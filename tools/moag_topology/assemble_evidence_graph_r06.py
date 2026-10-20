#!/usr/bin/env python3
"""МОАГ R06: assemble typed evidence components through observed route occurrences.

No claim that a connected graph is a traversable plan, shared wall, coordinate,
or a solid extra deck. Route steps are observations, NOT additional rooms.
R04/R05 source ledgers and R05 metric intervals remain authoritative inputs.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import json
from pathlib import Path
import assemble_spatial_constraints_r05 as r05
import progressive_constraint_solver_r05 as topology

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"
ROUTES = BASE / "v2" / "character_routes.json"
R04_SPATIAL = {
    "FUNCTIONAL_CONTAINMENT_NOT_WALL_GEOMETRY",
    "ROUTE_REACHABILITY_NOT_DIRECT_DOOR",
    "VERTICAL_OR_ROUTE_ACCESS",
    "PROXIMITY_NOT_SHAPE_PROOF",
    "DOOR_OR_PRESSURE_PORTAL_EVIDENCE",
}
R03_SPATIAL = {"RELATIVE_HEIGHT_OR_LEVEL"}
MULTILEVEL_KINDS = {"utility", "stair", "shaft", "technical_route",
                    "hatch", "hatch_group", "elevator", "technical"}
R03_ADDITIONAL_DIRECT_RELATIONS = {"LEADS_UP_TO", "DOOR_LEADS_TO", "ELEVATED_WITHIN", "DIRECT_PASSAGE_TO", "CONTAINS_EQUIPMENT"}
R03_OBSERVATION_ONLY_RELATIONS = {"SPANS_GLOBAL_LEVEL", "OVERLOOKS"}
AMBIGUOUS_LEGACY_SCENE_IDS = {
    "L1-CIRCULAR-STAIRS", "L1-CIRCULAR-CONTROL"
}
GAP = "NARRATIVE_GAP"
BRIDGES = SYNTH / "explicit_spatial_bridges_r06.json"
CONTEXT_CORRECTIONS = SYNTH / "route_context_corrections_r06.json"
R03_CONNECTING_RELATIONS = {
    "HAS_INTERNAL_UPPER_ROOM", "CONNECTS_FLOOR_TO_UPPER_ROOM",
    "HAS_UPPER_GALLERY", "CONNECTS_FLOOR_TO", "CONNECTS_UPPER_TO_LOWER"
}


class Components:
    def __init__(self, ids, physical_ids=()):
        self.parent = {x: x for x in ids}
        self.size = {x: 1 for x in ids}
        self.has_physical = {x: x in physical_ids for x in ids}

    def root(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        a, b = self.root(a), self.root(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        self.has_physical[a] = self.has_physical[a] or self.has_physical[b]
        return True

    def groups(self):
        out = defaultdict(list)
        for x in sorted(self.parent):
            out[self.root(x)].append(x)
        return sorted((sorted(v) for v in out.values()),
                      key=lambda members: (-len(members), members[0]))


def assemble(graph, fragments, routes, bounds, parameters=None, area_overrides=None,
             anchors=None, variants=None, explicit_bridges=None,
             route_corrections=None):
    if routes.get("schema") is None or not isinstance(routes.get("routes"), list):
        raise ValueError("BAD_ROUTE_LEDGER")
    if explicit_bridges is None:
        explicit_bridges = json.loads(BRIDGES.read_text(encoding="utf-8"))
    if route_corrections is None:
        route_corrections = json.loads(CONTEXT_CORRECTIONS.read_text(encoding="utf-8"))
    prior = r05.run(graph, fragments, bounds, parameters, area_overrides,
                    anchors, variants)
    level = {}
    for rec in prior["topology"]["known_or_inferred_levels"]:
        level[rec["node_id"]] = set((rec["global_level"],))
    for rec in prior["topology"]["level_domains_still_open"]:
        level[rec["node_id"]] = set(rec["possible_global_levels"])
    physical = graph["indexed_source_entities"] + graph["indexed_r03_entities"] + fragments["physical_entities"]
    kinds = {x["id"]: x["kind"] for x in physical}
    if len(kinds) != len(physical) or set(level) != set(kinds):
        raise ValueError("INCONSISTENT_PHYSICAL_INDEX")
    aliases = graph["legacy_id_to_stable_id"]
    nodes = [{
        "id": x["id"], "layer": "PHYSICAL_INDEX", "kind": x["kind"],
        "possible_global_levels": sorted(level[x["id"]]),
        "source_ids": x.get("source_ids", []), "coordinates_known": False
    } for x in physical]
    route_steps = {}
    route_groups = []
    for route in routes["routes"]:
        if route.get("route_kind") != "OBSERVED_CHARACTER_ROUTE":
            continue
        steps = route["nodes"]
        local_ids = set()
        for s in steps:
            rid = "ROUTE::" + route["id"] + "::" + s["id"]
            if rid in route_steps or s["id"] in local_ids:
                raise ValueError("DUPLICATE_ROUTE_STEP")
            local_ids.add(s["id"])
            if s.get("source_page_id") not in route["site_pages"]:
                raise ValueError("ROUTE_STEP_WITHOUT_PAGE_PROVENANCE")
            v = s.get("global_level")
            if v is not None and (type(v) is not int or v not in (1, 2, 3)):
                raise ValueError("INVALID_ROUTE_LEVEL")
            route_steps[rid] = s
            nodes.append({
                "id": rid, "layer": "ROUTE_OCCURRENCE",
                "route_id": route["id"], "step_id": s["id"],
                "source_page_id": s["source_page_id"],
                "method": s.get("movement_method"),
                "possible_global_levels": [v] if v is not None else [1, 2, 3],
                "coordinates_known": False,
                "not_a_separate_room": True
            })
        route_groups.append(route)
    ids = {n["id"] for n in nodes}
    if len(ids) != len(nodes):
        raise ValueError("DUPLICATE_GRAPH_VERTEX")
    uf = Components(ids, kinds)
    edges, bridges, physical_bridges, conflicts, gaps, verticals = [], [], [], [], [], []
    evidence_ids = set()

    def add(a, b, eid, kind, sources, *, connect=True, detail=None):
        if a not in ids or b not in ids or eid in evidence_ids:
            raise ValueError("INVALID_OR_DUPLICATED_EVIDENCE_EDGE: " + eid)
        if not sources:
            raise ValueError("UNSOURCED_ASSEMBLY_EDGE: " + eid)
        evidence_ids.add(eid)
        root_a, root_b = uf.root(a), uf.root(b)
        links_two_physical_islands = (connect and root_a != root_b
            and uf.has_physical[root_a] and uf.has_physical[root_b]
            and kind in ("ROUTE_VISITS_INDEX", "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR"))
        joined = uf.union(a, b) if connect else False
        edge = {"id": eid, "from": a, "to": b, "type": kind,
                "source_ids": sources, "joins_components": joined,
                "connects_evidence_graph": connect,
                "metric_geometry_proven": False}
        if detail is not None:
            edge["detail"] = detail
        edges.append(edge)
        if joined:
            bridges.append({"edge_id": eid, "type": kind, "source_ids": sources,
                            "from": a, "to": b})
            if links_two_physical_islands:
                physical_bridges.append({"edge_id": eid, "from": a, "to": b,
                                         "source_ids": sources,
                                         "result": "PHYSICAL_EVIDENCE_COMPONENTS_CONNECTED_NOT_METRIC"})
        return joined

    for e in graph["source_relationships"]:
        if e["semantic_class"] not in R04_SPATIAL or e["binding_status"] in (
                "QUARANTINED_DO_NOT_USE_AS_DIRECT_GEOMETRY", "RECHECK_REQUIRED"):
            continue
        # Spatial proximity is descriptive context, not a connected passage.
        # Likewise inferred-review edges are explicitly unconfirmed and must
        # not fuse previously disconnected source-backed components.
        permitted = (e["semantic_class"] != "PROXIMITY_NOT_SHAPE_PROOF" and
                     e["binding_status"] != "INFERRED_REVIEW")
        add(e["from"], e["to"], e["id"],
            "R04_QUALITATIVE_ASSOCIATION" if permitted
            else "R04_PROVISIONAL_CONTEXT_NOT_CONNECTING",
            e["source_ids"], connect=permitted,
            detail={"semantic_class": e["semantic_class"],
                    "source_binding_status": e["binding_status"]})
    after_r04_physical_components = len({uf.root(node) for node in kinds})
    for e in graph["derived_r03_relationships"]:
        relation = e["relation"]
        is_level = e["semantic_class"] in R03_SPATIAL
        is_direct = (relation in R03_ADDITIONAL_DIRECT_RELATIONS and
                     e["evidence_state"] == "DIRECT_TEXT")
        is_context = (relation in R03_OBSERVATION_ONLY_RELATIONS and
                      e["evidence_state"] == "DIRECT_TEXT")
        if not (is_level or is_direct or is_context) or e["evidence_state"] == "HYPOTHESIS":
            continue
        connects = relation in R03_CONNECTING_RELATIONS or is_direct
        if is_direct:
            kind = "R03_DIRECT_INTERNAL_ASSOCIATION"
        elif relation == "SPANS_GLOBAL_LEVEL":
            kind = "R03_VOLUME_SPANS_LEVEL_NOT_ACCESS"
        elif relation == "OVERLOOKS":
            kind = "R03_OVERLOOK_NOT_ACCESS"
        else:
            kind = "R03_RECORDED_INTERNAL_SPACE_RELATION" if connects else "R03_RELATIVE_VERTICAL_EVIDENCE"
        add(e["from"], e["to"], e["id"], kind,
            e["source_observation_ids"], connect=connects,
            detail={"semantic_class": e["semantic_class"], "relation": relation})
    after_r03_physical_components = len({uf.root(node) for node in kinds})
    for e in fragments["typed_edges"]:
        if e["relation"] not in topology.TOPOLOGICAL or e.get("certainty") == "HYPOTHESIS":
            continue
        add(e["from"], e["to"], e["id"], "R05_QUALITATIVE_ASSOCIATION",
            e["source_ids"], detail=e["relation"])
    after_r05_physical_components = len({uf.root(node) for node in kinds})
    if explicit_bridges.get("schema") != "APA-MOAG-EXPLICIT-SPATIAL-BRIDGES-R06/0.1":
        raise ValueError("BAD_SPATIAL_BRIDGE_SCHEMA")
    records = {x["id"]: x for x in graph["observations"]}
    if len(records) != len(graph["observations"]):
        raise ValueError("DUPLICATE_OBSERVATION_IDENTIFIER")
    allowed = {"LOCAL_STAIR_ACCESS", "LOCAL_STAIR_IN_HANGAR",
               "EQUIPMENT_INSIDE_WORKSHOP", "LOCAL_STAIR_FROM_GALLERY",
               "ROUTE_VIA_UNMODELED_TUNNEL",
               "VEHICLE_STORED_IN_HANGAR",
               "AIRLOCK_GATE_BETWEEN_HANGAR_AND_CHAMBER",
               "FREIGHT_LIFTS_TO_CARGO_HALL_VIA_WIDE_PASSAGE",
               "SPACESUIT_ALCOVE_BY_CARGO_HALL",
               "CARGO_HALL_FACES_PRODUCTION_GATE",
               "HISTORIC_CONTROLLER_OF_CARGO_HANGAR_COMPLEX",
               "SEQUENTIAL_BASE_GATES_VIA_INTERMEDIATE_CORRIDOR"}
    for e in explicit_bridges["typed_edges"]:
        if e["relation"] not in allowed or e["from"] not in kinds or e["to"] not in kinds:
            raise ValueError("UNSUPPORTED_EXPLICIT_SPATIAL_LINK")
        if e["from"] == e["to"] or e.get("certainty") != "DIRECT_TEXT_REVIEWED":
            raise ValueError("INVALID_EXPLICIT_SPATIAL_CLAIM")
        source_ids = e.get("source_ids") or []
        if not all(s in records and records[s]["station"] == "MOAG"
                   and records[s]["evidence_class"] == "DIRECT_TEXT"
                   for s in source_ids):
            raise ValueError("EXPLICIT_LINK_SOURCE_NOT_VERIFIED")
        if not level[e["from"]] & level[e["to"]]:
            raise ValueError("EXPLICIT_LINK_DISJOINT_LEVELS")
        add(e["from"], e["to"], e["id"], "R06_OBSERVATION_DERIVED_SPACE_LINK",
            source_ids, detail={"relation": e["relation"], "explanation": e["explanation"],
                                "not_a_direct_door": not bool(e.get("proves_direct_door"))})
    after_explicit_physical_components = len({uf.root(node) for node in kinds})
    reference_promotions = []
    review_promotions = []
    for n in graph["indexed_source_entities"]:
        target = n.get("promoted_physical_entity_id")
        if not target:
            continue
        if target not in kinds:
            raise ValueError("DANGLING_PROMOTION_TARGET")
        promotion = {"source_concept_id": n["id"], "new_physical_id": target,
                     "source_ids": n.get("source_ids", []),
                     "status": n.get("promotion_verdict"),
                     "not_a_physical_connection": True}
        if n.get("promotion_verdict") == "PROVISIONAL_EXPLICIT_DESCRIPTION":
            reference_promotions.append(promotion)
        else:
            review_promotions.append(promotion)
    if route_corrections.get("schema") != "APA-MOAG-ROUTE-CONTEXT-CORRECTIONS-R06/0.1":
        raise ValueError("INVALID_ROUTE_CONTEXT_CORRECTIONS_SCHEMA")
    episode_repairs = {x["observation_id"]: x for x in graph["identity_repairs"]}
    all_route_steps = {(ro["id"], s["id"]): s
                       for ro in route_groups for s in ro["nodes"]}
    corrections = {}
    for fix in route_corrections["corrections"]:
        key = (fix["route_id"], fix["step_id"])
        if key not in all_route_steps or key in corrections:
            raise ValueError("UNKNOWN_OR_DUPLICATE_ROUTE_CONTEXT_CORRECTION")
        step = all_route_steps[key]
        observation = records.get(fix["observation_id"])
        if (observation is None or observation["station"] != "MOAG" or
                observation["evidence_class"] != "DIRECT_TEXT" or
                observation["page"] != fix["source_page_id"] or
                step["source_page_id"] != fix["source_page_id"] or
                step.get("existing_graph_node") != fix["legacy_alias"]):
            raise ValueError("CONTEXT_CORRECTION_SOURCE_MISMATCH")
        action = fix["action"]
        if action == "REMAP_TO_EPISODE_SPECIFIC_PHYSICAL_INDEX":
            repaired = episode_repairs.get(fix["observation_id"])
            target = fix["new_index_id"]
            if (target not in kinds or repaired is None or
                    target not in repaired["verified_or_provisional_physical_entity_ids"] or
                    fix["legacy_alias"] not in repaired["source_legacy_node_refs"] or
                    target in repaired["forbidden_automatic_candidates"] or
                    observation["new_status"] != "CORRECTED_FALSE_IDENTITY_ALIAS"):
                raise ValueError("ROUTE_CORRECTION_IDENTITY_NOT_SOURCE_BACKED")
        elif action == "QUARANTINE_UNRESOLVED_LEGACY_ALIAS":
            if fix.get("new_index_id") is not None or not fix.get("reason"):
                raise ValueError("INVALID_AMBIGUOUS_ROUTE_QUARANTINE")
        else:
            raise ValueError("UNSUPPORTED_ROUTE_CORRECTION_ACTION")
        corrections[key] = fix
    for x in route_corrections.get("negative_identity_constraints", []):
        if (x["first"] not in kinds or x["second"] not in kinds or
                x["first"] == x["second"]):
            raise ValueError("INVALID_NEGATIVE_IDENTITY_CONSTRAINT")
    contextual_route_repairs = []
    contextual_route_quarantines = []
    before_routes = len(uf.groups())
    before_physical_components = len({uf.root(node) for node in kinds})
    level_suggestions = defaultdict(list)

    for route in route_groups:
        steps = route["nodes"]
        local = {s["id"]: "ROUTE::" + route["id"] + "::" + s["id"] for s in steps}
        for i, s in enumerate(steps):
            a = local[s["id"]]
            source = s["source_page_id"]
            mapped = s.get("existing_graph_node")
            correction = corrections.get((route["id"], s["id"]))
            if mapped in AMBIGUOUS_LEGACY_SCENE_IDS and correction is None:
                raise ValueError("AMBIGUOUS_ROUTE_ALIAS_REQUIRES_CONTEXT: " +
                                 route["id"] + "::" + s["id"])
            if correction and correction["action"] == "QUARANTINE_UNRESOLVED_LEGACY_ALIAS":
                contextual_route_quarantines.append({
                    "route_id": route["id"], "step_id": s["id"],
                    "source_page_id": source, "legacy_alias": mapped,
                    "source_observation_id": correction["observation_id"],
                    "status": "UNRESOLVED_PHYSICAL_REFERENT_NOT_JOINED"})
                mapped = None
            if mapped is not None:
                target = (correction["new_index_id"]
                          if correction else aliases.get(mapped, mapped))
                if correction:
                    contextual_route_repairs.append({
                        "route_id": route["id"], "step_id": s["id"],
                        "source_page_id": source, "legacy_alias": mapped,
                        "new_physical_index_id": target,
                        "source_observation_id": correction["observation_id"],
                        "not_a_metric_position": True})
                if target not in kinds:
                    conflicts.append({"code": "ROUTE_ALIAS_UNRESOLVED",
                                      "route_id": route["id"], "step_id": s["id"],
                                      "alias": mapped, "page": source})
                else:
                    v = s.get("global_level")
                    mismatch = v is not None and v not in level[target]
                    multilevel = kinds[target] in MULTILEVEL_KINDS
                    if mismatch:
                        # A shared utility network can have access points on
                        # other decks. A non-network room at a contradictory
                        # level, however, cannot attach to the graph.
                        review = ("MULTILEVEL_ALIAS_REVIEW" if multilevel
                                  else "ROUTE_LOCATION_LEVEL_CONFLICT")
                        # Resolve only the *semantic* network contact when the
                        # same route documents a directed descent/ascent from
                        # this contact to a node at the indexed level. It never
                        # fixes the network's global origin or its metric Z.
                        witnesses = []
                        if multilevel:
                            by_step = {x["id"]: x for x in steps}
                            for z in route.get("constraints", []):
                                if z.get("kind") != "RELATIVE_Z":
                                    continue
                                hi = by_step.get(z.get("higher"))
                                lo = by_step.get(z.get("lower"))
                                if hi is None or lo is None or z.get("source_page_id") not in route["site_pages"]:
                                    continue
                                counterpart = (lo if hi["id"] == s["id"] else
                                               hi if lo["id"] == s["id"] else None)
                                if counterpart is None:
                                    continue
                                other_level = counterpart.get("global_level")
                                if other_level in level[target] and other_level != v:
                                    witnesses.append({
                                        "other_step": counterpart["id"],
                                        "other_level": other_level,
                                        "relative_z": "HIGHER" if hi["id"] == s["id"] else "LOWER",
                                        "source_page_id": z["source_page_id"]})
                        conflicts.append({
                            "code": review, "route_id": route["id"],
                            "step_id": s["id"], "target": target,
                            "page": source, "observed_level": v,
                            "indexed_levels": sorted(level[target]),
                            "connection_accepted": multilevel,
                            "vertical_transition_witnesses": witnesses,
                            "semantic_review": (
                                "DOCUMENTED_LEVEL_CROSSING_NETWORK_CONTACT"
                                if witnesses else "UNRESOLVED_NETWORK_CONTACT"
                                if multilevel else "INCOMPATIBLE_ROOM_LEVEL"),
                            "interpretation": (
                                "NETWORK_CONTACT_LEVEL_NOT_SINGLE_ROOM_ELEVATION"
                                if multilevel else "SOURCE_LEVEL_CONTRADICTION_NO_JOIN")})
                    elif v is not None and not multilevel:
                        level_suggestions[target].append(
                            (v, route["id"], s["id"], source))
                    # Keep a multilevel system contact as a qualitative witness,
                    # but refuse to union any ordinary room with contradictory level.
                    if not mismatch or multilevel:
                        add(a, target, "VISIT::" + route["id"] + "::" + s["id"],
                            "ROUTE_VISITS_INDEX", [source],
                            detail={"alias": mapped, "network_contact": multilevel})
            if i > 0:
                prev = steps[i - 1]
                if s.get("movement_method") == GAP or prev.get("movement_method") == GAP:
                    gaps.append({"route_id": route["id"], "from": prev["id"],
                                 "to": s["id"], "source_pages": [prev["source_page_id"], source],
                                 "status": "NARRATIVE_GAP_NO_ADJACENCY"})
                else:
                    exterior_event = (
                        s.get("local_stratum") == "outer-space" or
                        prev.get("local_stratum") == "outer-space" or
                        s.get("movement_method") == "VEHICLE_ENTRY"
                    )
                    # An aircraft leaving the hull, or a different aircraft
                    # entering the scene, is NOT an internal corridor of MOAG.
                    add(local[prev["id"]], a,
                        "STEP::" + route["id"] + "::" + prev["id"] + "::" + s["id"],
                        "EXTERIOR_OR_OTHER_VEHICLE_EVENT_NOT_INTERNAL_PASSAGE"
                        if exterior_event else "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR",
                        sorted({prev["source_page_id"], source}),
                        connect=not exterior_event,
                        detail={"arrival_method": s.get("movement_method"),
                                "outside_internal_station_graph": exterior_event})
        for c in route.get("constraints", []):
            if c.get("kind") != "RELATIVE_Z":
                continue
            if c.get("higher") not in local or c.get("lower") not in local:
                raise ValueError("VERTICAL_REFERENCE_NOT_IN_ROUTE")
            higher, lower = local[c["higher"]], local[c["lower"]]
            if higher == lower:
                raise ValueError("VERTICAL_SELF_CYCLE")
            page = c.get("source_page_id")
            if page not in route["site_pages"]:
                raise ValueError("VERTICAL_WITHOUT_SOURCE_PAGE")
            verticals.append({"higher": higher, "lower": lower, "source_page_id": page,
                              "metric_z_proven": False})
    # A cycle in qualitative higher/lower statements is an unresolved conflict,
    # NOT a signal to pick a convenient vertical elevation.
    order = defaultdict(list)
    indegree = defaultdict(int)
    for v in verticals:
        hi, lo = v["higher"], v["lower"]
        order[hi].append(lo)
        indegree[lo] += 1
        indegree.setdefault(hi, 0)
    q = deque(sorted(n for n in indegree if indegree[n] == 0))
    seen = 0
    while q:
        n = q.popleft()
        seen += 1
        for other in order[n]:
            indegree[other] -= 1
            if indegree[other] == 0:
                q.append(other)
    if seen != len(indegree):
        conflicts.append({"code": "VERTICAL_ORDER_CYCLE", "affected_step_ids": sorted(
            x for x, d in indegree.items() if d > 0)})
    resolved = []
    for target, witnesses in sorted(level_suggestions.items()):
        unique = {x[0] for x in witnesses}
        possible = level[target] & unique
        if len(unique) > 1 or not possible:
            conflicts.append({"code": "CONFLICTING_ROUTE_LEVEL_WITNESSES",
                              "target": target, "witnesses": witnesses})
        elif len(level[target]) > 1:
            resolved.append({"target": target, "inferred_global_level": next(iter(possible)),
                             "supporting_route_witnesses": witnesses,
                             "status": "PROVISIONAL_INFERENCE_NOT_AUTHORITATIVE_XY"})
    # Unresolved gaps become a source-review queue, never inferred passages.
    route_by_id = {r["id"]: r for r in route_groups}
    frontiers = []
    for gap in gaps:
        route = route_by_id[gap["route_id"]]
        steps = route["nodes"]
        idx = next(i for i, s in enumerate(steps) if s["id"] == gap["from"])
        def nearest_mapped(items):
            for step in items:
                alias = step.get("existing_graph_node")
                if alias is not None:
                    target = aliases.get(alias, alias)
                    if target in kinds:
                        return target
            return None
        left = nearest_mapped(reversed(steps[:idx + 1]))
        right = nearest_mapped(steps[idx + 1:])
        different_islands = bool(left and right and uf.root(left) != uf.root(right))
        frontiers.append({
            "route_id": gap["route_id"], "gap_between": [gap["from"], gap["to"]],
            "left_indexed_witness": left, "right_indexed_witness": right,
            "source_pages": gap["source_pages"],
            "priority": ("P1_DISCONNECTED_KNOWN_ENDPOINTS" if different_islands
                         else "P2_GAP_RECHECK_WITH_CONTEXT"),
            "status": "RESEARCH_FRONTIER_NOT_AN_ADDED_GRAPH_EDGE"
        })
    component_members = uf.groups()
    after_physical_components = len({uf.root(node) for node in kinds})
    # Referential overlay: an old concept may denote the same modeled subject
    # as an R03 object, but the pairing does not prove an access route or same room.
    context = Components(ids, kinds)
    for edge in edges:
        if edge["connects_evidence_graph"]:
            context.union(edge["from"], edge["to"])
    context_promotions_joined = 0
    for rec in reference_promotions:
        if context.union(rec["source_concept_id"], rec["new_physical_id"]):
            context_promotions_joined += 1
    context_members = context.groups()
    context_physical_components = len({context.root(node) for node in kinds})
    if context_physical_components > after_physical_components:
        raise ValueError("CONTEXT_OVERLAY_BROKE_SPATIAL_GRAPH")
    physical_only = [sorted(n for n in members if n in kinds) for members in component_members]
    source_physical = {x["id"]: x for x in physical}
    safe_referents = {x["new_physical_id"]: x["source_concept_id"]
                      for x in reference_promotions}
    uncertain_referents = {x["new_physical_id"]: x["source_concept_id"]
                          for x in review_promotions}
    nonroom_containers = {"global_block", "vertical_industrial_volume", "historical_zone"}
    nonroom_craft = {"small_combat_craft", "starship", "spherical_craft",
                     "cargo_cruiser_class", "cruiser"}
    isolated_counts_by_role = defaultdict(int)
    isolated_queue = []
    for members, p in zip(component_members, physical_only):
        if len(members) != 1 or len(p) != 1:
            continue
        n = source_physical[p[0]]
        provenance = n.get("source_ids") or n.get("source_observation_ids") or []
        crosswalk = safe_referents.get(n["id"])
        review = uncertain_referents.get(n["id"])
        role = ("GLOBAL_OR_HISTORICAL_CONTAINER_NOT_INDEPENDENT_ROOM"
                if n["kind"] in nonroom_containers else
                "VEHICLE_OR_VEHICLE_CLASS_NOT_STATION_ROOM"
                if n["kind"] in nonroom_craft else
                "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE")
        isolated_counts_by_role[role] += 1
        isolated_queue.append({
            "physical_index_id": n["id"], "name": n["name"], "kind": n["kind"],
            "spatial_inventory_role": role,
            "not_automatically_a_separate_room": role != "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE",
            "source_ids": provenance,
            "crosswalk_to_existing_concept": crosswalk,
            "identity_review_concept": review,
            "priority": ("P1_VALIDATE_EXISTING_REFERENT" if crosswalk else
                         "P2_RECHECK_SOURCE_AND_LINK" if provenance else
                         "P3_CLASSIFY_NONROOM_OR_GLOBAL_HULL"),
            "status": "SOURCE_LOOKUP_REQUIRED_NOT_AUTO_CONNECTED"
        })
    isolated_queue.sort(key=lambda x:(x["priority"], x["physical_index_id"]))
    all_kinds = defaultdict(int)
    for e in edges:
        all_kinds[e["type"]] += 1
    area = prior["area_and_volume"]
    return {
        "schema": "APA-MOAG-ROUTE-GRAPH-ASSEMBLY-R06/0.1",
        "status": "REVIEW_REQUIRED" if conflicts or prior["status"] == "CONFLICTS" else "CONSISTENT_PARTIAL",
        "based_on": {"r04_schema": graph["schema"], "r05_schema": fragments["schema"],
                     "route_ledger_schema": routes["schema"],
                     "r05_status": prior["status"]},
        "counts": {
            "physical_indices": len(physical), "route_occurrences": len(route_steps),
            "route_ledgers": len(route_groups), "before_routes_components": before_routes,
            "after_r04_physical_components": after_r04_physical_components,
            "after_r03_physical_components": after_r03_physical_components,
            "after_r05_physical_components": after_r05_physical_components,
            "after_explicit_physical_components": after_explicit_physical_components,
            "r03_local_relation_component_reductions": after_r04_physical_components - after_r03_physical_components,
            "r05_typed_link_component_reductions": after_r03_physical_components - after_r05_physical_components,
            "r06_explicit_link_component_reductions": after_r05_physical_components - after_explicit_physical_components,
            "reference_promotion_crosswalks": len(reference_promotions),
            "promotions_needing_identity_review": len(review_promotions),
            "context_component_promotions_joined": context_promotions_joined,
            "context_affiliation_components_with_physical_indices": context_physical_components,
            "after_routes_components": len(component_members),
            "before_routes_physical_components": before_physical_components,
            "after_routes_physical_components": after_physical_components,
            "physical_components_joined": before_physical_components - after_physical_components,
            "isolated_physical_indices": sum(len(p) == 1 and len(members) == 1
                                             for members, p in zip(component_members, physical_only)),
            "route_only_components": sum(not p for p in physical_only),
            "unconnected_index_research_tasks": len(isolated_queue),
            "isolated_candidates_by_role": dict(sorted(isolated_counts_by_role.items())),
            "isolated_fixed_room_corridor_door_or_technical_infrastructure": isolated_counts_by_role[
                "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE"],
            "route_context_disambiguations": len(contextual_route_repairs),
            "route_context_quarantines": len(contextual_route_quarantines),
            "route_bridge_events": sum(e["joins_components"] for e in edges
                                       if e["type"].startswith(("ROUTE_", "OBSERVED_"))),
            "physical_fragment_bridge_events": len(physical_bridges),
            "narrative_gaps": len(gaps), "frontiers_for_targeted_review": len(frontiers),
            "high_priority_disconnected_frontiers": sum(x["priority"].startswith("P1_") for x in frontiers),
            "vertical_order_constraints": len(verticals),
            "crosswalk_review_conflicts": len(conflicts),
            "documented_multilevel_network_contacts": sum(
                x.get("semantic_review") == "DOCUMENTED_LEVEL_CROSSING_NETWORK_CONTACT"
                for x in conflicts),
            "ordinary_room_level_conflicts": sum(
                x["code"] == "ROUTE_LOCATION_LEVEL_CONFLICT" for x in conflicts),
            "inferred_route_level_candidates": len(resolved),
            "source_backed_edges_by_class": dict(sorted(all_kinds.items())),
            "area_profiles": area["counts"]["with_area"], "area_check_failures": area["counts"]["fails"]
        },
        "nodes": nodes, "typed_evidence_edges": edges,
        "connected_evidence_components": [
            {"id": "COMP-%03d" % (i + 1), "all_node_ids": members,
             "physical_index_ids": p,
             "route_occurrence_count": len(members) - len(p),
             "coordinates_proven": False, "walkable_subgraph_proven": False}
            for i, (members, p) in enumerate(zip(component_members, physical_only))
        ],
        "referential_context_overlay": {
            "status": "CONCEPT_TO_R03_REFERENT_ASSOCIATION_ONLY",
            "not_a_travel_graph": True,
            "not_physical_room_unification": True,
            "source_backed_affiliation_groups": [
                {"id": "CTX-%03d" % (i + 1),
                 "member_ids": members,
                 "physical_index_ids": sorted(x for x in members if x in kinds),
                 "metric_layout_proven": False}
                for i, members in enumerate(context_members)
            ]
        },
        "bridge_events": bridges,
        "physical_fragment_bridge_events": physical_bridges,
        "route_location_review": conflicts,
        "route_context_disambiguation_audit": contextual_route_repairs,
        "route_context_quarantine_audit": contextual_route_quarantines,
        "route_negative_identity_constraints": route_corrections.get(
            "negative_identity_constraints", []),
        "reference_promotion_crosswalks_not_spatial_links": reference_promotions,
        "promotion_identity_review_queue": review_promotions,
        "deferred_spatial_hypotheses_not_linked": explicit_bridges.get("deferred_hypotheses", []),
        "identity_hypotheses_not_merged": prior["topology"]["identity_hypotheses"],
        "negative_identity_constraints": prior["topology"]["identity_exclusions"],
        "narrative_gaps": gaps, "research_frontiers_not_edges": frontiers,
        "unconnected_index_source_review_queue": isolated_queue,
        "vertical_partial_order": verticals,
        "new_level_candidates": resolved,
        "area_volume": {
            "status": prior["status"], "counts": area["counts"],
            "per_index": area["per_index"],
            "level_allocation_budgets": area["level_allocation_budgets"],
            "failed_checks": [c for c in area["checks"] if c["status"] == "FAIL"],
            "compared_variants": prior["compared_variants"],
            "variation_summary": prior["variation_summary"]
        },
        "gates": {"routes_do_not_define_adjacency": True, "identity_merge_permitted": False,
                  "metric_xy_known": False, "metric_z_known": False,
                  "global_extra_decks_inferred_from_local_galleries": False,
                  "geometry_approved": False, "archicad_write": False}
    }



def trace_between(result, start, goal):
    """Find a source-backed association chain, NOT a verified travel route."""
    names = {x["id"] for x in result["nodes"]}
    if start not in names or goal not in names:
        raise ValueError("UNKNOWN_TRACE_ENDPOINT")
    graph = defaultdict(list)
    for edge in result["typed_evidence_edges"]:
        # Vertical ordering is not access and does not fuse places.
        if not edge.get("connects_evidence_graph", False):
            continue
        graph[edge["from"]].append((edge["to"], edge))
        graph[edge["to"]].append((edge["from"], edge))
    previous = {start: None}
    queue = deque([start])
    while queue and goal not in previous:
        current = queue.popleft()
        for nxt, edge in sorted(graph[current], key=lambda x: x[1]["id"]):
            if nxt not in previous:
                previous[nxt] = (current, edge)
                queue.append(nxt)
    if goal not in previous:
        return {"status": "UNCONNECTED_UNDER_RECORDED_EVIDENCE",
                "from": start, "to": goal, "edge_chain": [],
                "geometry_proven": False}
    chain = []
    at = goal
    while at != start:
        origin, edge = previous[at]
        chain.append({"from": origin, "to": at, "edge_id": edge["id"],
                      "kind": edge["type"], "source_ids": edge["source_ids"]})
        at = origin
    chain.reverse()
    return {"status": "QUALITATIVE_ASSOCIATION_CHAIN_NOT_TRAVEL_ITINERARY",
            "from": start, "to": goal, "edge_chain": chain,
            "geometry_proven": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", type=Path, default=SYNTH / "full_indexed_parametric_graph_r04.json")
    ap.add_argument("--fragments", type=Path, default=SYNTH / "progressive_fragments_r05.json")
    ap.add_argument("--routes", type=Path, default=ROUTES)
    ap.add_argument("--bridges", type=Path, default=BRIDGES)
    ap.add_argument("--context-corrections", type=Path, default=CONTEXT_CORRECTIONS)
    ap.add_argument("--bounds", type=Path, default=SYNTH / "area_volume_bounds_r05.json")
    ap.add_argument("--anchors", type=Path)
    ap.add_argument("--r04-parameters", type=Path)
    ap.add_argument("--area-overrides", type=Path)
    ap.add_argument("--variants", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--between", nargs=2, metavar=("FROM_ID", "TO_ID"))
    arg = ap.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8")) if p else None
    result = assemble(read(arg.graph), read(arg.fragments), read(arg.routes),
                      read(arg.bounds), read(arg.r04_parameters),
                      read(arg.area_overrides), read(arg.anchors), read(arg.variants),
                      read(arg.bridges), read(arg.context_corrections))
    if arg.between:
        result["requested_evidence_trace"] = trace_between(result, *arg.between)
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if arg.out:
        arg.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 2 if result["counts"]["area_check_failures"] or any(
        item["code"] == "VERTICAL_ORDER_CYCLE"
        for item in result["route_location_review"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
