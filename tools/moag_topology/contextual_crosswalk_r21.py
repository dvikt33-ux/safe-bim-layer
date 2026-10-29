#!/usr/bin/env python3
"""МОАГ R21 — source-qualified episode crosswalk for overloaded legacy indices.

The existing R09 physical graph, R14 route anchors and R15 12 scenario boxes
are immutable. Identity tokens mean only named physical referents in a book
episode; they are NOT metres, XYZ, wall geometry, portals or a new room list.
"""
from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
import shutil

import solver_r11 as r11
import integrated_spatial_r15 as r15
import identity_alternatives_r18 as r18
import sealed_paths_r20 as r20

HERE=Path(__file__).parent
ALIASES=("L1-ANGAR-HALL","L1-CIRCULAR-CONTROL","L1-CIRCULAR-STAIRS",
         "L1-OLD-FREIGHT-HANGAR","L1-SEALED")
EXPECTED={"L1-ANGAR-HALL":4,"L1-CIRCULAR-CONTROL":3,
          "L1-CIRCULAR-STAIRS":4,"L1-OLD-FREIGHT-HANGAR":8,"L1-SEALED":11}
EVIDENCE={
    "RT024-F":("M-L1-AH-OLD-001","P-311","P-313"),
    "RT024-H":("M-L1-AH-OLD-CTRL-001","P-313"),
    "RT024-I":("M-L1-AH-OLD-CTRL-001","P-316"),
    "RT015-L":("MOAG-G-0060","P-221"),
    "RT031-F":("EPISODE_ONLY_WORKING_MILITARY_HANGAR","P-375"),
    "RT031-G":("EPISODE_ONLY_WORKING_MILITARY_HANGAR","P-376","P-377"),
    "RT015-G":("MOAG-G-0057","P-216"),
    "RT030-D":("MOAG-G-0017","P-362")
}
SOURCED_SAME=(
    ("RT024-F","M-L1-AH-OLD-001","P-313"),
    ("RT024-H","M-L1-AH-OLD-CTRL-001","P-313"),
    ("RT024-I","RT024-H","P-316"),
    ("RT015-L","MOAG-G-0060","P-221"),
    ("RT031-G","RT031-F","P-376")
)
OPEN_PAIRS=(
    ("MOAG-G-0060","M-L1-AH-OLD-CTRL-001",
     "Manual lock controls B1-076 vs raised old-hangar control B1-110"),
    ("RT031-F","M-L1-FH-001",
     "B2-017 working military hangar vs previously documented first boat hangar"),
    ("RT024-F","MOAG-G-0057",
     "Old raised-control hangar B1-110 vs sleepers' hall B1-075")
)
NEW_REFERENTS=("RT024-F","RT024-H","RT024-I","RT015-L",
               "MOAG-G-0060","M-L1-AH-OLD-CTRL-001",
               "RT031-F","RT031-G")


def observation(obs_id):
    o=next((x for x in r11.read(r11.BASE/"v2/page_observations.json")["observations"]
            if x["id"]==obs_id),None)
    if o is None or o["station_id"]!="MOAG" or o["evidence_class"]!="DIRECT_TEXT":
        raise ValueError("R21_SOURCE_OBSERVATION_MISSING_OR_NOT_DIRECT: "+obs_id)
    return o


def source(obs_id):
    o=observation(obs_id)
    return {"id":obs_id,"page_id":o["page_id"],"url":o["citation_url"],
            "summary":o["spatial_assertion"],
            "source_quality":"PREEXISTING_BOOK_PAGE_OBSERVATION"}


def classify(alias,stage):
    if stage in EVIDENCE:
        return "EXPLICIT_BOOK_REFERENT"+(
            "_LEGACY_ANCHOR_CONFLICT" if stage in ("RT015-G","RT024-F","RT024-H","RT024-I","RT031-F")
            else "_EPISODE_CONTEXT")
    if alias=="L1-OLD-FREIGHT-HANGAR":
        return "CARGO_AREA_OR_CORRIDOR_NOT_AN_INDIVIDUAL_ROOM"
    if alias=="L1-SEALED":
        return "SEALED_SECTOR_OR_EPISODE_GATE_NOT_ONE_SHARED_DOOR"
    if alias=="L1-CIRCULAR-STAIRS":
        return "STAIR_IDENTITY_HANDLED_SEPARATELY_R18"
    return "REVIEW_REQUIRED_NO_NEW_PHYSICAL_IDENTITY"


def build():
    m,a20,h19,a18=r20.build()
    raw,frag,_,_,_=r11.inputs()
    route_rows=r11.read(r11.BASE/"v2/character_routes.json")["routes"]
    master_steps={s["id"]:s for s in m["r14"]["steps"]}
    valid={x["id"] for x in raw["indexed_source_entities"]+
           raw["indexed_r03_entities"]+frag["physical_entities"]}
    registry=[]
    counts=Counter()
    for route in route_rows:
        for stage in route["nodes"]:
            alias=stage["existing_graph_node"]
            if alias not in ALIASES:
                continue
            sid=stage["id"]
            counts[alias]+=1
            eid=raw["legacy_id_to_stable_id"][alias]
            if master_steps[sid]["stable_graph_anchor"]!=eid:
                raise ValueError("R21_LEGACY_CROSSWALK_DRIFT: "+sid)
            claim=EVIDENCE.get(sid)
            if claim and claim[0]!="EPISODE_ONLY_WORKING_MILITARY_HANGAR" and claim[0] not in valid:
                raise ValueError("R21_SOURCE_CORRECTION_NOT_EXISTING_PHYSICAL_INDEX: "+sid)
            registry.append({
                "stage_id":sid,"route_id":route["id"],
                "original_legacy_alias":alias,"original_R14_stable_anchor":eid,
                "episode_book_page":stage["source_page_id"],
                "episode_label":stage["label"],
                "review_class":classify(alias,sid),
                "evidence_backed_episode_referent":claim[0] if claim else None,
                "source_observations":list(claim[1:]) if claim else [],
                "unchanged_original_route_anchor":True,
                "new_physical_room_created":False,
                "metric_geometry_authorized":False,
                "hard_identity_without_direct_evidence":False
            })
    if dict(counts)!=EXPECTED or len(registry)!=sum(EXPECTED.values()):
        raise ValueError("R21_NOT_ALL_OVERLOADED_ALIASES_AUDITED")
    ids={x["stage_id"] for x in registry}
    if len(ids)!=len(registry):
        raise ValueError("R21_DUPLICATE_ROUTE_STAGE")

    tokens=dict(a18["tokens"])
    for referent in NEW_REFERENTS:
        if referent in tokens:
            raise ValueError("R21_EXISTING_TOKEN_REASSIGNED")
        idx=len(m["variables"])
        m["variables"].append({"name":"R21::EPISODE-IDENTITY::"+referent,
                               "domain":[0,22],"interval":True})
        tokens[referent]=idx
    for ref in ("RT015-G","RT015-I"):
        tokens[ref]=a20["referent_variables"][ref]
    # R20 already proved RT015-G == G0057; here no extra physical facts.
    if tokens["RT015-G"]==a20["source_sleeping_hall_token"]:
        raise ValueError("R21_SAME_VARIABLE_INSTEAD_OF_EVIDENCE_CONSTRAINT")

    proven=[]
    for step,entity,src in SOURCED_SAME:
        if step not in tokens or entity not in tokens or step==entity:
            raise ValueError("R21_NOT_REGISTERED_IDENTITY_REFERENT")
        c={"id":"R21-SAME::"+step+"::"+entity,
           "rows":[r15.row([(tokens[step],1),(tokens[entity],-1)],0),
                   r15.row([(tokens[entity],1),(tokens[step],-1)],0)],
           "sources":[source(src)],
           "status":"BOOK_EPISODE_PHYSICAL_REFERENT_NOT_METRIC_PLACEMENT",
           "any_of":False,"family":"r21_source_identity"}
        m["constraints"].append(c)
        proven.append({"id":c["id"],"book_observation":src,
            "episode":step,"referent":entity,
            "R14_anchor_rewritten":False,"physical_XYZ_asserted":False})

    unresolved=[]
    for left,right,reason in OPEN_PAIRS:
        if left not in tokens or right not in tokens:
            raise ValueError("R21_UNRESOLVED_PAIR_MISSING_TOKEN")
        unresolved.append({
           "a":left,"b":right,"reason":reason,
           "same_physical_entity_proven":False,
           "different_physical_entities_proven":False,
           "two_alternatives_must_remain_SAT":True
        })
    # Check R20 book fix instead of inadvertently losing it.
    discrepancy=a20["legacy_anchor_discrepancy"]
    if discrepancy["route_stage_id"]!="RT015-G" or discrepancy["source_supported_episode_referent"]!="MOAG-G-0057":
        raise ValueError("R21_R20_MISINDEXED_SLEEPERS_REPAIR_LOST")
    result={
       "schema":"MOAG-R21-ALL-HIGH-RISK-ALIASES-SOURCE-EPISODE-CROSSWALK/1",
       "base_R20_commit":"6906e1668e239084741ddfd6d009c5f2b358e252",
       "R09_fingerprint":m["R09_fingerprint"],
       "reviewed_aliases":dict(sorted(counts.items())),
       "all_30_legacy_uses":registry,
       "evidence_backed_episode_corrections":proven,
       "unresolved_cross_episode_pairs":unresolved,
       "reference_tokens":tokens,
       "new_referent_token_names":list(NEW_REFERENTS),
       "legacy_R14_label_collision_not_physical_identity":True,
       "R20_sleepers_mismatch_still_open_for_canonical_source_repair":True,
       "R18_six_pairs_remain_uncertain":True,
       "R15_bound_visits_unchanged":25,
       "R15_unbound_visits_unchanged":353,
       "original_route_stage_count":378,
       "original_R09_edge_count":845,
       "new_source_rooms":0,"new_physical_portals":0,
       "new_metric_XYZ_constraints":0,
       "main_changed":False,"archicad_write":False
    }
    validate(m,result,h19,a18)
    return m,result,h19,a18


def validate(m,a,h19,a18):
    r15.validate(m)
    # Do not call the full R20.build() again; check its characteristic constraints.
    existing={c["id"]:c for c in m["constraints"]}
    if not all(k in existing for k in (
        "R20-REPAIR-RT015-G-SLEEPING-HALL",
        "R20-RT015-I-ROUND-HALL",
        "R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT",
        "R19-DIFFERENT-LOWER-CARGO-VS-THIRD-CARGO")):
        raise ValueError("R21_PREVIOUS_R19_R20_SOURCE_FACT_LOST")
    if a["reviewed_aliases"]!=dict(sorted(EXPECTED.items())):
        raise ValueError("R21_LEGACY_AUDIT_COUNTS_CHANGED")
    if len(a["all_30_legacy_uses"])!=30 or len({x["stage_id"] for x in a["all_30_legacy_uses"]})!=30:
        raise ValueError("R21_AUDIT_ROWS_LOST")
    if len(a["evidence_backed_episode_corrections"])!=len(SOURCED_SAME):
        raise ValueError("R21_EVIDENCE_BACKED_EPISODES_DROPPED")
    if len(a["unresolved_cross_episode_pairs"])!=len(OPEN_PAIRS):
        raise ValueError("R21_STILL_UNRESOLVED_IDENTITIES_LOST")
    if set(a["new_referent_token_names"])!=set(NEW_REFERENTS):
        raise ValueError("R21_NEW_EPISODE_TOKEN_RENAMED")
    for x in a["all_30_legacy_uses"]:
        if (not x["unchanged_original_route_anchor"] or
            x["new_physical_room_created"] or x["metric_geometry_authorized"] or
            x["hard_identity_without_direct_evidence"]):
            raise ValueError("R21_UNSOURCED_LEGACY_ALIAS_PROMOTED")
    for step,entity,src in SOURCED_SAME:
        cid="R21-SAME::"+step+"::"+entity
        if cid not in existing or existing[cid]["rows"]!=[
          r15.row([(a["reference_tokens"][step],1),(a["reference_tokens"][entity],-1)],0),
          r15.row([(a["reference_tokens"][entity],1),(a["reference_tokens"][step],-1)],0)]:
            raise ValueError("R21_BOOK_CONTEXT_IDENTITY_NOT_COMPILED: "+cid)
        if existing[cid]["any_of"] or {s["id"] for s in existing[cid]["sources"]}!={src}:
            raise ValueError("R21_DIRECT_BOOK_EVIDENCE_LOST: "+cid)
    if any(x["same_physical_entity_proven"] or x["different_physical_entities_proven"]
           for x in a["unresolved_cross_episode_pairs"]):
        raise ValueError("R21_UNSOURCED_CROSS_SCENE_MERGE")
    if (not a["legacy_R14_label_collision_not_physical_identity"] or
            not a["R20_sleepers_mismatch_still_open_for_canonical_source_repair"] or
            a["new_source_rooms"] or a["new_physical_portals"] or
            a["new_metric_XYZ_constraints"] or a["main_changed"] or a["archicad_write"] or
            len(m["r14"]["steps"])!=378 or len(m["unbound_route_steps"])!=353 or
            len(m["r13"]["volumes"])!=12 or not a["R18_six_pairs_remain_uncertain"]):
        raise ValueError("R21_PREMATURE_SOURCE_OR_GEOMETRY_MUTATION")
    return True


def disagree(a,left,right,name):
    return r18.query({"tokens":a["reference_tokens"]},left,right,"different",name)

def compare(a,left,right,kind,name):
    return r18.query({"tokens":a["reference_tokens"]},left,right,kind,name)


def experiment(out,exe):
    out.mkdir(parents=True,exist_ok=True)
    m,a,h,ident=build()
    r11.write(out/"all-overloaded-route-uses.json",a)
    cp=r15.cp_solve(m)
    mz=r15.mzn_solve(m,exe,out,"crosswalk-sat")
    if cp["status"]!="SAT" or mz["status"]!="SAT":
        raise RuntimeError("R21_FULL_SOURCE_CROSSWALK_NOT_SAT")
    replay=r15.mzn_solve(m,exe,out,"python-witness-replay",fixed=cp["witness"])
    if replay["status"]!="SAT":
        raise RuntimeError("R21_FULL_WITNESS_NOT_REPLAYED")
    conflicts=[]
    for step,entity,src in SOURCED_SAME:
        q=disagree(a,step,entity,"R21-SYNTHETIC-SPLIT-"+step)
        absent=r15.cp_solve(m,[q],exclude_families=("r21_source_identity",))
        bad=r15.cp_solve(m,[q])
        bad_mz=r15.mzn_solve(m,exe,out,"false-split-"+step,[q])
        ids={x["id"] for x in bad["unsat_core"]}
        required="R21-SAME::"+step+"::"+entity
        if (absent["status"]!="SAT" or bad["status"]!="INFEASIBLE" or
            bad_mz["status"]!="INFEASIBLE" or not {q["id"],required}<=ids):
            raise RuntimeError("R21_NOT_SOURCE_EXPLAINED_IDENTITY:"+step)
        cp_core=r15.cp_solve(m,[q],active=ids)
        mz_core=r15.mzn_solve(m,exe,out,"core-split-"+step,[q],active=ids)
        if cp_core["status"]!="INFEASIBLE" or mz_core["status"]!="INFEASIBLE":
            raise RuntimeError("R21_IDENTITY_CONFLICT_CORE_NOT_REPLAYED:"+step)
        conflicts.append({"episode":step,"index":entity,"source":src,
                          "without_source":"SAT","with_source":"UNSAT",
                          "unsat_core":bad["unsat_core"],"cross_backend_core":True})
    alternatives=[]
    for i,x in enumerate(a["unresolved_cross_episode_pairs"]):
        for kind in ("same","different"):
            q=compare(a,x["a"],x["b"],kind,"R21-UNPROVEN-"+str(i)+"-"+kind)
            z=r15.cp_solve(m,[q])
            mz=r15.mzn_solve(m,exe,out,"unresolved-"+str(i)+"-"+kind,[q])
            if z["status"]!="SAT" or mz["status"]!="SAT":
                raise RuntimeError("R21_UNPROVEN_IDENTITY_PROMOTED:"+str(x)+" "+kind)
            replay=r15.mzn_solve(m,exe,out,
               "replay-unresolved-"+str(i)+"-"+kind,[q],fixed=z["witness"])
            if replay["status"]!="SAT":
                raise RuntimeError("R21_ALTERNATIVE_WITNESS_NOT_ACCEPTED")
            alternatives.append({"a":x["a"],"b":x["b"],"kind":kind,
                                 "python":"SAT","minizinc":"SAT","witness_replayed":True})
    if r11.digest(r11.inputs()[-1])!=a["R09_fingerprint"]:
        raise RuntimeError("R21_R09_MASTER_CHANGED")
    res={
        "schema":"MOAG-R21-CONTEXTUAL-CROSSWALK-RESULTS/1",
        "status":"R21_OVERLOADED_ANCHORS_AUDITED_AND_SOURCE_COUNTERMODELS_PASS",
        "audit_aliases":len(ALIASES),
        "audit_route_occurrences":len(a["all_30_legacy_uses"]),
        "new_sourced_same_episode_relations":len(SOURCED_SAME),
        "source_split_unsat_proofs":conflicts,
        "unproven_same_and_different_alternatives":alternatives,
        "all_original_R09_nodes_edges_unchanged":True,
        "route_stages":378,"R15_bound":25,"R15_unbound":353,
        "no_metric_XYZ_constraints":True,"no_new_rooms":True,
        "python_cp_sat":cp["status"],"minizinc_cp_sat":"SAT",
        "replay_full_witness":True,
        "archicad_write":False}
    r11.write(out/"results.json",res)
    print({k:res[k] for k in ("status","audit_aliases",
          "audit_route_occurrences","new_sourced_same_episode_relations")})
    return res


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    p.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    z=p.parse_args()
    if z.minizinc is None:p.error("Official MiniZinc cp-sat executable required")
    experiment(z.out,z.minizinc)


if __name__=="__main__":main()
