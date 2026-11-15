"""Classify Tapir 2.0 change GUIDs without inventing root BIM objects.

This is an offline evidence adapter. An event GUID is a root only when a
separate successful creation receipt and GUID readback confirm that identity.
All other new GUIDs remain unresolved, not inferred subelements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

GUID=re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
KEYS=("newElements","modifiedElements","deletedElements")

def invalid(message):
    raise ValueError("APA_AC30_CHANGE_"+message)

def events(diff):
    if not isinstance(diff,dict):
        invalid("DIFF_REQUIRED")
    result={}
    for key in KEYS:
        rows=diff.get(key,[])
        if not isinstance(rows,list):
            invalid("BAD_CHANGE_ROWS")
        guids=[]
        for row in rows:
            try:
                guid=row["elementId"]["guid"]
            except (TypeError,KeyError):
                invalid("BAD_CHANGE_GUID")
            if not isinstance(guid,str) or not GUID.fullmatch(guid):
                invalid("BAD_CHANGE_GUID")
            guids.append(guid.upper())
        if len(guids)!=len(set(guids)):
            invalid("DUPLICATE_GUID_WITHIN_CLASS")
        result[key]=guids
    if sum(map(len,result.values()))!=len(set().union(*(set(v) for v in result.values()))):
        invalid("OVERLAPPING_CHANGE_CLASSES")
    return result

def normalize(diff, proven_roots):
    classes=events(diff)
    if not isinstance(proven_roots,dict) or not proven_roots:
        invalid("ROOT_EVIDENCE_REQUIRED")
    known={}
    for typ, ids in proven_roots.items():
        if not isinstance(typ,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*",typ) or not isinstance(ids,list):
            invalid("INVALID_ROOT_TYPE")
        guids=[]
        for guid in ids:
            if not isinstance(guid,str) or not GUID.fullmatch(guid):
                invalid("INVALID_ROOT_GUID")
            guids.append(guid.upper())
        if len(guids)!=len(set(guids)):
            invalid("DUPLICATE_PROVEN_ROOT")
        known[typ]=guids
    roots={guid for ids in known.values() for guid in ids}
    if len(roots)!=sum(map(len,known.values())):
        invalid("ROOT_ASSIGNED_MULTIPLE_TYPES")
    if not roots.issubset(set(classes["newElements"])):
        invalid("ROOT_NOT_IN_NEW_EVENTS")
    unresolved=[guid for guid in classes["newElements"] if guid not in roots]
    return {"status":"ROOTS_CONFIRMED_OTHERS_UNRESOLVED",
            "eventCounts":{key:len(rows) for key,rows in classes.items()},
            "provenRoots":known,"rootCount":len(roots),
            "unresolvedGUIDs":unresolved,"unresolvedCount":len(unresolved),
            "modelWrites":0,"executionPermission":False,
            "note":"Unresolved GUIDs are NOT independently confirmed BIM objects or necessarily subelements."}

def load(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>4_000_000:
        invalid("EVIDENCE_MISSING_OR_OVERSIZED")
    raw=path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")),hashlib.sha256(raw).hexdigest()

def from_creation_receipts(diff_file, readback_file, final_file, intent_file, create_response_file):
    diff,sha1=load(diff_file)
    readback,sha2=load(readback_file)
    final,sha3=load(final_file)
    intent,sha4=load(intent_file)
    creation,sha5=load(create_response_file)
    if not isinstance(diff,dict) or not isinstance(diff.get("diff"),dict):
        invalid("WRONG_DIFF_STRUCTURE")
    if (not isinstance(readback,dict) or not isinstance(final,dict)
            or final.get("status")!="PASS" or final.get("deleted") is not True
            or not isinstance(readback.get("new"),list)
            or readback.get("new")!=[readback.get("created")]
            or final.get("createdGuid")!=readback.get("created")):
        invalid("INDEPENDENT_ROOT_CREATION_NOT_PROVEN")
    if (not isinstance(intent,dict) or intent.get("command")!="CreateNativeAssemblyV1"
            or not isinstance(intent.get("args"),dict) or intent["args"].get("kind")!="Railing"
            or not isinstance(creation,dict) or not isinstance(creation.get("result"),dict)
            or creation["result"].get("nativeModelWrites")!=1
            or creation["result"].get("createdElements")!=[
                {"elementId":{"guid":readback["created"]}}]):
        invalid("CREATE_INTENT_RESPONSE_TYPE_OR_GUID_MISMATCH")
    result=normalize(diff["diff"],{intent["args"]["kind"]:readback["new"]})
    result["historicalCreationCommand"]=intent["command"]
    result["historicalCreationKind"]=intent["args"]["kind"]
    result["sourceSHA256"]={"diff":sha1,"readback":sha2,"final":sha3,
                            "creationIntent":sha4,"creationResponse":sha5}
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diff",type=Path,required=True)
    parser.add_argument("--readback",type=Path,required=True)
    parser.add_argument("--final",type=Path,required=True)
    parser.add_argument("--intent",type=Path,required=True)
    parser.add_argument("--create-response",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if not args.output.is_absolute() or not args.output.parent.is_dir() or args.output.exists():
            invalid("OUTPUT_MUST_BE_NEW")
        record=from_creation_receipts(args.diff,args.readback,args.final,args.intent,args.create_response)
        with args.output.open("x",encoding="utf-8",newline="\n") as stream:
            json.dump(record,stream,ensure_ascii=False,indent=2,allow_nan=False)
            stream.write("\n")
        print(json.dumps({"status":record["status"],"rootCount":record["rootCount"],
                          "unresolvedCount":record["unresolvedCount"],
                          "output":str(args.output)},ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)},ensure_ascii=False))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
