#!/usr/bin/env python3
"""МОАГ R18 — evidence-bounded physical identity alternatives, not geometry.

Identity is an equivalence relation over explicitly selected episode references.
An equality is hard only when a source describes the *same* stair/space;
shared legacy graph labels are NEVER automatically equated. A recorded
distinctness is separate from route connectivity. Abstract tokens are not XYZ.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil

import solver_r11 as r11
import integrated_spatial_r15 as r15
import lower_evidence_r17 as r17

HERE=Path(__file__).parent
# Each chosen token refers to a real registered candidate / episode, not a new room.
REFERENTS=(
    "RT015-J", "RT023-A", "RT024-G", "RT024-J", "RT030-G",
    "M-L1-CH-ST-001", "M-L1-AH-OLD-ST-001", "M-L1-FH-001-ST",
    "M-L1-FH-002-ST", "MOAG-G-0053", "M-L1-CG-001",
    "M-L1-AH-OLD-001", "MOAG-G-0057", "M-L1-FH-001",
    "M-L1-FH-002"
)
# Source-confirmed same physical referent (not equal coordinates, no whole floor).
SAME=(
    ("RT015-J","M-L1-CH-ST-001","P-220"),
    ("RT024-G","M-L1-AH-OLD-ST-001","P-313"),
    ("RT024-J","RT024-G","P-317"),
    ("RT030-G","M-L1-FH-001-ST","P-365")
)
# Two boat hangars are explicitly different physical hangars; their upper
# operator cabins communicate but are NOT one room as a result.
DIFFERENT=(("M-L1-FH-001","M-L1-FH-002","P-367","P-368"),)
# Neither sameness nor difference follows from these pairs of descriptions.
UNKNOWN=(
    ("RT015-J","RT024-G","round-hall broken steps vs suspended old-hangar stair"),
    ("RT023-A","RT015-J","old service-room exit vs round-hall bridge"),
    ("RT023-A","RT024-G","old service-room exit vs old-hangar control"),
    ("MOAG-G-0053","M-L1-CG-001","old freight source concept vs R03 physical complex"),
    ("M-L1-CG-001","M-L1-AH-OLD-001","old freighter complex vs B1-110 raised control hangar"),
    ("MOAG-G-0057","M-L1-AH-OLD-001","sleeping adults hall vs old-hangar control episode")
)


def read_source_map():
    return {o["id"]:o for o in r11.read(r11.BASE/"v2/page_observations.json")["observations"]}


def relation(a,b,source,kind):
    o=read_source_map()[source]
    return {"a":a,"b":b,"kind":kind,"source_observation_id":source,
        "source_page_id":o["page_id"],"source_url":o["citation_url"],
        "summary":o["spatial_assertion"],"metric_xyz_implied":False,
        "new_physical_room_created":False}


def build():
    m,lower=r17.build()
    original,fragments,_,_,_=r11.inputs()
    valid={x["id"] for x in original["indexed_source_entities"]+
          original["indexed_r03_entities"]+fragments["physical_entities"]}
    steps={x["id"]:x for x in m["r14"]["steps"]}
    sources=read_source_map()
    for ref in REFERENTS:
        if ref not in valid and ref not in steps:
            raise ValueError("R18_REFERENT_NOT_REGISTERED: "+ref)
    # R17 warned that four steps mapped to G0059 were *not* necessarily one
    # physical ladder. Keep independent tokens until explicit source linkage.
    for ref in ("RT015-J","RT023-A","RT024-G","RT024-J"):
        if steps[ref]["stable_graph_anchor"]!="MOAG-G-0059":
            raise ValueError("R17_SHARED_LEGACY_STAIR_ANCHOR_CHANGED")
    if steps["RT030-G"]["stable_graph_anchor"]!="MOAG-G-0019":
        raise ValueError("B2_OPERATOR_ROUTE_ANCHOR_CHANGED")
    tokens={}
    for ref in REFERENTS:
        ix=len(m["variables"])
        m["variables"].append({"name":"R18::IDENTITY::"+ref,
                               "domain":[0,len(REFERENTS)-1],"interval":True})
        tokens[ref]=ix
    certified_same=[];certified_distinct=[]
    def add_eq(a,b,src):
        evidence=relation(a,b,src,"BOOK_PROVEN_SAME_PHYSICAL_REFERENT")
        ix,iy=tokens[a],tokens[b]
        cid="R18-SAME::"+a+"::"+b
        m["constraints"].append({"id":cid,
            "rows":[r15.row([(ix,1),(iy,-1)],0),r15.row([(iy,1),(ix,-1)],0)],
            "sources":[{"id":src,"url":evidence["source_url"],"page_id":evidence["source_page_id"],
                        "summary":evidence["summary"]}],
            "status":"SOURCED_IDENTITY_NOT_GEOMETRIC_COINCIDENCE",
            "any_of":False,"family":"r18_identity"})
        certified_same.append({**evidence,"id":cid})
    def add_neq(a,b,src1,src2):
        e1=relation(a,b,src1,"BOOK_PROVEN_DIFFERENT_PHYSICAL_ROOMS")
        e2=relation(a,b,src2,"BOOK_PROVEN_DIFFERENT_PHYSICAL_ROOMS")
        ix,iy=tokens[a],tokens[b]
        cid="R18-DIFFERENT::"+a+"::"+b
        m["constraints"].append({"id":cid,
            "rows":[r15.row([(ix,1),(iy,-1)],1),r15.row([(iy,1),(ix,-1)],1)],
            "sources":[{"id":src,"url":sources[src]["citation_url"],
                        "page_id":sources[src]["page_id"],
                        "summary":sources[src]["spatial_assertion"]} for src in (src1,src2)],
            "status":"SOURCED_ROOM_DISTINCTNESS_NOT_XYZ_DISJOINTNESS",
            "any_of":True,"family":"r18_distinct"})
        certified_distinct.append({**e1,"id":cid,
                                   "additional_source_observation_id":src2,
                                   "additional_source_url":e2["source_url"]})
    for a,b,src in SAME:add_eq(a,b,src)
    for a,b,src1,src2 in DIFFERENT:add_neq(a,b,src1,src2)
    unresolved=[]
    for a,b,explanation in UNKNOWN:
        if a==b or a not in tokens or b not in tokens:
            raise ValueError("UNKNOWN_IDENTITY_PAIR_CORRUPTED")
        unresolved.append({"id":"R18-UNKNOWN::"+a+"::"+b,"a":a,"b":b,
            "status":"BOTH_SAME_AND_DIFFERENT_STILL_SOURCE_COMPATIBLE",
            "reason":explanation,
            "hard_identity_added":False,"hard_distinctness_added":False,
            "source_review_needed":True})
    audit={
       "schema":"MOAG-R18-SOURCED-IDENTITY-AND-OPEN-ALTERNATIVES/1",
       "R17_commit":"e565faa8669848e299568e1a75f68853ee445ffb",
       "R09_fingerprint":m["R09_fingerprint"],
       "tokens":tokens,
       "proven_same":certified_same,"proven_different":certified_distinct,
       "not_yet_decidable":unresolved,
       "shared_legacy_label_is_not_physical_identity":True,
       "identities_are_tokens_not_xyz":True,
       "full_3d_geometry_proven":False,"new_physical_rooms_created":0,
       "r15_bound_visits":25,"r15_unbound_visits":353,
       "new_metric_xyz_constraints":0,"archicad_write":False
    }
    validate(m,audit)
    return m,audit


def validate(m,audit):
    r15.validate(m)
    if set(audit["tokens"])!=set(REFERENTS) or len(audit["proven_same"])!=len(SAME):
        raise ValueError("R18_SOURCE_IDENTITY_RECORDS_LOST")
    if len(audit["proven_different"])!=len(DIFFERENT) or len(audit["not_yet_decidable"])!=len(UNKNOWN):
        raise ValueError("R18_IDENTITY_UNCERTAINTY_LOST")
    cs={c["id"]:c for c in m["constraints"]}
    t=audit["tokens"]
    for a,b,src in SAME:
        cid="R18-SAME::"+a+"::"+b
        if cid not in cs or cs[cid]["rows"]!=[
             r15.row([(t[a],1),(t[b],-1)],0),
             r15.row([(t[b],1),(t[a],-1)],0)]:
            raise ValueError("R18_SOURCED_SAME_DROPPED")
        if not any(x.get("id")==src for x in cs[cid]["sources"]):
            raise ValueError("R18_SOURCE_PROVENANCE_DROPPED")
    for a,b,src1,src2 in DIFFERENT:
        cid="R18-DIFFERENT::"+a+"::"+b
        if cid not in cs or cs[cid]["rows"]!=[
            r15.row([(t[a],1),(t[b],-1)],1),
            r15.row([(t[b],1),(t[a],-1)],1)] or not cs[cid]["any_of"]:
            raise ValueError("R18_DISTINCT_OBJECTS_COLLAPSED")
        if {x["id"] for x in cs[cid]["sources"]}!={src1,src2}:
            raise ValueError("R18_DISTINCTNESS_SOURCE_LOST")
    for x in audit["not_yet_decidable"]:
        if x["hard_identity_added"] or x["hard_distinctness_added"]:
            raise ValueError("R18_UNSUPPORTED_IDENTITY_PROMOTED")
        if any(x["id"] in k for k in cs):
            raise ValueError("R18_UNRESOLVED_PAIR_WAS_HARD_CONSTRAINED")
    if (audit["archicad_write"] or audit["full_3d_geometry_proven"] or
            audit["new_metric_xyz_constraints"] or audit["new_physical_rooms_created"] or
            not audit["shared_legacy_label_is_not_physical_identity"]):
        raise ValueError("R18_GEOMETRY_OR_SOURCE_PROMOTION")
    return True


def query(audit,a,b,kind,name=None):
    x,y=audit["tokens"][a],audit["tokens"][b]
    if kind=="same":
        rows=[r15.row([(x,1),(y,-1)],0),
              r15.row([(y,1),(x,-1)],0)]
    elif kind=="different":
        rows=[r15.row([(x,1),(y,-1)],1),
              r15.row([(y,1),(x,-1)],1)]
    else:raise ValueError("UNKNOWN_IDENTITY_QUERY")
    c=r15.probe(name or "R18-TEST::"+kind+"::"+a+"::"+b,rows)
    c["any_of"]=kind=="different"
    c["status"]="SYNTHETIC_IDENTITY_COUNTERMODEL_NOT_SOURCE_PROOF"
    return c


def experiment(out,executable):
    out.mkdir(parents=True,exist_ok=True)
    m,audit=build()
    r11.write(out/"source-identity-audit.json",audit)
    py=r15.cp_solve(m)
    mz=r15.mzn_solve(m,executable,out,"all-source-identities-sat")
    if py["status"]!=mz["status"] or py["status"]!="SAT":
        raise RuntimeError("R18_SAT_NOT_PROVEN_BOTH_BACKENDS")
    replay=r15.mzn_solve(m,executable,out,"python-witness",fixed=py["witness"])
    if replay["status"]!="SAT":
        raise RuntimeError("R18_SOLVER_WITNESS_CROSSCHECK_FAILED")

    countermodels=[]
    for i,item in enumerate(audit["not_yet_decidable"]):
        for kind in ("same","different"):
            extra=query(audit,item["a"],item["b"],kind,name=f"R18-ALT-{i}-{kind}")
            cp=r15.cp_solve(m,[extra])
            minizinc=r15.mzn_solve(m,executable,out,f"alternative-{i}-{kind}",[extra])
            if cp["status"]!="SAT" or minizinc["status"]!="SAT":
                raise RuntimeError("R18_UNJUSTIFIED_IDENTITY_DEDUCTION: "+item["id"]+" "+kind)
            again=r15.mzn_solve(m,executable,out,f"replay-alternative-{i}-{kind}",
                                 [extra],fixed=cp["witness"])
            if again["status"]!="SAT":
                raise RuntimeError("R18_ALTERNATIVE_CROSS_BACKEND_REPLAY_FAILED")
            countermodels.append({"pair":item["id"],"alternative":kind,
                                  "python":cp["status"],"minizinc":minizinc["status"],
                                  "fixed_python_witness_replayed":True})
    contradictions=[]
    tests=[
        ("BOOK-REPEATED-UPPER-LADDER",query(audit,"RT024-G","RT024-J","different",
            "R18-SYNTHETIC-FALSE-DIFFERENT-RT024"),"R18-SAME::RT024-J::RT024-G","r18_identity"),
        ("BOOK-DISTINCT-BOAT-HANGARS",query(audit,"M-L1-FH-001","M-L1-FH-002","same",
            "R18-SYNTHETIC-MERGED-BOAT-HANGARS"),
            "R18-DIFFERENT::M-L1-FH-001::M-L1-FH-002","r18_distinct")
    ]
    for title,probe,cid,family in tests:
        # Ablation: same bad probe must be possible without the source constraint.
        before=r15.cp_solve(m,[probe],exclude_families=(family,))
        cp=r15.cp_solve(m,[probe])
        mz_bad=r15.mzn_solve(m,executable,out,title.lower()+"-unsat",[probe])
        ids={x["id"] for x in cp["unsat_core"]}
        if before["status"]!="SAT" or cp["status"]!="INFEASIBLE" or (
           mz_bad["status"]!="INFEASIBLE") or not {probe["id"],cid}<=ids:
            raise RuntimeError("R18_SOURCE_CONFLICT_NOT_ESTABLISHED: "+title)
        cpc=r15.cp_solve(m,[probe],active=ids)
        mzc=r15.mzn_solve(m,executable,out,title.lower()+"-core",[probe],active=ids)
        if cpc["status"]!=mzc["status"] or cpc["status"]!="INFEASIBLE":
            raise RuntimeError("R18_CONFLICT_CORE_REPLAY_FAILED: "+title)
        contradictions.append({"name":title,"status":"INFEASIBLE",
            "unsat_core":cp["unsat_core"],
            "without_source_constraint":before["status"],
            "core_rechecked_by_both":True})
    if r11.digest(r11.inputs()[-1])!=audit["R09_fingerprint"]:
        raise RuntimeError("R09_MASTER_MUTATED")
    result={"schema":"MOAG-R18-IDENTITY-COUNTERMODELS-1",
        "status":"SOURCED_IDENTITY_SAT_UNSAT_AND_ALTERNATIVE_MODELS_PASS",
        "source_proven_same_pairs":len(SAME),
        "source_proven_different_pairs":len(DIFFERENT),
        "open_identity_pairs":len(UNKNOWN),
        "alternative_countermodels":countermodels,
        "independently_rechecked_source_conflicts":contradictions,
        "python_cp_sat":py["status"],"minizinc_cp_sat":mz["status"],
        "full_witness_replayed":replay["status"]=="SAT",
        "route_stages_kept":len(m["r14"]["steps"]),
        "bound_visits_unchanged":25,"unbound_visits_unchanged":353,
        "xyz_uncertainty_reduced":False,
        "new_geometric_rooms_created":0,"archicad_write":False,
        "full_geometry_approved":False}
    r11.write(out/"results.json",result)
    print({k:result[k] for k in ("status","source_proven_same_pairs",
             "source_proven_different_pairs","open_identity_pairs")})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    p.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    args=p.parse_args()
    if args.minizinc is None:p.error("Official MiniZinc cp-sat executable required")
    experiment(args.out,args.minizinc)


if __name__=="__main__":main()
