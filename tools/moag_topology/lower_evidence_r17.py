#!/usr/bin/env python3
"""МОАГ R17: exact-source Lower sector split and existing portal-chain evidence.

The categorical solver variables are *NOT XYZ*, metre distance, wall geometry,
floors or an assumed north/south orientation. Keep R09-R16 unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import shutil

import solver_r11 as r11
import integrated_spatial_r15 as r15
import evidence_triage_r16 as r16

HERE=Path(__file__).parent
SOURCE_SECTOR_PAGE="B2-014"
SOURCE_SECTOR_URL="https://loveread.ec/read_book.php?id=53370&p=14"
SOURCE_BRIDGE_PAGE="B1-076"
SOURCE_BRIDGE_URL="https://loveread.ec/read_book.php?id=48197&p=76"
FIVE_PRIORITY={
 "MOAG-G-0021":"SEALED_REGION_NOT_SINGLE_ROOM",
 "MOAG-G-0053":"OLD_FREIGHT_SECTOR_CONCEPT_UNRESOLVED_IDENTITY",
 "MOAG-G-0014":"RECYCLING_WORKSHOP_PHYSICAL_CANDIDATE_NOT_BOX",
 "MOAG-G-0017":"ANGAR_MAIN_CORRIDOR_NOT_HALL_ROOM",
 "MOAG-G-0059":"UPPER_BRIDGE_STAIR_ID_REQUIRES_EPISODE_DISAMBIGUATION",
}
# E69 and E70 are sourced direct portals. E20 is *access_to*, so it is NOT
# silently promoted to the exact same relation type as E69/E70.
PORTAL_IDS=("MOAG-RG-E69","MOAG-RG-E70")
ACCESS_ID="MOAG-RG-E20"

def build():
    m, audit=r16.build()
    raw,_,_,_,_=r11.inputs()
    edges={e["id"]:e for e in raw["source_relationships"]}
    steps={s["id"]:s for s in m["r14"]["steps"]}
    review=audit["review_queue"]
    by_id=Counter(x["index_anchor"] for x in review if x["index_anchor"])
    for eid in FIVE_PRIORITY:
        if eid not in by_id:
            raise ValueError("PRIORITY_SOURCE_INDEX_MISSING: "+eid)
    if {eid:by_id[eid] for eid in FIVE_PRIORITY}!={
            "MOAG-G-0021":11,"MOAG-G-0053":8,"MOAG-G-0014":6,
            "MOAG-G-0017":4,"MOAG-G-0059":4}:
        raise ValueError("LOWER_FOCUS_COUNTS_CHANGED")

    if steps["RT030-D"]["stable_graph_anchor"]!="MOAG-G-0017" or (
       steps["RT030-E"]["stable_graph_anchor"]!="MOAG-G-0018"):
        raise ValueError("HANGAR_CORRIDOR_OR_FIRST_HANGAR_ID_CHANGED")
    # The B2 p14 speaker explicitly distinguishes the inhabited bases
    # from the hangar part of Lower. No direction, length, absolute XY,
    # shape or pairwise disjointness of every hypothetical room follows.
    lo=len(m["variables"])
    m["variables"].append({"name":"R17::REGION-LABEL::INHABITED-BASES",
                           "domain":[0,2],"interval":True})
    hi=len(m["variables"])
    m["variables"].append({"name":"R17::REGION-LABEL::HANGAR-SECTOR",
                           "domain":[0,2],"interval":True})
    distinct={
       "id":"R17-DISTINCT-BASE-HANGAR-SECTORS-B2-014",
       "rows":[r15.row([(lo,1),(hi,-1)],1),
               r15.row([(hi,1),(lo,-1)],1)],
       "sources":[{"id":"B2-014","page_id":"B2-014","url":SOURCE_SECTOR_URL,
                   "summary":"Базы в другой части Нижнего; развилка ведёт в ангарные проходы"}],
       "status":"DIRECT_BOOK_FUNCTIONAL_SECTOR_DISTINCTION_NOT_XY_DISJOINTNESS",
       "any_of":True,"family":"r17_sector"}
    m["constraints"].append(distinct)
    portals=[]
    for eid in PORTAL_IDS:
        e=edges[eid]
        if (e["relation"]!="door_to" or
            e["semantic_class"]!="DOOR_OR_PRESSURE_PORTAL_EVIDENCE" or
            e["evidence_state"]!="TEXT_DIRECT"):
            raise ValueError("SOURCE_DIRECT_DOOR_EVIDENCE_DRIFT: "+eid)
        portals.append({"id":eid,"from":e["from"],"to":e["to"],
                        "type":"BOOK_DIRECT_DOOR_BETWEEN_EXISTING_INDICES",
                        "source_edge":eid,"source_page":SOURCE_BRIDGE_PAGE,
                        "source_url":SOURCE_BRIDGE_URL,
                        "new_physical_door_id_created":False,
                        "metric_door_width_proven":False,
                        "XY_or_slab_claimed":False})
    e=edges[ACCESS_ID]
    if (e["relation"]!="access_to" or e["from"]!="MOAG-G-0017" or
        e["to"]!="MOAG-G-0018" or e["evidence_state"]!="TEXT_DIRECT"):
        raise ValueError("SOURCE_HANGAR_ACCESS_DRIFT")
    portals.append({"id":ACCESS_ID,"from":e["from"],"to":e["to"],
                    "type":"SOURCE_ACCESS_TO_WITH_DOOR_NARRATIVE_NOT_GEOMETRIC_DOOR_ID",
                    "source_edge":ACCESS_ID,"source_page":SOURCE_SECTOR_PAGE,
                    "source_url":SOURCE_SECTOR_URL,
                    "new_physical_door_id_created":False,
                    "metric_door_width_proven":False,"XY_or_slab_claimed":False})
    # Model source-backed existence of book passages as categorical Boolean
    # witnesses. No new R09 edge, no drawing of a corridor or common stair.
    flag_ids={}
    for p in portals:
        var=len(m["variables"])
        m["variables"].append({"name":"R17::SOURCE-PASSAGE::"+p["id"],
                               "domain":[0,1],"interval":True})
        flag_ids[p["id"]]=var
        m["constraints"].append({
            "id":"R17-SOURCE-PASSAGE::"+p["id"],
            "rows":[r15.row([(var,1)],1)],
            "sources":[{"id":p["source_edge"],"page_id":p["source_page"],
                        "url":p["source_url"],"summary":p["type"]}],
            "status":"BOOK_PASSAGE_RELATION_BETWEEN_EXISTING_INDICES_NOT_XY_GEOMETRY",
            "any_of":False,"family":"r17_passage"})
    # Source R09 G0059 is used for stairs in multiple scenes, but the user
    # wants no forced merging with the high operator ladder. These stages are
    # NOT made equal in XYZ and no pair is asserted physically different.
    ladders=["RT015-J","RT023-A","RT024-G","RT024-J"]
    if any(steps[x]["stable_graph_anchor"]!="MOAG-G-0059" for x in ladders):
        raise ValueError("SOURCE_STAIR_INDEX_MOVED")
    ambiguity={
       "source_index":"MOAG-G-0059","route_occurrences":ladders,
       "book_bridge_climb":"RT015-J",
       "operator_climb":"RT024-G",
       "claim":"SAME_LEGACY_LABEL_NOT_PROVEN_SAME_PHYSICAL_STAIR",
       "source_pages":["B1-076","B1-104","B1-110","B1-113"],
       "mandatory_XYZ_equivalence":False,
       "mandatory_different_stairs":False,
       "do_not_promote_cross_scene_identity":True}

    focus=[]
    for eid,kind in FIVE_PRIORITY.items():
        subset=[x for x in review if x["index_anchor"]==eid]
        focus.append({"id":eid,"classification":kind,"unbound_visits":len(subset),
                      "visit_ids":[x["id"] for x in subset],
                      "source_refs":[x["evidence_reference"] for x in subset],
                      "physical_volume_created":False,
                      "needs_object_identity_or_domain_review":True})
    info={
       "schema":"MOAG-R17-LOWER-QUALITATIVE-SECTORS-AND-SOURCE-PORTALS/1",
       "base_R16_head":"31fb9e2829ccffd998d4f06a892921366c8a29a3",
       "R09_fingerprint":m["R09_fingerprint"],"R16_fork_retained":True,
       "focus":focus,"functional_sectors":{"base":lo,"hangar":hi,
          "relation_id":distinct["id"],"source_page":SOURCE_SECTOR_PAGE,
          "distinct_as_functional_region_only":True,
          "sector_count_of_whole_station_inferred":False,
          "rank_or_direction_from_picture_inferred":False,
          "metric_separation_proven":False,
          "new_disjoint_3d_boxes_created":False},
       "source_portal_relations":portals,"portal_flags":flag_ids,
       "stairs_ambiguity":ambiguity,
       "existing_route_R14_stage_count":len(m["r14"]["steps"]),
       "R15_bound_visits_count":sum(p["id"] in m["order_variables"] and
            "host_volume" in p for p in m["points"]),
       "R15_unbound_visits_count":len(m["unbound_route_steps"]),
       "new_route_nodes_created":0,"new_physical_rooms_created":0,
       "new_spatial_XYZ_constraints_added":0,
       "books_reaudited_full":False,
       "author_images_preserved":True,
       "main_modified":False,"archicad_write":False,
       "geometry_approved":False,
    }
    validate(m,info)
    return m,info


def validate(m,info):
    r15.validate(m)
    if len(info["focus"])!=5 or sum(x["unbound_visits"] for x in info["focus"])!=33:
        raise ValueError("R17_PRIORITY_REVIEW_LOST")
    if len(m["r14"]["steps"])!=378 or len(m["unbound_route_steps"])!=353:
        raise ValueError("R14_R15_VISITS_DROPPED")
    if info["R15_bound_visits_count"]!=25 or info["R15_unbound_visits_count"]!=353:
        raise ValueError("R15_GENUINE_BINDINGS_CHANGED")
    C={x["id"]:x for x in m["constraints"]}
    sector=info["functional_sectors"]
    if C[sector["relation_id"]]["rows"]!=[
         r15.row([(sector["base"],1),(sector["hangar"],-1)],1),
         r15.row([(sector["hangar"],1),(sector["base"],-1)],1)]:
        raise ValueError("R17_SECTOR_INEQUALITY_CHANGED")
    if C[sector["relation_id"]]["any_of"] is not True:
        raise ValueError("R17_SECTOR_NOT_DISTINCT")
    for p in info["source_portal_relations"]:
        cid="R17-SOURCE-PASSAGE::"+p["id"]
        if cid not in C or C[cid]["rows"]!=[r15.row([(info["portal_flags"][p["id"]],1)],1)]:
            raise ValueError("R17_SOURCE_PASSAGE_LOST")
        if p["new_physical_door_id_created"] or p["metric_door_width_proven"] or p["XY_or_slab_claimed"]:
            raise ValueError("R17_SOURCE_ACCESS_PROMOTED_TO_METRIC_GEOMETRY")
    if (info["new_spatial_XYZ_constraints_added"] or info["new_physical_rooms_created"]
            or info["new_route_nodes_created"] or info["geometry_approved"] or
            info["main_modified"] or info["archicad_write"] or
            info["functional_sectors"]["new_disjoint_3d_boxes_created"] or
            info["stairs_ambiguity"]["mandatory_XYZ_equivalence"]):
        raise ValueError("R17_PREMATURE_GEOMETRIC_ASSERTION")
    return True


def experiment(out, executable):
    out.mkdir(parents=True,exist_ok=True)
    m,info=build()
    r11.write(out/"qualitative-evidence.json",info)
    # R16 full model plus all R17 relations in the same solver problem.
    py=r15.cp_solve(m)
    mz=r15.mzn_solve(m,executable,out,"source-sat")
    if py["status"]!=mz["status"] or py["status"]!="SAT":
        raise RuntimeError("R17_CP_SAT_MINIZINC_SAT_NOT_PROVEN")
    replay=r15.mzn_solve(m,executable,out,"source-cp-witness",fixed=py["witness"])
    if replay["status"]!="SAT":
        raise RuntimeError("R17_INDEPENDENT_WITNESS_REPLAY_FAILED")
    sector=info["functional_sectors"]
    # Synthetic impossibility: book says distinct functional sectors.
    equal=r15.probe("R17-SYNTHETIC-SAME-SECTOR",[
        r15.row([(sector["base"],1),(sector["hangar"],-1)],0),
        r15.row([(sector["hangar"],1),(sector["base"],-1)],0)])
    before=r15.cp_solve(m,[equal],exclude_families=("r17_sector",))
    if before["status"]!="SAT":raise RuntimeError("R17_SECTOR_ABLATION_WAS_NOT_SAT")
    inverse=r15.cp_solve(m,[equal])
    inverse_mz=r15.mzn_solve(m,executable,out,"same-sector-unsat",[equal])
    ids={x["id"] for x in inverse["unsat_core"]}
    if (inverse["status"]!=inverse_mz["status"] or inverse["status"]!="INFEASIBLE" or
        not {equal["id"],sector["relation_id"]}<=ids):
        raise RuntimeError("R17_SOURCE_DISTINCTION_CONFLICT_NOT_DIAGNOSED")
    core=r15.cp_solve(m,[equal],active=ids)
    mz_core=r15.mzn_solve(m,executable,out,"same-sector-core",[equal],active=ids)
    if core["status"]!=mz_core["status"] or core["status"]!="INFEASIBLE":
        raise RuntimeError("R17_CORE_NOT_INDEPENDENTLY_REPRODUCED")
    # Also prove that the passage evidence is *enforced*, not decoration.
    source_id="MOAG-RG-E69"
    flag=info["portal_flags"][source_id]
    broken=r15.probe("R17-SYNTHETIC-MISSING-PORTAL-E69",[
        r15.row([(flag,-1)],0)])
    door_before=r15.cp_solve(m,[broken],exclude_families=("r17_passage",))
    door_after=r15.cp_solve(m,[broken])
    door_mz=r15.mzn_solve(m,executable,out,"bridge-door-unsat",[broken])
    door_ids={x["id"] for x in door_after["unsat_core"]}
    if (door_before["status"]!="SAT" or door_after["status"]!="INFEASIBLE" or
        door_mz["status"]!="INFEASIBLE" or
        not {broken["id"],"R17-SOURCE-PASSAGE::"+source_id}<=door_ids):
        raise RuntimeError("R17_SOURCE_DOOR_NOT_COMPILED")
    if r11.digest(r11.inputs()[-1])!=info["R09_fingerprint"]:
        raise RuntimeError("SOURCE_R09_MUTATED")
    result={
        "schema":"MOAG-R17-LOWER-SOURCE-GATES/1",
        "status":"SOURCE_CATEGORICAL_SECTOR_AND_PORTAL_SAT_UNSAT_PASS",
        "five_focus_unbound_visits":sum(x["unbound_visits"] for x in info["focus"]),
        "r15_bound_visits":25,"r15_unbound_visits":353,
        "new_book_qualified_functional_sector_distinctions":1,
        "existing_direct_book_portal_relations_compiled":2,
        "existing_access_to_relations_compiled_as_access_not_exact_doors":1,
        "python_cp_sat":py["status"],"minizinc_cp_sat":mz["status"],
        "cross_backend_replay":replay["status"],
        "source_sector_contradiction_cp_sat":inverse["status"],
        "source_sector_contradiction_minizinc":inverse_mz["status"],
        "sufficient_core_replay_cp_sat":core["status"],
        "sufficient_core_replay_minizinc":mz_core["status"],
        "sector_equality_without_source":"SAT",
        "book_source_portal_negative_test_cp_sat":door_after["status"],
        "book_source_portal_negative_test_minizinc":door_mz["status"],
        "passage_absence_without_source":"SAT",
        "sector_unsat_core":inverse["unsat_core"],
        "portal_unsat_core":door_after["unsat_core"],
        "metric_XYZ_uncertainty_reduced":False,
        "no_new_rooms_or_archicad_write":True,
        "main_unchanged":True
    }
    r11.write(out/"results.json",result)
    print({k:result[k] for k in ("status","five_focus_unbound_visits",
        "new_book_qualified_functional_sector_distinctions",
        "existing_direct_book_portal_relations_compiled")})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    port=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    port=port or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    p.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or port)
    args=p.parse_args()
    if args.minizinc is None:p.error("Official MiniZinc CP-SAT executable required")
    experiment(args.out,args.minizinc)

if __name__=="__main__":
    main()
