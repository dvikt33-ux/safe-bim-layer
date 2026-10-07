"""Rebuild Series 178-07см.86 from the user's red wall markup.

STRICT:
- only native Archicad BIM/document tools: Wall, Door, Window, Slab, Stair,
  associative Dimension, Text;
- no Line/Polyline/Arc drawing at all;
- walls are segmented as panel runs;
- internal openings use real Door elements hosted by Walls;
- never opens/switches/saves/closes PLN.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", ROOT/"safe-bim-mvp-evidence"))
SK = ROOT/"series178-direct-19725-created.json"
OUT = BASE/"series178-PANEL-REBUILD"/"manifest.json"
PORT = None

X = [0.0, 3.0, 6.6, 9.6, 13.2, 16.8, 20.4, 23.4]
Y = [0.0, 5.4, 7.8, 13.2]

WALLS = [
    ("EXT_S_01",(0,0),(3,0),0.30,"external"),
    ("EXT_S_02",(3,0),(6.6,0),0.30,"external"),
    ("EXT_S_03",(6.6,0),(9.6,0),0.30,"external"),
    ("EXT_S_04",(9.6,0),(13.2,0),0.30,"external"),
    ("EXT_S_05",(13.2,0),(16.8,0),0.30,"external"),
    ("EXT_S_06",(16.8,0),(20.4,0),0.30,"external"),
    ("EXT_S_07",(20.4,0),(23.4,0),0.30,"external"),
    ("EXT_N_01",(0,13.2),(3,13.2),0.30,"external"),
    ("EXT_N_02",(3,13.2),(6.6,13.2),0.30,"external"),
    ("EXT_N_03",(6.6,13.2),(9.6,13.2),0.30,"external"),
    ("EXT_N_04",(9.6,13.2),(13.2,13.2),0.30,"external"),
    ("EXT_N_05",(13.2,13.2),(16.8,13.2),0.30,"external"),
    ("EXT_N_06",(16.8,13.2),(20.4,13.2),0.30,"external"),
    ("EXT_N_07",(20.4,13.2),(23.4,13.2),0.30,"external"),
    ("EXT_W_01",(0,0),(0,5.4),0.30,"external"),
    ("EXT_W_02",(0,5.4),(0,7.8),0.30,"external"),
    ("EXT_W_03",(0,7.8),(0,13.2),0.30,"external"),
    ("EXT_E_01",(23.4,0),(23.4,5.4),0.30,"external"),
    ("EXT_E_02",(23.4,5.4),(23.4,7.8),0.30,"external"),
    ("EXT_E_03",(23.4,7.8),(23.4,13.2),0.30,"external"),

    ("V_X3_N",(3.0,8.93),(3.0,13.2),0.16,"panel"),
    ("V_X3_S",(3.0,0.0),(3.0,7.8),0.16,"panel"),
    ("V_X66_N",(6.6,6.75),(6.6,13.2),0.16,"panel"),
    ("V_X66_S1",(6.6,0.0),(6.6,2.10),0.16,"panel"),
    ("V_X66_S2",(6.6,2.30),(6.6,3.95),0.16,"panel"),
    ("V_X96_N",(9.6,6.75),(9.6,13.2),0.16,"panel"),
    ("V_X924_S",(9.24,0.0),(9.24,3.95),0.16,"panel"),
    ("V_X132",(13.2,0.0),(13.2,13.2),0.16,"panel"),
    ("V_X168",(16.8,0.0),(16.8,13.2),0.16,"panel"),
    ("V_X204",(20.4,0.0),(20.4,13.2),0.16,"panel"),

    ("V_L_SVC1",(1.14,5.4),(1.14,7.8),0.08,"partition"),
    ("V_L_SVC2",(5.25,5.62),(5.25,6.95),0.08,"partition"),
    ("V_R_SVC1",(18.00,5.4),(18.00,7.8),0.08,"partition"),
    ("V_R_SVC2",(22.00,5.4),(22.00,7.8),0.08,"partition"),

    ("H_N_L_KITCH",(3.0,9.58),(6.6,9.58),0.08,"partition"),
    ("H_N_R_KITCH",(16.8,9.58),(20.4,9.58),0.08,"partition"),
    ("H_N_L_ROOM",(0.0,8.93),(3.0,8.93),0.16,"panel"),
    ("H_N_R_ROOM",(20.4,8.93),(23.4,8.93),0.16,"panel"),

    ("H_B_L",(0.0,7.8),(3.0,7.8),0.16,"panel"),
    ("H_B_LC",(3.0,7.8),(6.6,7.8),0.16,"panel"),
    ("H_B_C1",(6.6,7.8),(9.6,7.8),0.16,"panel"),
    ("H_B_STAIR",(9.6,7.8),(13.2,7.8),0.16,"panel"),
    ("H_B_C2",(13.2,7.8),(16.8,7.8),0.16,"panel"),
    ("H_B_RC",(16.8,7.8),(20.4,7.8),0.16,"panel"),
    ("H_B_R",(22.0,7.8),(23.4,7.8),0.16,"panel"),

    ("H_A_L",(0.0,5.4),(3.0,5.4),0.16,"panel"),
    ("H_A_LSVC",(5.25,5.4),(6.6,5.4),0.16,"panel"),
    ("H_A_C1",(6.6,5.4),(9.6,5.4),0.16,"panel"),
    ("H_A_C2",(9.6,5.4),(13.2,5.4),0.16,"panel"),
    ("H_A_C3",(13.2,5.4),(16.8,5.4),0.16,"panel"),
    ("H_A_RSVC",(16.8,5.4),(18.0,5.4),0.16,"panel"),
    ("H_A_R",(20.4,5.4),(23.4,5.4),0.16,"panel"),

    ("H_R_MID",(20.4,4.24),(23.4,4.24),0.08,"partition"),
    ("H_2B_TOP",(6.6,3.95),(9.24,3.95),0.08,"partition"),
    ("H_L_SOUTH",(3.0,2.76),(6.6,2.76),0.08,"partition"),
    ("H_R_SOUTH",(16.8,2.76),(20.4,2.76),0.08,"partition"),
]

DOORS = [
    ("D_3B_L_ENTRY","V_X66_N",1.55,0.90),
    ("D_3B_L_ROOM11","H_N_L_ROOM",2.35,0.80),
    ("D_3B_L_KITCH","H_N_L_KITCH",2.70,0.80),
    ("D_3B_L_SVC","H_B_LC",1.05,0.70),

    ("D_3B_R_ENTRY","V_X168",8.30,0.90),
    ("D_3B_R_ROOM11","H_N_R_ROOM",0.65,0.80),
    ("D_3B_R_KITCH","H_N_R_KITCH",0.90,0.80),
    ("D_3B_R_SVC","H_B_RC",2.55,0.70),

    ("D_2B_ENTRY","H_A_C2",0.75,0.90),
    ("D_1B_ENTRY","H_A_C3",0.70,0.90),

    ("D_2B_ROOM10","H_2B_TOP",1.95,0.80),
    ("D_L_SOUTH","H_L_SOUTH",2.25,0.80),
    ("D_R_SOUTH","H_R_SOUTH",1.00,0.80),
    ("D_R_MID","H_R_MID",0.85,0.80),
]

def call(port, cmd, params=None, timeout=90):
    body={"command":"API.ExecuteAddOnCommand","parameters":{
        "addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},
        "addOnCommandParameters":params or {}}}
    req=urllib.request.Request(
        f"http://127.0.0.1:{port}",
        json.dumps(body,ensure_ascii=False).encode("utf-8"),
        {"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        env=json.loads(r.read())
    if not env.get("succeeded"):
        raise RuntimeError(f"{port}/{cmd} transport failed")
    out=env.get("result",{}).get("addOnCommandResponse",{})
    if isinstance(out,dict) and out.get("error") is not None:
        raise RuntimeError(f"{port}/{cmd}: {out['error']}")
    return out

def discover():
    hits=[]
    for p in range(19723,19731):
        try:
            info=call(p,"GetProjectInfo",timeout=3)
            path=info.get("projectPath","")
            if "SafeBIM_Global_Library_Test_Projects".lower() in path.lower():
                hits.append((p,path))
        except Exception:
            pass
    if not hits:
        raise RuntimeError("target PLN not found on Tapir ports 19723..19730")
    for p,path in hits:
        if "план типовая" in path.lower():
            return p,path
    return hits[0]

def api(cmd,p=None): return call(PORT,cmd,p)
def E(g): return {"elementId":{"guid":g}}

def all_rows():
    return api("GetAllElements").get("elements",[])

def live():
    return {
        r["elementId"]["guid"].lower()
        for r in all_rows()
        if r.get("elementId",{}).get("guid")
    }

def detail(g):
    rows=api("GetDetailsOfElements",{"elements":[E(g)]}).get("detailsOfElements",[])
    if len(rows)!=1: raise RuntimeError(f"detail missing: {g}")
    return rows[0]

def one(res,label):
    gs=[r.get("elementId",{}).get("guid") for r in res.get("elements",[])]
    gs=[g for g in gs if g]
    if len(gs)!=1: raise RuntimeError(f"{label}: {res}")
    return gs[0]

def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")

def add(m,id_,typ,g,**meta):
    m["created"].append({"id":id_,"type":typ,"guid":g,**meta})
    save(m)
    return g

def collect_old():
    out=set()
    def take(d):
        if not isinstance(d,dict): return
        for k in ("guid","slabGuid"):
            if isinstance(d.get(k),str): out.add(d[k])
        for k in ("wallGuids","createdWallGuids","createdSlabGuids","dimensionGuids"):
            out.update(g for g in (d.get(k) or []) if isinstance(g,str))
        for row in d.get("created",[]) or []:
            if isinstance(row,dict) and isinstance(row.get("guid"),str):
                out.add(row["guid"])
    if SK.is_file():
        try: take(json.loads(SK.read_text(encoding="utf-8-sig")))
        except Exception: pass
    if BASE.exists():
        for folder in BASE.glob("series178*"):
            if not folder.is_dir(): continue
            for f in folder.rglob("*.json"):
                if f.name in ("before.json","after.json","latest.json","plan.json"): continue
                try:
                    if f.stat().st_size > 2_000_000: continue
                    take(json.loads(f.read_text(encoding="utf-8-sig")))
                except Exception: pass
    return out

def cleanup(m):
    L=live()
    targets=[g for g in collect_old() if g.lower() in L]
    priority={"Zone":0,"Text":1,"Dimension":1,"Polyline":1,"Line":1,"Arc":1,
              "Window":2,"Door":2,"Stair":3,"Slab":4,"Wall":5}
    typed=[]
    for g in targets:
        try: typ=detail(g).get("type","")
        except Exception: typ=""
        typed.append((priority.get(typ,9),typ,g))
    typed.sort()
    for _,typ,g in typed:
        if g.lower() not in live(): continue
        api("DeleteElements",{"elements":[E(g)]})
        if g.lower() in live(): raise RuntimeError(f"delete failed {typ} {g}")
        m["deleted"].append({"guid":g,"type":typ})
        save(m)

def create_wall(a,b,story,t,h=2.84):
    g=one(api("CreateWalls",{"wallsData":[{
        "begCoordinate":{"x":a[0],"y":a[1]},
        "endCoordinate":{"x":b[0],"y":b[1]},
        "floorIndex":story,"zCoordinate":0.0,"height":h,
        "thickness":t,"offset":0.0,"arcAngle":0.0,
        "referenceLineLocation":"Center","structureType":"Basic"
    }]}),"CreateWalls")
    if detail(g).get("type")!="Wall": raise RuntimeError(f"wall readback {g}")
    return g

def create_door(host,offset,width,height=2.10):
    g=one(api("CreateDoors",{"doorsData":[{
        "ownerWallId":{"guid":host},
        "centerOffset":offset,
        "sillHeight":0.0,"width":width,"height":height,
        "reflected":False,"refSide":False,"oSide":False
    }]}),"CreateDoors")
    if detail(g).get("type")!="Door": raise RuntimeError(f"door readback {g}")
    return g

def create_window(host,offset,width=1.45,height=1.50,sill=.90):
    g=one(api("CreateWindows",{"windowsData":[{
        "ownerWallId":{"guid":host},
        "centerOffset":offset,"sillHeight":sill,
        "width":width,"height":height,
        "reflected":False,"refSide":False,"oSide":False
    }]}),"CreateWindows")
    if detail(g).get("type")!="Window": raise RuntimeError(f"window readback {g}")
    return g

def create_slab(poly,story,level,t=.16):
    g=one(api("CreateSlabs",{"slabsData":[{
        "level":level,"floorIndex":story,"thickness":t,
        "referencePlaneLocation":"Top",
        "polygonCoordinates":[{"x":x,"y":y} for x,y in poly]
    }]}),"CreateSlabs")
    if detail(g).get("type")!="Slab": raise RuntimeError(f"slab readback {g}")
    return g

def create_stair(ox,oy,level,story):
    baseline=[
        {"x":ox+10.10,"y":oy+8.15},
        {"x":ox+10.10,"y":oy+12.20},
        {"x":ox+12.70,"y":oy+12.20},
        {"x":ox+12.70,"y":oy+8.15},
    ]
    return one(api("CreateStairs",{"stairsData":[{
        "baseLinePoints":baseline,
        "zCoordinate":level,"floorIndex":story,
        "totalHeight":3.0,"flightWidth":1.05,
        "stepNum":18,"riserHeight":3.0/18.0,"treadDepth":0.28
    }]}),"CreateStairs")

def create_dim(ref,direction,story,witnesses):
    return one(api("CreateAssociativeDimensions",{"dimensionsData":[{
        "referencePoint":{"x":ref[0],"y":ref[1]},
        "direction":{"x":direction[0],"y":direction[1]},
        "floorIndex":story,
        "witnessPoints":[{"elementId":{"guid":g},"inIndex":idx} for g,idx in witnesses]
    }]}),"CreateAssociativeDimensions")

def create_text(x,y,z,story,value,height=1.8):
    return one(api("CreateTexts",{"textsData":[{
        "coordinate":{"x":x,"y":y,"z":z},
        "text":value,"height":height,"pen":1,
        "angle":0.0,"justification":"Center","floorIndex":story
    }]}),"CreateTexts")

def main():
    global PORT
    ap=argparse.ArgumentParser()
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    PORT,path=discover()
    if not SK.is_file(): raise RuntimeError(f"missing {SK}")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    ox=float(sk["originX"]); oy=float(sk["originY"])
    story=int(sk.get("storyIndex",0))

    stories=api("GetStories")
    if int(stories.get("actStory",-999))!=story:
        raise RuntimeError(f"active story {stories.get('actStory')} != target {story}")
    sr=next((s for s in stories.get("stories",[]) if int(s["index"])==story),None)
    if sr is None: raise RuntimeError(f"story {story} missing")
    level=float(sr.get("level",0.0))

    m={
        "status":"DRY_RUN" if not args.execute else "IN_PROGRESS",
        "port":PORT,"projectPath":path,"storyIndex":story,
        "origin":{"x":ox,"y":oy},
        "mode":"USER_RED_MARKUP_PANEL_BIM_ONLY",
        "rules":{
            "no2DLines":True,
            "walls":"native Archicad Wall, segmented by panel run",
            "doors":"native hosted Archicad Door",
            "windows":"native hosted Archicad Window",
            "balconies":"native Slab + low Wall parapet",
            "stair":"native Archicad Stair",
            "dimensions":"native associative Dimension",
            "zones":False
        },
        "created":[],"deleted":[],"savedProject":False
    }
    if not args.execute:
        print(json.dumps(m,ensure_ascii=False,indent=2)); return
    save(m)
    cleanup(m)

    A=lambda p:(ox+p[0],oy+p[1])

    add(m,"SLAB_MAIN","Slab",
        create_slab([A((0,0)),A((23.4,0)),A((23.4,13.2)),A((0,13.2))],story,level))

    hosts={}
    for name,a,b,t,role in WALLS:
        g=create_wall(A(a),A(b),story,t)
        hosts[name]=g
        add(m,name,"Wall",g,role=role,thickness=t)

    for name,host_name,off,w in DOORS:
        if host_name not in hosts: raise RuntimeError(f"missing door host {host_name}")
        g=create_door(hosts[host_name],off,w)
        add(m,name,"Door",g,host=host_name,width=w)

    for i in range(1,8):
        s=hosts[f"EXT_S_{i:02d}"]; n=hosts[f"EXT_N_{i:02d}"]
        L=X[i]-X[i-1]
        if i in (2,6):
            add(m,f"BAL_DOOR_S_{i}","Door",create_door(s,0.65,.90),host=f"EXT_S_{i:02d}")
            add(m,f"BAL_WIN_S_{i}","Window",create_window(s,2.30,1.35),host=f"EXT_S_{i:02d}")
            add(m,f"BAL_DOOR_N_{i}","Door",create_door(n,0.65,.90),host=f"EXT_N_{i:02d}")
            add(m,f"BAL_WIN_N_{i}","Window",create_window(n,2.30,1.35),host=f"EXT_N_{i:02d}")
        else:
            add(m,f"WIN_S_{i}","Window",create_window(s,L/2.0),host=f"EXT_S_{i:02d}")
            add(m,f"WIN_N_{i}","Window",create_window(n,L/2.0),host=f"EXT_N_{i:02d}")

    for host_name in ("EXT_W_01","EXT_W_03","EXT_E_01","EXT_E_03"):
        add(m,"WIN_"+host_name,"Window",create_window(hosts[host_name],2.70),host=host_name)

    add(m,"STAIR","Stair",create_stair(ox,oy,level,story))

    balconies=[
        ("BAL_N_L",[(3.0,13.2),(3.0,14.70),(6.6,14.70),(6.6,13.2)]),
        ("BAL_N_R",[(16.8,13.2),(16.8,14.70),(20.4,14.70),(20.4,13.2)]),
        ("BAL_S_L",[(3.0,0.0),(3.0,-1.60),(6.6,-1.60),(6.6,0.0)]),
        ("BAL_S_R",[(16.8,0.0),(16.8,-1.60),(20.4,-1.60),(20.4,0.0)]),
    ]
    for name,poly in balconies:
        add(m,name,"Slab",create_slab([A(p) for p in poly],story,level,.16))
        p0,p1,p2,p3=poly
        for k,(a,b) in enumerate(((p0,p1),(p1,p2),(p2,p3)),1):
            add(m,f"{name}_PAR_{k}","Wall",create_wall(A(a),A(b),story,.10,1.05),
                role="balcony parapet")

    S=[hosts[f"EXT_S_{i:02d}"] for i in range(1,8)]
    W=[hosts[f"EXT_W_{i:02d}"] for i in range(1,4)]
    xwit=[(S[0],1)]+[(S[i],2) for i in range(7)]
    ywit=[(W[0],1),(W[0],2),(W[1],2),(W[2],2)]
    add(m,"DIM_X_CHAIN","Dimension",create_dim(A((0,-2.20)),(1,0),story,xwit))
    add(m,"DIM_X_TOTAL","Dimension",create_dim(A((0,-3.00)),(1,0),story,[xwit[0],xwit[-1]]))
    add(m,"DIM_Y_CHAIN","Dimension",create_dim(A((-2.20,0)),(0,1),story,ywit))
    add(m,"DIM_Y_TOTAL","Dimension",create_dim(A((-3.00,0)),(0,1),story,[ywit[0],ywit[-1]]))

    for idx,(val,x,y) in enumerate([
        ("11,25",1.5,11.7),("8,76",4.8,11.7),("17,96",8.1,11.7),
        ("17,96",15.0,11.7),("8,76",18.7,11.7),("11,25",21.9,11.7),
        ("12,38",1.5,1.0),("8,76",4.8,1.0),("10,39",8.1,1.0),
        ("17,96",11.4,1.0),("17,96",15.0,1.0),("8,76",18.7,1.0),("12,38",21.9,1.0),
        ("6,19",11.7,6.45),
    ],1):
        add(m,f"TXT_AREA_{idx:02d}","Text",create_text(ox+x,oy+y,level,story,val,1.6))
    for idx,(val,x,y) in enumerate([
        ("3Б  41,59 / 70,87",8.1,9.6),
        ("3Б  41,59 / 70,87",15.2,9.6),
        ("2Б  28,35 / 53,27",11.2,4.45),
        ("1Б  17,96 / 38,43",15.0,4.45),
    ],1):
        add(m,f"TXT_APT_{idx}","Text",create_text(ox+x,oy+y,level,story,val,1.9))

    m["status"]="PASS"
    m["elementCountAfter"]=len(all_rows())
    m["nextPhase"]="visual compare to user red markup; adjust only wall/door offsets"
    save(m)

    try:
        api("FitInWindow",{})
    except Exception:
        pass
    print(json.dumps(m,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({
            "status":"BLOCKED","error":str(e),"evidence":str(OUT),
            "note":"do not blindly rerun after a partial failure; inspect manifest"
        },ensure_ascii=False,indent=2))
        raise SystemExit(2)
