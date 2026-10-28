#!/usr/bin/env python3
"""R12: source-backed qualitative vertical envelopes, not a 3D floor layout.

Keeps the R09 graph and R11 ordinal base unchanged; only promotes explicit
"raised within"/"upper gallery" source records to *nonmetric* enclosure checks.
Neither a general room containment nor a route becomes a geometric join.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import solver_r11 as r11

SYNTH = r11.SYNTH
BASE = r11.BASE
HERE = Path(__file__).parent
R03_TYPES = {"HAS_INTERNAL_UPPER_ROOM", "HAS_UPPER_GALLERY", "ELEVATED_WITHIN"}
# Exact R04 relationships: additional conceptual indexes, never alias-merged.
R04_ENVELOPES = {"MOAG-RG-E21", "MOAG-RG-E66", "MOAG-RG-E91"}
# First source-backed tests of routes between named bases; not direct doors.
BASE_ROUTES = ("P-024", "P-305")


def build(scope=1):
    base = r11.build(scope)
    originals = r11.read(SYNTH / "full_indexed_parametric_graph_r04.json")
    observations = {o["id"]: o for o in r11.read(BASE / "v2/page_observations.json")["observations"]}
    sources = {s["id"]: s for s in r11.read(BASE / "v1/evidence_graph.json")["sources"]}
    entities = {e["id"] for e in base["entities"]}
    items = []

    def source_info(ids):
        if not ids:
            raise ValueError("MISSING_PRIMARY_SOURCE")
        out = []
        for sid in ids:
            if sid in observations:
                o = observations[sid]
                out.append({"id": sid, "page_id": o["page_id"],
                            "url": o["citation_url"], "summary": o["spatial_assertion"]})
            elif sid in sources:
                s = sources[sid]
                out.append({"id": sid, "section": s["section"], "url": s["url"]})
            else:
                raise ValueError("UNKNOWN_SOURCE_REFERENCE: " + sid)
        return out

    def add(e, container, upper, refs, origin):
        if container not in entities or upper not in entities:
            return
        if container == upper:
            raise ValueError("ENVELOPE_SELF_REFERENCE")
        items.append({"id": e["id"], "container": container, "upper": upper,
                      "type": "PARTIAL_UPPER_AREA_IN_HIGH_VOLUME_NONMETRIC",
                      "sources": source_info(refs), "origin": origin,
                      "confirmed_object_relation": True,
                      "metric_height_proven": False,
                      "floor_plan_geometry_proven": False,
                      "full_upper_floor_inferred": False,
                      "two_legacy_names_merged": False})

    for e in originals["derived_r03_relationships"]:
        if e["relation"] not in R03_TYPES or e["evidence_state"] != "DIRECT_TEXT":
            continue
        if e["relation"] == "ELEVATED_WITHIN":
            container, upper = e["to"], e["from"]
        else:
            container, upper = e["from"], e["to"]
        add(e, container, upper, e["source_observation_ids"], "R03_DIRECT_TEXT")

    matched = set()
    for e in originals["source_relationships"]:
        if e["id"] not in R04_ENVELOPES:
            continue
        matched.add(e["id"])
        if e["evidence_state"] != "TEXT_DIRECT" or e["relation"] != "contains":
            raise ValueError("R04_ENVELOPE_EVIDENCE_DRIFT: " + e["id"])
        add(e, e["from"], e["to"], e["source_ids"], "R04_EXPLICIT_UPPER_CONTENT")
    if matched != R04_ENVELOPES:
        raise ValueError("MISSING_R04_UPPER_RECORD")

    route_context = []
    if scope == 1:
        for sid in BASE_ROUTES:
            o = observations[sid]
            route_context.append({
                "id": "R12-BASE-ROUTE-" + sid,
                "from": "MOAG-G-0008", "to": "MOAG-G-0009",
                "via": "UNKNOWN_INTERMEDIATE_PIPE_OR_SERVICE_PATH",
                "source": source_info([sid])[0],
                "type": "OBSERVED_OR_DESCRIBED_INDIRECT_ROUTE_NOT_A_DOOR",
                "direct_access_claim": False,
                "shortest_path_length_proven": False,
                "numerical_length_m": None,
                "path_geometry_proven": False,
            })
    if len({x["id"] for x in items}) != len(items):
        raise ValueError("DUPLICATE_ENVELOPE_SOURCE")
    output = {"schema": "MOAG-R12-QUALITATIVE-ENVELOPES/1",
              "scope": scope, "r11": base, "envelopes": sorted(items, key=lambda x: x["id"]),
              "source_backed_routes_not_solver_constraints": route_context,
              "R09_fingerprint": base["R09_fingerprint"], "immutable_R09": True,
              "geometry_approved": False, "archicad_write": False}
    validate(output)
    return output


def validate(p):
    entities = {e["id"] for e in p["r11"]["entities"]}
    original = {e["id"]: e for e in r11.build(p["scope"])["constraints"]}
    for c in p["r11"]["constraints"]:
        if c != original.get(c["id"]):
            raise ValueError("R11_PROVEN_CONSTRAINT_CHANGED")
    for e in p["envelopes"]:
        if e["container"] not in entities or e["upper"] not in entities:
            raise ValueError("UNKNOWN_ENVELOPE_ENDPOINT")
        if not e["sources"] or any(not x.get("url") for x in e["sources"]):
            raise ValueError("ENVELOPE_WITHOUT_SOURCE_URL")
        if e["type"] != "PARTIAL_UPPER_AREA_IN_HIGH_VOLUME_NONMETRIC" or e["full_upper_floor_inferred"]:
            raise ValueError("GEOMETRIC_PROMOTION")
    for r in p["source_backed_routes_not_solver_constraints"]:
        if r["direct_access_claim"] or r["numerical_length_m"] is not None:
            raise ValueError("INDIRECT_ROUTE_PROMOTED_TO_DIRECT_ACCESS")
        if {r["from"], r["to"]} != {"MOAG-G-0008", "MOAG-G-0009"}:
            raise ValueError("BASE_ROUTE_ENDPOINT_DRIFT")
    if p["r11"]["hypothesis_edges_used_as_hard_constraints"] or p["geometry_approved"] or p["archicad_write"]:
        raise ValueError("WRITE_OR_HYPOTHESIS_PROMOTION")
    return True


def verify(p, w):
    ids = [e["id"] for e in p["r11"]["entities"]]
    r11.verify(p["r11"], {key: w[key] for key in ("block", "z", "plan_x", "plan_y")})
    if len(w["top"]) != len(ids) or any(type(z) is not int or not 0 <= z <= 2*len(ids) for z in w["top"]):
        raise ValueError("BAD_ENVELOPE_TOP_WITNESS")
    ix = {e: i for i,e in enumerate(ids)}
    for e in p["envelopes"]:
        floor = w["z"][ix[e["container"]]]
        upper = w["z"][ix[e["upper"]]]
        ceiling = w["top"][ix[e["container"]]]
        if not floor < upper < ceiling:
            raise ValueError("VERTICAL_ENVELOPE_CONTRADICTION: " + e["id"])
    return True


def cp_solve(p, inject=None):
    from ortools.sat.python import cp_model
    n = len(p["r11"]["entities"])
    ids = {e["id"]: i for i,e in enumerate(p["r11"]["entities"])}
    m = cp_model.CpModel()
    v = {key: [m.new_int_var(0,n,key+str(i)) for i in range(n)]
         for key in ("z", "plan_x", "plan_y")}
    v["block"] = [m.new_int_var_from_domain(
        cp_model.Domain.from_values(e["global_level_domain"]), "block"+str(i))
        for i,e in enumerate(p["r11"]["entities"])]
    v["top"] = [m.new_int_var(0,2*n,"aux_envelope_top"+str(i)) for i in range(n)]
    guards = {}
    def assume(cid, source, constraints):
        g = m.new_bool_var(cid)
        for expr in constraints:
            m.add(expr).only_enforce_if(g)
        m.add_assumption(g)
        guards[g.index] = source
    for c in p["r11"]["constraints"]:
        axis = {1:"z",2:"plan_x",3:"plan_y"}[c["kind"]]
        assume(c["id"], c, [v[axis][ids[c["a"]]] > v[axis][ids[c["b"]]]])
    for e in p["envelopes"]:
        parent, upper = ids[e["container"]],ids[e["upper"]]
        assume(e["id"], e, [v["z"][upper] > v["z"][parent],
                            v["top"][parent] > v["z"][upper]])
    if inject:
        if inject["id"] in {e["id"] for e in p["envelopes"]}:
            raise ValueError("TEST_ID_COLLISION")
        if inject["type"] != "SYNTHETIC_CEILING_BELOW_UPPER":
            raise ValueError("UNKNOWN_SYNTHETIC_PROBE")
        parent, upper = ids[inject["container"]], ids[inject["upper"]]
        assume(inject["id"], inject, [v["top"][parent] <= v["z"][upper]])
    s=cp_model.CpSolver()
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = 15
    s.parameters.random_seed = 0
    state=s.solve(m)
    good=state in (cp_model.OPTIMAL,cp_model.FEASIBLE)
    witness={k:[s.value(x) for x in cells] for k,cells in v.items()} if good else None
    if good:
        verify(p,witness)
    core=[guards[i] for i in s.sufficient_assumptions_for_infeasibility()] if state == cp_model.INFEASIBLE else []
    return {"status": "SAT" if good else s.status_name(state),
            "witness": witness, "unsat_core":core,
            "core_minimality_claimed": False}


def data(p):
    ids={e["id"]:i+1 for i,e in enumerate(p["r11"]["entities"])}
    es=p["envelopes"]
    return (r11.dzn(p["r11"],p["r11"]["constraints"])
            + "q="+str(len(es))+";\n"
            + "parent=["+",".join(str(ids[e["container"]]) for e in es)+"];\n"
            + "upper=["+",".join(str(ids[e["upper"]]) for e in es)+"];\n")


def mzn_solve(p, executable, outdir, label, inject=None, fixed=None):
    outdir.mkdir(parents=True,exist_ok=True)
    spec=data(p)
    if inject:
        ids={e["id"]:i+1 for i,e in enumerate(p["r11"]["entities"])}
        if inject["type"] != "SYNTHETIC_CEILING_BELOW_UPPER":
            raise ValueError("UNKNOWN_SYNTHETIC_PROBE")
        spec += ("constraint top["+str(ids[inject["container"]])
                 +"] <= z["+str(ids[inject["upper"]])+"];\n")
    if fixed:
        for key, values in fixed.items():
            spec += "constraint "+key+" = ["+",".join(map(str, values))+"];\n"
    file=outdir/(label+".mzn")
    file.write_text(spec,encoding="utf-8")
    run=subprocess.run([str(executable),"--solver","cp-sat","--time-limit","15000",
        "--output-mode","item",str(HERE/"spatial_constraints_r12.mzn"),str(file)],
        capture_output=True,text=True,encoding="utf-8",timeout=40)
    (outdir/(label+".stdout.txt")).write_text(run.stdout,encoding="utf-8")
    (outdir/(label+".stderr.txt")).write_text(run.stderr,encoding="utf-8")
    if run.returncode:
        raise RuntimeError("R12_MINIZINC_EXIT: "+run.stderr)
    rows=[json.loads(line) for line in run.stdout.splitlines() if line.startswith("{")]
    if rows and not inject:
        for row in rows: verify(p,row)
    status="SAT" if rows else "INFEASIBLE" if "=====UNSATISFIABLE=====" in run.stdout else "UNKNOWN"
    return {"status": status, "witnesses": rows, "input":file.name}


def experiment(scope, executable, outdir):
    p=build(scope)
    outdir.mkdir(parents=True,exist_ok=True)
    r11.write(outdir/"qualitative-model.json",p)
    cp=cp_solve(p)
    mz=mzn_solve(p,executable,outdir,"sat")
    if cp["status"]!=mz["status"]!="SAT":
        raise RuntimeError("R12_SAT_NOT_CONFIRMED")
    replay=mzn_solve(p,executable,outdir,"cp-witness",fixed=cp["witness"])
    if replay["status"]!="SAT":
        raise RuntimeError("R12_CROSS_BACKEND_WITNESS_REJECTED")
    source=p["envelopes"][0]
    inject={"id":"R12-SYNTHETIC-INVERSE-"+source["id"],
            "type":"SYNTHETIC_CEILING_BELOW_UPPER",
            "container":source["container"],"upper":source["upper"],
            "status":"synthetic_test_only"}
    bad=cp_solve(p,inject=inject)
    mz_bad=mzn_solve(p,executable,outdir,"synthetic-unsat",inject=inject)
    if bad["status"]!="INFEASIBLE" or mz_bad["status"]!="INFEASIBLE":
        raise RuntimeError("R12_CONTRADICTION_UNDETECTED")
    ids={c["id"] for c in bad["unsat_core"]}
    if source["id"] not in ids or inject["id"] not in ids:
        raise RuntimeError("R12_CONFLICT_EXPLANATION_INCOMPLETE")
    if r11.digest(r11.inputs()[-1])!=p["R09_fingerprint"]:
        raise RuntimeError("R09_MUTATED")
    result={"schema":"MOAG-R12-ENVELOPE-EXPERIMENT/1",
            "status":"SOURCE_BOUNDED_NONMETRIC_SAT_UNSAT_PASS",
            "scope":scope,
            "entities":len(p["r11"]["entities"]),
            "strict_R11_order_constraints":len(p["r11"]["constraints"]),
            "new_local_envelope_constraints":len(p["envelopes"]),
            "identified_indirect_base_routes":len(p["source_backed_routes_not_solver_constraints"]),
            "cp_sat_status":cp["status"],"minizinc_status":mz["status"],
            "cp_witness_replayed":replay["status"]=="SAT",
            "synthetic_unsat_cp":bad["status"],
            "synthetic_unsat_mzn":mz_bad["status"],
            "unsat_core":bad["unsat_core"],
            "global_graph_fingerprint_unchanged":True,
            "full_level_geometry_proven":False,
            "metric_envelope_dimensions_proven":False,
            "author_hull_compatibility_proven":False,
            "archicad_write":False}
    r11.write(outdir/"results.json",result)
    print(json.dumps({k:result[k] for k in ("status","scope","entities",
          "strict_R11_order_constraints","new_local_envelope_constraints",
          "identified_indirect_base_routes")},ensure_ascii=False))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope",type=int,choices=(1,2),default=1)
    ap.add_argument("--out",type=Path,required=True)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    ap.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    args=ap.parse_args()
    if args.minizinc is None: ap.error("Real MiniZinc cp-sat executable required")
    experiment(args.scope,args.minizinc,args.out)


if __name__=="__main__":
    main()
