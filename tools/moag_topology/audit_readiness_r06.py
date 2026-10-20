#!/usr/bin/env python3
"""MOAG R06 measurable readiness audit. Counts are evidence coverage, NOT BIM %."""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path

import assemble_evidence_graph_r06 as assembly
import inspect_graph_structure_r06 as structural

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
SYNTH = BASE / "synthesis"
BOOKS = {"B1": 114, "B2": 148, "B3": 71, "B4": 79}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit():
    graph = read(SYNTH / "full_indexed_parametric_graph_r04.json")
    fragments = read(SYNTH / "progressive_fragments_r05.json")
    bounds = read(SYNTH / "area_volume_bounds_r05.json")
    routes = read(BASE / "v2/character_routes.json")
    result = assembly.assemble(graph, fragments, routes, bounds)
    projection = structural.project(graph, fragments, bounds, result)

    full_pages = Counter()
    all_pages = 0
    for book, expected in BOOKS.items():
        manifest = read(BASE / "v2/pages" / (book + ".json"))
        if len(manifest["pages"]) != expected:
            raise ValueError("INCOMPLETE_PAGE_MANIFEST: " + book)
        all_pages += len(manifest["pages"])
        full_pages[book] = sum(x["status"] == "REVIEWED_FULL_PAGE"
                               for x in manifest["pages"])
    audited_total = sum(full_pages.values())
    if all_pages != 412:
        raise ValueError("CORPUS_PAGE_COUNT_CHANGED")

    source = read(BASE / "v2/page_observations.json")
    indexed = result["counts"]["physical_indices"]
    occurrences = result["counts"]["route_occurrences"]
    route_mapped = sum(bool(x.get("existing_graph_node"))
                       for route in routes["routes"] for x in route["nodes"])
    connected_visits = sum(x["type"] == "ROUTE_VISITS_INDEX"
                           for x in result["typed_evidence_edges"])
    if connected_visits > route_mapped:
        raise ValueError("ROUTE_VISITS_EXCEED_MAPPED_STEPS")
    level_singletons = sum(len(x["possible_global_levels"]) == 1
                           for x in result["nodes"]
                           if x["layer"] == "PHYSICAL_INDEX")
    values = projection["spatial_area_volume_profiles"]
    scenario_profiles = sum(x["editable_project_bounds"]["footprint_area_m2"] is not None
                            for x in values)
    source_numeric_proven = sum(
        x["book_derived_numeric_limits"]["footprint_area_m2"] is not None
        for x in values)
    directly_mapped = sum(len(x["possible_global_levels"]) == 1
                          for x in result["nodes"]
                          if x["layer"] == "ROUTE_OCCURRENCE")
    geocoordinates = sum(bool(x["coordinates_known"])
                         for x in result["nodes"] if x["layer"] == "PHYSICAL_INDEX")

    return {
        "schema": "APA-MOAG-R06-MEASURED-READINESS/0.1",
        "status": "EVIDENCE_TOPOLOGY_PARTIAL_NOT_MODEL_OR_APPROVED_DRAWINGS",
        "no_single_subjective_completion_percentage": True,
        "source_reading": {
            "first_pass_fully_reviewed_pages": audited_total,
            "total_corpus_pages": all_pages,
            "percent": round(audited_total / all_pages * 100, 1),
            "by_book": dict(full_pages),
            "indexed_spatial_observations": len(source["observations"]),
            "independent_textological_audit_completed": False,
        },
        "graph_structure": {
            "indexed_physical_and_conceptual_candidates": indexed,
            "qualitative_components": result["counts"]["after_routes_physical_components"],
            "fully_isolated_indices": result["counts"]["isolated_physical_indices"],
            "direct_access_links": len(projection["direct_access_graph"]["edges"]),
            "direct_access_components": projection["direct_access_graph"]["component_count"],
            "semantic_review_links_excluded_from_connectivity":
                result["counts"]["source_backed_edges_by_class"].get(
                    "R04_PROVISIONAL_CONTEXT_NOT_CONNECTING", 0),
            "unresolved_promotions": result["counts"]["promotions_needing_identity_review"],
        },
        "routes": {
            "registered_routes": result["counts"]["route_ledgers"],
            "recorded_steps": occurrences,
            "steps_with_existing_index_reference": route_mapped,
            "steps_with_accepted_source_index_link": connected_visits,
            "mapped_ratio_percent": round(route_mapped / occurrences * 100, 1),
            "narrative_gap_boundaries": result["counts"]["narrative_gaps"],
            "vertical_order_constraints": result["counts"]["vertical_order_constraints"],
            "supported_multilevel_network_contacts":
                result["counts"]["documented_multilevel_network_contacts"],
        },
        "area_volume": {
            "indexed_profiles": len(values),
            "applicable_project_interval_profiles": scenario_profiles,
            "non_area_indices": len(values) - scenario_profiles,
            "book_metric_footprint_profiles": source_numeric_proven,
            "scenario_interval_failures": result["counts"]["area_check_failures"],
            "book_metric_range_proof_not_substituted_with_scenario": True,
            "actual_ship_manoeuvre_clearances_proven": False,
        },
        "levels_and_geometry": {
            "indexed_candidates_with_single_global_level_domain": level_singletons,
            "indexed_candidates_with_multivalued_level_domain": indexed - level_singletons,
            "route_steps_with_single_global_level": directly_mapped,
            "physically_confirmed_xy_index_count": geocoordinates,
            "metric_vertical_offsets_verified": False,
            "plans_elevations_sections_mutually_verified": False,
        },
        "hard_blockers_for_BIM": [
            "CORPUS_FIRST_PASS_INCOMPLETE",
            "IDENTITY_REVIEW_PENDING",
            "DIRECT_ACCESS_GRAPH_FRAGMENTED",
            "MISSING_VERIFIED_METRIC_XY_AND_Z",
            "HIGH_VOLUME_INTERIOR_DECKS_NOT_GEOMETRICALLY_VALIDATED",
            "NO_APPROVED_COHERENT_3D_MODEL",
        ],
        "gates": {
            "source_ledger_validated_by_separate_CI": True,
            "geometry_unique": False,
            "archicad_write": False,
            "BIM_release_ready": False,
            "readiness_percentage_can_be_interpreted_as_project_completion": False,
        }
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = audit()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
