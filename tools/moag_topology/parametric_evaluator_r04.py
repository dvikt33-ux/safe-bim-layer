#!/usr/bin/env python3
"""APA-MOAG-R04 offline parametric spatial-constraint evaluator.

Uses the existing APA geometric helpers only for an optional user-authored
rectangle inspection. Never connects to Archicad, executes commands, writes PLN,
or changes original source files. Unknown parameters stay UNKNOWN.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

GRAPH = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag/synthesis/full_indexed_parametric_graph_r04.json"
EPS = 1e-9

def positive(value, name, *, allow_zero=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"NONFINITE_{name}")
    if value < 0 or (not allow_zero and value == 0):
        raise ValueError(f"NONPOSITIVE_{name}")
    return float(value)

def evaluate(graph, changes, authored_rectangles=None):
    """Pure offline evaluator; no speculative metric values are inserted."""
    if graph.get("schema") != "APA-MOAG-FULL-INDEXED-PARAMETRIC-GRAPH/0.4":
        raise ValueError("GRAPH_SCHEMA_MISMATCH")
    params = graph["parameters"]
    if not isinstance(changes, dict) or set(changes) - set(params):
        raise ValueError("UNKNOWN_PARAMETER_OVERRIDE")
    values = {k: v["value"] for k, v in params.items()}
    for k, value in changes.items():
        if not params[k].get("editable", False):
            raise ValueError("SOURCE_OBSERVATION_READONLY: " + k)
        values[k] = value
    for k, v in values.items():
        if v is not None:
            if k in {"cargo_cruisers_simultaneous_in_hangar","upper_cruisers_simultaneous_in_hangar_count"}:
                if type(v) is not int or v < 1:
                    raise ValueError("CRUISER_COUNT_POSITIVE_INTEGER_REQUIRED")
            else:
                positive(v, k)
    statuses = []
    def record(code, ok=None, detail="", source=""):
        statuses.append({"id": code, "status": "NOT_EVALUABLE" if ok is None else
            ("PASS" if ok else "FAIL"), "detail": detail, "evidence_class": source})
    def need(*keys):
        return all(values.get(k) is not None for k in keys)
    for rule in graph["rules"]:
        rid, typ = rule["rule"], rule["type"]
        epistemic = rule["epistemic"]
        if typ == "gt":
            x, y = rule["left"], rule["right"]
            record(rid, values[x] > values[y] if need(x,y) else None,
                   f"{x} must exceed {y}", epistemic)
        elif typ == "occupancy_rectangular_area_min":
            a,b,c,d,e = [rule[k] for k in ("hangar_length","hangar_width","craft_length","craft_width","clearance")]
            if need(a,b,c,d,e):
                necessary = rule["count"]*(values[c]+2*values[e])*(values[d]+2*values[e])
                given = values[a]*values[b]
                record(rid,given+EPS >= necessary,
                    f"Clear hangar area {given:.3f} m2; minimum rectangular berth envelopes {necessary:.3f} m2. Necessary only, NOT proof of packing.",epistemic)
            else: record(rid,None,"Hangar and craft envelope values missing",epistemic)
        elif typ == "cargo_cruiser_capacity_area_min":
            a,b,c,d,n,e = [rule[k] for k in ("hostLength","hostWidth","craftLength","craftWidth","count","clearance")]
            if need(a,b,c,d,n,e):
                minimum = values[n]*(values[c]+2*values[e])*(values[d]+2*values[e])
                given = values[a]*values[b]
                record(rid,given+EPS >= minimum,
                    f"Cargo area {given:.3f} m2 vs >= {minimum:.3f} m2 for {values[n]} cruiser(s); turning and circulation NOT verified",epistemic)
            else: record(rid,None,"Cruiser dimensions/count/hangar unknown",epistemic)
        elif typ in ("min_with_clearance","vertical_clearance"):
            a,b,c = rule["host"],rule["craft"],rule["clearance"]
            if need(a,b,c):
                threshold = values[b]+(values[c] if typ=="vertical_clearance" else 2*values[c])
                record(rid,values[a]+EPS>=threshold,
                    f"{a}={values[a]:.3f} m; must be >= {threshold:.3f} m",epistemic)
            else: record(rid,None,"Craft or clearance dimensions missing",epistemic)
        elif typ == "mez_clearance":
            a,b,c = rule["hostHeight"],rule["floorZ"],rule["roomHeight"]
            record(rid,values[a]+EPS >= values[b]+values[c] if need(a,b,c) else None,
                   "Raised room must fit under ceiling; does not establish support design",epistemic)
        elif typ == "enclosure_diameter_necessary":
            diameter, length, width = rule["diameter"],rule["length"],rule["width"]
            if need(diameter,length,width):
                diagonal=math.hypot(values[length],values[width])
                record(rid,values[diameter]+EPS>=diagonal,
                       f"Necessary span: {diagonal:.3f} m rectangular bay diagonal <= assumed circular hull diameter {values[diameter]:.3f} m; NOT sufficient for placement amid other volumes",epistemic)
            else: record(rid,None,"Envelope/bay span not known",epistemic)
        elif typ == "stair_duration_feasible":
            height, speed = rule["height"], rule["speed"]
            if need(height,speed):
                t=values[height]/values[speed]
                record(rid,t<=rule["total_time_s"]+EPS,
                       f"Vertical portion of stairs alone {t:.2f} s vs scene {rule['total_time_s']} s, leaving time for horizontal movement; no path length inferred",epistemic)
            else: record(rid,None,"Local height or assumed vertical climbing speed not known",epistemic)
        elif typ == "elevator_duration_feasible":
            height, speed, nontravel = rule["height"],rule["speed"],rule["nontravel"]
            if need(height,speed,nontravel):
                t=values[height]/values[speed]+values[nontravel]
                record(rid,t<=rule["total_time_s"]+EPS,
                       f"Assumed lift run+nontravel {t:.2f} s vs scene {rule['total_time_s']} s; no evidence of constant lift velocity",epistemic)
            else: record(rid,None,"Lift height, speed or nontravel delay not known",epistemic)
        elif typ == "volume_does_not_approve_geometry":
            record(rid, graph["gates"]["metric_geometry_solved"] is False and
                graph["gates"]["archicad_write"] is False,"No geometric or BIM write authorization",epistemic)
        else:
            raise ValueError("UNSUPPORTED_RULE_"+typ)
    # Approximate scene duration cannot be multiplied by a single walking speed
    # unless a route segment is explicitly assigned this movement mode.
    timing = []
    for mode, key in [("WALK","assumed_walking_speed_mps"),
                      ("RUN","assumed_running_speed_mps"),
                      ("MAGNETIC_BOARD","assumed_magnetic_board_speed_mps")]:
        if values[key] is not None:
            timing.append({"mode":mode,"assumed_speed_mps":values[key],
                "example_30s_unobstructed_distance_m":round(30*values[key],3),
                "status":"HYPOTHETICAL_NOT_ASSIGNED_TO_ANY_BOOK_ROUTE"})
    apa = None
    if authored_rectangles is not None:
        # Reuse real APA author's geometric primitives, not a parallel
        # guessed wall generator. Rectangles must be supplied and source-owned.
        scripts = Path(__file__).resolve().parents[2] / "scripts"
        sys.path.insert(0,str(scripts))
        import archicad_semantic_spatial as SPATIAL
        if not isinstance(authored_rectangles,list):
            raise ValueError("APA_RECTANGLES_MUST_BE_LIST")
        boxes={}
        for x in authored_rectangles:
            if not isinstance(x,dict) or set(x)!={"id","rectangle"} or x["id"] in boxes:
                raise ValueError("APA_INVALID_RECTANGLE_IDENTITY")
            boxes[x["id"]]=SPATIAL.rectangle(x["rectangle"],"MOAG_"+x["id"])
        hits=[]
        ids=list(boxes)
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                area=SPATIAL.overlap_area(boxes[a],boxes[b])
                if area>EPS: hits.append({"a":a,"b":b,"overlap_area_m2":area,
                    "a_contains_b":SPATIAL.contains(boxes[a],boxes[b]),
                    "b_contains_a":SPATIAL.contains(boxes[b],boxes[a]),
                    "decision":"REQUIRES_AUTHOR_GEOMETRIC_REVIEW"})
        apa={"status":"EXISTING_APA_SPATIAL_PRIMITIVES_USED_READ_ONLY",
             "authored_count":len(boxes),"overlap_candidates":hits}
    failures=sum(x["status"]=="FAIL" for x in statuses)
    pending=sum(x["status"]=="NOT_EVALUABLE" for x in statuses)
    return {"schema":"APA-MOAG-PARAMETRIC-EVALUATION/0.4",
            "status":"CONSTRAINT_FAIL" if failures else "PARTIAL_NO_APPROVED_GEOMETRY",
            "counts":{"rules":len(statuses),"failed":failures,"unevaluable":pending,
                      "passed":len(statuses)-failures-pending},
            "parameter_values":values,"rules":statuses,"movement_what_if":timing,
            "apa_geometric_readonly_check":apa,
            "gates":{"geometry_approved":False,"archicad_written":False,
                      "no_unverified_metric_claims":True}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,default=GRAPH)
    p.add_argument("--overrides",type=Path)
    p.add_argument("--apa-rectangles",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    graph=json.loads(args.graph.read_text(encoding="utf-8"))
    overrides=json.loads(args.overrides.read_text(encoding="utf-8")) if args.overrides else {}
    rects=json.loads(args.apa_rectangles.read_text(encoding="utf-8")) if args.apa_rectangles else None
    result=evaluate(graph,overrides,rects)
    output=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if args.out:
        args.out.write_text(output,encoding="utf-8")
    else: print(output,end="")
    return 2 if result["counts"]["failed"] else 0

if __name__=="__main__":
    raise SystemExit(main())
