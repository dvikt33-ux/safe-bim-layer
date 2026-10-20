#!/usr/bin/env python3
"""МОАГ R10: source-page bridge triage derived from canonical R09, NOT spatial proof.

Do not treat co-occurrence on a page, a traversed narrative interval, or a
candidate functional anchor as evidence of a door, shared room, or metric XY/Z.
This program is an auditable RESEARCH QUEUE ONLY.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

import reconcile_uncertainty_r09 as r09

BASE = r09.BASE
SYNTH = r09.SYNTH
BOOK_TOTALS = {"B1": 114, "B2": 148, "B3": 71, "B4": 79}
IDENTITIES = SYNTH / "global_identity_review_r06.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evidence_pages():
    observations = read(BASE / "v2/page_observations.json")["observations"]
    observation_page = {}
    for obs in observations:
        if obs["id"] in observation_page:
            raise ValueError("R10_DUPLICATE_OBSERVATION_ID")
        observation_page[obs["id"]] = obs["page_id"]
    ledger = {}
    for book, total in BOOK_TOTALS.items():
        rows = read(BASE / "v2/pages" / (book + ".json"))["pages"]
        if len(rows) != total:
            raise ValueError("R10_PAGE_LEDGER_SIZE_CHANGED")
        for row in rows:
            if row["id"] in ledger:
                raise ValueError("R10_DUPLICATE_PAGE_ID")
            ledger[row["id"]] = row
    if len(ledger) != 412:
        raise ValueError("R10_PAGE_COVERAGE_NOT_412")
    return observation_page, ledger


def resolve(sources, observed, ledger):
    """Keep unknown source IDs explicit; never silently map them to a page."""
    result, unresolved = set(), set()
    for source in sources:
        if source in observed:
            page = observed[source]
        else:
            match = re.search(r"(B[1-4])-(\d+)$", source)
            page = "%s-%03d" % (match.group(1), int(match.group(2))) if match else None
        if page not in ledger:
            unresolved.add(source)
        else:
            result.add(page)
    return sorted(result), sorted(unresolved)


def build(graph, fragments, bounds, routes, *, master=None, left=None,
          identity_register=None, observation_page=None, page_ledger=None):
    left = left if left is not None else r09.r08a.build(graph, fragments, bounds, routes)
    master = master if master is not None else r09.build(
        graph, fragments, bounds, routes, left=left)
    identities = identity_register if identity_register is not None else read(IDENTITIES)
    if observation_page is None or page_ledger is None:
        observation_page, page_ledger = evidence_pages()
    if master["schema"] != "APA-MOAG-RECONCILED-HYPOTHESIS-OVERLAY-R09/0.1":
        raise ValueError("R10_REQUIRES_CANONICAL_R09")
    if (master["source_invariants"]["proven_nodes"] != 575
            or master["source_invariants"]["proven_edges"] != 761
            or master["source_invariants"]["proven_components"] != 39
            or master["source_invariants"]["approved_direct_access"] != 25
            or master["quantities"]["total_vertices"] != 593
            or master["quantities"]["total_typed_edges"] != 845
            or master["quantities"]["hypothetical_edges"] != 84):
        raise ValueError("R10_MASTER_INVARIANT_MISMATCH")
    if (master["nodes"][:575] != left["unified_evidence_graph"]["nodes"]
            or master["edges"][:761] != left["unified_evidence_graph"]["edges"]):
        raise ValueError("R10_R07_PREFIX_CHANGED")
    if (master["gates"]["archicad_write"]
            or master["gates"]["hypothesis_may_merge_evidence_components"]):
        raise ValueError("R10_GRAPH_RELEASE_GATE_OPEN")

    nodes = {x["id"]: x for x in master["nodes"]}
    edges = {x["id"]: x for x in master["edges"]}
    components = left["unified_evidence_graph"]["component_membership"]
    if (len(nodes) != 593 or len(edges) != 845
            or set(components) != {x["id"] for x in master["nodes"][:575]}):
        raise ValueError("R10_GRAPH_MEMBERSHIP_INVALID")
    pages = defaultdict(lambda: {
        "fixed_indices": set(), "narrative_gaps": set(),
        "witnessed_intervals": set(), "identity_questions": set()})

    def attach(page_ids, key, identifier):
        for page in page_ids:
            pages[page][key].add(identifier)

    groups = master["unlocated_fixed_element_options"]
    fixed = []
    if len(groups) != 12 or len({g["target_index_id"] for g in groups}) != 12:
        raise ValueError("R10_FIXED_GROUP_LOST")
    for g in groups:
        target = g["target_index_id"]
        if (target not in components or not g["not_selected"]
                or not g["none_of_the_above_is_allowed"]
                or len(g["original_option_ids"]) != 2
                or len(g["canonical_edge_ids"]) != 2):
            raise ValueError("R10_FIXED_OPTIONS_INVALID")
        choices = []
        for original, canonical in zip(g["original_option_ids"], g["canonical_edge_ids"]):
            if not canonical:
                raise ValueError("R10_LOST_CANONICAL_OPTION")
            candidate_anchors = []
            for cid in canonical:
                e = edges.get(cid)
                if (not e or target not in (e["from"], e["to"])
                        or e.get("proves_direct_access", False)
                        or e.get("direct_access_proven", False)
                        or e.get("joins_approved_evidence_component", False)
                        or e.get("connects_proven_components", False)
                        or e.get("metric_geometry_proven", True)):
                    raise ValueError("R10_OPTION_PROMOTED_OR_MISSING")
                anchor = e["to"] if e["from"] == target else e["from"]
                if anchor not in components:
                    raise ValueError("R10_OPTION_ANCHOR_NOT_PROVEN_INDEX")
                candidate_anchors.append({
                    "anchor_id": anchor,
                    "anchor_proven_component": components[anchor],
                    "different_components_if_later_proven":
                        components[anchor] != components[target]})
            choices.append({
                "original_option_id": original, "canonical_edge_ids": canonical,
                "candidate_anchors_not_proven_neighbors": candidate_anchors,
                "approved_as_link": False})
        page_ids, missing = resolve(g["source_ids"], observation_page, page_ledger)
        attach(page_ids, "fixed_indices", target)
        fixed.append({
            "target_index_id": target,
            "source_ids": g["source_ids"], "source_pages": page_ids,
            "unresolved_source_ids": missing,
            "current_proven_component": components[target],
            "possible_options": choices, "may_remain_unlocated": True,
            "source_page_cooccurrence_does_not_prove_a_link": True,
            "next_action": "READ_SOURCE_PAGE_AND_CHECK_EXACT_ENDPOINT_REFERENTS"})
    gaps = []
    for g in master["gap_placeholders"]:
        canonical = g["canonical_hypothetical_node_id"]
        route, a, b = g["route_id"], *g["step_ids"]
        original = edges.get("MISSING-TRANSIT:" + route + "::" + a + "::" + b)
        if (not original or original["layer"] != "DOCUMENTED_GAP_NO_ROUTE_LINK"
                or original["proves_direct_access"]
                or original["joins_approved_evidence_component"]
                or canonical not in nodes
                or not nodes[canonical].get("not_a_separate_room")):
            raise ValueError("R10_NARRATIVE_GAP_PROMOTED_OR_LOST")
        page_ids, missing = resolve(original["source_ids"], observation_page, page_ledger)
        attach(page_ids, "narrative_gaps", canonical)
        gaps.append({
            "id": canonical, "route_id": route, "end_route_step_ids": [a, b],
            "boundary_source_pages": page_ids, "unresolved_source_ids": missing,
            "shared_boundary_level_domain": g["joint_candidate_level_domain"],
            "intermediate_level_remains_unbounded_by_endpoints": True,
            "possible_intermediate_decks_not_as_certainty":
                g["global_deck_domain_of_actual_intermediate_path"],
            "no_direct_link_or_new_corridor_proven": True,
            "next_action": "FIND_INTERVENING_NARRATIVE_OR_LEAVE_GAP_UNKNOWN"})
    if len(gaps) != 18 or len({x["id"] for x in gaps}) != 18:
        raise ValueError("R10_GAP_COUNT_CHANGED")

    intervals = []
    for s in master["witnessed_route_steps_with_unresolved_intermediate_geometry"]:
        start, end = s["from_occurrence"], s["to_occurrence"]
        underlying = edges.get(s["id"])
        if (not underlying or underlying["layer"] != "OBSERVED_TRAJECTORY"
                or underlying["proves_direct_access"]
                or start not in components or end not in components
                or not s["intermediate_geometry_unknown"]
                or s["direct_door_or_same_corridor_proven"]):
            raise ValueError("R10_WITNESSED_INTERVAL_PROMOTED_OR_LOST")
        page_ids, missing = resolve(s["source_ids"], observation_page, page_ledger)
        attach(page_ids, "witnessed_intervals", s["id"])
        intervals.append({
            "id": s["id"], "from_occurrence": start, "to_occurrence": end,
            "source_pages": page_ids, "unresolved_source_ids": missing,
            "both_steps_in_same_current_qualitative_component":
                components[start] == components[end],
            "not_proof_of_immediate_access": True,
            "unknown_number_of_intervening_elements": True})
    if len(intervals) != 306 or len({x["id"] for x in intervals}) != 306:
        raise ValueError("R10_WITNESSED_INTERVAL_COUNT_CHANGED")

    review_items = identities["review_items"]
    if len(review_items) != 5:
        raise ValueError("R10_GLOBAL_IDENTITY_DEBT_CHANGED")
    identity_questions = []
    for item in review_items:
        if (item["global_identity_approved"]
                or item["metric_extent_equivalence_approved"]):
            raise ValueError("R10_UNREVIEWED_IDENTITY_WAS_PROMOTED")
        key = item["source_concept_id"] + ":" + item["candidate_physical_index_id"]
        page_ids, missing = resolve(
            item["source_observation_ids"], observation_page, page_ledger)
        attach(page_ids, "identity_questions", key)
        identity_questions.append({
            "id": key, "review_kind": item["review_kind"],
            "source_pages": page_ids, "unresolved_source_ids": missing,
            "unapproved_merge": True, "additive_area_count_forbidden": True})

    # Review score is an ordering device ONLY. Same-page mention is not a
    # physical connection; route steps may already share one evidence component.
    page_queue = []
    for page_id, associations in pages.items():
        roles = {k: sorted(v) for k, v in associations.items()}
        score = (8 * len(roles["fixed_indices"])
                 + 5 * len(roles["narrative_gaps"])
                 + 4 * len(roles["identity_questions"])
                 + min(6, len(roles["witnessed_intervals"])))
        reviewed = page_ledger[page_id]["status"] == "REVIEWED_FULL_PAGE"
        page_queue.append({
            "page_id": page_id, "url": page_ledger[page_id]["url"],
            "already_marked_full_page_reviewed": reviewed,
            "priority_score_not_confidence": score,
            **roles,
            "cooccurrence_is_only_a_review_hint": True,
            "can_merge_components": False})
    page_queue.sort(key=lambda row: (
        -row["priority_score_not_confidence"],
        row["already_marked_full_page_reviewed"], row["page_id"]))
    referenced = {x for row in page_queue for x in [row["page_id"]]}
    all_missing = sorted({
        source for group in fixed + gaps + intervals + identity_questions
        for source in group["unresolved_source_ids"]})
    return {
        "schema": "APA-MOAG-REVIEW-FRONTIERS-R10/0.1",
        "status": "SOURCE_PAGE_TRIAGE_ONLY_PROOF_GRAPH_UNMODIFIED",
        "derivation": "Canonical R09 + original R07 component membership + page ledger",
        "immutable_graph_quantities": dict(master["source_invariants"]),
        "fixed_isolates": fixed, "narrative_route_gaps": gaps,
        "witnessed_intervals_without_direct_geometry": intervals,
        "global_identity_questions": identity_questions,
        "source_page_review_queue": page_queue,
        "quantities": {
            "fixed_isolates": len(fixed), "candidate_options": sum(
                len(x["possible_options"]) for x in fixed),
            "narrative_gaps": len(gaps), "witnessed_intervals": len(intervals),
            "global_identity_questions": len(identity_questions),
            "pages_with_one_or_more_frontier_signals": len(referenced),
            "pages_with_frontier_signals_not_marked_full_review": sum(
                not x["already_marked_full_page_reviewed"] for x in page_queue),
            "unresolved_source_references": len(all_missing)
        },
        "unresolved_source_references": all_missing,
        "priority_method": "8*isolates + 5*gaps + 4*identities + min(6, witnessed); not evidence strength",
        "gates": {
            "topology_changed": False, "hypothesis_to_direct_access": False,
            "same_page_means_adjacent": False, "book_dimensions_invented": False,
            "XY_Z_assigned": False, "area_recounted": False,
            "archicad_write": False, "BIM_release_ready": False
        }
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
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
