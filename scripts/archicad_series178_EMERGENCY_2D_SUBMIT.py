"""EMERGENCY submission plan for 178-07см.86.

Purpose: produce a clean 2D Archicad plan that visually follows the photographed
passport instead of continuing the incorrect BIM guesses.

This script:
- auto-discovers the target PLN;
- deletes only elements created by our prior Series-178 scripts;
- draws a clean source-faithful plan with native Archicad Polyline/Arc/Text tools;
- adds four balconies, central stair symbol, room/apartment labels;
- adds native Archicad associative dimensions from a minimal hidden BIM frame;
- creates no Zones;
- never saves/opens/switches/closes the PLN.

The minimal BIM frame (outer segmented walls) exists only to host real dimensions.
The visible plan itself is native 2D Archicad linework.
"""
from __future__ import annotations

import argparse, json, os, tempfile, urllib.request, math
from pathlib import Path

ROOT=Path(tempfile.gettempdir())
BASE=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))
SK=ROOT/"series178-direct-19725-created.json"
OUT=BASE/"series178-EMERGENCY-2D"/"manifest.json"
PORT=None

OLD_DIRS=[
 "series178-v02","series178-v03","series178-v04","series178-v05","series178-v06",
 "series178-v07","series178-v08","series178-FINAL","series178-CLEAN",
 "series178-SOURCE-TRACE"
]

def call(port,cmd,p=None,timeout=90):
    body={"command":"API.ExecuteAddOnCommand","parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},"addOnCommandParameters":p or {}}}
    req=urllib.request.Request(f"http://127.0.0.1:{port}",json.dumps(body,ensure_ascii=False).encode("utf-8"),{"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: env=json.loads(r.read())
    if not env.get("succeeded"): raise RuntimeError(f"{port}/{cmd} transport failed")
    out=env.get("result",{}).get("addOnCommandResponse",{})
    if isinstance(out,dict) and out.get("error") is not None: raise RuntimeError(f"{port}/{cmd}: {out['error']}")
    return out

def discover():
    hits=[]
    for p in range(19723,19731):
        try:
            info=call(p,"GetProjectInfo",timeout=3); path=info.get("projectPath","")
            if "SafeBIM_Global_Library_Test_Projects".lower() in path.lower():
                hits.append((p,path))
        except Exception: pass
    if not hits: raise RuntimeError("target PLN not found on Tapir ports 19723..19730")
    for p,path in hits:
        if "план типовая" in path.lower(): return p,path
    return hits[0]

def api(cmd,p=None): return call(PORT,cmd,p)
def E(g): return {"elementId":{"guid":g}}
def live_rows(): return api("GetAllElements").get("elements",[])
def live(): return {x["elementId"]["guid"].lower() for x in live_rows() if x.get("elementId",{}).get("guid")}

def detail(g):
    a=api("GetDetailsOfElements",{"elements":[E(g)]}).get("detailsOfElements",[])
    if len(a)!=1: raise RuntimeError(f"detail missing {g}")
    return a[0]

def one(res,label):
    gs=[x.get("elementId",{}).get("guid") for x in res.get("elements",[])]
    gs=[g for g in gs if g]
    if len(gs)!=1: raise RuntimeError(f"{label}: {res}")
    return gs[0]

def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")

def add(m,id_,typ,g):
    m["created"].append({"id":id_,"type":typ,"guid":g}); save(m); return g

def collect_old():
    out=set()
    if SK.is_file():
        try:
            d=json.loads(SK.read_text(encoding="utf-8-sig"))
            if d.get("slabGuid"): out.add(d["slabGuid"])
            out.update(d.get("wallGuids",[]))
        except Exception: pass
    for dn in OLD_DIRS:
        folder=BASE/dn
        if not folder.exists(): continue
        for f in folder.glob("*.json"):
            try: d=json.loads(f.read_text(encoding="utf-8-sig"))
            except Exception: continue
            if isinstance(d.get("guid"),str): out.add(d["guid"])
            for row in d.get("created",[]):
                if isinstance(row,dict) and row.get("guid"): out.add(row["guid"])
            for g in d.get("dimensionGuids",[]):
                if isinstance(g,str): out.add(g)
    if OUT.is_file():
        try:
            d=json.loads(OUT.read_text(encoding="utf-8-sig"))
            for row in d.get("created",[]):
                if row.get("guid"): out.add(row["guid"])
        except Exception: pass
    return out

def cleanup(m):
    L=live()
    targets=[g for g in collect_old() if g.lower() in L]
    priority={"Zone":0,"Text":1,"Dimension":2,"Polyline":2,"Line":2,"Arc":2,
              "Window":3,"Door":3,"Stair":4,"Slab":5,"Wall":6}
    typed=[]
    for g in targets:
        try: typ=detail(g).get("type","")
        except Exception: typ=""
        typed.append((priority.get(typ,9),typ,g))
    typed.sort()
    for _,typ,g in typed:
        if g.lower() not in live(): continue
        try: api("DeleteElements",{"elements":[E(g)]})
        except Exception:
            if g.lower() in live(): raise
        m["deleted"].append({"guid":g,"type":typ}); save(m)

def poly(points,story,weight=.45):
    return one(api("CreatePolylines",{"polylinesData":[{
      "floorInd":story,"linePenIndex":1,"penWeightMm":weight,"roomSeparator":False,
      "coordinates":[{"x":x,"y":y} for x,y in points]
    }]}),"CreatePolylines")

def line(a,b,story,weight=.35):
    return poly([a,b],story,weight)

def arc(origin,r,a1,a2,story):
    return one(api("CreateArcs",{"arcsData":[{
      "floorInd":story,"origin":{"x":origin[0],"y":origin[1]},"radius":r,
      "begAngle":a1,"endAngle":a2,"linePenIndex":1,"roomSeparator":False
    }]}),"CreateArcs")

def txt(x,y,z,story,s,h=2.5):
    return one(api("CreateTexts",{"textsData":[{
      "coordinate":{"x":x,"y":y,"z":z},"text":s,"height":h,"pen":1,
      "angle":0.0,"justification":"Center","floorIndex":story
    }]}),"CreateTexts")

def wall(a,b,story,t=.05,h=.15):
    # thin BIM frame only for associative dimensions, visually unobtrusive
    return one(api("CreateWalls",{"wallsData":[{
      "begCoordinate":{"x":a[0],"y":a[1]},"endCoordinate":{"x":b[0],"y":b[1]},
      "floorIndex":story,"zCoordinate":0.0,"height":h,"thickness":t,
      "offset":0.0,"arcAngle":0.0,"referenceLineLocation":"Center","structureType":"Basic"
    }]}),"CreateWalls")

def dim(ref,direction,story,wit):
    return one(api("CreateAssociativeDimensions",{"dimensionsData":[{
      "referencePoint":{"x":ref[0],"y":ref[1]},
      "direction":{"x":direction[0],"y":direction[1]},
      "floorIndex":story,
      "witnessPoints":[{"elementId":{"guid":g},"inIndex":idx} for g,idx in wit]
    }]}),"CreateAssociativeDimensions")

def door_symbol(x,y,orient,story,w=.80):
    # gap is already left in traced wall; draw leaf + swing only
    if orient=="N":
        addpts=[((x,y),(x,y+w)),(x,y,0,math.pi/2)]
    elif orient=="S":
        addpts=[((x,y),(x,y-w)),(x,y,-math.pi/2,0)]
    elif orient=="E":
        addpts=[((x,y),(x+w,y)),(x,y,0,math.pi/2)]
    else:
        addpts=[((x,y),(x-w,y)),(x,y,math.pi/2,math.pi)]
    lg=line(addpts[0][0],addpts[0][1],story,.30)
    ag=arc((addpts[1][0],addpts[1][1]),w,addpts[1][2],addpts[1][3],story)
    return [lg,ag]

def main():
    global PORT
    ap=argparse.ArgumentParser(); ap.add_argument("--execute",action="store_true"); args=ap.parse_args()
    PORT,path=discover()
    if not SK.is_file(): raise RuntimeError(f"missing origin manifest {SK}")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    ox=float(sk["originX"]); oy=float(sk["originY"])
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")
    sr=next(s for s in stories["stories"] if int(s["index"])==story)
    z=float(sr.get("level",0.0))

    m={"status":"DRY_RUN" if not args.execute else "IN_PROGRESS","port":PORT,"projectPath":path,
       "storyIndex":story,"mode":"EMERGENCY_SOURCE_FAITHFUL_2D","created":[],"deleted":[],
       "savedProject":False}
    if not args.execute:
        print(json.dumps(m,ensure_ascii=False,indent=2)); return
    save(m); cleanup(m)

    # Outer building outline.
    outline=[(0,0),(23.4,0),(23.4,13.2),(0,13.2),(0,0)]
    add(m,"OUTLINE","Polyline",poly([(ox+x,oy+y) for x,y in outline],story,.70))

    # Major bearing/reference walls, segmented to keep corridor and door gaps.
    segs=[
      # north apartment/stair verticals
      ((3.0,9.55),(3.0,13.2)),((6.6,9.15),(6.6,13.2)),
      ((9.6,7.8),(9.6,13.2)),((13.2,7.8),(13.2,13.2)),
      ((16.8,9.15),(16.8,13.2)),((20.4,9.55),(20.4,13.2)),
      # south verticals
      ((3.0,0),(3.0,4.95)),((6.6,0),(6.6,5.4)),
      ((9.6,0),(9.6,4.60)),((13.2,0),(13.2,5.4)),
      ((16.8,0),(16.8,5.4)),((20.4,0),(20.4,4.95)),
      # corridor boundaries / apartment fronts
      ((6.6,7.8),(9.9,7.8)),((12.7,7.8),(16.8,7.8)),
      ((6.6,5.4),(10.2,5.4)),((11.0,5.4),(13.8,5.4)),((14.6,5.4),(16.8,5.4)),
      # left north 3B service cluster
      ((0,8.95),(1.95,8.95)),((2.75,8.95),(3.0,8.95)),
      ((1.15,7.8),(1.15,8.95)),((1.15,9.65),(1.15,10.15)),
      ((0,10.15),(3.0,10.15)),
      ((3.0,10.75),(4.15,10.75)),((4.95,10.75),(6.6,10.75)),
      ((4.55,7.8),(4.55,9.25)),((4.55,10.05),(4.55,10.75)),
      ((3.0,9.55),(4.10,9.55)),((4.90,9.55),(6.6,9.55)),
      # right north symmetric
      ((20.4,8.95),(21.15,8.95)),((21.95,8.95),(23.4,8.95)),
      ((22.25,7.8),(22.25,8.95)),((22.25,9.65),(22.25,10.15)),
      ((20.4,10.15),(23.4,10.15)),
      ((16.8,10.75),(18.45,10.75)),((19.25,10.75),(20.4,10.75)),
      ((18.85,7.8),(18.85,9.25)),((18.85,10.05),(18.85,10.75)),
      ((16.8,9.55),(18.50,9.55)),((19.30,9.55),(20.4,9.55)),
      # left south service cluster
      ((0,4.15),(1.15,4.15)),((1.95,4.15),(3.0,4.15)),
      ((1.15,4.15),(1.15,5.4)),((0,4.75),(3.0,4.75)),
      ((3.0,2.45),(4.15,2.45)),((4.95,2.45),(6.6,2.45)),
      ((4.55,2.45),(4.55,3.75)),((4.55,4.55),(4.55,5.4)),
      ((3.0,4.15),(4.10,4.15)),((4.90,4.15),(6.6,4.15)),
      ((6.6,3.45),(8.0,3.45)),((8.8,3.45),(9.6,3.45)),
      ((7.4,4.35),(7.4,5.4)),
      # right south
      ((20.4,4.15),(21.45,4.15)),((22.25,4.15),(23.4,4.15)),
      ((22.25,4.15),(22.25,5.4)),((20.4,4.75),(23.4,4.75)),
      ((16.8,2.45),(18.45,2.45)),((19.25,2.45),(20.4,2.45)),
      ((18.85,2.45),(18.85,3.75)),((18.85,4.55),(18.85,5.4)),
      ((16.8,4.15),(18.45,4.15)),((19.25,4.15),(20.4,4.15)),
      ((15.95,4.35),(15.95,5.4))
    ]
    for i,(a,b) in enumerate(segs,1):
        add(m,f"WALL2D_{i:03d}","Polyline",
            line((ox+a[0],oy+a[1]),(ox+b[0],oy+b[1]),story,.60))

    # Four balconies/loggias clearly outside the facade.
    bals=[
      [(3.0,-1.25),(6.6,-1.25),(6.6,0),(3.0,0),(3.0,-1.25)],
      [(16.8,-1.25),(20.4,-1.25),(20.4,0),(16.8,0),(16.8,-1.25)],
      [(3.0,13.2),(3.0,14.45),(6.6,14.45),(6.6,13.2)],
      [(16.8,13.2),(16.8,14.45),(20.4,14.45),(20.4,13.2)]
    ]
    for i,p in enumerate(bals,1):
        add(m,f"BALCONY_{i}","Polyline",poly([(ox+x,oy+y) for x,y in p],story,.50))

    # Central stair cell, connected to corridor.
    stair=[
      ((10.20,7.80),(10.20,12.50)),((12.80,7.80),(12.80,12.50)),
      ((10.20,12.50),(12.80,12.50)),((10.20,10.15),(12.80,10.15))
    ]
    for k,(a,b) in enumerate(stair,1):
        add(m,f"STAIR_FRAME_{k}","Line",line((ox+a[0],oy+a[1]),(ox+b[0],oy+b[1]),story,.45))
    for k in range(8):
        y=8.15+k*.28
        add(m,f"STAIR_L_{k}","Line",line((ox+10.25,oy+y),(ox+11.35,oy+y),story,.25))
        add(m,f"STAIR_R_{k}","Line",line((ox+11.65,oy+y),(ox+12.75,oy+y),story,.25))

    # Door symbols at the source-style openings.
    doors=[
      (3.0,8.95,"E"),(4.55,9.55,"N"),(6.6,8.25,"E"),
      (16.8,8.25,"W"),(18.85,9.55,"N"),(20.4,8.95,"W"),
      (3.0,4.15,"E"),(4.55,4.15,"N"),(6.6,4.60,"E"),
      (9.6,5.4,"E"),(13.2,5.4,"W"),(16.8,4.60,"W"),
      (18.85,4.15,"N"),(20.4,4.15,"W"),
      (9.9,7.8,"N"),(12.7,7.8,"N")
    ]
    for i,(x,y,o) in enumerate(doors,1):
        lg,ag=door_symbol(ox+x,oy+y,o,story,.80)
        add(m,f"DOOR_LEAF_{i}","Polyline",lg); add(m,f"DOOR_ARC_{i}","Arc",ag)

    # Minimal hidden dimension frame.
    xs=[0,3,6.6,9.6,13.2,16.8,20.4,23.4]
    S=[]
    for i in range(7):
        S.append(add(m,f"DIMHOST_S{i}","Wall",wall((ox+xs[i],oy),(ox+xs[i+1],oy),story)))
    ys=[0,5.4,7.8,13.2]
    W=[]
    for i in range(3):
        W.append(add(m,f"DIMHOST_W{i}","Wall",wall((ox,oy+ys[i]),(ox,oy+ys[i+1]),story)))
    xwit=[(S[0],1),(S[0],2),(S[1],2),(S[2],2),(S[3],2),(S[4],2),(S[5],2),(S[6],2)]
    ywit=[(W[0],1),(W[0],2),(W[1],2),(W[2],2)]
    add(m,"DIM_X_CHAIN","Dimension",dim((ox,oy-1.8),(1,0),story,xwit))
    add(m,"DIM_X_TOTAL","Dimension",dim((ox,oy-2.7),(1,0),story,[xwit[0],xwit[-1]]))
    add(m,"DIM_Y_CHAIN","Dimension",dim((ox-1.8,oy),(0,1),story,ywit))
    add(m,"DIM_Y_TOTAL","Dimension",dim((ox-2.7,oy),(0,1),story,[ywit[0],ywit[-1]]))

    labels=[
      ("11,25",1.5,12.0),("8,76",4.8,12.0),("17,96",8.1,11.7),
      ("17,96",15.2,11.7),("8,76",18.7,12.0),("11,25",22.0,12.0),
      ("12,38",1.5,1.2),("8,76",4.8,1.2),("10,39",8.1,1.2),
      ("17,96",11.4,1.2),("17,96",15.0,1.2),("8,76",18.7,1.2),("12,38",22.0,1.2),
      ("6,19",11.7,6.55),
      ("3Б  41,59 / 70,87",8.25,9.75),("3Б  41,59 / 70,87",15.15,9.75),
      ("2Б  28,35 / 53,27",10.8,4.25),("1Б  17,96 / 38,43",14.55,4.25)
    ]
    for i,(s,x,y) in enumerate(labels,1):
        add(m,f"TXT_{i:02d}","Text",txt(ox+x,oy+y,z,story,s,2.4 if i<=14 else 3.0))

    m["status"]="PASS"; m["elementCountAfter"]=len(live_rows()); m["nextPhase"]="PRINT/SUBMIT"; save(m)
    try: api("FitInWindow",{})
    except Exception: pass
    print(json.dumps(m,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT)},ensure_ascii=False,indent=2))
        raise SystemExit(2)
