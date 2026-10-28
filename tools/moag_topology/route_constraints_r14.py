#!/usr/bin/env python3
"""МОАГ R14: enforce ALL recorded route-order and relative-Z evidence without inventing doors.

The computed t and z coordinates are *ordinal* witnesses, NEVER travel time,
distance, global survey elevations, plan dimensions, or BIM coordinates.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import shutil
import subprocess

import solver_r11 as r11
import spatial_constraints_r12 as r12
import scenario_volumes_r13 as r13

HERE = Path(__file__).parent
SELECTED_ROUTES = ("RT-001", "RT-006", "RT-007", "RT-008", "RT-009")
SPECIAL_ROUTE_LABELS = {
    "RT-006": ("MOAG-G-0008", "MOAG-G-0010"),
    "RT-008": ("MOAG-G-0008", "MOAG-G-0026"),
}
# Recorded comparison, never approved identity: the R03 and R04 refs may
# overlap, but the B1-044 route itself has no approved graph node mapping.
CARGO_STEP_CANDIDATE = ("RT007-H", "MOAG-G-0080", "P-169")


def source_page_map():
    obs = r11.read(r11.BASE / "v2/page_observations.json")["observations"]
    pages = {}
    for o in obs:
        if o.get("station_id") == "MOAG" and o.get("citation_url"):
            pages.setdefault(o["page_id"], o["citation_url"])
    return pages, {o["id"]: o for o in obs}


def build():
    physical = r11.read(r11.SYNTH / "full_indexed_parametric_graph_r04.json")
    all_routes = r11.read(r11.BASE / "v2/character_routes.json")["routes"]
    pages, observations = source_page_map()
    author_routes = r12.build(1)["source_backed_routes_not_solver_constraints"]
    r13_reference = r13.build()
    crosswalk = physical["legacy_id_to_stable_id"]
    routes, steps, z_constraints, chronology, quarantined = [], [], [], [], []
    step_ids = set()
    unknown_pages = set()

    for route in all_routes:
        ids = []
        for order, n in enumerate(route["nodes"]):
            sid = n["id"]
            if sid in step_ids:
                raise ValueError("DUPLICATE_STEP_IDENTIFIER: " + sid)
            step_ids.add(sid)
            ids.append(sid)
            page = n["source_page_id"]
            if page not in pages: unknown_pages.add(page)
            legacy = n.get("existing_graph_node")
            stable = crosswalk.get(legacy) if legacy else None
            if legacy and stable is None:
                raise ValueError("DROPPED_EXISTING_GRAPH_ANCHOR: " + legacy)
            if n.get("absolute_z_m") is not None or n.get("relative_xy") is not None:
                raise ValueError("UNEXPECTED_UNVERIFIED_ROUTE_COORDINATES: " + sid)
            steps.append({
                "id": sid, "route": route["id"], "sequence_index": order,
                "label": n["label"], "movement_method": n["movement_method"],
                "global_block": n["global_level"], "local_stratum": n["local_stratum"],
                "observed_constraint": n["observed_constraint"],
                "page_id": page, "citation_url": pages.get(page),
                "citation_status": "PAGE_OBSERVATION_CROSS_REF" if page in pages else "ROUTE_RECORD_ONLY_PAGE_NEEDS_RECHECK",
                "legacy_graph_anchor": legacy, "stable_graph_anchor": stable,
                "anchor_geometry_status": "INDEXED_REFERENT_NOT_METRIC_PLACEMENT" if stable else "UNPLACED_NARRATIVE_STAGE_NOT_PHYSICAL_ROOM",
                "xy_m": None, "z_m": None, "new_physical_node_created": False,
            })
        if len(ids) < 2:
            raise ValueError("ROUTE_TOO_SHORT: " + route["id"])
        for i, (start, end) in enumerate(zip(ids, ids[1:])):
            chronology.append({
                "id": "R14-SEQ-" + route["id"] + "-" + str(i),
                "route": route["id"], "a": start, "b": end,
                "kind": "RECORDED_NARRATIVE_ORDER_NOT_PHYSICAL_DIRECT_ACCESS",
                "direct_door_asserted": False, "metric_distance_m": None,
                "source_page_ids": [route["nodes"][i]["source_page_id"],
                                    route["nodes"][i+1]["source_page_id"]]})
        for i, c in enumerate(route.get("constraints", [])):
            if c["higher"] not in ids or c["lower"] not in ids:
                raise ValueError("ROUTE_HEIGHT_ENDPOINT_NOT_IN_ROUTE: " + route["id"])
            page=c["source_page_id"]
            if page not in pages: unknown_pages.add(page)
            entry={"id": "R14-Z-" + route["id"] + "-" + str(i),
                   "route": route["id"], "higher": c["higher"], "lower": c["lower"],
                   "source_page_id": page, "citation_url": pages.get(page),
                   "source_claim": c["claim"], "original_kind": c["kind"],
                   "metres_proven": False, "cross_route_identity_merged": False}
            if c["kind"] == "RELATIVE_Z":
                z_constraints.append(entry)
            else:
                quarantined.append({**entry, "reason": "NOT_STRICT_HEIGHT_RELATION_DO_NOT_SOLVE_AS_ONE"})

        routes.append({
            "id": route["id"], "title": route["title"],
            "step_ids": ids, "site_pages": route["site_pages"],
            "minimum_recorded_intermediate_stages": len(ids)-2,
            "route_order_is_not_corridor_length": True,
            "direct_door_between_endpoints_proven_by_this_record": False,
            "all_intermediate_stages_retained": True,
            "route_geometry_approved": False})

    # Two *different source descriptions*, not a guessed common corridor or
    # a new physical junction. Both are tied to their real indexed endpoint bases.
    overlays=[]
    for x in author_routes:
        overlays.append({
            "id": x["id"], "from": x["from"], "to": x["to"],
            "source": x["source"],
            "intermediate_path_kind": "DESCRIBED_NOT_GEOMETRICALLY_LOCATED",
            "path_has_intermediate_description": True,
            "segments_are_direct_doors": False,
            "endpoints_are_index_anchors": True,
            "unplaced_free_floating_corridor_allowed": False,
            "distinct_route_description_not_disjoint_tunnels": True,
            "length_m": None, "corridor_xy_m": None})

    cargo_node,cargo_cand,cargo_source=CARGO_STEP_CANDIDATE
    if cargo_node not in step_ids or cargo_source not in observations:
        raise ValueError("CARGO_EPISODE_CROSS_REFERENCE_MISSING")
    if cargo_cand not in {e["id"] for e in r13_reference["volumes"]} and cargo_cand not in {x["id"] for x in physical["indexed_source_entities"]}:
        raise ValueError("CARGO_CANDIDATE_NOT_INDEXED")
    candidates=[{
        "step_id": cargo_node, "candidate_index": cargo_cand,
        "source_observation": cargo_source,
        "source_page": observations[cargo_source]["page_id"],
        "source_url": observations[cargo_source]["citation_url"],
        "status": "CANDIDATE_CONTEXTUAL_MATCH_NOT_APPROVED_PHYSICAL_IDENTITY",
        "becomes_hard_geometry_anchor": False
    }]
    model={
        "schema": "MOAG-R14-ROUTE-TOPOLOGY-AND-VERTICAL-ORDINAL/1",
        "station": "МОАГ = Млечный Путь",
        "routes": routes, "steps": steps, "observed_order_not_direct_access": chronology,
        "strict_local_or_global_relative_z": z_constraints,
        "non_strict_route_flags": quarantined,
        "author_attached_base_route_overlays": overlays,
        "candidate_only_step_index_matches": candidates,
        "unverified_page_cross_references": sorted(unknown_pages),
        "numeric_rank_is_neither_metre_nor_straight_line_distance": True,
        "unknown_intermediate_steps_are_not_new_rooms": True,
        "global_blocks": [1,2,3], "R13_fingerprint": r11.digest(r13_reference),
        "R09_fingerprint": r13_reference["R09_fingerprints"]["1"],
        "R09_unchanged": True, "geometry_approved": False,
        "archicad_write": False, "source_mutation": False
    }
    validate(model)
    return model


def validate(m):
    step = {s["id"]:s for s in m["steps"]}
    route={r["id"]:r for r in m["routes"]}
    if len(route)!=52 or len(step)!=378 or len(m["strict_local_or_global_relative_z"])!=32:
        raise ValueError("ROUTE_SOURCE_COUNTS_DRIFT")
    if len(m["observed_order_not_direct_access"])!=378-52:
        raise ValueError("OBSERVED_ORDER_LOST")
    if len(m["non_strict_route_flags"])!=1:
        raise ValueError("UNKNOWN_VERTICAL_PATH_WAS_DROPPED")
    for r in m["routes"]:
        if len(r["step_ids"])!=len(set(r["step_ids"])) or r["minimum_recorded_intermediate_stages"]!=len(r["step_ids"])-2:
            raise ValueError("ROUTE_STAGES_DROPPED")
        if not r["all_intermediate_stages_retained"] or r["direct_door_between_endpoints_proven_by_this_record"]:
            raise ValueError("ROUTE_PROMOTED_TO_DOOR")
        for sid in r["step_ids"]:
            if sid not in step or step[sid]["route"]!=r["id"]:
                raise ValueError("ROUTE_STEP_UNRESOLVED")
    for c in m["observed_order_not_direct_access"]:
        a,b=step[c["a"]],step[c["b"]]
        if a["route"]!=b["route"] or a["sequence_index"]+1!=b["sequence_index"]:
            raise ValueError("FABRICATED_NARRATIVE_ADJACENCY")
        if c["direct_door_asserted"] or c["metric_distance_m"] is not None:
            raise ValueError("ROUTE_ORDER_BECAME_GEOMETRIC_ACCESS")
    for c in m["strict_local_or_global_relative_z"]:
        if c["higher"] not in step or c["lower"] not in step or c["higher"]==c["lower"]:
            raise ValueError("INVALID_VERIFIED_HEIGHT_RELATION")
        if c["original_kind"]!="RELATIVE_Z" or c["metres_proven"] or c["cross_route_identity_merged"]:
            raise ValueError("INVALID_METRIC_PROMOTION")
    for rid, anchors in SPECIAL_ROUTE_LABELS.items():
        ids=route[rid]["step_ids"]
        if step[ids[0]]["stable_graph_anchor"]!=anchors[0] or step[ids[-1]]["stable_graph_anchor"]!=anchors[1]:
            raise ValueError("AUTHOR_ROUTE_ENDPOINTS_FLOATING: "+rid)
    for x in m["author_attached_base_route_overlays"]:
        if {x["from"],x["to"]}!={"MOAG-G-0008","MOAG-G-0009"}:
            raise ValueError("BASE_ROUTE_DISCONNECTED_FROM_BASE_ANCHORS")
        if x["segments_are_direct_doors"] or x["unplaced_free_floating_corridor_allowed"] or x["length_m"] is not None or x["corridor_xy_m"] is not None:
            raise ValueError("BASE_ROUTE_UNSOURCED_GEOMETRY")
    if {x["source"]["id"] for x in m["author_attached_base_route_overlays"]}!={"P-024","P-305"}:
        raise ValueError("BASE_ROUTE_SOURCE_IDENTITY_CHANGED")
    for c in m["candidate_only_step_index_matches"]:
        if c["becomes_hard_geometry_anchor"]:
            raise ValueError("UNAPPROVED_CARGO_REFERENT_MERGE")
    if (not m["numeric_rank_is_neither_metre_nor_straight_line_distance"]
        or not m["unknown_intermediate_steps_are_not_new_rooms"] or m["geometry_approved"]
        or m["archicad_write"] or m["source_mutation"]):
        raise ValueError("RECONSTRUCTION_PREMATURELY_APPROVED")
    return True


def domain(step,n):
    span=n+8
    block=step["global_block"]
    if block is None:
        return 0,4*span-1
    if block not in (1,2,3):
        raise ValueError("INVALID_GLOBAL_LEVEL")
    return block*span,(block+1)*span-1


def verify(m,w,include_z=None,inject=None):
    ids={s["id"]:i for i,s in enumerate(m["steps"])}
    n=len(ids)
    if set(w)!={"z","t"} or len(w["z"])!=n or len(w["t"])!=n:
        raise ValueError("BAD_ORDINAL_WITNESS")
    for i,step in enumerate(m["steps"]):
        lo,hi=domain(step,n)
        if type(w["z"][i])!=int or not lo<=w["z"][i]<=hi or type(w["t"][i])!=int or not 0<=w["t"][i]<=n:
            raise ValueError("STAGE_RANK_DOMAIN")
    for c in m["observed_order_not_direct_access"]:
        if w["t"][ids[c["b"]]] <= w["t"][ids[c["a"]]]:
            raise ValueError("NARRATIVE_ORDER_CONTRADICTION: "+c["id"])
    for c in include_z if include_z is not None else m["strict_local_or_global_relative_z"]:
        if w["z"][ids[c["higher"]]]<=w["z"][ids[c["lower"]]]:
            raise ValueError("SOURCE_VERTICAL_ORDER_CONTRADICTION: "+c["id"])
    if inject and inject["type"]=="COMPRESSED_ROUTE_SHORTCUT":
        r=next(r for r in m["routes"] if r["id"]==inject["route"])
        if w["t"][ids[r["step_ids"][-1]]] > w["t"][ids[r["step_ids"][0]]]+1:
            raise ValueError("INJECTED_SHORTCUT_VIOLATION")
    return True


def cp_solve(m, inject=None):
    from ortools.sat.python import cp_model
    validate(m)
    n=len(m["steps"])
    ids={s["id"]:i for i,s in enumerate(m["steps"])}
    model=cp_model.CpModel()
    z=[model.new_int_var(*domain(s,n),"z_"+str(i)) for i,s in enumerate(m["steps"])]
    t=[model.new_int_var(0,n,"route_order_"+str(i)) for i in range(n)]
    guards={}
    def add(c,clauses):
        guard=model.new_bool_var(c["id"])
        for clause in clauses: model.add(clause).only_enforce_if(guard)
        model.add_assumption(guard)
        guards[guard.index]=c
    for c in m["observed_order_not_direct_access"]:
        add(c,[t[ids[c["b"]]]>t[ids[c["a"]]]])
    for c in m["strict_local_or_global_relative_z"]:
        add(c,[z[ids[c["higher"]]]>z[ids[c["lower"]]]])
    if inject:
        if inject["type"]=="REVERSED_RECORDED_HEIGHT":
            c=next(c for c in m["strict_local_or_global_relative_z"] if c["id"]==inject["reverse_id"])
            add(inject,[z[ids[c["lower"]]]>z[ids[c["higher"]]]])
        elif inject["type"]=="COMPRESSED_ROUTE_SHORTCUT":
            r=next(r for r in m["routes"] if r["id"]==inject["route"])
            add(inject,[t[ids[r["step_ids"][-1]]] <= t[ids[r["step_ids"][0]]]+1])
        else:
            raise ValueError("UNKNOWN_SYNTHETIC_TEST")
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=20
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=0
    status=solver.solve(model)
    sat=status in (cp_model.OPTIMAL,cp_model.FEASIBLE)
    witness={"z":[solver.value(x) for x in z], "t":[solver.value(x) for x in t]} if sat else None
    if sat:verify(m,witness,inject=inject)
    core=[guards[i] for i in solver.sufficient_assumptions_for_infeasibility()] if status==cp_model.INFEASIBLE else []
    return {"status":"SAT" if sat else solver.status_name(status),
            "witness":witness, "unsat_core":core, "core_minimality_claimed":False}


def mzn_data(m):
    ids={s["id"]:i+1 for i,s in enumerate(m["steps"])}
    n=len(ids);zs=m["strict_local_or_global_relative_z"];edges=m["observed_order_not_direct_access"]
    arr=lambda seq:"["+",".join(map(str,seq))+"]"
    return "\n".join((
        f"n={n};",f"nz={len(zs)};",f"nt={len(edges)};",
        "lo="+arr(domain(x,n)[0] for x in m["steps"])+";",
        "hi="+arr(domain(x,n)[1] for x in m["steps"])+";",
        "high="+arr(ids[x["higher"]] for x in zs)+";",
        "low="+arr(ids[x["lower"]] for x in zs)+";",
        "earlier="+arr(ids[x["a"]] for x in edges)+";",
        "later="+arr(ids[x["b"]] for x in edges)+";"
    ))+"\n"


def mzn_solve(m,executable,outdir,label,inject=None,fixed=None):
    outdir.mkdir(parents=True,exist_ok=True)
    ids={s["id"]:i+1 for i,s in enumerate(m["steps"])}
    spec=mzn_data(m)
    if inject:
        if inject["type"]=="REVERSED_RECORDED_HEIGHT":
            c=next(c for c in m["strict_local_or_global_relative_z"] if c["id"]==inject["reverse_id"])
            spec+=f"constraint z[{ids[c['lower']]}] > z[{ids[c['higher']]}];\n"
        elif inject["type"]=="COMPRESSED_ROUTE_SHORTCUT":
            r=next(r for r in m["routes"] if r["id"]==inject["route"])
            spec+=f"constraint t[{ids[r['step_ids'][-1]]}] <= t[{ids[r['step_ids'][0]]}]+1;\n"
        else:raise ValueError("UNKNOWN_SYNTHETIC_TEST")
    if fixed:
        for name in ("z","t"):
            spec+="constraint "+name+" = ["+",".join(map(str,fixed[name]))+"];\n"
    path=outdir/(label+".mzn")
    path.write_text(spec,encoding="utf-8")
    run=subprocess.run([str(executable),"--solver","cp-sat","--time-limit","20000",
         "--output-mode","item",str(HERE/"route_constraints_r14.mzn"),str(path)],
         capture_output=True,text=True,encoding="utf-8",timeout=50)
    (outdir/(label+".stdout.txt")).write_text(run.stdout,encoding="utf-8")
    (outdir/(label+".stderr.txt")).write_text(run.stderr,encoding="utf-8")
    if run.returncode:
        raise RuntimeError("R14_MINIZINC_EXIT: "+run.stderr)
    rows=[json.loads(line) for line in run.stdout.splitlines() if line.startswith("{")]
    if rows and not inject:
        for w in rows:verify(m,w)
    return {"status":"SAT" if rows else "INFEASIBLE" if "=====UNSATISFIABLE=====" in run.stdout else "UNKNOWN",
            "solution_count_in_this_run":len(rows), "input":path.name}


def experiment(outdir,executable):
    outdir.mkdir(parents=True,exist_ok=True)
    m=build()
    r11.write(outdir/"route-evidence.json",m)
    cp=cp_solve(m)
    mz=mzn_solve(m,executable,outdir,"all-routes-sat")
    if cp["status"]!="SAT" or mz["status"]!="SAT":
        raise RuntimeError("ROUTE_CONSTRAINTS_NOT_SAT_ON_BOTH")
    replay=mzn_solve(m,executable,outdir,"python-witness",fixed=cp["witness"])
    if replay["status"]!="SAT":raise RuntimeError("R14_CROSSCHECK_FAILED")
    c=next(x for x in m["strict_local_or_global_relative_z"] if
           x["higher"]=="RT006-D" and x["lower"]=="RT006-E")
    inverse={"id":"R14-TEST-INVERSE-RT006", "type":"REVERSED_RECORDED_HEIGHT",
             "reverse_id":c["id"],"source_status":"SYNTHETIC_NOT_BOOK_FACT"}
    forced={"id":"R14-TEST-ONE-HOP-RT006", "type":"COMPRESSED_ROUTE_SHORTCUT",
            "route":"RT-006","source_status":"SYNTHETIC_NOT_BOOK_FACT"}
    conflicts=[]
    for test,label in ((inverse,"height-unsat"),(forced,"shortcut-unsat")):
        bad=cp_solve(m,inject=test)
        bm=mzn_solve(m,executable,outdir,label,inject=test)
        core={e["id"] for e in bad["unsat_core"]}
        if bad["status"]!="INFEASIBLE" or bm["status"]!="INFEASIBLE" or test["id"] not in core:
            raise RuntimeError("R14_CONTRADICTION_NOT_CAUGHT: "+test["id"])
        if test["type"]=="REVERSED_RECORDED_HEIGHT" and c["id"] not in core:
            raise RuntimeError("R14_VERTICAL_SOURCE_MISSING_FROM_CORE")
        if test["type"]=="COMPRESSED_ROUTE_SHORTCUT" and not any(i.startswith("R14-SEQ-RT-006") for i in core):
            raise RuntimeError("R14_ROUTE_STAGES_MISSING_FROM_CORE")
        conflicts.append({"synthetic_test":test,"cp_sat":bad["status"],
                          "minizinc_cp_sat":bm["status"],
                          "unsat_core":bad["unsat_core"]})
    if r11.digest(r11.inputs()[-1])!=m["R09_fingerprint"]:
        raise RuntimeError("R09_WAS_MUTATED")
    result={
        "schema":"MOAG-R14-RECORDED-ROUTE-ORDER-SAT/1",
        "status":"ALL_REGISTERED_ROUTES_ORDINAL_SAT_UNSAT_PASS",
        "route_count":len(m["routes"]),
        "observed_stages":len(m["steps"]),
        "order_only_links":len(m["observed_order_not_direct_access"]),
        "source_recorded_relative_z":len(m["strict_local_or_global_relative_z"]),
        "non_strict_vertical_path_flags_retained":len(m["non_strict_route_flags"]),
        "base_route_descriptions_attached_to_indexed_endpoints":len(m["author_attached_base_route_overlays"]),
        "unlocated_source_page_crossrefs":m["unverified_page_cross_references"],
        "python_cp_sat":cp["status"],"minizinc_cp_sat":mz["status"],
        "actual_independent_replay":replay["status"],
        "synthetic_contradictions":conflicts,
        "no_direct_access_inferred_from_route_order":True,
        "no_full_station_3d_geometry_claimed":True,
        "R09_unchanged":True,"archicad_write":False}
    r11.write(outdir/"results.json",result)
    print(json.dumps({k:result[k] for k in ("status","route_count","observed_stages",
        "order_only_links","source_recorded_relative_z","non_strict_vertical_path_flags_retained",
        "base_route_descriptions_attached_to_indexed_endpoints")},ensure_ascii=False))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    p.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    a=p.parse_args()
    if not a.minizinc:p.error("Official MiniZinc with CP-SAT backend required")
    experiment(a.out,a.minizinc)


if __name__=="__main__":
    main()
