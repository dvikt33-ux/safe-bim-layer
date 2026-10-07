"""Series 178 v0.6: put verified control dimensions on plan, then clean provisional junk.

Order is deliberate:
1) create visible control dimension graphics from the passport's verified grid;
2) only after the dimensions are present, delete provisional v0.3/v0.4/v0.5
   room partitions and internal doors;
3) preserve the bearing-wall topology, stair, facade windows/doors and balconies.

Dimensions are native Archicad Line + Text elements for reliability on this
Tapir build. They are control annotations, not associative Dimension elements.
Verified values:
X = 3000+3600+3000+3600+3600+3600+3000 = 23400 mm
Y = 5400+2400+5400 = 13200 mm

Never opens/switches/saves/closes the PLN.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

PORT = 19725
ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", ROOT/"safe-bim-mvp-evidence"))
SK = ROOT/"series178-direct-19725-created.json"
V03 = BASE/"series178-v03"/"manifest.json"
V04 = BASE/"series178-v04"/"manifest.json"
V05 = BASE/"series178-v05"/"manifest.json"
OUT = BASE/"series178-v06"/"manifest.json"

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

def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")

def guids_from(res):
    out=[]
    for x in res.get("elements",[]):
        g=x.get("elementId",{}).get("guid")
        if g: out.append(g)
    return out

def line(a,b,story):
    return {
      "floorInd":story,
      "begCoordinate":{"x":a[0],"y":a[1]},
      "endCoordinate":{"x":b[0],"y":b[1]},
      "linePenIndex":1
    }

def text_at(x,y,z,story,text,angle=0.0):
    return {
      "coordinate":{"x":x,"y":y,"z":z},
      "text":str(text),
      "height":2.5,
      "pen":1,
      "angle":angle,
      "justification":"Center",
      "floorIndex":story
    }

def main():
    global PORT
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=PORT)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args(); PORT=args.port

    for p in (SK,V03,V04,V05):
        if not p.is_file(): raise RuntimeError(f"missing required manifest: {p}")

    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    v03=json.loads(V03.read_text(encoding="utf-8-sig"))
    v04=json.loads(V04.read_text(encoding="utf-8-sig"))
    v05=json.loads(V05.read_text(encoding="utf-8-sig"))

    project=api("GetProjectInfo"); path=project.get("projectPath","")
    if "SafeBIM_Global_Library_Test_Projects".lower() not in path.lower():
        raise RuntimeError(f"wrong project {path}")

    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")
    srow=next(s for s in stories["stories"] if int(s["index"])==story)
    z=float(srow.get("level",0.0))
    ox=float(sk["originX"]); oy=float(sk["originY"])
    L=live()

    if OUT.is_file():
        old=json.loads(OUT.read_text(encoding="utf-8-sig"))
        if old.get("status")=="PASS" and any(g.lower() in L for g in old.get("dimensionGuids",[])):
            raise RuntimeError("v0.6 already present")

    # Exact verified modular coordinates from the passport.
    xs=[0.0,3.0,6.6,9.6,13.2,16.8,20.4,23.4]
    xlabels=[3000,3600,3000,3600,3600,3600,3000]
    ys=[0.0,5.4,7.8,13.2]
    ylabels=[5400,2400,5400]

    # Cleanup targets: remove only geometry explicitly introduced as provisional
    # room/detail work. Preserve facade openings, balcony doors/slabs, stair and
    # the v0.5 split bearing-wall segments.
    cleanup=[]
    for x in v04.get("created",[]):
        if x.get("type") in ("Wall","Door"):
            cleanup.append({"source":"v04","id":x.get("id"),"guid":x.get("guid")})
    for x in v05.get("created",[]):
        if x.get("type")=="Door":
            cleanup.append({"source":"v05","id":x.get("id"),"guid":x.get("guid")})
    for x in v03.get("created",[]):
        if x.get("id") in ("D_2B","D_1B","D_3B_L","D_3B_R"):
            cleanup.append({"source":"v03","id":x.get("id"),"guid":x.get("guid")})

    # Deduplicate by GUID.
    seen=set(); dedup=[]
    for x in cleanup:
        g=(x.get("guid") or "").lower()
        if g and g not in seen:
            seen.add(g); dedup.append(x)
    cleanup=dedup

    plan={
      "status":"DRY_RUN" if not args.execute else "IN_PROGRESS",
      "port":PORT,"projectPath":path,"storyIndex":story,
      "dimensions":{
        "xSegmentsMm":xlabels,"xOverallMm":23400,
        "ySegmentsMm":ylabels,"yOverallMm":13200,
        "method":"native Line + Text control annotations"
      },
      "cleanupTargets":cleanup,
      "dimensionGuids":[],
      "deleted":[],
      "skippedMissing":[],
      "savedProject":False
    }
    if not args.execute:
        print(json.dumps(plan,ensure_ascii=False,indent=2)); return
    save(plan)

    # ----- 1. DIMENSIONS FIRST -----
    lines=[]
    texts=[]

    # Bottom modular chain and extension lines; below 1.2 m balconies.
    ydim=oy-2.00
    yoverall=oy-2.80
    tick=.12
    for xv in xs:
        x=ox+xv
        lines.append(line((x,oy-1.25),(x,yoverall-.15),story))
        lines.append(line((x-tick,ydim),(x+tick,ydim),story))
        lines.append(line((x-tick,yoverall),(x+tick,yoverall),story))
    lines.append(line((ox+xs[0],ydim),(ox+xs[-1],ydim),story))
    lines.append(line((ox+xs[0],yoverall),(ox+xs[-1],yoverall),story))
    for i,val in enumerate(xlabels):
        xm=ox+(xs[i]+xs[i+1])/2
        texts.append(text_at(xm,ydim-.18,z,story,val))
    texts.append(text_at(ox+23.4/2,yoverall-.18,z,story,23400))

    # Left vertical modular chain.
    xdim=ox-2.00
    xoverall=ox-2.80
    for yv in ys:
        y=oy+yv
        lines.append(line((ox-.15,y),(xoverall-.15,y),story))
        lines.append(line((xdim,y-tick),(xdim,y+tick),story))
        lines.append(line((xoverall,y-tick),(xoverall,y+tick),story))
    lines.append(line((xdim,oy+ys[0]),(xdim,oy+ys[-1]),story))
    lines.append(line((xoverall,oy+ys[0]),(xoverall,oy+ys[-1]),story))
    for i,val in enumerate(ylabels):
        ym=oy+(ys[i]+ys[i+1])/2
        texts.append(text_at(xdim-.18,ym,z,story,val,1.57079632679))
    texts.append(text_at(xoverall-.18,oy+13.2/2,z,story,13200,1.57079632679))

    lr=api("CreateLineElements",{"linesData":lines})
    lg=guids_from(lr)
    if len(lg)!=len(lines):
        raise RuntimeError(f"dimension lines incomplete: {len(lg)}/{len(lines)}")
    plan["dimensionGuids"].extend(lg); save(plan)

    tr=api("CreateTexts",{"textsData":texts})
    tg=guids_from(tr)
    if len(tg)!=len(texts):
        raise RuntimeError(f"dimension texts incomplete: {len(tg)}/{len(texts)}")
    plan["dimensionGuids"].extend(tg); save(plan)

    # ----- 2. CLEAN PROVISIONAL JUNK AFTER DIMENSIONS EXIST -----
    for x in cleanup:
        g=x["guid"]
        current=live()
        if g.lower() not in current:
            plan["skippedMissing"].append(x); save(plan); continue
        api("DeleteElements",{"elements":[E(g)]})
        if g.lower() in live():
            raise RuntimeError(f"delete failed: {x}")
        plan["deleted"].append(x); save(plan)

    plan["status"]="PASS"
    plan["elementCountAfter"]=len(live())
    plan["nextPhase"]="rebuild rooms from dimensioned plan, not from guessed areas"
    save(plan)

    try:
        api("FitInWindow",{})
    except Exception:
        pass

    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
          "status":"BLOCKED","error":str(e),"evidence":str(OUT),
          "note":"dimensions are created before cleanup; do not blindly rerun"
        },ensure_ascii=False,indent=2))
        raise SystemExit(2)
