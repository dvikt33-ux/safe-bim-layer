#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose a partial native BDD house write (Archicad 29 only).

READ ONLY. Never changes the active PLN, never saves, switches projects or
deletes/modifies BIM elements. Optional --publish writes a diagnostic report
to private GitHub safe-bim-bridge mailbox using an existing gh login.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
import urllib.request

PORT=19727
ORIGINAL=Path("C:/LocalAI/SafeBIM_Global_Library_Test_Projects/BDD \u0434\u043e\u043c .pln")
WORKING=ORIGINAL.with_name("BDD \u0434\u043e\u043c - \u043f\u043e \u0447\u0435\u0440\u0442\u0435\u0436\u0430\u043c 2022.pln")
MANIFEST=Path(tempfile.gettempdir())/"APA_BDD_House_Construction"/"house_native_manifest.json"
OUTPUT_DIR=Path(tempfile.gettempdir())/"APA_BDD_House_Construction"
READ_COMMANDS={"GetProjectInfo","GetAllElements","GetDetailsOfElements","Get3DBoundingBoxes","GetAddOnVersion"}

def api(command,parameters=None):
    if command not in READ_COMMANDS:
        raise RuntimeError("READ_ONLY_FENCE "+command)
    body={"command":"API.ExecuteAddOnCommand",
          "parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand","commandName":command},
                        "addOnCommandParameters":parameters or {}}}
    req=urllib.request.Request(
        "http://127.0.0.1:%d"%PORT,
        json.dumps(body,ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=90) as r:
        envelope=json.load(r)
    if envelope.get("succeeded") is not True:
        raise RuntimeError("%s transport failed: %r"%(command,envelope.get("error")))
    result=envelope.get("result",{}).get("addOnCommandResponse",{})
    if not isinstance(result,dict) or result.get("error") is not None:
        raise RuntimeError("%s returned error"%command)
    return result

def verify_active():
    from archicad import ACConnection
    c=ACConnection.connect(PORT)
    if c is None or tuple(c.commands.GetProductInfo())[:2]!=(29,5101):
        raise RuntimeError("WRONG ARCHICAD INSTANCE")
    p=api("GetProjectInfo")
    path=p.get("projectPath") or p.get("projectLocation") or ""
    if path.casefold()!=str(WORKING).casefold() or p.get("isUntitled"):
        raise RuntimeError("WRONG PROJECT: expected working copy, actual=%r"%path)
    return p

def element_map():
    data=api("GetAllElements").get("elements")
    if not isinstance(data,list):
        raise RuntimeError("Missing GetAllElements elements array")
    out={}
    for row in data:
        elid=row.get("elementId") if isinstance(row,dict) else None
        guid=elid.get("guid") if isinstance(elid,dict) else None
        guid=guid or (row.get("guid") if isinstance(row,dict) else None)
        if not isinstance(guid,str) or not guid:
            raise RuntimeError("Model element without GUID")
        key=guid.casefold()
        if key in out:
            raise RuntimeError("Duplicate GUID "+guid)
        out[key]={"guid":guid,"elementSummary":row}
    return out

def safe_details(ids):
    records=[]
    errors=[]
    for i in range(0,len(ids),16):
        chunk=ids[i:i+16]
        arg={"elements":[{"elementId":{"guid":g}} for g in chunk]}
        try:
            ds=api("GetDetailsOfElements",arg).get("detailsOfElements",[])
            bb=api("Get3DBoundingBoxes",arg).get("boundingBoxes3D",[])
            if len(ds)!=len(chunk) or len(bb)!=len(chunk):
                raise RuntimeError("Batch response shape mismatch")
            for guid,detail,box in zip(chunk,ds,bb):
                records.append({"guid":guid,"detail":detail,
                                "boundingBox":box})
        except Exception as exc:
            errors.append({"start":i,"error":type(exc).__name__+": "+str(exc)[:200]})
            for guid in chunk:
                record={"guid":guid,"detail":None,"boundingBox":None}
                single={"elements":[{"elementId":{"guid":guid}}]}
                for cmd,key,target in [
                    ("GetDetailsOfElements","detailsOfElements","detail"),
                    ("Get3DBoundingBoxes","boundingBoxes3D","boundingBox")]:
                    try:
                        rows=api(cmd,single).get(key,[])
                        if isinstance(rows,list) and len(rows)==1:
                            record[target]=rows[0]
                    except Exception as e:
                        errors.append({"guid":guid,"command":cmd,
                                       "error":type(e).__name__+": "+str(e)[:150]})
                records.append(record)
    return records,errors

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def publish(path):
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination=("safe-bim-mailbox/gpt-live/results/"
                 "apa-bdd-first-batch-diagnostic-%s-%s.json"%(stamp,uuid.uuid4().hex[:8]))
    args={"message":"BDD house native first-batch failure diagnostic (read-only)",
          "branch":"main",
          "content":base64.b64encode(path.read_bytes()).decode("ascii")}
    upload=path.with_suffix(".github-payload.tmp.json")
    try:
        save(upload,args)
        p=subprocess.run(
            ["gh","api","--method","PUT",
             "repos/dvikt33-ux/safe-bim-bridge/contents/"+destination,
             "--input",str(upload)],text=True,capture_output=True,timeout=150,
            check=False)
        if p.returncode:
            raise RuntimeError("Report upload failed: "+p.stderr[-500:])
    finally:
        upload.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/"+destination

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    before=verify_active()
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    baseline=manifest.get("initialGUIDs")
    if not isinstance(baseline,list) or len(baseline)!=21:
        raise RuntimeError("Expected original 21 GUID baseline in manifest")
    baseline_set={x.casefold() for x in baseline}
    first=element_map()
    new_keys=set(first)-baseline_set
    removed_keys=baseline_set-set(first)
    new=[first[g]["guid"] for g in sorted(new_keys)]
    details,errors=safe_details(new)
    after=verify_active()
    second=element_map()
    if set(first)!=set(second) or before.get("projectPath")!=after.get("projectPath"):
        raise RuntimeError("Project/element set changed during diagnostic; do not publish")
    by_type=dict(Counter(
        (row["detail"].get("type") or "UNKNOWN")
        if isinstance(row["detail"],dict) else "MISSING_DETAILS"
        for row in details))
    report={
        "schema":"apa.bdd.first-batch-diagnostic.v1",
        "capturedUTC":datetime.now(timezone.utc).isoformat(),
        "status":"READ_ONLY_DIAGNOSTIC",
        "port":PORT,"project":before.get("projectPath"),
        "sourceManifest":str(MANIFEST),
        "manifestStatus":manifest.get("status"),
        "stagesRecorded":manifest.get("stages",[]),
        "originalCount":len(baseline_set),
        "actualTotalCount":len(first),
        "newCount":len(new_keys),
        "missingOriginalCount":len(removed_keys),
        "missingOriginalGuids":sorted(removed_keys),
        "newByType":by_type,
        "newElements":details,
        "readErrors":errors,
        "plnSavedByDiagnostic":False,
        "liveArchicadCapture":True
    }
    out=OUTPUT_DIR/("first_batch_diagnostic_%s.json"%
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    save(out,report)
    print("TARGET VERIFIED: Archicad 29 working copy")
    print("BASELINE:",len(baseline_set),"ACTUAL:",len(first))
    print("NEW:",len(new_keys),"MISSING ORIGINAL:",len(removed_keys))
    print("NEW TYPES:",json.dumps(by_type,ensure_ascii=True))
    print("MANIFEST RECORDED STAGES:",len(manifest.get("stages",[])))
    print("LOCAL DIAGNOSTIC:",out)
    if args.publish:
        print("PRIVATE GITHUB DIAGNOSTIC:",publish(out))
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("DIAGNOSTIC FAILED:",type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(2)
