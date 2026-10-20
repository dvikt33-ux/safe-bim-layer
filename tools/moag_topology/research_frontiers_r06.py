#!/usr/bin/env python3
"""МОАГ R06: source-resolvable work queue, not a geometric connection solver."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

import assemble_evidence_graph_r06 as assembly

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"
BOOK_TOTALS = {"B1": 114, "B2": 148, "B3": 71, "B4": 79}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assemble_review():
    g = read(SYNTH / "full_indexed_parametric_graph_r04.json")
    fragments = read(SYNTH / "progressive_fragments_r05.json")
    area = read(SYNTH / "area_volume_bounds_r05.json")
    routes = read(BASE / "v2/character_routes.json")
    result = assembly.assemble(g, fragments, routes, area)
    observations = {x["id"]: x for x in read(BASE / "v2/page_observations.json")["observations"]}
    pages = {}
    for book, total in BOOK_TOTALS.items():
        ledger = read(BASE / "v2/pages" / (book + ".json"))
        if len(ledger["pages"]) != total:
            raise ValueError("INCORRECT_PAGE_LEDGER")
        pages.update({x["id"]: x for x in ledger["pages"]})
    graph_nodes = {n["id"]: n for n in result["nodes"]
                   if n["layer"] == "PHYSICAL_INDEX"}
    raw_relations = defaultdict(list)
    for e in g["source_relationships"]:
        raw_relations[e["from"]].append(e)
        raw_relations[e["to"]].append(e)

    def resolve(ref):
        if ref in observations:
            page = observations[ref]["page_id"]
            return {"source_id": ref, "page_id": page, "kind": "PRIMARY_PAGE_OBSERVATION",
                    "observation_evidence": observations[ref]["evidence_class"],
                    "station_scope": observations[ref]["station_id"],
                    "reviewed": pages[page]["status"] == "REVIEWED_FULL_PAGE",
                    "url": pages[page]["url"]}
        match = re.search(r"(B[1-4])-(\d+)$", ref)
        if not match:
            return {"source_id": ref, "page_id": None,
                    "kind": "UNRESOLVED_SOURCE_REFERENCE", "reviewed": False}
        page = f"{match.group(1)}-{int(match.group(2)):03d}"
        if page not in pages:
            raise ValueError("SOURCE_PAGE_OUTSIDE_CORPUS: " + page)
        return {"source_id": ref, "page_id": page,
                "kind": "LEGACY_SITE_PAGE_REFERENCE",
                "reviewed": pages[page]["status"] == "REVIEWED_FULL_PAGE",
                "url": pages[page]["url"]}

    tasks = []
    for row in result["unconnected_index_source_review_queue"]:
        if row["spatial_inventory_role"] != (
                "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE"):
            continue
        node = graph_nodes[row["physical_index_id"]]
        src = [resolve(x) for x in row["source_ids"]]
        unaccepted = []
        for e in raw_relations.get(row["physical_index_id"], []):
            if (e["semantic_class"] not in assembly.R04_SPATIAL or
                    e["binding_status"] != "PROVISIONAL_SOURCE_RELATION" or
                    e["semantic_class"] == "PROXIMITY_NOT_SHAPE_PROOF"):
                unaccepted.append({
                    "edge_id": e["id"], "other_index": (
                        e["to"] if e["from"] == node["id"] else e["from"]),
                    "relation": e["relation"],
                    "binding_status": e["binding_status"],
                    "semantic_class": e["semantic_class"],
                    "not_an_approved_spatial_connection": True})
        tasks.append({
            "index_id": node["id"], "name": row["name"], "kind": row["kind"],
            "possible_global_levels": node["possible_global_levels"],
            "sources": src, "all_cited_pages_in_ledger": all(x["reviewed"] for x in src),
            "unaccepted_neighbor_hypotheses": unaccepted,
            "source_preserving_next_action": (
                "READ_AND_DISAMBIGUATE_EXISTING_REVIEWED_PAGE_REFERENT"),
            "no_automatic_link": True,
            "no_geometric_extent_proven": True,
            "not_identified_as_distinct_room_by_isolation_alone": True
        })
    tasks.sort(key=lambda row: (
        not row["all_cited_pages_in_ledger"], -len(row["unaccepted_neighbor_hypotheses"]),
        row["index_id"]))

    gaps = []
    for f in result["research_frontiers_not_edges"]:
        page_refs = [resolve(x) for x in f["source_pages"]]
        gaps.append({
            **f, "primary_page_sources": page_refs,
            "all_boundary_pages_reviewed": all(p["reviewed"] for p in page_refs),
            "next_action": "REEXAMINE_ROUTE_TRANSITION_OR_KEEP_NARRATIVE_GAP",
            "link_automatically": False,
        })
    if len(tasks) != result["counts"][
            "isolated_fixed_room_corridor_door_or_technical_infrastructure"]:
        raise ValueError("FIXED_INFRASTRUCTURE_REVIEW_COUNT_MISMATCH")
    if len(gaps) != result["counts"]["narrative_gaps"]:
        raise ValueError("NARRATIVE_RESEARCH_FRONTIER_COUNT_MISMATCH")
    return {
        "schema": "APA-MOAG-RESEARCH-FRONTIERS-R06/0.1",
        "status": "SOURCE_REVIEW_REQUIRED_NO_AUTO_CONNECT",
        "physical_index_inventory": result["counts"]["physical_indices"],
        "fixed_infrastructure_isolation_count": len(tasks),
        "total_isolated_indices_including_ships_and_reference_volumes": result["counts"]["isolated_physical_indices"],
        "still_unverified_station_candidates": result["counts"]["unverified_moag_station_identity_indices"],
        "isolated_fixed_infrastructure": tasks,
        "narrative_route_gaps": gaps,
        "total_route_gaps": len(gaps),
        "page_provenance_gate": "SOURCE_PAGE_LEDGER_DOES_NOT_PROVE_EVERY_POTENTIAL_LINK",
        "geometry_approved": False,
        "archicad_write": False
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    output = json.dumps(assemble_review(), ensure_ascii=False, indent=2) + "\n"
    if a.out:
        a.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
