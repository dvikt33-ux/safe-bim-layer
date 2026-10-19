#!/usr/bin/env python3
"""MOAG R05 evidence-linked, editable area and spatial-volume interval solver.

No Archicad calls, no unmeasured exact geometry. Scenario ranges are NOT
canon. Uses the existing R04 parametrization as a shared value source.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research/apa-results/moag/synthesis"
EPS=1e-7
ADJUST_FIELDS={"min_area_m2","max_area_m2","min_height_m","max_height_m",
               "chosen_area_m2","chosen_height_m"}
FOOTPRINT_PARAMETERS={
 "M-L1-CG-001":("lower_old_cargo_hangar_clear_length_m","lower_old_cargo_hangar_clear_width_m","lower_old_cargo_hangar_clear_height_m"),
 "M-L3-CG-001":("upper_cargo_hangar_clear_length_m","upper_cargo_hangar_clear_width_m","upper_cargo_hangar_clear_height_m"),
 "M-L1-FH-001":("fighter_hangar_1_clear_length_m","fighter_hangar_1_clear_width_m","fighter_hangar_1_clear_height_m"),
 "M-L1-FH-002":("fighter_hangar_2_clear_length_m","fighter_hangar_2_clear_width_m","fighter_hangar_2_clear_height_m"),
 "M-L1-FH-LOCK-001":("fighter_airlock_clear_length_m","fighter_airlock_clear_width_m","fighter_airlock_clear_height_m"),
}
LEVEL_PARAMETERS={
 "M-STA-L1-001":("lower_level_diameter_m","lower_level_total_structural_height_m"),
 "M-STA-L2-001":("children_level_diameter_m","children_level_total_structural_height_m"),
 "M-STA-L3-001":("upper_level_diameter_m","upper_level_total_structural_height_m"),
}
CAPACITY={
 "M-L1-CG-001":("cargo_cruiser_length_m","cargo_cruiser_width_m",
                 "cargo_cruisers_simultaneous_in_hangar"),
 "M-L3-CG-001":("upper_service_cruiser_length_m","upper_service_cruiser_width_m",
                 "upper_cruisers_simultaneous_in_hangar_count"),
 "M-L1-FH-001":("single_small_craft_length_m","single_small_craft_width_m",2),
 "M-L1-FH-002":("single_small_craft_length_m","single_small_craft_width_m",3),
}
def number(v,name,allow_zero=False):
    if type(v) not in (int,float) or not math.isfinite(v) or v<0 or (not allow_zero and v==0):
        raise ValueError("BAD_NUMERIC_VALUE: "+name)
    return float(v)

def _values(graph,parameter_changes):
    if not isinstance(parameter_changes,dict) or set(parameter_changes)-set(graph["parameters"]):
        raise ValueError("UNKNOWN_R04_PARAMETER")
    values={k:v["value"] for k,v in graph["parameters"].items()}
    for k,v in parameter_changes.items():
        if not graph["parameters"][k].get("editable"):
            raise ValueError("READ_ONLY_EVIDENCE_PARAMETER: "+k)
        if k.endswith("_count") or k=="cargo_cruisers_simultaneous_in_hangar":
            if type(v) is not int or v<1: raise ValueError("BAD_POSITIVE_INTEGER: "+k)
        else: number(v,k)
        values[k]=v
    return values

def solve(bounds,graph,parameter_changes=None,area_overrides=None,candidates=None):
    parameter_changes={} if parameter_changes is None else parameter_changes
    area_overrides={} if area_overrides is None else area_overrides
    if bounds.get("schema")!="APA-MOAG-AREA-VOLUME-BOUNDS-R05/0.1":
        raise ValueError("BAD_BOUNDS_SCHEMA")
    if graph.get("schema")!="APA-MOAG-FULL-INDEXED-PARAMETRIC-GRAPH/0.4":
        raise ValueError("BAD_GRAPH_SCHEMA")
    if not isinstance(area_overrides,dict): raise ValueError("OVERRIDES_NOT_OBJECT")
    values=_values(graph,parameter_changes)
    h=number(values["human_reference_height_m"],"human_reference_height_m")
    existing={x["id"] for x in graph["indexed_source_entities"]+graph["indexed_r03_entities"]}
    if len(bounds["profiles"])!=len({x["id"] for x in bounds["profiles"]}):
        raise ValueError("DUPLICATE_BOUNDS_INDEX")
    if len(bounds["profiles"])<len(existing) or not existing.issubset({x["id"] for x in bounds["profiles"]}):
        raise ValueError("INCOMPLETE_INDEX_COVERAGE")
    if set(area_overrides)-{x["id"] for x in bounds["profiles"]}:
        raise ValueError("UNKNOWN_ENTITY_OVERRIDE")
    effective={}
    checks=[]
    def note(id,condition,detail,source="PROJECT_CONSTRAINT"):
        checks.append({"id":id,"status":"NOT_EVALUABLE" if condition is None else
                       ("PASS" if condition else "FAIL"),"detail":detail,"provenance":source})
    for profile in bounds["profiles"]:
        id=profile["id"];b=profile["bounds"];changes=area_overrides.get(id,{})
        if not isinstance(changes,dict) or set(changes)-ADJUST_FIELDS:
            raise ValueError("BAD_AREA_OVERRIDE_FIELDS: "+id)
        if b is None:
            if changes: raise ValueError("NON_AREA_ENTITY_CANNOT_HAVE_AREA: "+id)
            effective[id]={"status":"NOT_AREA_BEARING","role":profile["area_role"],
                           "source_kind":profile["kind"]}
            continue
        if b["min_module2"] is None:
            min_a=b["editable_area_min_m2"]
            max_a=b["editable_area_max_m2"]
            min_h=b["editable_height_min_m"]
            max_h=b["editable_height_max_m"]
        else:
            min_a=b["editable_area_min_m2"] or b["min_module2"]*h*h
            max_a=b["editable_area_max_m2"] or b["max_module2"]*h*h
            min_h=b["editable_height_min_m"] or b["min_height_in_human_modules"]*h
            max_h=b["editable_height_max_m"] or b["max_height_in_human_modules"]*h
        min_a=number(changes.get("min_area_m2",min_a),id+".min_area")
        max_a=number(changes.get("max_area_m2",max_a),id+".max_area")
        min_h=number(changes.get("min_height_m",min_h),id+".min_height")
        max_h=number(changes.get("max_height_m",max_h),id+".max_height")
        chosen_area=changes.get("chosen_area_m2")
        chosen_height=changes.get("chosen_height_m")
        if id in FOOTPRINT_PARAMETERS:
            l,w,h_key=FOOTPRINT_PARAMETERS[id]
            if values[l] is not None and values[w] is not None:
                measured=values[l]*values[w]
                if chosen_area is not None and abs(chosen_area-measured)>EPS:
                    raise ValueError("CONFLICT_WITH_SHARED_APA_ENVELOPE: "+id)
                chosen_area=measured
            if values[h_key] is not None:
                if chosen_height is not None and abs(chosen_height-values[h_key])>EPS:
                    raise ValueError("CONFLICT_WITH_SHARED_APA_HEIGHT: "+id)
                chosen_height=values[h_key]
        elif id in LEVEL_PARAMETERS:
            diameter,height_key=LEVEL_PARAMETERS[id]
            if values[diameter] is not None:
                projected=math.pi*values[diameter]**2/4
                if chosen_area is not None and abs(chosen_area-projected)>EPS:
                    raise ValueError("CONFLICT_WITH_SHARED_APA_LEVEL_DIAMETER: "+id)
                chosen_area=projected
            if values[height_key] is not None:
                if chosen_height is not None and abs(chosen_height-values[height_key])>EPS:
                    raise ValueError("CONFLICT_WITH_SHARED_APA_LEVEL_HEIGHT: "+id)
                chosen_height=values[height_key]
        if chosen_area is not None:
            chosen_area=number(chosen_area,id+".chosen_area")
        if chosen_height is not None:
            chosen_height=number(chosen_height,id+".chosen_height")
        effective[id]={"role":profile["area_role"],"source_kind":profile["kind"],
            "metric_provenance":"PROJECT_SCENARIO_EDITABLE_NOT_BOOK_METERS",
            "min_area_m2":min_a,"max_area_m2":max_a,
            "min_height_m":min_h,"max_height_m":max_h,
            "chosen_area_m2":chosen_area,"chosen_height_m":chosen_height,
            "clear_volume_bounds_m3":[min_a*min_h,max_a*max_h],
            "clear_volume_interpretation":"BOUNDING_PRISM_ONLY_NOT_USABLE_FLOOR_SUM",
            "source_ids":profile["source_ids"],
            "accounting_role":"INDEPENDENT_OR_CONTAINER; NO_AUTOMATIC_LEVEL_SUM"}
        note("LOCAL_INTERVAL_"+id,min_a<=max_a and min_h<=max_h,
             "Area and height bound order; NOT proof of dimensions")
        if chosen_area is not None:
            note("CHOSEN_AREA_"+id,min_a-EPS<=chosen_area<=max_a+EPS,
                 f"{chosen_area:.2f} in [{min_a:.2f}, {max_a:.2f}] m2")
        if chosen_height is not None:
            note("CHOSEN_HEIGHT_"+id,min_h-EPS<=chosen_height<=max_h+EPS,
                 f"{chosen_height:.2f} in [{min_h:.2f}, {max_h:.2f}] m")
    # Dynamic lower bounds on hangar footprint from number of berth envelopes.
    # NECESSARY area only; not sufficient for docking / turning / installation.
    clearance=values["technical_clearance_each_side_m"]
    for id,(l,w,nkey) in CAPACITY.items():
        count=nkey if type(nkey) is int else values[nkey]
        if not all(v is not None for v in (values[l],values[w],count,clearance)):
            note("BERTH_MIN_"+id,None,"Missing selected craft hull, count, or clearance")
            continue
        necessary=count*(values[l]+2*clearance)*(values[w]+2*clearance)
        e=effective[id]
        before=e["min_area_m2"]
        e["min_area_m2"]=max(before,necessary)
        e["clear_volume_bounds_m3"][0]=e["min_area_m2"]*e["min_height_m"]
        e["derived_lower_bound_m2"]=necessary
        note("BERTH_MIN_"+id,e["min_area_m2"]<=e["max_area_m2"]+EPS and
             (e["chosen_area_m2"] is None or e["chosen_area_m2"]+EPS>=necessary),
             f"at least {necessary:.2f} m2 from hulls/count; packing and turning still unverified",
             "TEXT_CAPACITY_AND_NONCANONICAL_CRAFT_DIMENSIONS")
    # Room partition sum is only meaningful for explicitly disjoint rooms
    # contained inside the same suite, never for arbitrary graph proximity.
    for group in bounds["nonoverlapping_interior_groups"]:
        par=effective[group["parent"]]
        children=[effective[x] for x in group["disjoint_children"]]
        minimum=sum(x["min_area_m2"] for x in children)
        par["min_area_m2"]=max(par["min_area_m2"],minimum)
        par["clear_volume_bounds_m3"][0]=par["min_area_m2"]*par["min_height_m"]
        note("DISJOINT_ROOMS_"+group["parent"],
             minimum<=par["max_area_m2"]+EPS and
             (par["chosen_area_m2"] is None or
              (all(c["chosen_area_m2"] is not None for c in children) and
               sum(c["chosen_area_m2"] for c in children)<=par["chosen_area_m2"]+EPS) or
              not all(c["chosen_area_m2"] is not None for c in children)),
             f"sum of independent room minima {minimum:.2f} m2; this is not a second level")
    for item in bounds["contained_subarea_guards"]:
        parent=effective[item["master"]]
        child=effective[item["member"]]
        note("FITS_BLOCK_"+item["member"],
             child["min_area_m2"]<=parent["max_area_m2"]+EPS and
             (parent["chosen_area_m2"] is None or child["chosen_area_m2"] is None or
              child["chosen_area_m2"]<=parent["chosen_area_m2"]+EPS),
             "Child footprint cannot exceed block envelope; does NOT prove location",
             "LEVEL_MEMBERSHIP_SOURCE")
    # Hypothetical independent major-space allocations: check BOTH total
    # footprint and spatial prism budget; never sum every R04/R05 node,
    # because container zones and their child rooms otherwise double count.
    allocation_budgets=[]
    for group in bounds.get("assumed_disjoint_level_budgets",[]):
        parent=effective[group["parent"]]
        members=[effective[id] for id in group["members"]]
        if "min_area_m2" not in parent or any("min_area_m2" not in e for e in members):
            raise ValueError("NON_AREA_MEMBER_IN_DISJOINT_BUDGET")
        member_min=sum(e["min_area_m2"] for e in members)
        allocated=sum(e["chosen_area_m2"] if e["chosen_area_m2"] is not None else e["min_area_m2"]
                      for e in members)
        host_ceiling=parent["chosen_area_m2"] if parent["chosen_area_m2"] is not None else parent["max_area_m2"]
        volume_min=sum(
            (e["chosen_area_m2"] if e["chosen_area_m2"] is not None else e["min_area_m2"]) *
            (e["chosen_height_m"] if e["chosen_height_m"] is not None else e["min_height_m"])
            for e in members)
        host_volume_ceiling=(
            (parent["chosen_area_m2"] if parent["chosen_area_m2"] is not None else parent["max_area_m2"]) *
            (parent["chosen_height_m"] if parent["chosen_height_m"] is not None else parent["max_height_m"]))
        footprint_ok=allocated<=host_ceiling+EPS
        volume_ok=volume_min<=host_volume_ceiling+EPS
        note("LEVEL_FOOTPRINT_BUDGET_"+group["id"],footprint_ok,
             f"assigned-or-min footprint {allocated:.2f} m2 / available {host_ceiling:.2f} m2",
             group["status"])
        note("LEVEL_VOLUME_BUDGET_"+group["id"],volume_ok,
             f"assigned-or-min bounding volumes {volume_min:.2f} m3 / host {host_volume_ceiling:.2f} m3",
             group["status"])
        allocation_budgets.append({"id":group["id"],"parent_id":group["parent"],
             "member_ids":group["members"],"scenario_not_text_proven":True,
             "min_member_footprints_m2":member_min,"allocated_floor_plan_m2":allocated,
             "host_footprint_capacity_m2":host_ceiling,
             "min_allocated_prism_volume_m3":volume_min,
             "host_prism_volume_capacity_m3":host_volume_ceiling,
             "footprint_ok":footprint_ok,"volume_ok":volume_ok,
             "do_not_double_count_nested_rooms":True})
    lv=[effective[x] for x in bounds["global_accounting"]["level_envelopes"]]
    for j,(a,b) in enumerate(zip(lv,lv[1:]),1):
        aA,bA=a["chosen_area_m2"],b["chosen_area_m2"]
        impossible=a["max_area_m2"]<=b["min_area_m2"]
        note("BLOCK_FOOTPRINT_ORDER_"+str(j),
             (not impossible and (aA is None or bA is None or aA>bA)),
             "Lower level envelope must be larger; book direct L1>L3, intervening user design order")
    # Non-unique area assignments survive because interval overlap is allowed.
    possible_level_orders=sum(1 for a,b in zip(lv,lv[1:])
                              if a["min_area_m2"]<=b["max_area_m2"])
    for profile in bounds["profiles"]:
        e=effective[profile["id"]]
        if e.get("status")=="NOT_AREA_BEARING":continue
        if e["min_area_m2"]>e["max_area_m2"]+EPS:
            note("TIGHTENED_INTERVAL_"+profile["id"],False,
                 "Functional constraint required area beyond user maximum")
        if e["chosen_area_m2"] is not None and e["chosen_area_m2"]+EPS<e["min_area_m2"]:
            note("AFTER_TIGHTENING_"+profile["id"],False,
                 "Chosen area too small after dependent capacity/room constraints")
    errors=[x for x in checks if x["status"]=="FAIL"]
    # A placement choice must be checked against source-level and area domain.
    # Area narrows candidate list but does NOT create geographical coordinates.
    ranked=[]
    levels={x["id"]:x["global_level"] for x in bounds["profiles"]}
    for candidate in candidates or []:
        if not isinstance(candidate,dict) or not {"id","assignments"}.issubset(candidate):
            raise ValueError("BAD_PLACEMENT_CANDIDATE")
        failures=[]
        penalty=0.
        for entity,target in candidate["assignments"].items():
            if entity not in effective or target not in effective:
                raise ValueError("UNRECOGNIZED_CANDIDATE_PLACEMENT")
            child=effective[entity]
            host=effective[target]
            if levels[entity] is not None and levels[target] is not None and levels[entity]!=levels[target]:
                failures.append({"id":entity,"host":target,"reason":"KNOWN_GLOBAL_LEVEL_CONFLICT"})
                continue
            if "min_area_m2" not in child or "max_area_m2" not in host:
                failures.append({"id":entity,"host":target,"reason":"NOT_A_FLOOR_AREA"})
                continue
            if child["min_area_m2"]>host["max_area_m2"]+EPS:
                failures.append({"id":entity,"host":target,"reason":"HARD_AREA_CAPACITY"})
            elif host["chosen_area_m2"] is not None and child["chosen_area_m2"] is not None and child["chosen_area_m2"]>host["chosen_area_m2"]+EPS:
                failures.append({"id":entity,"host":target,"reason":"SELECTED_AREA_TOO_LARGE"})
            else:
                penalty+=child["min_area_m2"]/max(host["max_area_m2"],EPS)
        ranked.append({"id":candidate["id"],"admissible_by_area":len(failures)==0,
                       "area_conflicts":failures,"secondary_area_utilization_score":round(penalty,6),
                       "geometry_proven":False,
                       "note":"Area only ranks candidates AFTER independent topology, identity and level checks"})
    ranked.sort(key=lambda c:(not c["admissible_by_area"],c["secondary_area_utilization_score"],c["id"]))
    return {"schema":"APA-MOAG-AREA-SOLUTION-R05/0.1",
        "status":"INCONSISTENT" if errors else "INTERVALS_CONSISTENT_NOT_GEOMETRY_PROVEN",
        "reference_human_m":h,"counts":{"indexed":len(effective),
           "with_area":sum("min_area_m2" in x for x in effective.values()),
           "not_area":sum("min_area_m2" not in x for x in effective.values()),
           "tests":len(checks),"fails":len(errors),
           "unresolved_relative_level_area_orders":possible_level_orders},
        "per_index":effective,"checks":checks,"level_allocation_budgets":allocation_budgets,
        "placement_variant_comparisons":ranked,
        "gates":{"metric_locations_approved":False,"geometry_unique":False,
                 "ship_turning_verified":False,"all_areas_book_facts":False,
                 "APA_Archicad_called":False,"main_changed":False}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bounds",type=Path,default=BASE/"area_volume_bounds_r05.json")
    p.add_argument("--graph",type=Path,default=BASE/"full_indexed_parametric_graph_r04.json")
    p.add_argument("--r04-parameters",type=Path)
    p.add_argument("--area-overrides",type=Path)
    p.add_argument("--candidates",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    read=lambda x:json.loads(x.read_text(encoding="utf-8")) if x else None
    result=solve(read(a.bounds),read(a.graph),read(a.r04_parameters),read(a.area_overrides),read(a.candidates))
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if a.out:a.out.write_text(payload,encoding="utf-8")
    else:print(payload,end="")
    return 2 if result["counts"]["fails"] else 0

if __name__=="__main__":raise SystemExit(main())
