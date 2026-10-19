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
GAP = "NARRATIVE_GAP"


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
             anchors=None, variants=None):
    if routes.get("schema") is None or not isinstance(routes.get("routes"), list):
        raise ValueError("BAD_ROUTE_LEDGER")
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
        add(e["from"], e["to"], e["id"], "R04_QUALITATIVE_ASSOCIATION",
            e["source_ids"], detail=e["semantic_class"])
    for e in graph["derived_r03_relationships"]:
        if e["semantic_class"] not in R03_SPATIAL or e["evidence_state"] == "HYPOTHESIS":
            continue
        add(e["from"], e["to"], e["id"], "R03_RELATIVE_VERTICAL_EVIDENCE",
            e["source_observation_ids"], connect=False, detail=e["semantic_class"])
    for e in fragments["typed_edges"]:
        if e["relation"] not in topology.TOPOLOGICAL or e.get("certainty") == "HYPOTHESIS":
            continue
        add(e["from"], e["to"], e["id"], "R05_QUALITATIVE_ASSOCIATION",
            e["source_ids"], detail=e["relation"])
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
            if mapped is not None:
                target = aliases.get(mapped, mapped)
                if target not in kinds:
                    conflicts.append({"code": "ROUTE_ALIAS_UNRESOLVED",
                                      "route_id": route["id"], "step_id": s["id"],
                                      "alias": mapped, "page": source})
                else:
                    v = s.get("global_level")
                    if v is not None and v not in level[target]:
                        # A shaft/utility may span more than its old single-level alias.
                        review = "MULTILEVEL_ALIAS_REVIEW" if kinds[target] in MULTILEVEL_KINDS else "ROUTE_LOCATION_LEVEL_CONFLICT"
                        conflicts.append({"code": review, "route_id": route["id"],
                                          "step_id": s["id"], "target": target,
                                          "page": source, "observed_level": v,
                                          "indexed_levels": sorted(level[target])})
                    else:
                        if v is not None and kinds[target] not in MULTILEVEL_KINDS:
                            level_suggestions[target].append((v, route["id"], s["id"], source))
                    # A visit links an occurrence to an indexed concept, not
                    # an identity union or proof of one-level physical placement.
                    add(a, target, "VISIT::" + route["id"] + "::" + s["id"],
                        "ROUTE_VISITS_INDEX", [source], detail={"alias": mapped})
            if i > 0:
                prev = steps[i - 1]
                if s.get("movement_method") == GAP or prev.get("movement_method") == GAP:
                    gaps.append({"route_id": route["id"], "from": prev["id"],
                                 "to": s["id"], "source_pages": [prev["source_page_id"], source],
                                 "status": "NARRATIVE_GAP_NO_ADJACENCY"})
                else:
                    add(local[prev["id"]], a,
                        "STEP::" + route["id"] + "::" + prev["id"] + "::" + s["id"],
                        "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR",
                        sorted({prev["source_page_id"], source}),
                        detail={"arrival_method": s.get("movement_method")})
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
    physical_only = [sorted(n for n in members if n in kinds) for members in component_members]
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
            "after_routes_components": len(component_members),
            "before_routes_physical_components": before_physical_components,
            "after_routes_physical_components": after_physical_components,
            "physical_components_joined": before_physical_components - after_physical_components,
            "isolated_physical_indices": sum(len(p) == 1 and len(members) == 1
                                             for members, p in zip(component_members, physical_only)),
            "route_only_components": sum(not p for p in physical_only),
            "route_bridge_events": sum(e["joins_components"] for e in edges
                                       if e["type"].startswith(("ROUTE_", "OBSERVED_"))),
            "physical_fragment_bridge_events": len(physical_bridges),
            "narrative_gaps": len(gaps), "frontiers_for_targeted_review": len(frontiers),
            "high_priority_disconnected_frontiers": sum(x["priority"].startswith("P1_") for x in frontiers),
            "vertical_order_constraints": len(verticals),
            "crosswalk_review_conflicts": len(conflicts),
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
        "bridge_events": bridges,
        "physical_fragment_bridge_events": physical_bridges,
        "route_location_review": conflicts,
        "identity_hypotheses_not_merged": prior["topology"]["identity_hypotheses"],
        "negative_identity_constraints": prior["topology"]["identity_exclusions"],
        "narrative_gaps": gaps, "research_frontiers_not_edges": frontiers,
        "vertical_partial_order": verticals,
        "new_level_candidates": resolved,
        "area_volume": {
            "status": prior["status"], "counts": area["counts"],
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
        if edge["type"] == "R03_RELATIVE_VERTICAL_EVIDENCE":
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
                      read(arg.area_overrides), read(arg.anchors), read(arg.variants))
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
