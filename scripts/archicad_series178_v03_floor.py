"""Fast Series 178 v0.3 floor completion pass over the proven skeleton.

Creates, with recovery logging after every mutation:
- stair access split in CORE_N (if still continuous);
- provisional apartment/service partitions;
- apartment/corridor doors;
- facade windows + balcony doors;
- four balcony slabs.

Uses standard Tapir on the current open PLN only. Never opens/switches/saves/closes.
All dimensions not legible on the passport are tagged provisional.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

PORT=19725
ROOT=Path(tempfile.gettempdir())
SK=ROOT/"series178-direct-19725-created.json"
STAIR=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))/"series178-v02"/"stair.json"
OUT=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))/"series178-v03"/"manifest.json"
WALL_IDS=[
"EXT_S_01","EXT_S_02","EXT_S_03","EXT_S_04","EXT_S_05","EXT_S_06","EXT_S_07",
"EXT_N_01","EXT_N_02","EXT_N_03","EXT_N_04","EXT_N_05","EXT_N_06","EXT_N_07",
"EXT_W_01","EXT_W_02","EXT_W_03","EXT_E_01","EXT_E_02","EXT_E_03",
"INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8","CORE_S","CORE_N"]

def api(cmd,p=None,port=PORT):
    body={"command":"API.ExecuteAddOnCommand","parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},"addOnCommandParameters":p or {}}}
    req=urllib.request.Request(f"http://127.0.0.1:{port}",json.dumps(body,ensure_ascii=False).encode(),{"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r: env=json.loads(r.read())
    if not env.get("succeeded"): raise RuntimeError(f"{cmd} transport failed")
    out=env.get("result",{}).get("addOnCommandResponse",{})
    if isinstance(out,dict) and out.get("error") is not None: raise RuntimeError(f"{cmd}: {out['error']}")
    return out

def E(g): return {"elementId":{"guid":g}}
def live():
    return {x["elementId"]["guid"].lower() for x in api("GetAllElements").get("elements",[]) if x.get("elementId",{}).get("guid")}
def detail(g):
    a=api("GetDetailsOfElements",{"elements":[E(g)]}).get("detailsOfElements",[])
    if len(a)!=1: raise RuntimeError(f"detail missing {g}")
    return a[0]
def one(res,label):
    g=[x.get("elementId",{}).get("guid") for x in res.get("elements",[])]
    g=[x for x in g if x]
    if len(g)!=1: raise RuntimeError(f"{label}: {res}")
    return g[0]
def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")
def addrec(m,id_,typ,g):
    m["created"].append({"id":id_,"type":typ,"guid":g}); save(m)

def wall(a,b,story,t=.08,h=2.84,source=None):
    row={"begCoordinate":{"x":a[0],"y":a[1]},"endCoordinate":{"x":b[0],"y":b[1]},"floorIndex":story,"zCoordinate":0.0,"height":h,"thickness":t,"offset":0.0,"arcAngle":0.0,"referenceLineLocation":"Center","structureType":"Basic"}
    if source:
        d=source["details"]; row.update({"height":float(d["height"]),"thickness":float(d.get("begThickness",t)),"zCoordinate":float(d.get("bottomOffset",0.0)),"offset":float(d.get("offset",0.0)),"referenceLineLocation":d.get("referenceLineLocation","Center")})
        bm=d.get("buildingMaterialId")
        if isinstance(bm,dict) and bm.get("guid"): row["buildingMaterialId"]=bm
    g=one(api("CreateWalls",{"wallsData":[row]}),"CreateWalls")
    rd=detail(g)
    if rd.get("type")!="Wall" or int(rd.get("floorIndex",-9))!=story: raise RuntimeError(f"wall readback {g}")
    return g

def door(host,off,w=.90,h=2.10):
    g=one(api("CreateDoors",{"doorsData":[{"ownerWallId":{"guid":host},"centerOffset":off,"sillHeight":0.0,"width":w,"height":h,"reflected":False,"refSide":False,"oSide":False}]}),"CreateDoors")
    if detail(g).get("type")!="Door": raise RuntimeError(f"door readback {g}")
    return g

def window(host,off,w=1.50,h=1.50,sill=.90):
    g=one(api("CreateWindows",{"windowsData":[{"ownerWallId":{"guid":host},"centerOffset":off,"sillHeight":sill,"width":w,"height":h,"reflected":False,"refSide":False,"oSide":False}]}),"CreateWindows")
    if detail(g).get("type")!="Window": raise RuntimeError(f"window readback {g}")
    return g

def slab(poly,story,level,t=.16):
    g=one(api("CreateSlabs",{"slabsData":[{"level":level,"floorIndex":story,"thickness":t,"referencePlaneLocation":"Top","polygonCoordinates":[{"x":x,"y":y} for x,y in poly]}]}),"CreateSlabs")
    if detail(g).get("type")!="Slab": raise RuntimeError(f"slab readback {g}")
    return g

def main():
    global PORT
    ap=argparse.ArgumentParser(); ap.add_argument("--port",type=int,default=PORT); ap.add_argument("--execute",action="store_true"); args=ap.parse_args()
    PORT=args.port
    if not SK.is_file(): raise RuntimeError(f"missing {SK}")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    if len(sk.get("wallGuids",[]))!=28: raise RuntimeError("need original 28-wall manifest")
    wm=dict(zip(WALL_IDS,sk["wallGuids"]))
    proj=api("GetProjectInfo"); path=proj.get("projectPath","")
    if "SafeBIM_Global_Library_Test_Projects".lower() not in path.lower(): raise RuntimeError(f"wrong project {path}")
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")
    srow=next(s for s in stories["stories"] if int(s["index"])==story)
    level=float(srow.get("level",0.0))
    L=live()
    required={sk["slabGuid"].lower(),*[g.lower() for g in sk["wallGuids"]]}
    missing=sorted(required-L)
    # CORE_N may be absent only if a previous access split already ran.
    if missing and missing!=[wm["CORE_N"].lower()]: raise RuntimeError(f"skeleton changed: {missing[:8]}")
    if OUT.is_file():
        old=json.loads(OUT.read_text(encoding="utf-8-sig"))
        if old.get("status")=="PASS" and any(x.get("guid","").lower() in L for x in old.get("created",[])): raise RuntimeError("v0.3 already present")
    ox=float(sk["originX"]); oy=float(sk["originY"])
    plan={"status":"DRY_RUN" if not args.execute else "IN_PROGRESS","projectPath":path,"port":PORT,"storyIndex":story,"origin":{"x":ox,"y":oy},"provisional":True,
          "scope":{"stairAccess":True,"partitions":8,"corridorDoors":4,"facadeOpenings":"north+south","balconySlabs":4},"created":[],"deleted":[],"savedProject":False}
    if not args.execute: print(json.dumps(plan,ensure_ascii=False,indent=2)); return
    save(plan)

    # 1) Stair access: replace CORE_N by two segments only if original still exists.
    if wm["CORE_N"].lower() in live():
        src=detail(wm["CORE_N"])
        l=wall((ox+6.6,oy+7.8),(ox+10.5,oy+7.8),story,source=src); addrec(plan,"CORE_N_L","Wall",l)
        r=wall((ox+12.3,oy+7.8),(ox+16.8,oy+7.8),story,source=src); addrec(plan,"CORE_N_R","Wall",r)
        api("DeleteElements",{"elements":[E(wm["CORE_N"])]})
        if wm["CORE_N"].lower() in live(): raise RuntimeError("CORE_N delete failed")
        plan["deleted"].append({"id":"CORE_N","guid":wm["CORE_N"]}); save(plan)
    else:
        # recover replacement GUIDs from previous stair-access evidence if present
        p=OUT.parent.parent/"series178-v02"/"stair-access.json"
        if p.is_file():
            q=json.loads(p.read_text(encoding="utf-8-sig"))
            for x in q.get("created",[]): plan["created"].append(x)
            save(plan)

    # resolve corridor north segments
    coreNL=next((x["guid"] for x in plan["created"] if x["id"]=="CORE_N_L"),None)
    coreNR=next((x["guid"] for x in plan["created"] if x["id"]=="CORE_N_R"),None)

    # 2) service/room partitions, symmetric + lower center
    parts=[
      ("P_L_S_H",(ox+3.0,oy+4.15),(ox+6.6,oy+4.15)),
      ("P_L_N_H",(ox+3.0,oy+9.05),(ox+6.6,oy+9.05)),
      ("P_L_M_V",(ox+4.55,oy+4.15),(ox+4.55,oy+9.05)),
      ("P_R_S_H",(ox+16.8,oy+4.15),(ox+20.4,oy+4.15)),
      ("P_R_N_H",(ox+16.8,oy+9.05),(ox+20.4,oy+9.05)),
      ("P_R_M_V",(ox+18.85,oy+4.15),(ox+18.85,oy+9.05)),
      ("P_C_S_L",(ox+6.6,oy+3.25),(ox+9.6,oy+3.25)),
      ("P_C_S_R",(ox+13.2,oy+3.25),(ox+16.8,oy+3.25)),
    ]
    for id_,a,b in parts:
        g=wall(a,b,story); addrec(plan,id_,"Wall",g)

    # 3) corridor apartment doors
    # CORE_S is 10.2 m from x=6.6 to16.8
    for id_,off in [("D_2B",2.15),("D_1B",7.65)]:
        g=door(wm["CORE_S"],off); addrec(plan,id_,"Door",g)
    if coreNL:
        g=door(coreNL,1.95); addrec(plan,"D_3B_L","Door",g)
    if coreNR:
        g=door(coreNR,2.25); addrec(plan,"D_3B_R","Door",g)

    # 4) facade windows. One centered window in ordinary 3.0/3.6 m panels.
    ordinary_s=["EXT_S_01","EXT_S_03","EXT_S_04","EXT_S_05","EXT_S_07"]
    ordinary_n=["EXT_N_01","EXT_N_03","EXT_N_04","EXT_N_05","EXT_N_07"]
    lengths={"EXT_S_01":3.0,"EXT_S_03":3.0,"EXT_S_04":3.6,"EXT_S_05":3.6,"EXT_S_07":3.0,
             "EXT_N_01":3.0,"EXT_N_03":3.0,"EXT_N_04":3.6,"EXT_N_05":3.6,"EXT_N_07":3.0}
    for wid in ordinary_s+ordinary_n:
        g=window(wm[wid],lengths[wid]/2); addrec(plan,"W_"+wid,"Window",g)

    # balcony facade bays: window + door on each 3.6 m wall
    for wid in ["EXT_S_02","EXT_S_06","EXT_N_02","EXT_N_06"]:
        gd=door(wm[wid],0.75,.90,2.10); addrec(plan,"BD_"+wid,"Door",gd)
        gw=window(wm[wid],2.35,1.40,1.45,.90); addrec(plan,"BW_"+wid,"Window",gw)

    # 5) balcony slabs, 1.20 m projection
    balconies=[
      ("BAL_S_L",[(ox+3.0,oy),(ox+6.6,oy),(ox+6.6,oy-1.2),(ox+3.0,oy-1.2)]),
      ("BAL_S_R",[(ox+16.8,oy),(ox+20.4,oy),(ox+20.4,oy-1.2),(ox+16.8,oy-1.2)]),
      ("BAL_N_L",[(ox+3.0,oy+13.2),(ox+6.6,oy+13.2),(ox+6.6,oy+14.4),(ox+3.0,oy+14.4)]),
      ("BAL_N_R",[(ox+16.8,oy+13.2),(ox+20.4,oy+13.2),(ox+20.4,oy+14.4),(ox+16.8,oy+14.4)]),
    ]
    for id_,poly in balconies:
        g=slab(poly,story,level,.16); addrec(plan,id_,"Slab",g)

    plan["status"]="PASS"; plan["elementCountAfter"]=len(live()); plan["nextPhase"]="one visual review -> corrections, then copy to upper stories"; save(plan)

    new=[E(x["guid"]) for x in plan["created"]]
    try:
        api("ChangeSelectionOfElements",{"addElementsToSelection":new})
        api("FitInWindow",{"elements":new})
    except Exception: pass
    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT),"note":"do not blindly rerun; manifest has every created GUID"},ensure_ascii=False,indent=2))
        raise SystemExit(2)
