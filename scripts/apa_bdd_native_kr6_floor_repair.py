#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KR-6 source-based repair of the existing BDD house native floor model.

Target: Archicad 29 build 5101, Tapir 1.5.x, port 19727, ONLY the
already-built working PLN. Never opens/saves/modifies the original PLN.

Repairs the 48 existing timber joist beams' elevation and 3 existing
native slab thickness/levels by GUID. No creation or deletion.
Creates a full byte-for-byte backup of the saved working PLN before writes.
Writes journal before and after each call. --apply required for any BIM write.
Publishes result/failure automatically when --publish is requested.

CAUTION: Surface/material assignments are NOT calibrated in this stage.
The KR-6 floor consists of CSP 22mm, screed 58mm, and finished layer 20mm;
this stage converts the existing floor slab into the 22mm base layer and
terrace slabs to 50mm. The 58/20mm upper layers will be added separately
after verifying this phase.
"""
from __future__ import annotations
import argparse,base64,collections,datetime,hashlib,json,math,pathlib,shutil,subprocess,sys,tempfile,urllib.request,uuid

PORT=19727
SOURCE=pathlib.Path("C:/LocalAI/SafeBIM_Global_Library_Test_Projects/BDD \u0434\u043e\u043c .pln")
TARGET=SOURCE.with_name("BDD \u0434\u043e\u043c - \u043f\u043e \u0447\u0435\u0440\u0442\u0435\u0436\u0430\u043c 2022.pln")
BASE=pathlib.Path(tempfile.gettempdir())/"APA_BDD_House_Construction"
CORE_MANIFEST=BASE/"house_native_manifest.json"
THIS_JOURNAL=BASE/"kr6_floor_correction.json"
BACKUP=TARGET.with_suffix(".before-KR6-floor-correction.pln")
READ_CMDS={"GetProjectInfo","GetAllElements","GetDetailsOfElements","Get3DBoundingBoxes"}
WRITE_CMDS={"ModifyBeams","ModifySlabs","SaveProject"}
CORE_STATUS="NATIVE_STRUCTURAL_CORE_SAVED__ROOF_AND_OPENINGS_PROVISIONAL"

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda:file.read(2**20),b""):h.update(chunk)
    return h.hexdigest()

def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".writing.tmp")
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(path)

def api(command,parameters=None,*,write=False):
    allowed=WRITE_CMDS if write else READ_CMDS
    if command not in allowed:
        raise RuntimeError("COMMAND_FENCE: %s write=%s"%(command,write))
    payload={"command":"API.ExecuteAddOnCommand","parameters":{
        "addOnCommandId":{"commandNamespace":"TapirCommand","commandName":command},
        "addOnCommandParameters":parameters or {}}}
    req=urllib.request.Request("http://127.0.0.1:%d"%PORT,
        json.dumps(payload,ensure_ascii=False).encode("utf-8"),
        {"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=150) as response:
        e=json.load(response)
    if e.get("succeeded") is not True:
        raise RuntimeError("%s transport error %r"%(command,e.get("error")))
    result=e.get("result",{}).get("addOnCommandResponse",{})
    if not isinstance(result,dict) or result.get("error") is not None:
        raise RuntimeError("%s failed with response %r"%(command,str(result)[:300]))
    return result

def assert_target():
    from archicad import ACConnection
    c=ACConnection.connect(PORT)
    if c is None:raise RuntimeError("Archicad not connected on 19727")
    product=c.commands.GetProductInfo()
    if int(product[0])!=29 or int(product[1])!=5101:
        raise RuntimeError("Wrong Archicad version/build %r"%(product,))
    proj=api("GetProjectInfo")
    path=proj.get("projectPath") or proj.get("projectLocation") or ""
    if path.casefold()!=str(TARGET).casefold() or proj.get("isUntitled") or proj.get("isTeamwork"):
        raise RuntimeError("Wrong active project %r"%path)
    return proj

def guid_map():
    elements=api("GetAllElements").get("elements",None)
    if not isinstance(elements,list):raise RuntimeError("No elements list")
    out={}
    for e in elements:
        g=(e.get("elementId") or {}).get("guid") or e.get("guid")
        if not isinstance(g,str) or not g or g.lower() in out:
            raise RuntimeError("Duplicate/missing native element GUID")
        out[g.lower()]=g
    return out

def read_details(guids):
    out={}
    for start in range(0,len(guids),12):
        g=guids[start:start+12]
        payload={"elements":[{"elementId":{"guid":x}} for x in g]}
        ds=api("GetDetailsOfElements",payload).get("detailsOfElements")
        bs=api("Get3DBoundingBoxes",payload).get("boundingBoxes3D")
        if not isinstance(ds,list) or not isinstance(bs,list) or len(ds)!=len(g) or len(bs)!=len(g):
            raise RuntimeError("Native detail/bbox array mismatch")
        for k,d,b in zip(g,ds,bs):
            bbox=b.get("boundingBox3D") if isinstance(b,dict) else None
            if not isinstance(d,dict) or not isinstance(d.get("details"),dict):
                raise RuntimeError("No native details for %s"%k)
            if not isinstance(bbox,dict) or any(abs(bbox.get(v,1e35))>1e5 for v in
                    ("xMin","xMax","yMin","yMax","zMin","zMax")):
                raise RuntimeError("Invalid native 3D bbox for %s"%k)
            out[k.lower()]={"type":d.get("type"),"details":d["details"],"bbox":bbox}
    return out

def near(v,expected,tol=0.008):
    return isinstance(v,(int,float)) and math.isfinite(v) and abs(v-expected)<=tol

def expected_journal():
    if not CORE_MANIFEST.is_file():
        raise RuntimeError("Core builder manifest missing")
    m=json.loads(CORE_MANIFEST.read_text(encoding="utf-8"))
    if m.get("status")!=CORE_STATUS or m.get("inFlight"):
        raise RuntimeError("Core build not completed")
    groups=collections.defaultdict(list)
    for stage in m.get("stages",[]):
        groups[stage.get("phase")].extend(stage.get("primaryGuids",[]))
    joists=groups.get("Timber joists nominal @ 600 mm",[])
    floor=groups.get("Floor sheathing",[])
    terraces=groups.get("Terrace platforms",[])
    if (len(joists),len(floor),len(terraces))!=(48,1,2):
        raise RuntimeError("Unexpected joist/floor/terrace GUID groups")
    all_ids={g.lower() for g in m.get("initialGUIDs",[])}
    primary={g.lower() for x in m.get("stages",[]) for g in x.get("primaryGuids",[])}
    children={g.lower() for x in m.get("stages",[]) for g in x.get("autoChildGuids",[])}
    if (len(all_ids),len(primary),len(children))!=(21,125,115):
        raise RuntimeError("Core GUID manifest not 21+125+115")
    if len(primary|children|all_ids)!=261:
        raise RuntimeError("Duplicate across native core GUID sets")
    return m,groups,primary|children|all_ids

def exact_inputs(rows,groups):
    joists={g.lower() for g in groups["Timber joists nominal @ 600 mm"]}
    floor={g.lower() for g in groups["Floor sheathing"]}
    terraces={g.lower() for g in groups["Terrace platforms"]}
    for g in joists:
        d=rows[g]["details"];b=rows[g]["bbox"]
        if rows[g]["type"]!="Beam" or not all(near(d.get(k),v) for k,v in
                (("width",.1),("height",.2),("level",-.3))):
            raise RuntimeError("Unexpected timber joist parameters at "+g)
        if not near(b["zMin"],-.5) or not near(b["zMax"],-.3):
            raise RuntimeError("Unexpected timber joist bbox "+g)
    for g in floor|terraces:
        d=rows[g]["details"];b=rows[g]["bbox"]
        z=0 if g in floor else -.05
        if (rows[g]["type"]!="Slab" or d.get("structureType")!="Composite"
            or not near(d.get("thickness"),.3) or not near(d.get("zCoordinate"),z)
            or not near(b["zMin"],z-.3) or not near(b["zMax"],z)):
            raise RuntimeError("Slab changed since audited, refuse: "+g)

def publish(path):
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest=("safe-bim-mailbox/gpt-live/results/"
          "apa-bdd-kr6-floor-repair-%s-%s.json"%(stamp,uuid.uuid4().hex[:8]))
    body={"branch":"main","message":"BDD house KR-6 native floor geometry correction journal",
          "content":base64.b64encode(path.read_bytes()).decode("ascii")}
    input_file=path.with_suffix(".github.tmp.json")
    try:
        save_json(input_file,body)
        p=subprocess.run(["gh","api","--method","PUT",
                          "repos/dvikt33-ux/safe-bim-bridge/contents/"+dest,
                          "--input",str(input_file)],capture_output=True,text=True,
                          timeout=150)
        if p.returncode:
            raise RuntimeError("GitHub upload: "+p.stderr[-350:])
    finally:input_file.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/"+dest

def apply_group(state,name,command,key,mods,verify_fn):
    for start in range(0,len(mods),8):
        items=mods[start:start+8]
        assert_target()
        ids_before=guid_map()
        state["inFlight"]={"phase":name,"command":command,"start":start,
                           "guid":[x["elementId"]["guid"] for x in items],"started":utc()}
        save_json(THIS_JOURNAL,state)
        response=api(command,{key:items},write=True)
        state["lastReply"]=response
        save_json(THIS_JOURNAL,state)
        # After a modification, even an unexpected child GUID change is
        # treated as a blocker, never retried automatically.
        ids_after=guid_map()
        if ids_before!=ids_after:
            raise RuntimeError("GUID set changed during in-place modification")
        read=read_details([x["elementId"]["guid"] for x in items])
        for item in items:
            verify_fn(read[item["elementId"]["guid"].lower()],item)
        state["completed"].append({"phase":name,"guid":state["inFlight"]["guid"],
                                    "finishedAt":utc()})
        state["inFlight"]=None
        save_json(THIS_JOURNAL,state)
        print("VERIFIED",name,min(start+len(items),len(mods)),"/",len(mods),flush=True)

def verify_joist(e,_):
    d=e["details"];b=e["bbox"]
    if e["type"]!="Beam" or not near(d.get("level"),-.1,0.004):
        raise RuntimeError("Joist modified elevation not applied")
    if not near(b.get("zMin"),-.3,0.004) or not near(b.get("zMax"),-.1,0.004):
        raise RuntimeError("Joist bbox not aligned with source KR-6")

def verify_slab(e,item):
    d=e["details"];b=e["bbox"]
    want=item["expected"]
    if (e["type"]!="Slab" or d.get("structureType")!="Basic"
            or not near(d.get("thickness"),want["thickness"],.003)
            or not near(d.get("zCoordinate"),want["top"],.003)
            or not near(b["zMax"],want["top"],.003)
            or not near(b["zMin"],want["top"]-want["thickness"],.003)):
        raise RuntimeError("Slab Basic geometry readback mismatch: "+item["elementId"]["guid"])

def run(args):
    if not SOURCE.is_file() or not TARGET.is_file():
        raise RuntimeError("Expected original and built working PLN must both exist")
    assert_target()
    base,groups,wanted_ids=expected_journal()
    current=guid_map()
    if set(current)!=wanted_ids or len(current)!=261:
        raise RuntimeError("Current model differs from completed native core GUID manifest")
    if digest(SOURCE)!=base.get("sourcePLNSHA256"):
        raise RuntimeError("Source PLN bytes changed unexpectedly")
    selected=[current[x.lower()] for key in
              ("Timber joists nominal @ 600 mm","Floor sheathing","Terrace platforms")
              for x in groups[key]]
    values=read_details(selected)
    exact_inputs(values,groups)
    joists=[{"elementId":{"guid":g},"level":-.1}
            for g in groups["Timber joists nominal @ 600 mm"]]
    slabs=[]
    for g in groups["Floor sheathing"]:
        slabs.append({"elementId":{"guid":g},"structureType":"Basic",
                      "thickness":.022,"zCoordinate":-.078,
                      "referencePlaneLocation":"Top",
                      "expected":{"thickness":.022,"top":-.078}})
    for g in groups["Terrace platforms"]:
        slabs.append({"elementId":{"guid":g},"structureType":"Basic",
                      "thickness":.05,"zCoordinate":-.05,
                      "referencePlaneLocation":"Top",
                      "expected":{"thickness":.05,"top":-.05}})
    print("SOURCE KR-6: 48 joists, CSP 22 mm, screed 58 mm, floor 20 mm, terrace decking 50 mm",flush=True)
    print("LIVE PREFLIGHT PASS: joists 48, slabs 3, GUID 261, source unchanged",flush=True)
    print("PLAN: move joists Z +0.2m; convert original slab to 22mm CSP base; "
          "terrace slabs to 50mm; NOT adding upper floor layers yet",flush=True)
    if not args.apply:
        print("DRY RUN: no changes made",flush=True)
        return 0
    if THIS_JOURNAL.exists() or BACKUP.exists():
        raise RuntimeError("Existing checkpoint or backup; never rerun without manual reconciliation")
    shutil.copy2(TARGET,BACKUP)
    backup_hash=digest(TARGET)
    if digest(BACKUP)!=backup_hash:
        raise RuntimeError("Backup checksum mismatch; no writes")
    state={"schema":"apa.bdd.native-KR6-floor-repair.v1",
        "startTimeUTC":utc(),"status":"BUILDING","port":PORT,
        "targetPLN":str(TARGET),"backupPLN":str(BACKUP),
        "backupSHA256":backup_hash,"initialGUIDCount":261,
        "materialStatus":"NOT_CALIBRATED; geometry-only source correction",
        "floorLayerConstruction":"CSP 22mm, screed 58mm, finish 20mm; last two pending",
        "expectedSource":"2022 KR PDF page 8 sheet KR-6",
        "completed":[],"inFlight":None}
    save_json(THIS_JOURNAL,state)
    apply_group(state,"48 joist elevation correction","ModifyBeams","beamsWithDetails",
                joists,verify_joist)
    # The helper 'expected' is local metadata and not accepted by Tapir.
    # Remove metadata from the transmitted payload, preserving it for verification.
    for item in slabs:
        item.setdefault("expected",{})
    for i,item in enumerate(slabs):
        raw={k:v for k,v in item.items() if k!="expected"}
        exp=item["expected"]
        expected_fn=lambda e, sent, w=exp:verify_slab(e,{"expected":w,
                                   "elementId":sent["elementId"]})
        apply_group(state,"CSP/terrace slab correction #%d"%(i+1),
                    "ModifySlabs","slabsWithDetails",[raw],expected_fn)
    if set(guid_map())!=wanted_ids:
        raise RuntimeError("Final native model GUIDs changed")
    assert_target()
    state["inFlight"]={"phase":"SaveProject","started":utc()}
    save_json(THIS_JOURNAL,state)
    api("SaveProject",{},write=True)
    assert_target()
    state["inFlight"]=None
    state["status"]="KR6_FLOOR_CORE_GEOMETRY_CORRECTED__LAYERS_AND_MATERIALS_PENDING"
    state["finishedAt"]=utc()
    state["sourcePLNUnchanged"]=(digest(SOURCE)==base.get("sourcePLNSHA256"))
    state["finalGUIDCount"]=len(guid_map())
    save_json(THIS_JOURNAL,state)
    print("KR6 FLOOR REPAIR SAVED:",state["status"],flush=True)
    print("SOURCE UNCHANGED:",state["sourcePLNUnchanged"],flush=True)
    print("BACKUP:",BACKUP,flush=True)
    if args.publish:print("PRIVATE GITHUB KR6 REPORT:",publish(THIS_JOURNAL),flush=True)
    return 0

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true",
                        help="Modify exact existing working PLN only, after backup and preflight")
    parser.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    try:
        sys.exit(run(args))
    except Exception as exc:
        print("KR6 REPAIR BLOCKED:",type(exc).__name__,str(exc),file=sys.stderr,flush=True)
        if args.publish:
            try:
                if THIS_JOURNAL.exists():
                    state=json.loads(THIS_JOURNAL.read_text(encoding="utf-8"))
                else: state={"schema":"apa.bdd.native-KR6-floor-repair.v1","status":"PREFLIGHT_BLOCKED"}
                state["error"]={"type":type(exc).__name__,
                                "message":str(exc)[:650],"atUTC":utc()}
                if state.get("status")=="BUILDING":state["status"]="BLOCKED_NEEDS_RECONCILIATION"
                save_json(THIS_JOURNAL,state)
                print("PRIVATE GITHUB KR6 FAILURE REPORT:",publish(THIS_JOURNAL),flush=True)
            except Exception as report_exc:
                print("REPORT FAILURE:",type(report_exc).__name__,str(report_exc)[:200],file=sys.stderr)
        print("Do not retry; inspect current in-memory PLN and journal first.",file=sys.stderr)
        sys.exit(2)
