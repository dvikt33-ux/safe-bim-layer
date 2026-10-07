"""Convert the emergency Series-178 2D trace into REAL Archicad walls.

Keeps the already-created dimensions/text/door symbols/stair graphics, removes only
our visible 2D wall polylines, and replaces them with BIM Walls.
Never opens/switches/saves/closes the PLN.
"""
from __future__ import annotations
import json, os, tempfile, urllib.request
from pathlib import Path

ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", ROOT/"safe-bim-mvp-evidence"))
SRC = BASE/"series178-EMERGENCY-2D"/"manifest.json"
OUT = BASE/"series178-EMERGENCY-BIM-WALLS"/"manifest.json"
SK = ROOT/"series178-direct-19725-created.json"
PORT = None

def call(port, cmd, p=None, timeout=90):
    body={"command":"API.ExecuteAddOnCommand","parameters":{
        "addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},
        "addOnCommandParameters":p or {}}}
    req=urllib.request.Request(
        f"http://127.0.0.1:{port}",
        json.dumps(body,ensure_ascii=False).encode("utf-8"),
        {"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
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
def live():
    return {x["elementId"]["guid"].lower() for x in api("GetAllElements").get("elements",[])
            if x.get("elementId",{}).get("guid")}

def one(res,label):
    gs=[x.get("elementId",{}).get("guid") for x in res.get("elements",[])]
    gs=[g for g in gs if g]
    if len(gs)!=1:
        raise RuntimeError(f"{label}: {res}")
    return gs[0]

def wall(a,b,story,t,h=2.84):
    return one(api("CreateWalls",{"wallsData":[{
        "begCoordinate":{"x":a[0],"y":a[1]},
        "endCoordinate":{"x":b[0],"y":b[1]},
        "floorIndex":story,
        "zCoordinate":0.0,
        "height":h,
        "thickness":t,
        "offset":0.0,
        "arcAngle":0.0,
        "referenceLineLocation":"Center",
        "structureType":"Basic"
    }]}),"CreateWalls")

def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")

def delete_guid(g):
    if g and g.lower() in live():
        api("DeleteElements",{"elements":[E(g)]})

def main():
    global PORT
    PORT,path=discover()
    if not SRC.is_file():
        raise RuntimeError(f"2D manifest not found: {SRC}")
    if not SK.is_file():
        raise RuntimeError(f"origin manifest not found: {SK}")

    src=json.loads(SRC.read_text(encoding="utf-8-sig"))
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    ox=float(sk["originX"]); oy=float(sk["originY"])
    story=int(sk.get("storyIndex",0))

    stories=api("GetStories")
    if int(stories.get("actStory",-999)) != story:
        raise RuntimeError(f"active story is {stories.get('actStory')}, expected {story}")

    m={"status":"IN_PROGRESS","port":PORT,"projectPath":path,"storyIndex":story,
       "created":[],"deleted2D":[],"savedProject":False}
    save(m)

    # Remove walls created by an earlier run of this converter.
    if OUT.is_file():
        try:
            prev=json.loads(OUT.read_text(encoding="utf-8-sig"))
            for row in prev.get("created",[]):
                g=row.get("guid")
                if g:
                    delete_guid(g)
        except Exception:
            pass

    # Remove ONLY the visible fake 2D walls from the previous emergency plan.
    # Keep door swings, stair graphics, texts, dimensions and balcony outlines.
    for row in src.get("created",[]):
        rid=str(row.get("id",""))
        if rid=="OUTLINE" or rid.startswith("WALL2D_"):
            g=row.get("guid")
            if g and g.lower() in live():
                delete_guid(g)
                m["deleted2D"].append({"id":rid,"guid":g})
                save(m)

    def A(p): return (ox+p[0],oy+p[1])
    def add_wall(id_,a,b,t,kind):
        g=wall(A(a),A(b),story,t)
        m["created"].append({"id":id_,"guid":g,"type":"Wall","kind":kind,"thickness":t})
        save(m)
        return g

    # External walls: 350 mm provisional reconstruction.
    ext=[
      ((0,0),(23.4,0)),((23.4,0),(23.4,13.2)),
      ((23.4,13.2),(0,13.2)),((0,13.2),(0,0))
    ]
    for i,(a,b) in enumerate(ext,1):
        add_wall(f"EXT_{i}",a,b,0.35,"external")

    # Main structural / apartment-separating walls: 160 mm provisional.
    bearing=[
      ((3.0,9.55),(3.0,13.2)),((6.6,9.15),(6.6,13.2)),
      ((9.6,7.8),(9.6,13.2)),((13.2,7.8),(13.2,13.2)),
      ((16.8,9.15),(16.8,13.2)),((20.4,9.55),(20.4,13.2)),
      ((3.0,0),(3.0,4.95)),((6.6,0),(6.6,5.4)),
      ((9.6,0),(9.6,4.60)),((13.2,0),(13.2,5.4)),
      ((16.8,0),(16.8,5.4)),((20.4,0),(20.4,4.95)),
      ((6.6,7.8),(9.9,7.8)),((12.7,7.8),(16.8,7.8)),
      ((6.6,5.4),(10.2,5.4)),((11.0,5.4),(13.8,5.4)),((14.6,5.4),(16.8,5.4)),
      # stair enclosure
      ((10.2,7.8),(10.2,12.5)),((12.8,7.8),(12.8,12.5)),((10.2,12.5),(12.8,12.5))
    ]
    for i,(a,b) in enumerate(bearing,1):
        add_wall(f"BEARING_{i:02d}",a,b,0.16,"bearing")

    # Apartment partitions: 80 mm provisional.
    parts=[
      # left north
      ((0,8.95),(1.95,8.95)),((2.75,8.95),(3.0,8.95)),
      ((1.15,7.8),(1.15,8.95)),((1.15,9.65),(1.15,10.15)),
      ((0,10.15),(3.0,10.15)),
      ((3.0,10.75),(4.15,10.75)),((4.95,10.75),(6.6,10.75)),
      ((4.55,7.8),(4.55,9.25)),((4.55,10.05),(4.55,10.75)),
      ((3.0,9.55),(4.10,9.55)),((4.90,9.55),(6.6,9.55)),
      # right north
      ((20.4,8.95),(21.15,8.95)),((21.95,8.95),(23.4,8.95)),
      ((22.25,7.8),(22.25,8.95)),((22.25,9.65),(22.25,10.15)),
      ((20.4,10.15),(23.4,10.15)),
      ((16.8,10.75),(18.45,10.75)),((19.25,10.75),(20.4,10.75)),
      ((18.85,7.8),(18.85,9.25)),((18.85,10.05),(18.85,10.75)),
      ((16.8,9.55),(18.50,9.55)),((19.30,9.55),(20.4,9.55)),
      # left south
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
    for i,(a,b) in enumerate(parts,1):
        add_wall(f"PART_{i:02d}",a,b,0.08,"partition")

    m["status"]="PASS"
    m["wallCount"]=len(m["created"])
    m["note"]="REAL Archicad Walls: ext 350mm / bearing 160mm / partitions 80mm (provisional)"
    save(m)
    try:
        api("FitInWindow",{})
    except Exception:
        pass
    print(json.dumps(m,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT)},ensure_ascii=False,indent=2))
        raise SystemExit(2)
