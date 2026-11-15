"""AC30/Tapir 2.0 read-only adapter for the existing APA R04 CLI.

This module does not modify the legacy AC29 Router/SceneWriter or the MCP
campaign contract. It never calls a native write command. It binds every
read to an operator-pinned local disposable PLN, its baseline backup, the
installed AC30 Tapir APX SHA256, port, and exact version.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import urllib.request

SCHEMA="APA_AC30_TAPIR20_READ_ONLY_V1"
GUID=re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
HEX=re.compile(r"^[a-f0-9]{64}$")
TYPE=re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
READS=frozenset({"GetProjectInfo","GetAddOnVersion","GetDetailsOfElements",
                 "GetQuantitiesOfElements","GetGroupsOfElements",
                 "GetSuspendGroupsMode"})
CONFIG_KEYS=frozenset({"schema","project","projectSha256","backup","backupSha256",
                       "addon","addonSha256","port","archicadVersion","tapirVersion"})
MAX_ELEMENTS=1000

class AC30GuardError(ValueError):
    pass

def fail(message):
    raise AC30GuardError("APA_AC30_"+message)

def exact_file(raw):
    if not isinstance(raw,str) or not raw:
        fail("PATH_REQUIRED")
    path=Path(raw)
    if not path.is_absolute() or not path.is_file() or path.resolve(strict=True)!=path:
        fail("UNTRUSTED_PATH")
    return path

def hash_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

def profile_from_path(path):
    path=exact_file(str(path))
    if path.stat().st_size > 16_384:
        fail("PROFILE_TOO_LARGE")
    conf=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(conf,dict) or set(conf)!=CONFIG_KEYS or conf["schema"]!=SCHEMA:
        fail("PROFILE_SCHEMA")
    if type(conf["port"]) is not int or not 1024 <= conf["port"] <= 65535:
        fail("INVALID_PORT")
    if conf["archicadVersion"]!=30 or conf["tapirVersion"]!="2.0.0":
        fail("VERSION_PROFILE")
    for name in ("projectSha256","backupSha256","addonSha256"):
        if not isinstance(conf[name],str) or not HEX.fullmatch(conf[name]):
            fail("INVALID_SHA256")
    paths={k:exact_file(conf[k]) for k in ("project","backup","addon")}
    if len(set(paths.values()))!=3 or paths["project"].suffix.casefold()!=".pln" or paths["backup"].suffix.casefold()!=".pln" or paths["addon"].suffix.casefold()!=".apx":
        fail("INVALID_SOURCE_KINDS")
    if conf["projectSha256"]!=conf["backupSha256"]:
        fail("BASELINE_BACKUP_NOT_IDENTICAL")
    for k,p in paths.items():
        if hash_file(p)!=conf[k+"Sha256"]:
            fail("FILE_HASH_DRIFT_"+k.upper())
    return conf

def api_http(port, command, params=None):
    if command!="API.GetProductInfo" and command not in READS:
        fail("READ_ONLY_COMMAND_REQUIRED")
    if command=="API.GetProductInfo":
        request={"command":command,"parameters":{}}
    else:
        request={"command":"API.ExecuteAddOnCommand",
                 "parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand",
                                                 "commandName":command},
                               "addOnCommandParameters":params or {}}}
    req=urllib.request.Request(
        f"http://127.0.0.1:{port}",method="POST",
        data=json.dumps(request,ensure_ascii=False,allow_nan=False).encode("utf-8"),
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as response:
        raw=response.read(16*1024*1024+1)
    if len(raw)>16*1024*1024:
        fail("OVERSIZED_API_RESPONSE")
    envelope=json.loads(raw.decode("utf-8"))
    if envelope.get("succeeded") is not True:
        fail("NATIVE_API_FAILURE")
    result=envelope.get("result")
    if not isinstance(result,dict):
        fail("MALFORMED_API_RESPONSE")
    if command!="API.GetProductInfo":
        result=result.get("addOnCommandResponse")
    if not isinstance(result,dict) or result.get("error") is not None:
        fail("TAPIR_COMMAND_FAILURE_"+command)
    return result

def inputs_file(path):
    path=exact_file(str(path))
    if path.stat().st_size>128_000:
        fail("ELEMENT_INPUT_TOO_LARGE")
    entries=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(entries,list) or not 1 <= len(entries) <= MAX_ELEMENTS:
        fail("ELEMENT_INPUT_COUNT")
    seen=set()
    for item in entries:
        if (not isinstance(item,dict) or set(item)!={"guid","type"}
                or not isinstance(item["guid"],str) or not GUID.fullmatch(item["guid"])
                or not isinstance(item["type"],str) or not TYPE.fullmatch(item["type"])):
            fail("ELEMENT_INPUT_SHAPE")
        key=item["guid"].upper()
        if key in seen:
            fail("DUPLICATE_GUID")
        seen.add(key)
    return entries

def elements_payload(guids):
    return [{"elementId":{"guid":guid}} for guid in guids]

class AC30ReadSession:
    def __init__(self, config, transport=None):
        if set(config)!=CONFIG_KEYS or config["schema"]!=SCHEMA:
            fail("PROFILE_SCHEMA")
        self.config=config
        self.transport=transport or api_http
        self.calls=[]
    def call(self, command, params=None):
        if command!="API.GetProductInfo" and command not in READS:
            fail("WRITE_OR_UNKNOWN_COMMAND")
        self.calls.append(command)
        return self.transport(self.config["port"],command,params)
    def guard(self):
        conf=self.config
        for key in ("project","backup","addon"):
            path=exact_file(conf[key])
            if hash_file(path)!=conf[key+"Sha256"]:
                fail("FILE_DRIFT_"+key.upper())
        project=self.call("GetProjectInfo")
        if (project.get("projectPath","").casefold()!=conf["project"].casefold()
                or project.get("isUntitled") is True
                or project.get("isTeamwork") is True):
            fail("WRONG_OPEN_PROJECT")
        product=self.call("API.GetProductInfo")
        if product.get("version")!=conf["archicadVersion"]:
            fail("ARCHICAD_VERSION_DRIFT")
        addon=self.call("GetAddOnVersion")
        if addon.get("version")!=conf["tapirVersion"]:
            fail("TAPIR_VERSION_DRIFT")
        return {"project":project.get("projectPath"),
                "archicadVersion":product.get("version"),
                "archicadBuild":product.get("buildNumber"),
                "tapirVersion":addon["version"],
                "addonSha256":conf["addonSha256"]}
    def quantities(self, entries):
        groups=OrderedDict()
        seen=set()
        for item in entries:
            typ,guid=item["type"],item["guid"]
            if not isinstance(guid,str) or not GUID.fullmatch(guid) or not isinstance(typ,str) or not TYPE.fullmatch(typ):
                fail("BAD_ELEMENT_ID_OR_TYPE")
            if guid.upper() in seen:
                fail("DUPLICATE_GUID")
            seen.add(guid.upper())
            groups.setdefault(typ,[]).append(guid)
        rows=[]
        for typ,guids in groups.items():
            details=self.call("GetDetailsOfElements",{"elements":elements_payload(guids)}).get("detailsOfElements")
            if not isinstance(details,list) or len(details)!=len(guids) or any(
                    not isinstance(row,dict) or row.get("type")!=typ for row in details):
                fail("NATIVE_ELEMENT_TYPE_MISMATCH")
            params={"elements":elements_payload(guids),"calculateInOneCall":True}
            fast=self.call("GetQuantitiesOfElements",params).get("quantitiesOfElements")
            params["calculateInOneCall"]=False
            direct=self.call("GetQuantitiesOfElements",params).get("quantitiesOfElements")
            if not isinstance(direct,list) or len(direct)!=len(guids):
                fail("INDEPENDENT_QUANTITY_COVERAGE")
            def valid(items):
                return (isinstance(items,list) and len(items)==len(guids)
                        and all(isinstance(row,dict) and row.get("type")==typ
                                and isinstance(row.get("quantities"),dict)
                                and row["quantities"] and "error" not in row for row in items))
            if not valid(direct):
                fail("INDEPENDENT_QUANTITY_ERROR")
            if valid(fast) and fast==direct:
                selected=fast
                strategy="typed-batch-exact-parity"
            elif not valid(fast):
                selected=direct
                strategy="typed-batch-failed-independent-fallback"
            else:
                fail("QUANTITY_PARITY_DRIFT")
            rows.append({"type":typ,"guids":guids,"strategy":strategy,
                         "quantities":{guid:row["quantities"] for guid,row in zip(guids,selected)},
                         "independentExactParity":strategy=="typed-batch-exact-parity"})
        return rows

def run_readonly(profile_path, elements_path, output_path, transport=None):
    config=profile_from_path(profile_path)
    elements=inputs_file(elements_path)
    output=Path(output_path)
    if output.exists() or not output.is_absolute() or not output.parent.is_dir() or output.resolve().is_relative_to(Path(config["project"]).parent):
        fail("OUTPUT_MUST_BE_NEW_OUTSIDE_MODEL_DIRECTORY")
    session=AC30ReadSession(config,transport=transport)
    before=session.guard()
    results=session.quantities(elements)
    after=session.guard()
    if before!=after:
        fail("NATIVE_IDENTITY_CHANGED_DURING_READ")
    result={"status":"AC30_TAPIR20_R04_SOURCE_READ_PASS",
            "schema":SCHEMA,"session":before,"elementCount":len(elements),
            "typedGroups":results,"readCalls":session.calls,"modelWrites":0,
            "executionPermission":False,"savedProjectSha256":config["projectSha256"],
            "backupSha256":config["backupSha256"],
            "note":"Source-only separate AC30 read-only adapter; not installed into R04 MCP."}
    with output.open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile",type=Path,required=True)
    parser.add_argument("--elements",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        result=run_readonly(args.profile,args.elements,args.output)
        print(json.dumps({"status":result["status"],"elementCount":result["elementCount"],
                          "groups":[{"type":x["type"],"count":len(x["guids"]),"strategy":x["strategy"]}
                                    for x in result["typedGroups"]],
                          "output":str(args.output)},ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({"status":"BLOCKED","reason":str(error)},ensure_ascii=False))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
