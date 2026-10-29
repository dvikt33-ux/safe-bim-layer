#!/usr/bin/env python3
"""МОАГ R20: preserve witnessed intermediate corridors and resolve one old-angar visit.

Only source-qualified *semantic* identity, corridor-stage, and temporarily
open-gate assertions are modelled. Nothing here places a door, wall or room
in XYZ. Earlier R09-R19 artifacts remain byte-for-byte untouched.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import solver_r11 as r11
import integrated_spatial_r15 as r15
import cargo_history_r19 as r19
import identity_alternatives_r18 as r18

HERE=Path(__file__).parent
SLEEPING="MOAG-G-0057"
ROUND="MOAG-G-0055"
SEALED="MOAG-G-0021"
ANGAR_PASSAGE="MOAG-G-0017"
OLD_CARGO_CONCEPT="MOAG-G-0053"
ACCESS_EDGE="MOAG-RG-E144"
SOURCE_IDS=("P-213","P-216","P-217","P-219","P-374","P-375")

def source_map():
    return {o["id"]:o for o in r11.read(r11.BASE/"v2/page_observations.json")["observations"]}

def evidence(obs_id,meaning=None):
    o=source_map()[obs_id]
    if o["station_id"]!="MOAG" or o["evidence_class"]!="DIRECT_TEXT":
        raise ValueError("R20_NON_STATION_OR_UNVERIFIED_EVIDENCE: "+obs_id)
    return {"id":obs_id,"page_id":o["page_id"],"url":o["citation_url"],
            "summary":meaning or o["spatial_assertion"],
            "source_type":"PREEXISTING_BOOK_PAGE_OBSERVATION"}

def build():
    m,history,identities=r19.build()
    raw,fragments,_,_,_=r11.inputs()
    indexed={x["id"]:x for x in raw["indexed_source_entities"]+
             raw["indexed_r03_entities"]+fragments["physical_entities"]}
    for key in (SLEEPING,ROUND,SEALED,ANGAR_PASSAGE,OLD_CARGO_CONCEPT):
        if key not in indexed:
            raise ValueError("R20_SOURCE_PHYSICAL_INDEX_MISSING: "+key)
    edges={x["id"]:x for x in raw["source_relationships"]}
    e=edges[ACCESS_EDGE]
    if (e["from"]!=SEALED or e["to"]!=ANGAR_PASSAGE or
        e["relation"]!="access_route_by_old_corridor" or
        e["semantic_class"]!="ROUTE_REACHABILITY_NOT_DIRECT_DOOR" or
        e["evidence_state"]!="TEXT_DIRECT"):
        raise ValueError("R20_OLD_CORRIDOR_SOURCE_RELATION_DRIFT")
    stages={x["id"]:x for x in m["r14"]["steps"]}
    for ids in (("RT015-C","RT015-D","RT015-E","RT015-F","RT015-G",
                 "RT015-H","RT015-I"),("RT031-D","RT031-E","RT031-F")):
        if not all(x in stages for x in ids):
            raise ValueError("R20_RECORDED_ROUTE_INTERMEDIATES_DROPPED")
    if not (stages["RT015-G"]["stable_graph_anchor"]==ANGAR_PASSAGE
        and stages["RT015-I"]["stable_graph_anchor"]==ROUND
        and stages["RT031-D"]["stable_graph_anchor"]==SEALED
        and stages["RT031-E"]["stable_graph_anchor"]==OLD_CARGO_CONCEPT
        and stages["RT031-F"]["stable_graph_anchor"]==ANGAR_PASSAGE):
        raise ValueError("R20_OLD_ROUTE_ANCHOR_DRIFT")
    src=source_map()
    if {(s,src[s]["page_id"]) for s in SOURCE_IDS}!={
        ("P-213","B1-074"),("P-216","B1-075"),("P-217","B1-075"),
        ("P-219","B1-076"),("P-374","B2-017"),("P-375","B2-017")}:
        raise ValueError("R20_BOOK_SOURCE_PAGE_DRIFT")
    oldtoken=identities["tokens"][SLEEPING]
    tokens={}
    for name in ("RT015-G","RT015-I",ROUND):
        i=len(m["variables"])
        m["variables"].append({"name":"R20::REFERENT::"+name,
                               "domain":[0,22],"interval":True})
        tokens[name]=i
    sourcefacts=[]
    def add(cid,rows,sources,family,kind,any_of=False):
        entry={"id":cid,"rows":rows,"sources":[evidence(x) for x in sources],
               "status":kind,"any_of":any_of,"family":family}
        m["constraints"].append(entry)
        sourcefacts.append({"id":cid,"family":family,"observations":list(sources),
                            "kind":kind,"physical_xy_claimed":False})
    def equal(a,b,cid,src,kind):
        add(cid,[r15.row([(a,1),(b,-1)],0),r15.row([(b,1),(a,-1)],0)],
            [src],"r20_visit_identity",kind)
    # The old route record RT015-G has a legacy broad ANGAR_PASSAGE anchor.
    # The explicit named visit is the *sleepers' hangar*; keep the old
    # anchor visible and file a correction for the index registry, rather
    # than editing earlier R14/R15 data or claiming a placed room.
    equal(tokens["RT015-G"],oldtoken,"R20-REPAIR-RT015-G-SLEEPING-HALL",
          "P-216","SOURCE_STABLE_REFERENT_OVERLAY_NOT_R14_ANCHOR_REWRITE")
    equal(tokens["RT015-I"],tokens[ROUND],"R20-RT015-I-ROUND-HALL",
          "P-219","SOURCE_STABLE_REFERENT_OVERLAY_NOT_METRIC_PLACEMENT")
    # B1-075: after the sleepers' hangar an explicit local descent leads
    # to "another hall"; B1-076 calls that latter space high and round.
    add("R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT",[
        r15.row([(oldtoken,1),(tokens[ROUND],-1)],1),
        r15.row([(tokens[ROUND],1),(oldtoken,-1)],1)],
        ["P-217","P-219"],"r20_hall_distinct",
        "SOURCE_TWO_DIFFERENT_HALLS_NOT_ASSERTED_DISTANCE_OR_FLOOR",True)

    bcount=len(m["variables"])
    m["variables"].append({"name":"R20::B1-074::DOCUMENTED-FORK-OPTIONS",
                           "domain":[0,8],"interval":True})
    # Three documented branches, not a proof of exactly 3 total built exits.
    add("R20-SEALED-FORK-HAS-AT-LEAST-THREE-RECORDED-OPTIONS",
        [r15.row([(bcount,1)],3)],["P-213"],"r20_fork",
        "SOURCE_MINIMUM_BRANCH_COUNT_NOT_NEW_CORRIDORS")
    gate=len(m["variables"])
    m["variables"].append({"name":"R20::RT031-D::GATE-OPEN-IN-EPISODE",
                           "domain":[0,1],"interval":True})
    add("R20-RT031-GATE-OPEN-WITH-ELECTRONIC-KEY",
        [r15.row([(gate,1)],1)],["P-374"],"r20_gate",
        "EPISODE_OPEN_STATE_NOT_PERMANENT_DOOR_STATE")
    mid=len(m["variables"])
    m["variables"].append({"name":"R20::RT031-E::WIDE-CORRIDOR-STAGE-KEPT",
                           "domain":[0,1],"interval":True})
    direct=len(m["variables"])
    m["variables"].append({"name":"R20::E144::RECORDED-PATH-IS-DIRECT-DOOR-REPRESENTATION",
                           "domain":[0,1],"interval":True})
    add("R20-RT031-INTERMEDIATE-WIDE-CORRIDOR-MUST-BE-RETAINED",[
        r15.row([(mid,1)],1)],["P-375"],"r20_corridor",
        "SOURCE_RECORDED_INTERMEDIATE_NOT_NEW_PHYSICAL_ROOM")
    # E144 is ROUTE_REACHABILITY_NOT_DIRECT_DOOR. For this episode,
    # forbid *replacing the recorded multi-stage route with a direct-door
    # edge*. This is NOT a claim that no door can physically exist elsewhere.
    add("R20-E144-NOT-A-DIRECT-DOOR-REPRESENTATION",[
        r15.row([(direct,-1)],0)],["P-375"],"r20_corridor",
        "GRAPH_EDGE_TYPE_NOT_ABSENCE_OF_OTHER_PHYSICAL_DOORS")
    # Link the existing indexed stages *as one recorded path* without
    # reassigning RT031-E's conceptual freight-region anchor to a room.
    overlay={
        "id":"R20-RT031-SEALED-OLD-CORRIDOR-HANGAR-EPISODE",
        "source_edge":ACCESS_EDGE,
        "source_kind":e["semantic_class"],"source_proof":"P-375",
        "endpoint_stage_ids":["RT031-D","RT031-F"],"intermediate_stage_id":"RT031-E",
        "source_endpoints":[SEALED,ANGAR_PASSAGE],
        "stage_original_graph_anchors":[SEALED,OLD_CARGO_CONCEPT,ANGAR_PASSAGE],
        "confirmed_visitation_order":True,
        "geometry_or_direct_door_established":False,
        "same_physical_gate_as_RT015_or_RT024_established":False,
        "real_corridor_width_m":None,"path_length_m":None,
        "intermediate_is_not_new_room":True
    }
    discrepancy={
        "route_stage_id":"RT015-G",
        "old_inherited_R14_anchor":ANGAR_PASSAGE,
        "source_supported_episode_referent":SLEEPING,
        "source_observation":"P-216",
        "status":"INDEX_CROSSWALK_REVIEW_REQUIRED_LEGACY_ANCHOR_NOT_REWRITTEN",
        "book_referent_token_var":tokens["RT015-G"],
        "canonical_sleeping_hall_var":oldtoken,
        "graph_repair_approved":False,
        "r15_geometry_binding_changed":False
    }
    data={
        "schema":"MOAG-R20-SEAL-ANGAR-QUALIFIED-PATHS-AND-ROOMS/1",
        "base_R19_commit":"c623a221394200841d7dea1646565f64cadc5009",
        "R09_fingerprint":m["R09_fingerprint"],
        "source_qualified_constraints":sourcefacts,
        "referent_variables":tokens,
        "source_sleeping_hall_token":oldtoken,
        "fork_count_var":bcount,"episode_gate_open_var":gate,
        "intermediate_stage_present_var":mid,
        "recorded_path_direct_door_representation_var":direct,
        "recorded_route_overlay":overlay,
        "legacy_anchor_discrepancy":discrepancy,
        "verified_live_web_book_pages":["B2-017","B1-076"],
        "B1_074_075_not_independently_accessible_in_web_R20":True,
        "no_new_direct_doors":True,"no_new_physical_rooms":True,
        "no_XYZ_or_area_inferred":True,
        "historical_cargo_R19_unchanged":True,
        "R18_six_undecided_pairs_still_open":True,
        "R15_bound_visits":25,"R15_unbound_visits":353,
        "main_untouched":True,"archicad_write":False
    }
    validate(m,data,history,identities)
    return m,data,history,identities


def validate(m,d,h,ident):
    r19.validate(m,h,ident)
    if len(m["r14"]["steps"])!=378 or len(m["unbound_route_steps"])!=353:
        raise ValueError("R20_ORIGINAL_ROUTE_STAGE_LOST")
    if len(d["source_qualified_constraints"])!=7 or len(d["referent_variables"])!=3:
        raise ValueError("R20_BOOK_DEPENDENCIES_INCOMPLETE")
    by={c["id"]:c for c in m["constraints"]}
    vars=d["referent_variables"]
    direct=d["recorded_path_direct_door_representation_var"]
    mid=d["intermediate_stage_present_var"]
    fork=d["fork_count_var"]
    gate=d["episode_gate_open_var"]
    proof={
      "R20-REPAIR-RT015-G-SLEEPING-HALL":
        [r15.row([(vars["RT015-G"],1),(d["source_sleeping_hall_token"],-1)],0),
         r15.row([(d["source_sleeping_hall_token"],1),(vars["RT015-G"],-1)],0)],
      "R20-RT015-I-ROUND-HALL":
        [r15.row([(vars["RT015-I"],1),(vars[ROUND],-1)],0),
         r15.row([(vars[ROUND],1),(vars["RT015-I"],-1)],0)],
      "R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT":
        [r15.row([(d["source_sleeping_hall_token"],1),(vars[ROUND],-1)],1),
         r15.row([(vars[ROUND],1),(d["source_sleeping_hall_token"],-1)],1)],
      "R20-SEALED-FORK-HAS-AT-LEAST-THREE-RECORDED-OPTIONS":[r15.row([(fork,1)],3)],
      "R20-RT031-GATE-OPEN-WITH-ELECTRONIC-KEY":[r15.row([(gate,1)],1)],
      "R20-RT031-INTERMEDIATE-WIDE-CORRIDOR-MUST-BE-RETAINED":[r15.row([(mid,1)],1)],
      "R20-E144-NOT-A-DIRECT-DOOR-REPRESENTATION":[r15.row([(direct,-1)],0)]
    }
    for cid,rows in proof.items():
        if cid not in by or by[cid]["rows"]!=rows or not by[cid]["sources"]:
            raise ValueError("R20_BOOK_RELATION_NOT_COMPILED: "+cid)
    if not by["R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT"]["any_of"]:
        raise ValueError("R20_DISTINCT_HALLS_DISJUNCTION_LOST")
    if d["recorded_route_overlay"]["stage_original_graph_anchors"]!=[
            SEALED,OLD_CARGO_CONCEPT,ANGAR_PASSAGE]:
        raise ValueError("R20_ORIGINAL_3_STAGE_LINK_NOT_PRESERVED")
    x=d["legacy_anchor_discrepancy"]
    if x["old_inherited_R14_anchor"]!=ANGAR_PASSAGE or x["source_supported_episode_referent"]!=SLEEPING:
        raise ValueError("R20_MISINDEXED_SLEEPING_HALL_WAS_HIDDEN")
    if (x["graph_repair_approved"] or x["r15_geometry_binding_changed"] or
        d["recorded_route_overlay"]["geometry_or_direct_door_established"] or
        d["recorded_route_overlay"]["same_physical_gate_as_RT015_or_RT024_established"] or
        not d["no_new_direct_doors"] or not d["no_new_physical_rooms"] or
        not d["no_XYZ_or_area_inferred"] or d["archicad_write"] or not d["main_untouched"]):
        raise ValueError("R20_UNSOURCED_GEO_DOOR_OR_CROSSWALK_PROMOTION")
    return True


def negative(m,d):
    tk=d["referent_variables"]
    test_merge=r15.probe("R20-TEST-MERGE-SLEEPERS-ROUND",[
       r15.row([(d["source_sleeping_hall_token"],1),(tk[ROUND],-1)],0),
       r15.row([(tk[ROUND],1),(d["source_sleeping_hall_token"],-1)],0)])
    test_fork=r15.probe("R20-TEST-TRUNCATE-FORK-TO-TWO",[
       r15.row([(d["fork_count_var"],-1)],-2)])
    test_gate=r15.probe("R20-TEST-CLAIM-GATE-CLOSED-DURING-PASSAGE",[
       r15.row([(d["episode_gate_open_var"],-1)],0)])
    test_corridor=r15.probe("R20-TEST-DELETE-PASSAGE-STAGE",[
       r15.row([(d["intermediate_stage_present_var"],-1)],0)])
    test_shortcut=r15.probe("R20-TEST-MAKE-E144-DIRECT-DOOR",[
       r15.row([(d["recorded_path_direct_door_representation_var"],1)],1)])
    return [
        ("hall-merge",test_merge,"R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT","r20_hall_distinct"),
        ("missing-third-branch",test_fork,"R20-SEALED-FORK-HAS-AT-LEAST-THREE-RECORDED-OPTIONS","r20_fork"),
        ("temporarily-closed-gate",test_gate,"R20-RT031-GATE-OPEN-WITH-ELECTRONIC-KEY","r20_gate"),
        ("missing-middle-corridor",test_corridor,"R20-RT031-INTERMEDIATE-WIDE-CORRIDOR-MUST-BE-RETAINED","r20_corridor"),
        ("false-direct-door-edge",test_shortcut,"R20-E144-NOT-A-DIRECT-DOOR-REPRESENTATION","r20_corridor")
    ]


def experiment(out,executable):
    out.mkdir(parents=True,exist_ok=True)
    m,d,h,a=build()
    r11.write(out/"book-paths-audit.json",d)
    cp=r15.cp_solve(m)
    mz=r15.mzn_solve(m,executable,out,"joint-path-sat")
    if cp["status"]!="SAT" or mz["status"]!="SAT":
        raise RuntimeError("R20_JOINT_MODEL_NOT_SAT")
    replay=r15.mzn_solve(m,executable,out,"cp-witness-replay",fixed=cp["witness"])
    if replay["status"]!="SAT":
        raise RuntimeError("R20_CROSS_BACKEND_REPLAY_FAILURE")
    corechecks=[]
    for label,probe,source_constraint,family in negative(m,d):
        baseline=r15.cp_solve(m,[probe],exclude_families=(family,))
        bad=r15.cp_solve(m,[probe])
        mb=r15.mzn_solve(m,executable,out,label+"-unsat",[probe])
        core={x["id"] for x in bad["unsat_core"]}
        if (baseline["status"]!="SAT" or bad["status"]!="INFEASIBLE"
              or mb["status"]!="INFEASIBLE" or
              not {probe["id"],source_constraint}<=core):
            raise RuntimeError("R20_SOURCE_CONFLICT_OR_ABLATION_MISSING: "+label)
        cp_core=r15.cp_solve(m,[probe],active=core)
        mz_core=r15.mzn_solve(m,executable,out,label+"-core",[probe],active=core)
        if cp_core["status"]!="INFEASIBLE" or mz_core["status"]!="INFEASIBLE":
            raise RuntimeError("R20_CONFLICT_CORE_NOT_REPLAYED: "+label)
        corechecks.append({"test":label,"synthetic":probe["id"],
           "source_constraint":source_constraint,"without_source":"SAT",
           "with_source":"INFEASIBLE","core":bad["unsat_core"],
           "core_reproduced_python_and_minizinc":True})
    # R18/R19 older uncertain physical pairs remain testable both ways.
    for kind in ("same","different"):
        q=r18.query(a,"M-L1-CG-001","M-L1-AH-OLD-001",kind)
        if r15.cp_solve(m,[q])["status"]!="SAT":
            raise RuntimeError("R20_OLD_CARGO_UNPROVEN_IDENTITY_WAS_FORCED: "+kind)
    if r11.digest(r11.inputs()[-1])!=d["R09_fingerprint"]:
        raise RuntimeError("R20_R09_CHANGED")
    res={"schema":"MOAG-R20-OLD-SEAL-TYPED-PATH-CONSTRAINTS/1",
      "status":"R20_SOURCE_HALL_AND_INTERMEDIATE_CORRIDOR_PASS",
      "source_constraint_count":len(d["source_qualified_constraints"]),
      "indexed_legacy_sleepers_visit_discrepancies_flagged":1,
      "distinct_sleepers_and_round_hall_book_supported":True,
      "three_documented_fork_options_minimum":3,
      "book_witnessed_RT031_middle_corridor_retained":True,
      "route_E144_not_promoted_to_direct_door":True,
      "new_physical_doors":0,"new_physical_rooms":0,
      "new_metric_xyz_constraints":0,
      "r15_bound_visits_unchanged":25,
      "r15_unbound_visits_unchanged":353,
      "R18_old_cargo_physical_identity_alternatives_still_open":True,
      "real_python_cp_sat":cp["status"],"real_minizinc_cp_sat":mz["status"],
      "fixed_witness_replayed_by_minizinc":True,
      "five_source_conflict_tests":corechecks,
      "main_modified":False,"archicad_write":False}
    r11.write(out/"results.json",res)
    print({x:res[x] for x in ("status","source_constraint_count",
             "indexed_legacy_sleepers_visit_discrepancies_flagged")})
    return res


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    parser.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    arg=parser.parse_args()
    if not arg.minizinc:parser.error("Official MiniZinc CP-SAT required")
    experiment(arg.out,arg.minizinc)

if __name__=="__main__":main()
