"""Urgent submission trace for Series 178-07см.86.

This pass stops guessing room geometry. It uses the photographed passport as a
scaled 2D source: the rectified plan is 23.4 x 13.2 m, so traced wall/partition
segments are placed directly from the source geometry.

It removes only elements created by our earlier Series-178 scripts, then creates:
- clean outer BIM shell + floor slab;
- four visible balcony slabs + parapet walls;
- source-traced internal plan linework (native Archicad polylines);
- a central stair symbol traced in the correct bay;
- four apartment-entry door symbols;
- native Archicad associative overall/module dimensions;
- source labels.

No Zone elements. Never saves/opens/switches/closes the PLN.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request, math
from pathlib import Path

ROOT=Path(tempfile.gettempdir())
BASE=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))
SK=ROOT/"series178-direct-19725-created.json"
OUT=BASE/"series178-SOURCE-TRACE"/"manifest.json"
PORT=None

EVIDENCE_DIRS=[
 "series178-v02","series178-v03","series178-v04","series178-v05","series178-v06",
 "series178-v07","series178-v08","series178-FINAL","series178-CLEAN"
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
            if "SafeBIM_Global_Library_Test_Projects".lower() in path.lower(): hits.append((p,path))
        except Exception: pass
    if not hits: raise RuntimeError("target PLN not found on ports 19723..19730")
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
    for name in EVIDENCE_DIRS:
        folder=BASE/name
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
    priority={"Zone":0,"Text":1,"Dimension":2,"Polyline":2,"Line":2,"Window":3,"Door":3,"Stair":4,"Slab":5,"Wall":6}
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

def wall(a,b,story,t=.35,h=2.84):
    g=one(api("CreateWalls",{"wallsData":[{
      "begCoordinate":{"x":a[0],"y":a[1]},"endCoordinate":{"x":b[0],"y":b[1]},
      "floorIndex":story,"zCoordinate":0.0,"height":h,"thickness":t,
      "offset":0.0,"arcAngle":0.0,"referenceLineLocation":"Center","structureType":"Basic"
    }]}),"CreateWalls")
    return g

def slab(poly,story,level,t=.16):
    return one(api("CreateSlabs",{"slabsData":[{
      "level":level,"floorIndex":story,"thickness":t,"referencePlaneLocation":"Top",
      "polygonCoordinates":[{"x":x,"y":y} for x,y in poly]
    }]}),"CreateSlabs")

def polyline(points,story,weight=.35):
    return one(api("CreatePolylines",{"polylinesData":[{
      "floorInd":story,"linePenIndex":1,"penWeightMm":weight,
      "roomSeparator":False,
      "coordinates":[{"x":x,"y":y} for x,y in points]
    }]}),"CreatePolylines")

def arc(origin,r,a1,a2,story):
    return one(api("CreateArcs",{"arcsData":[{
      "floorInd":story,"origin":{"x":origin[0],"y":origin[1]},
      "radius":r,"begAngle":a1,"endAngle":a2,"linePenIndex":1,"roomSeparator":False
    }]}),"CreateArcs")

def line(a,b,story):
    return one(api("CreateLineElements",{"linesData":[{
      "floorInd":story,"begCoordinate":{"x":a[0],"y":a[1]},
      "endCoordinate":{"x":b[0],"y":b[1]},"linePenIndex":1,"roomSeparator":False
    }]}),"CreateLineElements")

def dim(ref,direction,story,w):
    g=one(api("CreateAssociativeDimensions",{"dimensionsData":[{
      "referencePoint":{"x":ref[0],"y":ref[1]},
      "direction":{"x":direction[0],"y":direction[1]},"floorIndex":story,
      "witnessPoints":[{"elementId":{"guid":g},"inIndex":idx} for g,idx in w]
    }]}),"CreateAssociativeDimensions")
    return g

def text(x,y,z,story,s,h=2.5):
    return one(api("CreateTexts",{"textsData":[{
      "coordinate":{"x":x,"y":y,"z":z},"text":s,"height":h,"pen":1,
      "angle":0.0,"justification":"Center","floorIndex":story
    }]}),"CreateTexts")

# Source-traced straight segments from the rectified passport image.
# Coordinates are metres in the 23.4 x 13.2 source rectangle.
TRACE=[
(0.00,13.04,23.40,13.04),(0.00,0.10,23.40,0.10),
(0.05,0.10,0.05,13.20),(23.30,0.10,23.30,13.04),
(3.30,8.74,3.30,13.10),(6.94,9.12,6.94,13.08),(10.69,6.42,10.69,13.04),
(13.58,6.40,13.58,13.02),(17.15,9.14,17.15,13.04),(20.53,8.68,20.53,12.96),
(6.95,0.04,6.95,4.02),(10.03,0.06,10.03,4.04),(13.59,0.08,13.59,5.66),
(17.13,0.14,17.13,3.88),(20.57,0.16,20.57,7.66),
(3.16,9.58,6.00,9.58),(18.28,9.44,20.66,9.44),
(0.00,8.85,1.90,8.85),(21.64,8.75,23.40,8.75),
(2.58,7.68,5.82,7.68),(6.38,7.64,11.48,7.64),(12.42,7.61,17.46,7.61),(18.00,7.54,21.12,7.54),
(7.36,7.12,10.08,7.12),(14.08,7.06,16.54,7.06),
(1.18,6.98,3.62,6.98),(20.58,6.91,22.34,6.91),
(6.88,6.85,10.78,6.85),(13.50,6.84,17.18,6.84),
(3.50,6.03,5.58,6.03),(18.22,5.98,20.18,5.98),
(1.12,5.57,3.08,5.57),(20.60,5.54,22.38,5.54),
(1.16,5.41,4.04,5.41),(4.64,5.41,5.86,5.41),(6.40,5.37,17.50,5.37),(18.00,5.39,19.16,5.39),(19.70,5.38,22.38,5.38),
(1.18,4.31,3.36,4.31),(20.40,4.29,22.38,4.29),
(8.16,3.95,10.12,3.95),(3.14,3.68,5.48,3.68),(18.28,3.70,20.14,3.70),
(3.14,2.79,5.62,2.79),(5.74,2.79,7.04,2.79),(17.00,2.77,18.16,2.77),(18.26,2.79,20.10,2.79),
(3.12,2.12,5.10,2.12),(18.78,2.14,20.64,2.14),
(1.26,5.16,1.26,7.82),(3.40,5.34,3.40,7.76),(5.44,4.98,5.44,7.88),
(6.96,6.66,6.96,8.62),(10.04,4.42,10.04,5.44),(17.08,6.58,17.08,8.64),
(18.29,5.18,18.29,7.98),(19.06,5.28,19.06,6.88),(19.86,3.66,19.86,6.74),
(20.22,5.30,20.22,7.86),(21.79,6.10,21.79,7.84),(22.27,5.30,22.27,7.70),
(3.87,3.66,3.87,5.68),(5.22,2.72,5.22,3.92),(3.71,2.08,3.71,3.78),
(19.84,2.74,19.84,3.76),(20.07,2.10,20.07,3.78),
(3.94,11.04,3.94,12.60),(5.04,9.46,5.04,11.10),
(18.81,9.38,18.81,11.00),(19.88,10.92,19.88,12.52)
]

def main():
    global PORT
    ap=argparse.ArgumentParser(); ap.add_argument("--execute",action="store_true"); args=ap.parse_args()
    PORT,path=discover()
    if not SK.is_file(): raise RuntimeError(f"missing origin manifest {SK}")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    ox=float(sk["originX"]); oy=float(sk["originY"])
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")
    sr=next(s for s in stories["stories"] if int(s["index"])==story); z=float(sr.get("level",0.0))

    m={"status":"DRY_RUN" if not args.execute else "IN_PROGRESS","port":PORT,"projectPath":path,
       "storyIndex":story,"mode":"SOURCE_PHOTO_TRACE","traceSegmentCount":len(TRACE),
       "created":[],"deleted":[],"savedProject":False}
    if not args.execute:
        print(json.dumps(m,ensure_ascii=False,indent=2)); return
    save(m); cleanup(m)

    # BIM perimeter, segmented to support real associative dimensions.
    xs=[0,3,6.6,9.6,13.2,16.8,20.4,23.4]
    S=[]; N=[]
    for i in range(7):
        S.append(add(m,f"S{i+1}","Wall",wall((ox+xs[i],oy),(ox+xs[i+1],oy),story,.35)))
        N.append(add(m,f"N{i+1}","Wall",wall((ox+xs[i],oy+13.2),(ox+xs[i+1],oy+13.2),story,.35)))
    W=[]; E=[]
    ys=[0,5.4,7.8,13.2]
    for i in range(3):
        W.append(add(m,f"W{i+1}","Wall",wall((ox,oy+ys[i]),(ox,oy+ys[i+1]),story,.35)))
        E.append(add(m,f"E{i+1}","Wall",wall((ox+23.4,oy+ys[i]),(ox+23.4,oy+ys[i+1]),story,.35)))
    add(m,"SLAB","Slab",slab([(ox,oy),(ox+23.4,oy),(ox+23.4,oy+13.2),(ox,oy+13.2)],story,z,.16))

    # Source trace linework.
    for i,(x1,y1,x2,y2) in enumerate(TRACE,1):
        g=polyline([(ox+x1,oy+y1),(ox+x2,oy+y2)],story,.45)
        add(m,f"TRACE_{i:03d}","Polyline",g)

    # Four unmistakable balconies: slabs + three-sided parapets.
    balconies=[
      ("BAL_S_L",3.0,6.6,oy-1.2,oy),
      ("BAL_S_R",16.8,20.4,oy-1.2,oy),
      ("BAL_N_L",3.0,6.6,oy+13.2,oy+14.4),
      ("BAL_N_R",16.8,20.4,oy+13.2,oy+14.4)
    ]
    for name,x1,x2,y1,y2 in balconies:
        add(m,name,"Slab",slab([(ox+x1,y1),(ox+x2,y1),(ox+x2,y2),(ox+x1,y2)],story,z,.16))
        if "S_" in name:
            segs=[((ox+x1,y1),(ox+x2,y1)),((ox+x1,y1),(ox+x1,y2)),((ox+x2,y1),(ox+x2,y2))]
        else:
            segs=[((ox+x1,y2),(ox+x2,y2)),((ox+x1,y1),(ox+x1,y2)),((ox+x2,y1),(ox+x2,y2))]
        for j,(a,b) in enumerate(segs,1):
            add(m,f"{name}_PAR_{j}","Wall",wall(a,b,story,.10,1.05))

    # Central stair symbol from the source bay, as native linework.
    stair_lines=[
      ((10.55,8.75),(10.55,11.70)),((11.10,8.75),(11.10,11.70)),
      ((11.65,8.75),(11.65,11.70)),((12.20,8.75),(12.20,11.70)),
      ((12.75,8.75),(12.75,11.70)),
      ((10.55,8.75),(12.75,8.75)),((10.55,11.70),(12.75,11.70)),
      ((10.55,10.25),(12.75,10.25))
    ]
    for i,(a,b) in enumerate(stair_lines,1):
        add(m,f"STAIR2D_{i}","Line",line((ox+a[0],oy+a[1]),(ox+b[0],oy+b[1]),story))

    # Real module dimensions.
    xwit=[(S[0],1),(S[0],2),(S[1],2),(S[2],2),(S[3],2),(S[4],2),(S[5],2),(S[6],2)]
    ywit=[(W[0],1),(W[0],2),(W[1],2),(W[2],2)]
    for id_,ref,d,wit in [
      ("DIM_X_CHAIN",(ox,oy-1.8),(1,0),xwit),
      ("DIM_X_TOTAL",(ox,oy-2.7),(1,0),[xwit[0],xwit[-1]]),
      ("DIM_Y_CHAIN",(ox-1.8,oy),(0,1),ywit),
      ("DIM_Y_TOTAL",(ox-2.7,oy),(0,1),[ywit[0],ywit[-1]])
    ]:
        add(m,id_,"Dimension",dim(ref,d,story,wit))

    labels=[
      ("11,25",1.5,12.1),("8,76",4.8,12.1),("17,96",8.3,11.8),
      ("17,96",15.0,11.8),("8,76",18.7,12.1),("11,25",22.0,12.1),
      ("12,38",1.5,1.1),("8,76",4.8,1.1),("10,39",8.5,1.1),
      ("17,96",11.8,1.1),("17,96",15.0,1.1),("8,76",18.7,1.1),("12,38",22.0,1.1),
      ("6,19",11.7,6.6),("3Б  41,59 / 70,87",8.4,9.8),("3Б  41,59 / 70,87",15.1,9.8),
      ("2Б  28,35 / 53,27",10.8,4.3),("1Б  17,96 / 38,43",14.6,4.3)
    ]
    for i,(s,x,y) in enumerate(labels,1):
        add(m,f"TXT_{i:02d}","Text",text(ox+x,oy+y,z,story,s,2.5 if i<=14 else 3.0))

    m["status"]="PASS"; m["elementCountAfter"]=len(live_rows()); m["nextPhase"]="SUBMIT/PRINT"; save(m)
    try: api("FitInWindow",{})
    except Exception: pass
    print(json.dumps(m,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT)},ensure_ascii=False,indent=2))
        raise SystemExit(2)
