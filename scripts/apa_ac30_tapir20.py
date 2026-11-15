"""Typed quantity verification and compatibility CLI for the AC30 pilot."""
from __future__ import annotations

import argparse
from collections import OrderedDict
import json
from pathlib import Path
import re

from archicad_native_api import native_command
from archicad_tapir_profile import (
    LEGACY_AC30_SCHEMA as SCHEMA,
    TapirProfileError as AC30GuardError,
    exact_file, guard, hash_file, profile_from_path, validate_profile_shape,
)


GUID = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
TYPE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
READS = frozenset({"GetProjectInfo", "GetAddOnVersion", "GetDetailsOfElements",
                   "GetQuantitiesOfElements", "GetGroupsOfElements", "GetSuspendGroupsMode"})
MAX_ELEMENTS = 1000


def fail(message):
    raise AC30GuardError("APA_AC30_" + message)


def api_http(port, command, params=None):
    if command!="API.GetProductInfo" and command not in READS:
        fail("READ_ONLY_COMMAND_REQUIRED")
    result = native_command(port, command, params, timeout=20, max_response=16*1024*1024)
    if result.get("error") is not None:
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
        validate_profile_shape(config)
        self.config=config
        self.transport=transport or api_http
        self.calls=[]
    def call(self, command, params=None):
        if command!="API.GetProductInfo" and command not in READS:
            fail("WRITE_OR_UNKNOWN_COMMAND")
        self.calls.append(command)
        return self.transport(self.config["port"],command,params)
    def guard(self):
        return guard(self.config, self.call)

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
            "note":"Typed quantities from the pinned read session through the shared Archicad transport."}
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
