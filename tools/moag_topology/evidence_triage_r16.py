#!/usr/bin/env python3
"""МОАГ R16: review ALL 353 unbound R15 stages and retain a sourced route fork.

No new rooms or metrically placed corridors. The only NEW solver relation is
the qualitative B1-065 short-vs-long branch choice. All remaining categories
are review queues, NEVER automated author evidence or physical geometry.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
import shutil

import solver_r11 as r11
import integrated_spatial_r15 as r15

HERE = Path(__file__).parent
FOUR_PAGE_GAPS = ("B1-061", "B1-063", "B1-064", "B1-065")
FORK_INDEX = "MOAG-G-0100"
FORK_ROUTE = "RT-014"
VERTICAL_METHODS = {
    "ELEVATOR", "ELEVATOR_UP", "ELEVATOR_DOWN", "CLIMB_UP",
    "CLIMB_DOWN", "DROP_DOWN", "LADDER_UP", "STAIR", "HATCH_CLIMB"
}
PORTAL_METHODS = {"DOOR", "VEHICLE_ENTRY"}
AGGREGATE_KINDS = {"level", "zone", "space_group", "system", "logical_access", "utility"}
CIRCULATION_KINDS = {"circulation", "corridor", "vertical_route", "portal", "local_gallery"}


def classify(stage, entity):
    """Triage hints ONLY. Deliberately does not infer new physical entities."""
    if stage["stable_graph_anchor"]:
        kind = entity["kind"]
        if kind in AGGREGATE_KINDS:
            return "INDEXED_AGGREGATE_OR_SYSTEM_REQUIRES_DOMAIN_NOT_ROOM"
        if kind in CIRCULATION_KINDS:
            return "INDEXED_CORRIDOR_PORTAL_OR_SHAFT_REQUIRES_NONROOM_DOMAIN"
        if kind == "space":
            return "INDEXED_SPACE_REQUIRES_SOURCE_BACKED_VOLUME"
        return "INDEXED_UNCLASSIFIED_KIND_REVIEW"
    method = stage["movement_method"]
    if method == "NARRATIVE_GAP":
        return "UNLOCATED_NARRATIVE_GAP_NO_SHAFT_OR_ROOM_AUTHORIZED"
    if method in VERTICAL_METHODS:
        return "UNINDEXED_VERTICAL_TRAVERSAL_REVIEW_NOT_NEW_SHAFT"
    if method in PORTAL_METHODS:
        return "UNINDEXED_PORTAL_REVIEW_NOT_ROOM"
    return "UNINDEXED_MOVEMENT_OR_FEATURE_REVIEW_NOT_NEW_ROOM"


def build():
    # An exact R15 reprojection remains the starting point. Its constraints
    # and authoritative evidence are not rewritten.
    base = r15.build()
    baseline = r11.read(r11.SYNTH / "r15/calculation/missing_evidence.json")
    missing = base["unbound_route_steps"]
    if {s["id"] for s in missing} != {s["id"] for s in baseline["unbound_steps"]}:
        raise ValueError("R15_PUBLISHED_UNBOUND_STAGE_DRIFT")
    if len(missing) != 353:
        raise ValueError("R15_MISSING_STAGE_COUNT_DRIFT")

    raw, fragments, _, _, _ = r11.inputs()
    indexed = {e["id"]: e for e in raw["indexed_source_entities"] +
               raw["indexed_r03_entities"] + fragments["physical_entities"]}
    route_stage = {s["id"]: s for s in base["r14"]["steps"]}
    if len(route_stage) != 378:
        raise ValueError("R14_ROUTE_STAGES_NOT_COMPLETE")

    audit = []
    for item in missing:
        stage = route_stage[item["id"]]
        anchor = item["anchor"]
        if anchor != stage["stable_graph_anchor"]:
            raise ValueError("UNBOUND_STAGE_ANCHOR_DRIFT: " + item["id"])
        entity = indexed.get(anchor) if anchor else None
        if anchor and entity is None:
            raise ValueError("UNKNOWN_SOURCE_INDEX: " + anchor)
        if stage["citation_status"] != "PAGE_OBSERVATION_CROSS_REF" and stage["page_id"] not in FOUR_PAGE_GAPS:
            raise ValueError("UNKNOWN_ROUTE_PAGE_PROVENANCE")
        audit.append({
            "id": item["id"], "route": stage["route"], "source_page": stage["page_id"],
            "method": stage["movement_method"], "index_anchor": anchor,
            "index_kind": entity["kind"] if entity else None,
            "index_name": entity["name"] if entity else None,
            "global_block_domain": item["domain_blocks"],
            "review_class": classify(stage, entity),
            "review_priority": "P1_LOWER" if item["domain_blocks"] == [1] else
                               "P2_OTHER" if len(item["domain_blocks"]) == 1 else
                               "P3_UNRESOLVED_GLOBAL_BLOCK",
            "R15_reason": item["reason"],
            "evidence_reference": stage["citation_url"],
            "new_physical_entity_authorized": False,
            "placement_approved": False,
            "metric_area_authorized": False,
            "next_action": "CHECK_EXISTING_INDEX_AND_PRIMARY_SOURCE_NOT_ADD_RECTANGLE"
            if anchor else "VERIFY_STORY_STAGE_IS_A_PHYSICAL_OBJECT_BEFORE_ANY_INDEX",
        })
    audit.sort(key=lambda x: x["id"])

    # These pages have MISSING page_observation URLs, but their *existing
    # page-ledger* records do include full URLs. Citation linkage can therefore
    # be recovered without guessing page numbers or re-reading book text.
    ledger = r11.read(r11.BASE / "v2/pages/B1.json")
    page_map = {x["id"]: x for x in ledger["pages"]}
    if set(base["r14"]["unverified_page_cross_references"]) != set(FOUR_PAGE_GAPS):
        raise ValueError("R14_MISSING_URL_INVENTORY_CHANGED")
    recovered = []
    for page in FOUR_PAGE_GAPS:
        if page not in page_map or not page_map[page].get("url"):
            raise ValueError("PRIMARY_PAGE_LEDGER_URL_UNAVAILABLE: " + page)
        row = page_map[page]
        if row["status"] != "REVIEWED_FULL_PAGE" or row["target_station"] != "MOAG":
            raise ValueError("PAGE_NOT_ACCEPTED_AS_MOAG_REVIEWED: " + page)
        relevant = [s["id"] for s in base["r14"]["steps"] if s["page_id"] == page]
        if not relevant:
            raise ValueError("UNREFERENCED_LEDGER_GAP: " + page)
        recovered.append({
            "page_id": page, "url": row["url"],
            "source_of_url": "EXISTING_B1_PAGE_LEDGER_NOT_PAGE_OBSERVATION",
            "ledger_review_status": row["status"],
            "route_stages_with_page": relevant,
            "primary_text_reaudited_in_R16": False,
            "R14_source_record_rewritten": False,
            "citation_overlay_not_new_geometry": True
        })
    b1_65 = page_map["B1-065"]["notes"]
    if not all(t in b1_65.lower() for t in ("прав", "короче", "лев", "длиннее", "обход")):
        raise ValueError("FORK_LONG_SHORT_SOURCE_TEXT_CHANGED")
    fork = next(r for r in base["r14"]["routes"] if r["id"] == FORK_ROUTE)
    steps = {s["id"]: s for s in base["r14"]["steps"]}
    if not {"RT014-D", "RT014-E", "RT014-F"} <= set(fork["step_ids"]):
        raise ValueError("FORK_ROUTE_OBSERVED_STAGES_NOT_FOUND")
    if steps["RT014-D"]["stable_graph_anchor"] != FORK_INDEX:
        raise ValueError("FORK_NOT_CONNECTED_TO_INDEXED_BASE_APPROACH")
    if steps["RT014-E"]["stable_graph_anchor"] is not None:
        raise ValueError("LONG_BRANCH_IDENTITY_UNEXPECTEDLY_PROMOTED")
    if steps["RT014-E"]["page_id"] != "B1-065":
        raise ValueError("FORK_ROUTE_SOURCE_DRIFT")

    fork_fact = {
        "id": "R16-FORK-B1-065-LONGER-THAN-SHORTER",
        "route": FORK_ROUTE, "fork_index": FORK_INDEX,
        "observed_long_branch_stage": "RT014-E",
        "short_branch": "KNOWN_UNTRAVERSED_OPTION_NOT_A_NEW_ROOM",
        "long_branch": "OBSERVED_CHOSEN_OPTION_NOT_A_NEW_ROOM",
        "chosen_branch": "LONGER_LEFT_BY_OBSERVER_FRAME",
        "closed_branch": "SHORTER_RIGHT_BY_OBSERVER_FRAME",
        "source_page": "B1-065", "source_url": page_map["B1-065"]["url"],
        "source_origin": "PREEXISTING_PAGE_LEDGER_AND_ROUTE_RT014",
        "kind": "QUALITATIVE_RELATIVE_PATH_LENGTH_ONLY",
        "metric_distance_measured": False, "junction_xy_proven": False,
        "physical_door_proven": False, "both_branches_new_physical_nodes": False,
        "branch_lengths_are_abstract_ranks_not_metres": True,
    }

    # R16 introduces the one evidence-backed qualitative ordering into the
    # SAME R15 solver problem. Neither rank is a length in metres or a room.
    short_id = len(base["variables"])
    base["variables"].append({"name": "R16::B1-065::SHORTER-LENGTH-ORDER",
                              "domain": [0, 8], "interval": True})
    long_id = len(base["variables"])
    base["variables"].append({"name": "R16::B1-065::LONGER-LENGTH-ORDER",
                              "domain": [0, 8], "interval": True})
    base["constraints"].append({
        "id": fork_fact["id"],
        "rows": [r15.row([(long_id, 1), (short_id, -1)], 1)],
        "sources": [{"id": "LEDGER::B1-065", "page_id": "B1-065",
                     "url": fork_fact["source_url"],
                     "summary": "Правая ветвь короче, левая длиннее; выбран обход"}],
        "status": "source_qualitative_comparison_not_metric_length",
        "any_of": False, "family": "r16_branch_choice"
    })
    info = {
        "schema": "MOAG-R16-SOURCE-REVIEW-AND-ONE-QUALITATIVE-FORK/1",
        "base_R15_head": "2f965d12992073b8837d08b2d3e2a06d42994c4f",
        "R09_fingerprint": base["R09_fingerprint"],
        "unchanged_R15_unbound_count": len(missing),
        "review_queue": audit, "source_url_overlay": recovered,
        "fork_comparison": fork_fact,
        "fork_short_rank_var": short_id, "fork_long_rank_var": long_id,
        "page_ledger_recovered_without_new_book_reading": len(recovered),
        "nonmetric_review_categories_only": True,
        "R09_unchanged": True, "R15_route_bindings_unchanged": True,
        "R15_scenario_boxes_unchanged": True,
        "geometry_approved": False, "new_rooms_created": False,
        "archicad_write": False,
    }
    validate(base, info)
    return base, info


def validate(base, info):
    r15.validate(base)
    queue = info["review_queue"]
    if len(queue) != 353 or len({x["id"] for x in queue}) != len(queue):
        raise ValueError("R16_REVIEW_QUEUE_NOT_COMPLETE")
    if len([x for x in queue if x["index_anchor"]]) != 189:
        raise ValueError("INDEXED_UNBOUND_COUNT_DRIFT")
    if len([x for x in queue if not x["index_anchor"]]) != 164:
        raise ValueError("UNINDEXED_UNBOUND_COUNT_DRIFT")
    if len([x for x in queue if x["global_block_domain"] == [1]]) != 112:
        raise ValueError("LOWER_PRIORITY_COUNT_DRIFT")
    if any(x["new_physical_entity_authorized"] or x["placement_approved"] or x["metric_area_authorized"]
           for x in queue):
        raise ValueError("REVIEW_PROMOTED_TO_PHYSICAL_ROOM")
    if {x["page_id"] for x in info["source_url_overlay"]} != set(FOUR_PAGE_GAPS):
        raise ValueError("FOUR_PRIMARY_LEDGER_LINKS_NOT_RETAINED")
    if any(x["primary_text_reaudited_in_R16"] or x["R14_source_record_rewritten"]
           or not x["citation_overlay_not_new_geometry"] for x in info["source_url_overlay"]):
        raise ValueError("SOURCE_CITATION_REVIEW_STATUS_FALSIFIED")
    fact = info["fork_comparison"]
    c = next((x for x in base["constraints"] if x["id"] == fact["id"]), None)
    if c is None or c["rows"] != [r15.row(
            [(info["fork_long_rank_var"],1),(info["fork_short_rank_var"],-1)],1)]:
        raise ValueError("FORK_CONSTRAINT_MISSING_OR_INVERTED")
    if not any(x.get("url") == fact["source_url"] for x in c["sources"]):
        raise ValueError("FORK_SOURCE_NOT_IN_SOLVER")
    if fact["metric_distance_measured"] or fact["junction_xy_proven"] or fact["physical_door_proven"]:
        raise ValueError("QUALITATIVE_PATH_LENGTH_PROMOTED_TO_METRES")
    if (info["geometry_approved"] or info["new_rooms_created"] or info["archicad_write"]
            or not info["R09_unchanged"] or not info["R15_scenario_boxes_unchanged"]):
        raise ValueError("UNAPPROVED_BIM_OR_SOURCE_MUTATION")
    return True


def run(outdir, minizinc):
    outdir.mkdir(parents=True, exist_ok=True)
    m, info = build()
    r11.write(outdir / "review-queue.json", info)
    source_count = Counter(x["review_class"] for x in info["review_queue"])
    priority = Counter(x["review_priority"] for x in info["review_queue"])
    cp = r15.cp_solve(m)
    mz = r15.mzn_solve(m, minizinc, outdir, "integrated-fork-sat")
    if cp["status"] != mz["status"] or cp["status"] != "SAT":
        raise RuntimeError("R16_FORK_SAT_FAILED")
    replay = r15.mzn_solve(m, minizinc, outdir, "cp-witness", fixed=cp["witness"])
    if replay["status"] != "SAT":
        raise RuntimeError("R16_MINIZINC_CROSS_REPLAY_FAILED")

    before = r15.cp_solve(m, exclude_families=("r16_branch_choice",),
                          objective=(info["fork_long_rank_var"], "min"))
    after = r15.cp_solve(m, objective=(info["fork_long_rank_var"], "min"))
    if before["solver_status"] != "OPTIMAL" or after["solver_status"] != "OPTIMAL":
        raise RuntimeError("R16_ORDER_ABLATION_NOT_OPTIMAL")
    if before["objective"] != 0 or after["objective"] != 1:
        raise RuntimeError("R16_QUALITATIVE_LENGTH_NOT_ACTUALLY_RESTRICTED")

    inverse = r15.probe("R16-SYNTHETIC-REVERSE-B1-065",
                        [r15.row([(info["fork_short_rank_var"],1),
                                  (info["fork_long_rank_var"],-1)],0)])
    bad = r15.cp_solve(m, [inverse])
    mzb = r15.mzn_solve(m, minizinc, outdir, "reverse-fork-unsat", [inverse])
    core = {c["id"] for c in bad["unsat_core"]}
    if (bad["status"] != mzb["status"] or bad["status"] != "INFEASIBLE" or
            not {inverse["id"], info["fork_comparison"]["id"]} <= core):
        raise RuntimeError("R16_FORK_UNSAT_NOT_EXPLAINED")
    core_cp = r15.cp_solve(m, [inverse], active=core)
    core_mz = r15.mzn_solve(m, minizinc, outdir, "reverse-fork-core", [inverse], active=core)
    if core_cp["status"] != core_mz["status"] or core_cp["status"] != "INFEASIBLE":
        raise RuntimeError("R16_FORK_CORE_NOT_REPLAYED")
    if r11.digest(r11.inputs()[-1]) != info["R09_fingerprint"]:
        raise RuntimeError("R16_R09_MUTATED")
    result = {
        "schema": "MOAG-R16-AUDIT-AND-QUALITATIVE-BRANCH-SOLVER/1",
        "status": "FULL_R15_SAT_PLUS_SOURCE_FORK_SAT_UNSAT_PASS",
        "reviewed_unbound_stages": len(info["review_queue"]),
        "with_existing_index": 189, "without_existing_index": 164,
        "lower_block_only": 112,
        "review_category_counts": dict(sorted(source_count.items())),
        "priority_counts": dict(sorted(priority.items())),
        "preexisting_citation_urls_crosslinked": len(info["source_url_overlay"]),
        "citation_ids": [x["page_id"] for x in info["source_url_overlay"]],
        "source_fork": info["fork_comparison"],
        "python_cp_sat": cp["status"], "minizinc_cp_sat": mz["status"],
        "cross_backend_replay": replay["status"],
        "synthetic_inverse_python": bad["status"],
        "synthetic_inverse_minizinc": mzb["status"],
        "unsat_core": bad["unsat_core"],
        "core_replay_both_solvers": core_cp["status"] == core_mz["status"] == "INFEASIBLE",
        "long_branch_rank_min_without_source_relation": before["objective"],
        "long_branch_rank_min_with_source_relation": after["objective"],
        "rank_not_metres": True,
        "R15_geometric_binding_count_changed": False,
        "metric_volume_model_approved": False,
        "book_B3_B4_reaudit_completed": False,
        "new_physical_nodes_created": 0,
        "main_updated": False, "archicad_write": False,
    }
    r11.write(outdir / "results.json", result)
    print({"status": result["status"], "stages": len(info["review_queue"]),
           "ledger_urls": len(info["source_url_overlay"]),
           "source_branch_min_rank": after["objective"]})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    portable = next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"), None)
    portable = portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"), None)
    ap.add_argument("--minizinc", type=Path, default=shutil.which("minizinc") or portable)
    args = ap.parse_args()
    if args.minizinc is None:
        ap.error("Official MiniZinc CP-SAT executable required")
    run(args.out, args.minizinc)


if __name__ == "__main__":
    main()
