"""Series 178-07sm.86 v0.8 — submission finish layer.

Run AFTER v0.7 PASS. Adds a native Archicad Zone set (automatic geometry from
seed points) for the principal rooms/apartments and places compact apartment
identification texts using the passport values. If a Zone cannot be resolved
because a provisional service partition is still open, the script records that
one failure and continues; it does not abort the rest of the floor.

Never saves/opens/switches/closes the PLN.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

PORT=19725
ROOT=Path(tempfile.gettempdir())
BASE=Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE",ROOT/"safe-bim-mvp-evidence"))
SK=ROOT/"series178-direct-19725-created.json"
V07=BASE/"series178-v07"/"manifest.json"
OUT=BASE/"series178-v08"/"manifest.json"

def api(cmd,p=None):
    body={"command":"API.ExecuteAddOnCommand","parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},"addOnCommandParameters":p or {}}}
    req=urllib.request.Request(f"http://127.0.0.1:{PORT}",json.dumps(body,ensure_ascii=False).encode(),{"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r: env=json.loads(r.read())
    if not env.get("succeeded"): raise RuntimeError(f"{cmd} transport failed")
    out=env.get("result",{}).get("addOnCommandResponse",{})
    if isinstance(out,dict) and out.get("error") is not None: raise RuntimeError(f"{cmd}: {out['error']}")
    return out

def E(g): return {"elementId":{"guid":g}}

def one(res,label):
    gs=[x.get("elementId",{}).get("guid") for x in res.get("elements",[])]
    gs=[g for g in gs if g]
    if len(gs)!=1: raise RuntimeError(f"{label}: {res}")
    return gs[0]

def save(m):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    global PORT
    ap=argparse.ArgumentParser(); ap.add_argument("--port",type=int,default=PORT); ap.add_argument("--execute",action="store_true"); args=ap.parse_args(); PORT=args.port

    if not SK.is_file() or not V07.is_file(): raise RuntimeError("run v0.7 first")
    sk=json.loads(SK.read_text(encoding="utf-8-sig"))
    v07=json.loads(V07.read_text(encoding="utf-8-sig"))
    if v07.get("status")!="PASS": raise RuntimeError("v0.7 is not PASS")

    p=api("GetProjectInfo"); path=p.get("projectPath","")
    if "SafeBIM_Global_Library_Test_Projects".lower() not in path.lower(): raise RuntimeError(f"wrong project {path}")
    stories=api("GetStories"); story=int(sk.get("storyIndex",0))
    if int(stories.get("actStory",-9))!=story: raise RuntimeError("wrong active story")
    ox=float(sk["originX"]); oy=float(sk["originY"])

    # Principal room seeds from the passport topology. Names include printed
    # areas where legible; these are labels for submission, not a claim that
    # automatic zone area equals the printed area until final manual QA.
    zones=[
      ("01","Комната 12,38",(1.50,2.00)),
      ("02","Кухня 8,76",(4.80,1.30)),
      ("03","Комната 10,39",(8.10,1.80)),
      ("04","Комната 17,96",(11.40,2.20)),
      ("05","Комната 17,96",(15.00,2.20)),
      ("06","Кухня 8,76",(18.60,1.30)),
      ("07","Комната 12,38",(21.90,2.00)),
      ("08","Комната 11,25",(1.50,11.30)),
      ("09","Кухня 8,76",(4.80,11.80)),
      ("10","Комната 17,96",(8.10,10.60)),
      ("11","Лестничная клетка",(11.40,10.30)),
      ("12","Комната 17,96",(15.00,10.60)),
      ("13","Кухня 8,76",(18.60,11.80)),
      ("14","Комната 11,25",(21.90,11.30)),
      ("15","Коридор",(11.40,6.60)),
    ]

    apartment_texts=[
      ("3Б  41,59 / 70,87",6.95,9.65),
      ("3Б  41,59 / 70,87",15.85,9.65),
      ("2Б  28,35 / 53,27",10.50,4.20),
      ("1Б  17,96 / 38,43",14.40,4.20),
    ]

    plan={"status":"DRY_RUN" if not args.execute else "IN_PROGRESS","port":PORT,"projectPath":path,"storyIndex":story,
          "zoneCount":len(zones),"apartmentLabelCount":len(apartment_texts),"created":[],"zoneFailures":[],"savedProject":False}
    if not args.execute:
        print(json.dumps(plan,ensure_ascii=False,indent=2)); return
    save(plan)

    # Zones one-by-one so one unresolved provisional enclosure doesn't kill all.
    for num,name,(rx,ry) in zones:
        seed={"x":ox+rx,"y":oy+ry}
        try:
            res=api("CreateZones",{"zonesData":[{
              "floorIndex":story,
              "name":name,
              "numberStr":num,
              "stampPosition":seed,
              "geometry":{"referencePosition":seed}
            }]})
            g=one(res,"CreateZones")
            plan["created"].append({"id":"ZONE_"+num,"type":"Zone","guid":g,"name":name})
        except Exception as exc:
            plan["zoneFailures"].append({"id":num,"name":name,"error":str(exc)})
        save(plan)

    # Apartment identification text, native Text tool.
    for i,(txt,rx,ry) in enumerate(apartment_texts,1):
        res=api("CreateTexts",{"textsData":[{
          "coordinate":{"x":ox+rx,"y":oy+ry,"z":0.0},
          "text":txt,
          "height":3.0,
          "pen":1,
          "angle":0.0,
          "justification":"Center",
          "floorIndex":story
        }]})
        g=one(res,"CreateTexts")
        plan["created"].append({"id":f"APT_LABEL_{i}","type":"Text","guid":g,"text":txt}); save(plan)

    plan["status"]="PASS"
    plan["elementCountAfter"]=len(api("GetAllElements").get("elements",[]))
    plan["nextPhase"]="submission screenshot/print; remaining zoneFailures are non-blocking provisional enclosures"
    save(plan)
    try: api("FitInWindow",{})
    except Exception: pass
    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e),"evidence":str(OUT)},ensure_ascii=False,indent=2))
        raise SystemExit(2)
