"""FINAL one-shot cleanup/finish for Series 178-07sm.86 typical floor.

Submission-oriented pass:
- auto-discovers the currently open target PLN on Tapir ports 19723..19730;
- deletes only the Zone elements created by our v0.8 pass (blue crosses);
- deletes any remaining fake v0.6 Line/Text pseudo-dimensions;
- keeps the native Archicad Dimension chains created by v0.7;
- replaces the provisional floating Stair with a wider U-shaped Stair aligned to
  the corridor opening;
- widens/rebuilds the stair-access wall split so the Stair lands on the corridor;
- recreates the two north apartment entry doors on the new access-wall segments;
- creates clean room-area labels and four apartment labels from the passport;
- never opens/switches/saves/closes the PLN.

All destructive actions use exact GUIDs from our own evidence manifests only.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

ROOT=Path(tempfile.gettempdir())
BASE=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))
SK=ROOT/"series178-direct-19725-created.json"
V02_STAIR=BASE/"series178-v02"/"stair.json"
V03=BASE/"series178-v03"/"manifest.json"
V06=BASE/"series178-v06"/"manifest.json"
V07=BASE/"series178-v07"/"manifest.json"
V08=BASE/"series178-v08"/"manifest.json"
OUT=BASE/"series178-FINAL"/"manifest.json"

PORT=None

def call(port,cmd,p=None,timeout=60):
    body={"command":"API.ExecuteAddOnCommand","parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},"addOnCommandParameters":p or {}}}
    req=urllib.request.Request(f"http://127.0.0.1:{port}",json.dumps(body,ensure_ascii=False).encode("utf-8"),{"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: env=json.loads(r.read())
    if not env.get("succeeded"): raise RuntimeError(f"{port}/{cmd} transport failed")
    out=env.get("result",{}).get("addOnCommandResponse",{})
    if isinstance(out,dict) and out.get("error") is not None: raise RuntimeError(f"{port}/{cmd}: {out['error']}")
    return out

def discover():
    hits=[]
    for port in range(19723,19731):
        try:
            info=call(port,"GetProjectInfo",timeout=3)
            path=info.get("projectPath","")
            if "SafeBIM_Global_Library_Test_Projects".lower() in path.lower():
                hits.append((port,path))
        except Exception:
            pass
    if not hits:
        raise RuntimeError("target PLN not found on ports 19723..19730")
    # Prefer the one containing the exact project stem when several exist.
    for port,path in hits:
        if "план типовая" in path.lower():
            return port,path
    return hits[0]

def api(cmd,p=None):
    return call(PORT,cmd,p,90)

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

def create_wall_like(source,a,b,story):
    d=source["details"]
    row={
      "begCoordinate":{"x":a[0],"y":a[1]},
      "endCoordinate":{"x":b[0],"y":b[1]},
      "floorIndex":story,
      "zCoordinate":float(d.get("bottomOffset",0.0)),
      "height":float(d.get("height",2.84)),
      "thickness":float(d.get("begThickness",0.16)),
      "offset":float(d.get("offset",0.0)),
      "arcAngle":0.0,
      "referenceLineLocation":d.get("referenceLineLocation","Center"),
      "structureType":"Basic",
    }
    bm=d.get("buildingMaterialId")
    if isinstance(bm,dict) and bm.get("guid"): row["buildingMaterialId"]=bm
    g=one(api("CreateWalls",{"wallsData":[row]}),"CreateWalls")
    if detail(g).get("type")!="Wall": raise RuntimeError(f"wall readback {g}")
    return g

def create_door(host,off,w=.90,h=2.10):
    g=one(api("CreateDoors",{"doorsData":[{
      "ownerWallId":{"guid":host},"centerOffset":off,"sillHeight":0.0,
      "width":w,"height":h,"reflected":False,"refSide":False,"oSide":False
    }]}),"CreateDoors")
    if detail(g).get("type")!="Door": raise RuntimeError(f"door readback {g}")
    return g

def create_stair(ox,oy,z0,story):
    # Corridor is y=5.4..7.8; stair bay is x=9.6..13.2, y=7.8..13.2.
    # Ends sit directly behind the widened corridor opening.
    baseline=[
      {"x":ox+10.05,"y":oy+7.92},
      {"x":ox+10.05,"y":oy+12.90},
      {"x":ox+12.75,"y":oy+12.90},
      {"x":ox+12.75,"y":oy+7.92},
    ]
    g=one(api("CreateStairs",{"stairsData":[{
      "baseLinePoints":baseline,
      "zCoordinate":z0,
      "floorIndex":story,
      "totalHeight":3.0,
      "flightWidth":1.05,
      "stepNum":18,
      "riserHeight":3.0/18.0,
      "treadDepth":0.28
    }]}),"CreateStairs")
    d=detail(g)
    if d.get("type")!="Stair": raise RuntimeError(f"stair readback {d}")
    return g,baseline

def create_text(x,y,z,story,txt,h=2.6):
    g=one(api("CreateTexts",{"textsData":[{
      "coordinate":{"x":x,"y":y,"z":z},"text":txt,"height":h,
      "pen":1,"angle":0.0,"justification":"Center","floorIndex":story
    }]}),"CreateTexts")
    return g

def main():
    global PORT
    ap=argparse.ArgumentParser(); ap.add_argument("--execute",action="store_true"); args=ap.parse_args()

    PORT,path=discover()

    if not SK.is_file(): raise RuntimeError(f"missing skeleton manifest {SK}")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story:
        raise RuntimeError(f"active story {stories.get('actStory')} != {story}")
    srow=next(s for s in stories["stories"] if int(s["index"])==story)
    z0=float(srow.get("level",0.0))
    ox=float(sk["originX"]); oy=float(sk["originY"])
    L=live()

    if OUT.is_file():
        old=json.loads(OUT.read_text(encoding="utf-8-sig"))
        if old.get("status")=="PASS" and any(x.get("guid","").lower() in L for x in old.get("created",[])):
            raise RuntimeError("FINAL pass already present; refusing duplicate")

    delete_targets=[]

    # Blue-cross Zones from v0.8.
    if V08.is_file():
        v08=json.loads(V08.read_text(encoding="utf-8-sig"))
        for x in v08.get("created",[]):
            if x.get("type")=="Zone" and x.get("guid") and x["guid"].lower() in L:
                delete_targets.append({"source":"v08-zone","guid":x["guid"],"id":x.get("id")})

    # Fake dimensions from v0.6 — native v0.7 Dimensions stay.
    if V06.is_file():
        v06=json.loads(V06.read_text(encoding="utf-8-sig"))
        for g in v06.get("dimensionGuids",[]):
            if g and g.lower() in L:
                delete_targets.append({"source":"v06-fake-dim","guid":g,"id":"fake-dim"})

    # Old provisional Stair.
    old_stair=None
    if V02_STAIR.is_file():
        st=json.loads(V02_STAIR.read_text(encoding="utf-8-sig"))
        g=st.get("guid")
        if g and g.lower() in L:
            old_stair=g
            delete_targets.append({"source":"v02-stair","guid":g,"id":"old-stair"})

    # Existing CORE_N split segments. We'll replace them with a wider stair opening.
    old_core=[]
    if V03.is_file():
        v03=json.loads(V03.read_text(encoding="utf-8-sig"))
        for x in v03.get("created",[]):
            if x.get("id") in ("CORE_N_L","CORE_N_R") and x.get("guid") and x["guid"].lower() in L:
                old_core.append(x)
    if len(old_core)!=2:
        raise RuntimeError(f"need both live CORE_N_L/R segments, found {old_core}")

    plan={
      "status":"DRY_RUN" if not args.execute else "IN_PROGRESS",
      "port":PORT,"projectPath":path,"storyIndex":story,
      "deleteCount":len(delete_targets),
      "rebuildStair":True,
      "rebuildStairAccess":True,
      "roomAreaLabelCount":14,
      "apartmentLabelCount":4,
      "created":[],"deleted":[],"savedProject":False
    }
    if not args.execute:
        print(json.dumps(plan,ensure_ascii=False,indent=2)); return
    save(plan)

    # 1) New access walls FIRST, copied from current wall properties.
    left_src=detail(old_core[0]["guid"])
    right_src=detail(old_core[1]["guid"])
    # Opening 2.80 m wide: x=10.0..12.8 in the 3.6 m stair bay.
    newL=create_wall_like(left_src,(ox+6.60,oy+7.80),(ox+10.00,oy+7.80),story)
    add(plan,"FINAL_CORE_N_L","Wall",newL)
    newR=create_wall_like(right_src,(ox+12.80,oy+7.80),(ox+16.80,oy+7.80),story)
    add(plan,"FINAL_CORE_N_R","Wall",newR)

    # Delete old access wall segments; hosted old entry doors go with them.
    for x in old_core:
        g=x["guid"]
        api("DeleteElements",{"elements":[E(g)]})
        plan["deleted"].append({"source":"old-core","guid":g,"id":x.get("id")}); save(plan)

    # Recreate north apartment entry doors near corridor ends.
    d1=create_door(newL,1.65,.90,2.10); add(plan,"ENTRY_3B_L_FINAL","Door",d1)
    d2=create_door(newR,2.35,.90,2.10); add(plan,"ENTRY_3B_R_FINAL","Door",d2)

    # 2) Delete blue Zones / fake dimensions / old Stair.
    for x in delete_targets:
        g=x["guid"]
        if g.lower() not in live():
            continue
        api("DeleteElements",{"elements":[E(g)]})
        plan["deleted"].append(x); save(plan)

    # 3) Create the corrected Stair.
    stair,baseline=create_stair(ox,oy,z0,story)
    add(plan,"STAIR_FINAL","Stair",stair,{"baseline":baseline})

    # 4) Clean source-style room-area labels (no Zone crosses).
    room_labels=[
      ("11,25",1.50,11.75),
      ("8,76",4.80,11.75),
      ("17,96",8.10,11.45),
      ("17,96",15.00,11.45),
      ("8,76",18.60,11.75),
      ("11,25",21.90,11.75),
      ("12,38",1.50,1.25),
      ("8,76",4.80,1.25),
      ("10,39",8.10,1.25),
      ("17,96",11.40,1.25),
      ("17,96",15.00,1.25),
      ("8,76",18.60,1.25),
      ("12,38",21.90,1.25),
      ("6,19",11.40,6.60),
    ]
    for i,(txt,rx,ry) in enumerate(room_labels,1):
        g=create_text(ox+rx,oy+ry,z0,story,txt,2.4)
        add(plan,f"ROOM_AREA_{i:02d}","Text",g)

    apartment_labels=[
      ("3Б  41,59 / 70,87",7.85,9.90),
      ("3Б  41,59 / 70,87",15.55,9.90),
      ("2Б  28,35 / 53,27",10.30,4.25),
      ("1Б  17,96 / 38,43",14.55,4.25),
    ]

    # Remove old v0.8 apartment texts first to avoid duplicates.
    if V08.is_file():
        v08=json.loads(V08.read_text(encoding="utf-8-sig"))
        for x in v08.get("created",[]):
            if x.get("type")=="Text" and x.get("guid") and x["guid"].lower() in live():
                api("DeleteElements",{"elements":[E(x["guid"])]})
                plan["deleted"].append({"source":"v08-text","guid":x["guid"],"id":x.get("id")}); save(plan)

    for i,(txt,rx,ry) in enumerate(apartment_labels,1):
        g=create_text(ox+rx,oy+ry,z0,story,txt,3.0)
        add(plan,f"APT_{i}","Text",g)

    plan["status"]="PASS"
    plan["elementCountAfter"]=len(api("GetAllElements").get("elements",[]))
    plan["nextPhase"]="SUBMISSION: visual check/print. No more staged geometry passes."
    save(plan)

    try:
        api("FitInWindow",{})
    except Exception:
        pass

    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT)},ensure_ascii=False,indent=2))
        raise SystemExit(2)
