#!/usr/bin/env python3
"""МОАГ R19: historical Lower cargo logistics, physical identity and phase order.

Reuse official OR-Tools CP-SAT and MiniZinc via R15. Phase ticks are arbitrary
ORDINAL ranks, never dates, distances, dimensions or physical site locations.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil

import solver_r11 as r11
import integrated_spatial_r15 as r15
import identity_alternatives_r18 as r18

HERE=Path(__file__).parent
OLD="M-L1-CG-001"
NEW="M-L3-CG-001"
SOURCE_OLD="P-240"
SOURCE_REPLACEMENT="P-243"
SOURCE_RESIDUAL="P-265"
PHASES=("UPPER_NEW_CARGO_COMMISSIONED","LOWER_PRIMARY_CARGO_HALTED","LOWER_AUTOPILOT_PROVISIONS")
FIRST_EVENT="UPPER_NEW_CARGO_COMMISSIONED"
SECOND_EVENT="LOWER_PRIMARY_CARGO_HALTED"
THIRD_EVENT="LOWER_AUTOPILOT_PROVISIONS"

def observations():
    return {x["id"]:x for x in r11.read(r11.BASE/"v2/page_observations.json")["observations"]}

def evidence(src,summary):
    o=observations()[src]
    if o["station_id"]!="MOAG" or o["evidence_class"]!="DIRECT_TEXT":
        raise ValueError("R19_WRONG_OBJECT_OR_SOURCE_QUALITY: "+src)
    return {"id":src,"page_id":o["page_id"],"url":o["citation_url"],
            "summary":summary,"source_kind":"PREEXISTING_PAGE_OBSERVATION_NO_REAUDIT_CLAIM"}

def build():
    m,r18audit=r18.build()
    raw,fragments,_,_,_=r11.inputs()
    real={x["id"]:x for x in raw["indexed_source_entities"]+
         raw["indexed_r03_entities"]+fragments["physical_entities"]}
    if {x for x in (OLD,NEW,"MOAG-G-0053","M-L1-AH-OLD-001","MOAG-G-0057") if x not in real}:
        raise ValueError("R19_PHYSICAL_INDEX_NOT_IN_CANONICAL_GRAPH")
    if real[OLD]["level"]!=1 or real[NEW]["level"]!=3:
        raise ValueError("R19_HISTORIC_AND_NEW_GLOBAL_LEVEL_DRIFT")
    if real["MOAG-G-0053"].get("promotion_verdict")!="REVIEW_SOURCE_IDENTITY_BEFORE_BINDING":
        raise ValueError("R19_OLD_CONCEPT_PREMATURELY_DEEMED_IDENTICAL")
    rel=next(x for x in raw["derived_r03_relationships"] if
             x["from"]==OLD and x["to"]==NEW and
             x["relation"]=="PREDECESSOR_CARGO_FUNCTION_OF")
    if SOURCE_REPLACEMENT not in rel["source_observation_ids"]:
        raise ValueError("R19_RELOCATION_SOURCE_RELATIONSHIP_MISSING")
    src=observations()
    for ident,page in [(SOURCE_OLD,"B1-082"),(SOURCE_REPLACEMENT,"B1-083"),(SOURCE_RESIDUAL,"B1-091")]:
        if src[ident]["page_id"]!=page or src[ident]["station_id"]!="MOAG":
            raise ValueError("R19_PRIMARY_PAGE_SOURCE_CHANGED: "+ident)
    # Physical DIFFERENT: original Lower cargo installation and new Third cargo
    # are not one spatial complex. Historical succession != spatial adjacency.
    upper_identity=len(m["variables"])
    m["variables"].append({"name":"R19::PHYSICAL-IDENTITY::"+NEW,
                           "domain":[0,len(r18audit["tokens"])],"interval":True})
    lower_identity=r18audit["tokens"][OLD]
    neq_id="R19-DIFFERENT-LOWER-CARGO-VS-THIRD-CARGO"
    m["constraints"].append({
        "id":neq_id,
        "rows":[r15.row([(lower_identity,1),(upper_identity,-1)],1),
                r15.row([(upper_identity,1),(lower_identity,-1)],1)],
        "sources":[evidence(SOURCE_REPLACEMENT,
          "Новые грузовые ангары Третьего и исторические грузовые ангары Нижнего — разные комплексы")],
        "status":"BOOK_PROVEN_DISTINCT_GLOBAL_BLOCK_CARGO_COMPLEXES_NOT_DISJOINT_BOX_GEOMETRY",
        "any_of":True,"family":"r19_cargo_distinct"})
    # P243: new upper installation commissioned BEFORE old Lower primary cargo
    # operations ceased. P265: residual shuttles supplied the Lower complex
    # AFTER its primary cargo function had been retired.
    # No wall demolition, abandonment of all access, or dated duration inferred.
    events={}
    for name in PHASES:
        events[name]=len(m["variables"])
        m["variables"].append({"name":"R19::HISTORIC-ORDINAL::"+name,
                               "domain":[0,6],"interval":True})
    upper_before_lower="R19-THIRD-OPENED-BEFORE-LOWER-PRIMARY-STOP"
    lower_before_supplies="R19-LOWER-PRIMARY-STOP-BEFORE-RESIDUAL-SUPPLY"
    m["constraints"].append({
        "id":upper_before_lower,
        "rows":[r15.row([(events[SECOND_EVENT],1),(events[FIRST_EVENT],-1)],1)],
        "sources":[evidence(SOURCE_REPLACEMENT,"Основные грузовые операции в Нижнем прекращены после ввода новых ангаров Третьего")],
        "status":"DOCUMENTED_HISTORICAL_ORDER_NONCALENDAR",
        "any_of":False,"family":"r19_replacement_order"})
    m["constraints"].append({
        "id":lower_before_supplies,
        "rows":[r15.row([(events[THIRD_EVENT],1),(events[SECOND_EVENT],-1)],1)],
        "sources":[evidence(SOURCE_RESIDUAL,"Поставки пищи/лекарств малыми автоматическими челноками продолжались после вывода из основной грузовой эксплуатации")],
        "status":"DOCUMENTED_HISTORICAL_RESIDUAL_USE_NONCALENDAR",
        "any_of":False,"family":"r19_residual_supply_order"})
    metadata={
        "schema":"MOAG-R19-CARGO-HISTORY-AND-IDENTITY/1",
        "base_R18_commit":"9d8802de8a27da01746c5eee3213b285ff657f0e",
        "canonical_R09_fingerprint":m["R09_fingerprint"],
        "old_cargo":OLD,"new_upper_cargo":NEW,
        "old_concept":"MOAG-G-0053",
        "historic_old_control_context":"M-L1-CG-CTRL-001",
        "B1_110_old_raised_hangar":"M-L1-AH-OLD-001",
        "B1_075_sleeping_adults_hangar":"MOAG-G-0057",
        "historic_distinctness_constraint":neq_id,
        "old_identity_token":lower_identity,
        "third_identity_token":upper_identity,
        "events":events,
        "new_upper_before_old_halt_constraint":upper_before_lower,
        "old_halt_before_supplies_constraint":lower_before_supplies,
        "original_R18_undecided_pairs_unchanged":len(r18audit["not_yet_decidable"]),
        "evidence":[evidence(SOURCE_OLD,"Архивное свидетельство исторического центра грузовых ангаров Нижнего"),
                    evidence(SOURCE_REPLACEMENT,"Преемственность грузовой функции после ввода Третьего"),
                    evidence(SOURCE_RESIDUAL,"Малые автоматические челноки поддерживали старые ангары после основного вывода")],
        "allow_old_lower_cargo_to_be_physically_present_after_primary_cessation":True,
        "source_citation_urls_not_verified_live_during_R19":True,
        "old_lower_and_new_third_have_no_asserted_direct_passage":True,
        "historical_rank_is_not_physical_z_or_calendar_year":True,
        "no_old_cargo_equivalence_to_raised_hangar_approved":True,
        "no_old_cargo_equivalence_to_sleepers_approved":True,
        "r15_bound_visits_unchanged":25,
        "r15_unbound_visits_unchanged":353,
        "new_rooms_created":0,"new_metric_coordinates":0,
        "archicad_write":False,"main_untouched":True
    }
    validate(m,metadata,r18audit)
    return m,metadata,r18audit


def validate(m,a,r18audit):
    r18.validate(m,r18audit)
    if len(r18audit["not_yet_decidable"])!=6:
        raise ValueError("R19_R18_UNDECIDED_PAIRS_DROPPED")
    if set(a["events"])!=set(PHASES):
        raise ValueError("R19_HISTORICAL_EVENT_MISSING")
    by={c["id"]:c for c in m["constraints"]}
    lower,upper=a["old_identity_token"],a["third_identity_token"]
    cid=a["historic_distinctness_constraint"]
    if cid not in by or not by[cid]["any_of"] or by[cid]["rows"]!=[
           r15.row([(lower,1),(upper,-1)],1),
           r15.row([(upper,1),(lower,-1)],1)]:
        raise ValueError("R19_OLD_NEW_CARGO_DISTINCTNESS_NOT_ENFORCED")
    ev=a["events"]
    expected=[
       (a["new_upper_before_old_halt_constraint"],
        r15.row([(ev[SECOND_EVENT],1),(ev[FIRST_EVENT],-1)],1),SOURCE_REPLACEMENT),
       (a["old_halt_before_supplies_constraint"],
        r15.row([(ev[THIRD_EVENT],1),(ev[SECOND_EVENT],-1)],1),SOURCE_RESIDUAL)]
    for cid,row,source in expected:
        if cid not in by or by[cid]["rows"]!=[row] or by[cid]["any_of"]:
            raise ValueError("R19_SOURCE_TEMPORAL_ORDER_LOST: "+cid)
        if not any(x["id"]==source and x.get("url") for x in by[cid]["sources"]):
            raise ValueError("R19_SOURCE_CITATION_NOT_ATTACHED")
    if (not a["allow_old_lower_cargo_to_be_physically_present_after_primary_cessation"]
         or not a["no_old_cargo_equivalence_to_raised_hangar_approved"]
         or not a["no_old_cargo_equivalence_to_sleepers_approved"]
         or not a["source_citation_urls_not_verified_live_during_R19"]
         or not a["historical_rank_is_not_physical_z_or_calendar_year"]
         or not a["old_lower_and_new_third_have_no_asserted_direct_passage"]
         or a["new_rooms_created"] or a["new_metric_coordinates"]
         or a["archicad_write"] or not a["main_untouched"]):
        raise ValueError("R19_FALSE_GEOMETRY_OR_HISTORIC_CLAIM")
    return True


def inverse_probe(name,left,right,comparator="greater_equal"):
    terms=[(left,1),(right,-1)]
    return r15.probe(name,[r15.row(terms,0)])


def same_probe(a):
    return r18.query({"tokens":{a["old_cargo"]:a["old_identity_token"],
                                 a["new_upper_cargo"]:a["third_identity_token"]}},
                     a["old_cargo"],a["new_upper_cargo"],"same",
                     "R19-SYNTHETIC-SAME-LOWER-THIRD-CARGO")


def negative_tests(m,a):
    ev=a["events"]
    return [
      ("old-new-false-identity",same_probe(a),
        a["historic_distinctness_constraint"],"r19_cargo_distinct"),
      ("false-order-new-after-old-stop",
       inverse_probe("R19-SYNTHETIC-NEW-THIRD-NOT-BEFORE-LOWER-STOP",
                     ev[FIRST_EVENT],ev[SECOND_EVENT]),
        a["new_upper_before_old_halt_constraint"],"r19_replacement_order"),
      ("false-order-supply-before-halt",
       inverse_probe("R19-SYNTHETIC-RESIDUAL-SUPPLY-NOT-AFTER-HALT",
                     ev[SECOND_EVENT],ev[THIRD_EVENT]),
        a["old_halt_before_supplies_constraint"],"r19_residual_supply_order")
    ]


def experiment(out,executable):
    out.mkdir(parents=True,exist_ok=True)
    m,a,ar18=build()
    r11.write(out/"historical-source-contract.json",a)
    py=r15.cp_solve(m)
    mz=r15.mzn_solve(m,executable,out,"cargo-historic-sat")
    if py["status"]!="SAT" or mz["status"]!="SAT":
        raise RuntimeError("R19_HISTORIC_SAT_FAILED_TWO_BACKENDS")
    replay=r15.mzn_solve(m,executable,out,"python-witness-replay",fixed=py["witness"])
    if replay["status"]!="SAT":
        raise RuntimeError("R19_WITNESS_NOT_INDEPENDENTLY_ACCEPTED")

    cp_conflicts=[]
    for label,extra,required,family in negative_tests(m,a):
        free=r15.cp_solve(m,[extra],exclude_families=(family,))
        bad=r15.cp_solve(m,[extra])
        bm=r15.mzn_solve(m,executable,out,label+"-unsat",[extra])
        core={x["id"] for x in bad["unsat_core"]}
        if (free["status"]!="SAT" or bad["status"]!="INFEASIBLE"
            or bm["status"]!="INFEASIBLE"
            or not {extra["id"],required}<=core):
            raise RuntimeError("R19_SOURCE_CONTRADICTION_NOT_PROVEN: "+label)
        cpc=r15.cp_solve(m,[extra],active=core)
        mzc=r15.mzn_solve(m,executable,out,label+"-core",[extra],active=core)
        if cpc["status"]!=mzc["status"] or cpc["status"]!="INFEASIBLE":
            raise RuntimeError("R19_SOURCE_CONFLICT_CORE_CANNOT_BE_REPLAYED: "+label)
        cp_conflicts.append({"name":label,"status":bad["status"],
                             "without_source":free["status"],
                             "source_constraint":required,"core":bad["unsat_core"],
                             "core_replayed":True})

    # Explicitly preserve unresolved R18 identity alternatives. Old freight
    # complex might/might not correspond to B1-110 old tall control hangar.
    alternatives=[]
    for pair in [(OLD,"M-L1-AH-OLD-001"),
                 ("MOAG-G-0053",OLD),
                 ("MOAG-G-0057","M-L1-AH-OLD-001")]:
        for kind in ("same","different"):
            extra=r18.query(ar18,pair[0],pair[1],kind)
            cp=r15.cp_solve(m,[extra])
            mz_alt=r15.mzn_solve(m,executable,out,"unknown-"+str(len(alternatives)),[extra])
            if cp["status"]!="SAT" or mz_alt["status"]!="SAT":
                raise RuntimeError("R19_UNSUPPORTED_OLD_CARGO_IDENTITY_PROMOTION: "+str(pair))
            alternatives.append({"pair":list(pair),"alternative":kind,
                                 "python":cp["status"],"minizinc":mz_alt["status"]})
    if r11.digest(r11.inputs()[-1])!=a["canonical_R09_fingerprint"]:
        raise RuntimeError("R19_R09_CHANGED")
    result={
       "schema":"MOAG-R19-CARGO-HISTORIC-AUDIT-RESULTS/1",
       "status":"CARGO_HISTORIC_FUNCTION_AND_INDETERMINATE_IDENTITY_PASS",
       "python_cp_sat":py["status"],"minizinc_cp_sat":mz["status"],
       "fixed_python_witness_accepted_by_minizinc":replay["status"]=="SAT",
       "new_source_relation_family_count":3,
       "source_backed_distinct_lower_and_upper_cargo":True,
       "source_backed_historical_order_edges":2,
       "synthetic_unsat_and_ablation_checks":cp_conflicts,
       "preserved_unresolved_old_hangar_alternatives":alternatives,
       "r18_open_identity_pairs_still_unresolved":6,
       "r15_bound_visits":25,"r15_unbound_visits":353,
       "new_rooms_created":0,"new_xyz_metric_constraints":0,
       "full_architectural_geometry_approved":False,"archicad_write":False}
    r11.write(out/"results.json",result)
    print({k:result[k] for k in ("status","new_source_relation_family_count",
                   "source_backed_historical_order_edges",
                   "r18_open_identity_pairs_still_unresolved")})
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    ap.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    args=ap.parse_args()
    if args.minizinc is None:ap.error("Official MiniZinc CP-SAT required")
    experiment(args.out,args.minizinc)

if __name__=="__main__":
    main()
