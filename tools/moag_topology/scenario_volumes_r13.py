#!/usr/bin/env python3
"""МОАГ R13: a reversible, explicitly noncanonical 3D bounding-box *scenario*.

Not a geometric reconstruction or a station hull mesh. Boxes are only feasibility
witnesses in abstract grid units; R09/R12 evidence is never overwritten.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import solver_r11 as r11
import spatial_constraints_r12 as r12

HERE = Path(__file__).parent

# (indexed entity, global block, sample grid widths x,y,z, containing parent).
# ALL sizes are explicitly artificial. No book-derived dimensions are implied.
SPECS = [
    ("MOAG-G-0008",1,10,10,11,None),          # Темная база
    ("MOAG-G-0009",1,11,9,9,None),            # Овальная база
    ("MOAG-G-0010",1,8,8,9,None),            # База диких
    ("M-L1-FH-001",1,18,14,14,None),         # Первый ангар
    ("M-L1-FH-002",1,18,14,14,None),         # Соседний ангар
    ("M-L1-AH-OLD-001",1,20,16,16,None),    # Старый ангар
    ("M-L1-CH-001",1,16,16,16,None),        # Круглый зал: bbox, не прямоугольная комната
    ("M-L1-FH-001-CTRL",1,6,5,3,"M-L1-FH-001"),
    ("M-L1-FH-002-CTRL",1,6,5,3,"M-L1-FH-002"),
    ("M-L1-AH-OLD-CTRL-001",1,6,5,4,"M-L1-AH-OLD-001"),
    ("M-L2-PLAZA-001",2,20,20,10,None),    # Не форма площади; bbox
    ("MOAG-G-0036",3,16,16,12,None),        # Круглый зал отдыха: bbox
]
# Each block is a symbolic bounding domain, NOT the outline of the real hull.
# Widths, heights, offsets, centres and units are scenario hypotheses only.
BLOCKS = [
    {"id":1,"name":"Нижний","origin":[0,0,0],"bounds":[80,80,36]},
    {"id":2,"name":"Второй","origin":[8,8,36],"bounds":[64,64,26]},
    {"id":3,"name":"Третий","origin":[16,16,62],"bounds":[48,48,22]},
]
# Only separately described spaces. All other pairs have UNKNOWN relationship:
# no false automatic "every index must not intersect every other index".
EXCLUSIVE_PAIRS = [
    ("MOAG-G-0008","MOAG-G-0009"),
    ("MOAG-G-0008","MOAG-G-0010"),
    ("MOAG-G-0009","MOAG-G-0010"),
    ("M-L1-FH-001","M-L1-FH-002"),
]
# Four on-page LABEL order hints from the user's supplied author diagram;
# they operate in the image coordinate frame, not physical station north.
PLAN_HINTS = [
    ("MOAG-G-0010","MOAG-G-0008","x"),  # wild right of dark
    ("MOAG-G-0009","MOAG-G-0008","x"),  # oval right of dark
    ("MOAG-G-0008","MOAG-G-0010","y"), # dark lower on sheet than wild
    ("MOAG-G-0009","MOAG-G-0008","y"), # oval lower on sheet than dark
]

def build():
    source={k:r12.build(k) for k in (1,2,3)}
    lookup={e["id"]:e for p in source.values() for e in p["r11"]["entities"]}
    envelopes={(e["container"],e["upper"]):e for p in source.values() for e in p["envelopes"]}
    volumes=[]
    for eid,block,w,d,h,parent in SPECS:
        if eid not in lookup or lookup[eid]["global_level_domain"]!=[block]:
            raise ValueError("SOURCE_ENTITY_NOT_AT_EXPECTED_GLOBAL_BLOCK: "+eid)
        if parent and (parent,eid) not in envelopes:
            raise ValueError("PARENTAL_CONTAINMENT_LACKS_R12_PROOF: "+eid)
        volumes.append({"id":eid,"name":lookup[eid]["name"],"global_block":block,
                        "sample_size":[w,d,h],"parent":parent,
                        "shape":"BOUNDING_BOX_ONLY_NOT_REAL_ROOM_SHAPE",
                        "metric_length_known":False,"absolute_xy_proven":False,
                        "status":"ARTIFICIAL_SCENARIO_NOT_BOOK_MEASUREMENT",
                        "source_refs":lookup[eid]["source_refs"],
                        "R05_area_profile":lookup[eid]["area_volume_profile_R05"],
                        "area_profile_used_as_measured_m2":False,
                        "parent_enclosure_source":envelopes[(parent,eid)] if parent else None})
    ids={v["id"] for v in volumes}
    if any(a not in ids or b not in ids for a,b in EXCLUSIVE_PAIRS):
        raise ValueError("EXCLUSIVE_PAIR_OUTSIDE_SCENARIO")
    # Validate exactly the source-on-image constraints, rather than inventing
    # azimuth or assuming that labels give precise room centres.
    author_plan=source[1]["r11"]["source_review"]
    if {(c["a"],c["b"],{2:"x",3:"y"}[c["kind"]]) for c in author_plan["plan_constraints"]}!=set(PLAN_HINTS):
        raise ValueError("AUTHOR_LABEL_ORDER_CHANGED")
    model={"schema":"MOAG-R13-VOLUME-FEASIBILITY-SCENARIO/1",
           "station":"MOAG=Млечный Путь",
           "scope":"SELECTED_PROVEN_ENTITIES_ONLY_NO_FULL_3D_CLAIM",
           "blocks":BLOCKS,"volumes":volumes,
           "disjoint_3d_pairs":[{"a":a,"b":b,"status":"TESTED_DISTINCT_SPACES"} for a,b in EXCLUSIVE_PAIRS],
           "schematic_plan_label_order":[{"a":a,"b":b,"axis":axis,
                "status":"AUTHOR_LABEL_POSITION_NOT_PHYSICAL_COORDINATE"} for a,b,axis in PLAN_HINTS],
           "R12_envelope_count_by_block":{str(k):len(p["envelopes"]) for k,p in source.items()},
           "R09_fingerprints":{str(k):p["R09_fingerprint"] for k,p in source.items()},
           "R09_unchanged":True,"R12_preserved":True,
           "sample_grid_unit":"ARBITRARY_NOT_METRES",
           "block_rectangles_are_hull_mesh":False,
           "envelope_shapes_claimed_exact":False,
           "full_floors_inferred":False,
           "author_exterior_exact_mesh_verified":False,
           "cross_block_internal_routes_verified":False,
           "minimum_distance_between_bases_proven":False,
           "geometry_approved":False,"archicad_write":False}
    validate(model)
    return model

def validate(model):
    if len(model["blocks"])!=3 or [x["id"] for x in model["blocks"]]!=[1,2,3]:
        raise ValueError("GLOBAL_BLOCKS_NOT_THREE")
    if not (model["blocks"][0]["bounds"][0]>model["blocks"][1]["bounds"][0]>
            model["blocks"][2]["bounds"][0]):
        raise ValueError("STEPPED_CONTAINING_DOMAINS_LOST")
    if not (model["blocks"][0]["bounds"][1]>model["blocks"][1]["bounds"][1]>
            model["blocks"][2]["bounds"][1]):
        raise ValueError("STEPPED_CONTAINING_DOMAINS_LOST")
    ids={v["id"]:v for v in model["volumes"]}
    if len(ids)!=len(model["volumes"]): raise ValueError("DUPLICATE_VOLUME")
    for v in model["volumes"]:
        if v["parent"] and (v["parent"] not in ids or
                            v["parent_enclosure_source"]["upper"]!=v["id"] or
                            v["parent_enclosure_source"]["container"]!=v["parent"]):
            raise ValueError("UNPROVEN_PARENTHOOD")
        if v["shape"]!="BOUNDING_BOX_ONLY_NOT_REAL_ROOM_SHAPE" or v["metric_length_known"] or v["absolute_xy_proven"]:
            raise ValueError("UNSUPPORTED_MEASURED_GEOMETRY")
        if not v["source_refs"] or not all(x.get("url") for x in v["source_refs"]):
            raise ValueError("VOLUME_WITHOUT_SOURCE")
    for x in model["disjoint_3d_pairs"]:
        if x["a"] not in ids or x["b"] not in ids or x["a"]==x["b"]:
            raise ValueError("INVALID_NONOVERLAP_PAIR")
    if model["geometry_approved"] or model["archicad_write"] or model["envelope_shapes_claimed_exact"]:
        raise ValueError("UNAUTHORIZED_BIM_OR_SHAPE_PROMOTION")
    return True

def verify(model, w):
    ids={v["id"]:i for i,v in enumerate(model["volumes"])}
    if set(w)!={"x","y","z"} or any(len(w[k])!=len(ids) for k in ("x","y","z")):
        raise ValueError("INVALID_WITNESS")
    box={b["id"]:b for b in model["blocks"]}
    for i,v in enumerate(model["volumes"]):
        b=box[v["global_block"]]
        for k in range(3):
            q=("x","y","z")[k]
            val=w[q][i]
            if type(val)!=int or val<0 or val+v["sample_size"][k]>b["bounds"][k]:
                raise ValueError("OUTSIDE_SCENARIO_HULL_BOUNDING_DOMAIN: "+v["id"])
        if v["parent"]:
            p=ids[v["parent"]]
            for k in range(3):
                q=("x","y","z")[k]
                if w[q][i]<w[q][p] or (w[q][i]+v["sample_size"][k]>
                   w[q][p]+model["volumes"][p]["sample_size"][k]):
                    raise ValueError("CHILD_OUTSIDE_SOURCE_PARENT: "+v["id"])
            if w["z"][i]<=w["z"][p]:
                raise ValueError("UPPER_ROOM_NOT_ABOVE_PARENT_FLOOR: "+v["id"])
    for e in model["disjoint_3d_pairs"]:
        i,j=ids[e["a"]],ids[e["b"]]
        a,b=model["volumes"][i],model["volumes"][j]
        if not any(w[q][i]+a["sample_size"][k]<=w[q][j] or
                   w[q][j]+b["sample_size"][k]<=w[q][i]
                   for k,q in enumerate(("x","y","z"))):
            raise ValueError("IMPOSSIBLE_OVERLAP_OF_DISTINCT_SPACES")
    for e in model["schematic_plan_label_order"]:
        i,j=ids[e["a"]],ids[e["b"]];ax=e["axis"];t={"x":0,"y":1}[ax]
        if 2*w[ax][i]+model["volumes"][i]["sample_size"][t] <= 2*w[ax][j]+model["volumes"][j]["sample_size"][t]:
            raise ValueError("AUTHOR_SCHEMATIC_ORDER_LOST")
    return True

def cp_solve(model, inject=None):
    from ortools.sat.python import cp_model
    validate(model)
    n=len(model["volumes"])
    ids={v["id"]:i for i,v in enumerate(model["volumes"])}
    box={b["id"]:b for b in model["blocks"]}
    m=cp_model.CpModel()
    coords={q:[m.new_int_var(0,box[v["global_block"]]["bounds"][k]-v["sample_size"][k],q+str(i))
               for i,v in enumerate(model["volumes"])] for k,q in enumerate(("x","y","z"))}
    guards={}
    def source_assumption(record,exprs):
        g=m.new_bool_var(record["id"])
        for expr in exprs:m.add(expr).only_enforce_if(g)
        m.add_assumption(g)
        guards[g.index]=record
    for v in model["volumes"]:
        if not v["parent"]:continue
        c,p=ids[v["id"]],ids[v["parent"]]
        constraints=[coords[q][c]>=coords[q][p] for q in ("x","y","z")]
        constraints += [coords[q][c]+v["sample_size"][k]<=coords[q][p]+model["volumes"][p]["sample_size"][k] for k,q in enumerate(("x","y","z"))]
        constraints += [coords["z"][c]>coords["z"][p]]
        source_assumption({"id":"R13-ENCLOSE-"+v["id"],"type":"BOOK_UPPER_WITHIN_SCENARIO_BOX",
                           "sources":v["parent_enclosure_source"]["sources"]},constraints)
    for e in model["disjoint_3d_pairs"]:
        i,j=ids[e["a"]],ids[e["b"]]
        axes=[]
        for k,q in enumerate(("x","y","z")):
            g1=m.new_bool_var(f"sep_{i}_{j}_{q}_a")
            g2=m.new_bool_var(f"sep_{i}_{j}_{q}_b")
            m.add(coords[q][i]+model["volumes"][i]["sample_size"][k]<=coords[q][j]).only_enforce_if(g1)
            m.add(coords[q][j]+model["volumes"][j]["sample_size"][k]<=coords[q][i]).only_enforce_if(g2)
            axes.extend([g1,g2])
        m.add_bool_or(axes)
    for e in model["schematic_plan_label_order"]:
        i,j=ids[e["a"]],ids[e["b"]]
        q=e["axis"];k={"x":0,"y":1}[q]
        m.add(2*coords[q][i]+model["volumes"][i]["sample_size"][k]>
              2*coords[q][j]+model["volumes"][j]["sample_size"][k])
    if inject:
        if inject["type"]!="SYNTHETIC_CHILD_OUTSIDE_PARENT":raise ValueError("UNSUPPORTED_PROBE")
        c,p=ids[inject["child"]],ids[inject["parent"]]
        source_assumption({"id":inject["id"],"type":inject["type"],"sources":[]},
                          [coords["x"][c]>=coords["x"][p]+model["volumes"][p]["sample_size"][0]])
    s=cp_model.CpSolver()
    s.parameters.num_search_workers=1
    s.parameters.max_time_in_seconds=20
    s.parameters.random_seed=0
    state=s.solve(m)
    ok=state in (cp_model.OPTIMAL,cp_model.FEASIBLE)
    w={q:[s.value(var) for var in arr] for q,arr in coords.items()} if ok else None
    if ok:verify(model,w)
    core=[guards[i] for i in s.sufficient_assumptions_for_infeasibility()] if state==cp_model.INFEASIBLE else []
    return {"status":"SAT" if ok else s.status_name(state),"witness":w,
            "unsat_core":core,"unsat_core_claims_minimality":False}

def mzn_data(model):
    ids={v["id"]:i+1 for i,v in enumerate(model["volumes"])}
    hull={b["id"]:b for b in model["blocks"]}
    volumes=model["volumes"]
    a=lambda v:"["+",".join(map(str,v))+"]"
    src=lambda key:[v[key] for v in volumes]
    lines=[f"n={len(volumes)};",f"ne={len(model['disjoint_3d_pairs'])};",
           f"nh={len(model['schematic_plan_label_order'])};",
           "dw="+a(v["sample_size"][0] for v in volumes)+";",
           "dd="+a(v["sample_size"][1] for v in volumes)+";",
           "dh="+a(v["sample_size"][2] for v in volumes)+";",
           "bw="+a(hull[v["global_block"]]["bounds"][0] for v in volumes)+";",
           "bd="+a(hull[v["global_block"]]["bounds"][1] for v in volumes)+";",
           "bh="+a(hull[v["global_block"]]["bounds"][2] for v in volumes)+";",
           "parent="+a(ids[v["parent"]] if v["parent"] else 0 for v in volumes)+";",
           "e1="+a(ids[e["a"]] for e in model["disjoint_3d_pairs"])+";",
           "e2="+a(ids[e["b"]] for e in model["disjoint_3d_pairs"])+";",
           "h1="+a(ids[e["a"]] for e in model["schematic_plan_label_order"])+";",
           "h2="+a(ids[e["b"]] for e in model["schematic_plan_label_order"])+";",
           "haxis="+a(1 if e["axis"]=="x" else 2 for e in model["schematic_plan_label_order"])+";"]
    return "\n".join(lines)+"\n"

def mzn_solve(model, executable, outdir, label, inject=None, fixed=None):
    outdir.mkdir(parents=True,exist_ok=True)
    d=mzn_data(model)
    ids={v["id"]:i+1 for i,v in enumerate(model["volumes"])}
    if inject:
        c,p=ids[inject["child"]],ids[inject["parent"]]
        d+=f"constraint x[{c}] >= x[{p}] + dw[{p}];\n"
    if fixed:
        for k,values in fixed.items():
            d+=f"constraint {k} = ["+",".join(map(str,values))+"];\n"
    name=outdir/(label+".mzn")
    name.write_text(d,encoding="utf-8")
    proc=subprocess.run([str(executable),"--solver","cp-sat","--time-limit","20000",
                         "--output-mode","item",str(HERE/"scenario_volumes_r13.mzn"),str(name)],
                        capture_output=True,text=True,encoding="utf-8",timeout=45)
    (outdir/(label+".stdout.txt")).write_text(proc.stdout,encoding="utf-8")
    (outdir/(label+".stderr.txt")).write_text(proc.stderr,encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("MINIZINC_R13_FAILURE: "+proc.stderr)
    rows=[json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
    if rows and not inject:
        for row in rows:verify(model,row)
    return {"status":"SAT" if rows else "INFEASIBLE" if "=====UNSATISFIABLE=====" in proc.stdout else "UNKNOWN",
            "witnesses":rows,"input_file":name.name}

def experiment(outdir, executable):
    outdir.mkdir(parents=True,exist_ok=True)
    m=build()
    r11.write(outdir/"scenario.json",m)
    cp=cp_solve(m)
    mz=mzn_solve(m,executable,outdir,"sat")
    if cp["status"]!=mz["status"] or cp["status"]!="SAT":raise RuntimeError("R13_SAT_NOT_VERIFIED_BOTH_SOLVERS")
    replay=mzn_solve(m,executable,outdir,"cp-witness",fixed=cp["witness"])
    if replay["status"]!="SAT":raise RuntimeError("R13_SOLVER_WITNESS_NOT_CROSSCHECKED")
    child=next(v for v in m["volumes"] if v["id"]=="M-L1-FH-001-CTRL")
    inject={"id":"R13-TEST-CHILD-OUTSIDE","type":"SYNTHETIC_CHILD_OUTSIDE_PARENT",
            "child":child["id"],"parent":child["parent"]}
    bad=cp_solve(m,inject)
    mz_bad=mzn_solve(m,executable,outdir,"synthetic-unsat",inject=inject)
    core_ids={e["id"] for e in bad["unsat_core"]}
    if (bad["status"]!="INFEASIBLE" or mz_bad["status"]!="INFEASIBLE" or
        inject["id"] not in core_ids or "R13-ENCLOSE-"+child["id"] not in core_ids):
        raise RuntimeError("R13_UNSAT_SOURCE_CORE_NOT_PROVEN")
    # Because book does not fix height order of all bases vs all hangars,
    # require both internally consistent synthetic hull scenarios to exist.
    # These are *countermodels* to an unwarranted global claim.
    # R11 additionally proves the source-order alternatives.
    result={"schema":"MOAG-R13-BOUNDED-SCENARIO-CI/1","status":"SCENARIO_BOX_SAT_UNSAT_PASS_NOT_BOOK_GEOMETRY",
        "num_global_blocks":3,"num_scenario_volumes":len(m["volumes"]),
        "num_enclosed_upper_rooms":sum(bool(v["parent"]) for v in m["volumes"]),
        "num_separation_pairs":len(m["disjoint_3d_pairs"]),
        "num_author_label_order_hints":len(m["schematic_plan_label_order"]),
        "python_ortools":cp["status"],"minizinc_cp_sat":mz["status"],
        "cross_backend_sat_replay":replay["status"],
        "synthetic_clash_cp_sat":bad["status"],"synthetic_clash_minizinc":mz_bad["status"],
        "unsat_source_core":bad["unsat_core"],"all_R09_sha_equal":len(set(m["R09_fingerprints"].values()))==1,
        "source_R09_unchanged":m["R09_unchanged"],
        "scenario_boxes_not_real_rooms":True,"hull_compatibility_approved":False,
        "geometry_approved":False,"archicad_write":False}
    if not result["all_R09_sha_equal"] or r11.digest(r11.inputs()[-1])!=m["R09_fingerprints"]["1"]:
        raise RuntimeError("CANONICAL_R09_CHANGED")
    r11.write(outdir/"results.json",result)
    print(json.dumps({k:result[k] for k in ("status","num_global_blocks","num_scenario_volumes",
        "num_enclosed_upper_rooms","num_separation_pairs","num_author_label_order_hints")},ensure_ascii=False))
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    portable=next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc.exe"),None)
    portable=portable or next((r11.ROOT/".runtime/minizinc").glob("*/bin/minizinc"),None)
    ap.add_argument("--minizinc",type=Path,default=shutil.which("minizinc") or portable)
    args=ap.parse_args()
    if not args.minizinc:ap.error("MiniZinc cp-sat backend required")
    experiment(args.out,args.minizinc)

if __name__=="__main__":
    main()
