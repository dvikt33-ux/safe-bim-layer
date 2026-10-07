"""Series 178 v0.4: replace rough v0.3 room partitions by area-driven ones.

The photographed passport gives room-area labels. This pass uses those labels
with the verified 3.0/3.6 m modular bays to place the main north/south room
boundaries, instead of the arbitrary v0.3 offsets. It deletes only the eight
known v0.3 provisional partition GUIDs, creates the corrected boundaries, then
adds a small set of provisional internal room doors.

No PLN save/open/switch/close. Every mutation is logged by GUID.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

PORT=19725
ROOT=Path(tempfile.gettempdir())
SK=ROOT/"series178-direct-19725-created.json"
BASE=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))
V03=BASE/"series178-v03"/"manifest.json"
OUT=BASE/"series178-v04"/"manifest.json"
V03_PARTS={"P_L_S_H","P_L_N_H","P_L_M_V","P_R_S_H","P_R_N_H","P_R_M_V","P_C_S_L","P_C_S_R"}
WALL_IDS=[
"EXT_S_01","EXT_S_02","EXT_S_03","EXT_S_04","EXT_S_05","EXT_S_06","EXT_S_07",
"EXT_N_01","EXT_N_02","EXT_N_03","EXT_N_04","EXT_N_05","EXT_N_06","EXT_N_07",
"EXT_W_01","EXT_W_02","EXT_W_03","EXT_E_01","EXT_E_02","EXT_E_03",
"INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8","CORE_S","CORE_N"]

def api(cmd,p=None):
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
def addrec(m,id_,typ,g,meta=None):
    row={"id":id_,"type":typ,"guid":g}
    if meta: row["meta"]=meta
    m["created"].append(row); save(m)
def wall(a,b,story,t=.08,h=2.84):
    row={"begCoordinate":{"x":a[0],"y":a[1]},"endCoordinate":{"x":b[0],"y":b[1]},"floorIndex":story,"zCoordinate":0.0,"height":h,"thickness":t,"offset":0.0,"arcAngle":0.0,"referenceLineLocation":"Center","structureType":"Basic"}
    g=one(api("CreateWalls",{"wallsData":[row]}),"CreateWalls")
    d=detail(g)
    if d.get("type")!="Wall": raise RuntimeError(f"wall readback {g}")
    return g
def door(host,off,w=.80,h=2.05):
    g=one(api("CreateDoors",{"doorsData":[{"ownerWallId":{"guid":host},"centerOffset":off,"sillHeight":0.0,"width":w,"height":h,"reflected":False,"refSide":False,"oSide":False}]}),"CreateDoors")
    if detail(g).get("type")!="Door": raise RuntimeError(f"door readback {g}")
    return g

def main():
    global PORT
    ap=argparse.ArgumentParser(); ap.add_argument("--port",type=int,default=PORT); ap.add_argument("--execute",action="store_true"); args=ap.parse_args(); PORT=args.port
    if not SK.is_file() or not V03.is_file(): raise RuntimeError("missing skeleton or v0.3 manifest")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    v03=json.loads(V03.read_text(encoding="utf-8-sig"))
    if v03.get("status")!="PASS": raise RuntimeError("v0.3 is not PASS")
    proj=api("GetProjectInfo"); path=proj.get("projectPath","")
    if "SafeBIM_Global_Library_Test_Projects".lower() not in path.lower(): raise RuntimeError(f"wrong project {path}")
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")
    L=live()
    if OUT.is_file():
        old=json.loads(OUT.read_text(encoding="utf-8-sig"))
        if old.get("status")=="PASS" and any(x.get("guid","").lower() in L for x in old.get("created",[])): raise RuntimeError("v0.4 already present")
    ox=float(sk["originX"]); oy=float(sk["originY"])
    wm=dict(zip(WALL_IDS,sk["wallGuids"]))
    oldparts=[x for x in v03.get("created",[]) if x.get("id") in V03_PARTS]
    if len(oldparts)!=8: raise RuntimeError(f"expected 8 v0.3 partitions, found {len(oldparts)}")
    missing=[x["guid"] for x in oldparts if x["guid"].lower() not in L]
    if missing: raise RuntimeError(f"v0.3 partitions changed/missing: {missing[:4]}")
    # Areas printed in passport, used only to derive principal clear-depth candidates.
    dims={
      "S_W_OUT":12.38/3.0,   # 4.1267
      "S_W_IN":8.76/3.6,    # 2.4333
      "S_C_L":10.39/3.0,    # 3.4633
      "S_C_M":17.96/3.6,    # 4.9889
      "N_W_OUT":11.25/3.0,  # 3.75 from north facade
      "N_W_IN":8.76/3.6,    # 2.4333 from north facade
    }
    plan={"status":"DRY_RUN" if not args.execute else "IN_PROGRESS","port":PORT,"projectPath":path,"storyIndex":story,"origin":{"x":ox,"y":oy},
          "method":"passport room-area labels / verified modular bay widths","provisional":True,
          "deleteV03Partitions":[{"id":x["id"],"guid":x["guid"]} for x in oldparts],
          "derivedDepths":dims,"created":[],"deleted":[],"savedProject":False}
    if not args.execute:
        print(json.dumps(plan,ensure_ascii=False,indent=2)); return
    save(plan)
    # delete only known v0.3 provisional partitions
    for x in oldparts:
        api("DeleteElements",{"elements":[E(x["guid"])]})
        if x["guid"].lower() in live(): raise RuntimeError(f"delete failed {x['id']}")
        plan["deleted"].append({"id":x["id"],"guid":x["guid"]}); save(plan)

    # Main room-boundary walls, derived from printed areas and modular widths.
    walls=[
      ("S_12_38_L",(ox+0.0,oy+dims["S_W_OUT"]),(ox+3.0,oy+dims["S_W_OUT"]),12.38),
      ("S_8_76_L",(ox+3.0,oy+dims["S_W_IN"]),(ox+6.6,oy+dims["S_W_IN"]),8.76),
      ("S_10_39",(ox+6.6,oy+dims["S_C_L"]),(ox+9.6,oy+dims["S_C_L"]),10.39),
      ("S_17_96_2B",(ox+9.6,oy+dims["S_C_M"]),(ox+13.2,oy+dims["S_C_M"]),17.96),
      ("S_17_96_1B",(ox+13.2,oy+dims["S_C_M"]),(ox+16.8,oy+dims["S_C_M"]),17.96),
      ("S_8_76_R",(ox+16.8,oy+dims["S_W_IN"]),(ox+20.4,oy+dims["S_W_IN"]),8.76),
      ("S_12_38_R",(ox+20.4,oy+dims["S_W_OUT"]),(ox+23.4,oy+dims["S_W_OUT"]),12.38),
      ("N_11_25_L",(ox+0.0,oy+13.2-dims["N_W_OUT"]),(ox+3.0,oy+13.2-dims["N_W_OUT"]),11.25),
      ("N_8_76_L",(ox+3.0,oy+13.2-dims["N_W_IN"]),(ox+6.6,oy+13.2-dims["N_W_IN"]),8.76),
      ("N_8_76_R",(ox+16.8,oy+13.2-dims["N_W_IN"]),(ox+20.4,oy+13.2-dims["N_W_IN"]),8.76),
      ("N_11_25_R",(ox+20.4,oy+13.2-dims["N_W_OUT"]),(ox+23.4,oy+13.2-dims["N_W_OUT"]),11.25),
    ]
    for id_,a,b,area in walls:
        g=wall(a,b,story)
        addrec(plan,id_,"Wall",g,{"printedRoomAreaM2":area})

    # Provisional internal doors through bearing lines: enough to make the four
    # apartment groups navigable without inventing detailed wet-room geometry yet.
    door_specs=[
      ("RD_L_OUT_S",wm["INT_X_2"],3.25),
      ("RD_L_IN_S",wm["INT_X_3"],2.95),
      ("RD_2B",wm["INT_X_4"],2.65),
      ("RD_1B",wm["INT_X_6"],2.65),
      ("RD_R_IN_S",wm["INT_X_7"],2.95),
      ("RD_R_OUT_S",wm["INT_X_8"],3.25),
      ("RD_L_OUT_N",wm["INT_X_2"],10.05),
      ("RD_L_IN_N",wm["INT_X_3"],9.55),
      ("RD_R_IN_N",wm["INT_X_7"],9.55),
      ("RD_R_OUT_N",wm["INT_X_8"],10.05),
    ]
    for id_,host,off in door_specs:
        g=door(host,off)
        addrec(plan,id_,"Door",g,{"offsetFromHostStart":off,"status":"PROVISIONAL"})

    plan["status"]="PASS"; plan["elementCountAfter"]=len(live()); plan["nextPhase"]="visual check; then wet-room/service-core detail and upper-storey copy"; save(plan)
    try:
        new=[E(x["guid"]) for x in plan["created"]]
        api("ChangeSelectionOfElements",{"addElementsToSelection":new})
        api("FitInWindow",{"elements":new})
    except Exception: pass
    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT),"note":"do not blindly rerun"},ensure_ascii=False,indent=2))
        raise SystemExit(2)
