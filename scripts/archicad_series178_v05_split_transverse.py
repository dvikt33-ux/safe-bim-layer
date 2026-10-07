"""Series 178 v0.5: fix the main topology mistake from v0.4.

The six original full-depth transverse bearing walls are wrong for the passport
plan because the middle 2.4 m corridor must pass through them. This pass:
- creates north/south replacement segments for each transverse wall;
- reads them back before deleting the original full-depth wall;
- then recreates the provisional room doors on the new segments.

Keeps the v0.4 area-derived horizontal room boundaries, stair, facade openings,
and balconies. Never saves/opens/switches/closes the PLN.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

PORT = 19725
ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", ROOT/"safe-bim-mvp-evidence"))
SK = ROOT/"series178-direct-19725-created.json"
V04 = BASE/"series178-v04"/"manifest.json"
OUT = BASE/"series178-v05"/"manifest.json"

WALL_IDS = [
"EXT_S_01","EXT_S_02","EXT_S_03","EXT_S_04","EXT_S_05","EXT_S_06","EXT_S_07",
"EXT_N_01","EXT_N_02","EXT_N_03","EXT_N_04","EXT_N_05","EXT_N_06","EXT_N_07",
"EXT_W_01","EXT_W_02","EXT_W_03","EXT_E_01","EXT_E_02","EXT_E_03",
"INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8","CORE_S","CORE_N"
]
TARGETS = ["INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8"]

def api(cmd, p=None):
    body={"command":"API.ExecuteAddOnCommand","parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},"addOnCommandParameters":p or {}}}
    req=urllib.request.Request(f"http://127.0.0.1:{PORT}",json.dumps(body,ensure_ascii=False).encode(),{"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r: env=json.loads(r.read())
    if not env.get("succeeded"): raise RuntimeError(f"{cmd} transport failed")
    out=env.get("result",{}).get("addOnCommandResponse",{})
    if isinstance(out,dict) and out.get("error") is not None: raise RuntimeError(f"{cmd}: {out['error']}")
    return out

def E(g): return {"elementId":{"guid":g}}

def live():
    return {x["elementId"]["guid"].lower() for x in api("GetAllElements").get("elements",[]) if x.get("elementId",{}).get("guid")}

def detail(g):
    rows=api("GetDetailsOfElements",{"elements":[E(g)]}).get("detailsOfElements",[])
    if len(rows)!=1: raise RuntimeError(f"detail missing {g}")
    return rows[0]

def one(res,label):
    gs=[x.get("elementId",{}).get("guid") for x in res.get("elements",[])]
    gs=[g for g in gs if g]
    if len(gs)!=1: raise RuntimeError(f"{label}: {res}")
    return gs[0]

def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")

def add(m,id_,typ,g,meta=None):
    row={"id":id_,"type":typ,"guid":g}
    if meta: row["meta"]=meta
    m["created"].append(row); save(m)

def create_like(source, a, b, story):
    d=source["details"]
    if d.get("geometryType")!="Straight": raise RuntimeError("source wall not straight")
    if d.get("structureType","Basic")!="Basic": raise RuntimeError("source wall not Basic")
    row={
      "begCoordinate":{"x":a[0],"y":a[1]},
      "endCoordinate":{"x":b[0],"y":b[1]},
      "floorIndex":story,
      "zCoordinate":float(d.get("bottomOffset",0.0)),
      "height":float(d["height"]),
      "thickness":float(d.get("begThickness",0.16)),
      "offset":float(d.get("offset",0.0)),
      "arcAngle":0.0,
      "referenceLineLocation":d.get("referenceLineLocation","Center"),
      "structureType":"Basic",
    }
    bm=d.get("buildingMaterialId")
    if isinstance(bm,dict) and bm.get("guid"): row["buildingMaterialId"]=bm
    g=one(api("CreateWalls",{"wallsData":[row]}),"CreateWalls")
    rd=detail(g)
    if rd.get("type")!="Wall" or int(rd.get("floorIndex",-9))!=story:
        raise RuntimeError(f"wall readback mismatch {g}")
    return g

def door(host,off,w=.80,h=2.05):
    g=one(api("CreateDoors",{"doorsData":[{
      "ownerWallId":{"guid":host},"centerOffset":off,"sillHeight":0.0,
      "width":w,"height":h,"reflected":False,"refSide":False,"oSide":False
    }]}),"CreateDoors")
    if detail(g).get("type")!="Door": raise RuntimeError(f"door readback {g}")
    return g

def main():
    global PORT
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=PORT)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args(); PORT=args.port

    if not SK.is_file() or not V04.is_file(): raise RuntimeError("missing skeleton or v0.4 manifest")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    v04=json.loads(V04.read_text(encoding="utf-8-sig"))
    if v04.get("status")!="PASS": raise RuntimeError("v0.4 is not PASS")

    project=api("GetProjectInfo"); path=project.get("projectPath","")
    if "SafeBIM_Global_Library_Test_Projects".lower() not in path.lower(): raise RuntimeError(f"wrong project {path}")
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")

    wm=dict(zip(WALL_IDS,sk["wallGuids"]))
    L=live()
    missing=[wm[k] for k in TARGETS if wm[k].lower() not in L]
    if missing: raise RuntimeError(f"original transverse walls already changed: {missing[:4]}")

    if OUT.is_file():
        old=json.loads(OUT.read_text(encoding="utf-8-sig"))
        if old.get("status")=="PASS" and any(x.get("guid","").lower() in L for x in old.get("created",[])):
            raise RuntimeError("v0.5 already present")

    ox=float(sk["originX"]); oy=float(sk["originY"])
    xs={"INT_X_2":3.0,"INT_X_3":6.6,"INT_X_4":9.6,"INT_X_6":13.2,"INT_X_7":16.8,"INT_X_8":20.4}

    plan={
      "status":"DRY_RUN" if not args.execute else "IN_PROGRESS",
      "port":PORT,"projectPath":path,"storyIndex":story,
      "fix":"split six full-depth transverse walls around verified 2.4 m corridor",
      "corridor":{"y":[oy+5.4,oy+7.8],"width":2.4},
      "created":[],"deleted":[],"savedProject":False
    }
    if not args.execute:
        print(json.dumps(plan,ensure_ascii=False,indent=2)); return
    save(plan)

    replacements={}
    for key in TARGETS:
        x=ox+xs[key]
        src=detail(wm[key])

        gs=create_like(src,(x,oy+0.0),(x,oy+5.4),story)
        add(plan,key+"_S","Wall",gs,{"source":key})

        gn=create_like(src,(x,oy+7.8),(x,oy+13.2),story)
        add(plan,key+"_N","Wall",gn,{"source":key})

        replacements[key]={"S":gs,"N":gn}

        api("DeleteElements",{"elements":[E(wm[key])]})
        if wm[key].lower() in live(): raise RuntimeError(f"delete failed {key}")
        plan["deleted"].append({"id":key,"guid":wm[key]}); save(plan)

    # Recreate the useful provisional internal door locations from v0.4,
    # now on the correct north/south wall segments.
    specs=[
      ("RD_L_OUT_S","INT_X_2","S",3.25),
      ("RD_L_IN_S","INT_X_3","S",2.95),
      ("RD_2B","INT_X_4","S",2.65),
      ("RD_1B","INT_X_6","S",2.65),
      ("RD_R_IN_S","INT_X_7","S",2.95),
      ("RD_R_OUT_S","INT_X_8","S",3.25),
      ("RD_L_OUT_N","INT_X_2","N",2.25),
      ("RD_L_IN_N","INT_X_3","N",1.75),
      ("RD_R_IN_N","INT_X_7","N",1.75),
      ("RD_R_OUT_N","INT_X_8","N",2.25),
    ]
    for id_,key,side,off in specs:
        g=door(replacements[key][side],off)
        add(plan,id_,"Door",g,{"hostReplacement":key+"_"+side,"offset":off})

    plan["status"]="PASS"
    plan["elementCountAfter"]=len(live())
    plan["nextPhase"]="visual compare against passport; then service cores only"
    save(plan)

    try:
        ne=[E(x["guid"]) for x in plan["created"]]
        api("ChangeSelectionOfElements",{"addElementsToSelection":ne})
        api("FitInWindow",{"elements":ne})
    except Exception:
        pass

    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT),"note":"do not blindly rerun"},ensure_ascii=False,indent=2))
        raise SystemExit(2)
