"""Read-only grouped Wall preflight for AC30/Tapir 2.0.

This adapter does not execute ModifyWalls. It establishes required grouping
state before a future explicitly authorized isolated native-write transaction.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re

from apa_ac30_tapir20 import (
    AC30ReadSession, AC30GuardError, GUID, fail, profile_from_path,
)

def preflight(config, wall_guid, group_guid, expected_height, new_height, transport=None):
    if not isinstance(wall_guid,str) or not GUID.fullmatch(wall_guid):
        fail("WALL_GUID_REQUIRED")
    if not isinstance(group_guid,str) or not GUID.fullmatch(group_guid):
        fail("GROUP_GUID_REQUIRED")
    for value in (expected_height,new_height):
        if type(value) not in (float,int) or not math.isfinite(value) or value<=0:
            fail("FINITE_POSITIVE_HEIGHT_REQUIRED")
    if math.isclose(expected_height,new_height,abs_tol=1e-9):
        fail("NO_HEIGHT_CHANGE")
    session=AC30ReadSession(config,transport=transport)
    before=session.guard()
    result = read_grouped_wall(session.call, wall_guid, group_guid, expected_height)
    after=session.guard()
    if before!=after:
        fail("NATIVE_IDENTITY_CHANGED_DURING_PREFLIGHT")
    return {"status":"AC30_GROUPED_WALL_PREFLIGHT_PASS",
            "scope":"ISOLATED_AC30_TEST_COPY_ONLY",
            "session":before, "desiredHeight":new_height, **result,
            "requiredTransaction":["verify exact pinned PLN and active GUID immediately before write",
                                   "temporarily enable Suspend Groups when required",
                                   "ModifyWalls exact authorized wall only",
                                   "read back new height and returned element status",
                                   "restore exact prior group mode in finally",
                                   "on failure inspect state, then reconcile without automatic retry"],
            "modelWrites":0,"executionPermission":False,
            "note":"This is preflight only, not a native modification or an approval to execute."}


def read_grouped_wall(call, wall_guid, group_guid, expected_height):
    detail=call("GetDetailsOfElements",{
        "elements":[{"elementId":{"guid":wall_guid}}]}).get("detailsOfElements")
    if not isinstance(detail,list) or len(detail)!=1 or detail[0].get("type")!="Wall":
        fail("EXPECTED_WALL_NOT_FOUND")
    actual=detail[0].get("details",{}).get("height")
    if type(actual) not in (float,int) or not math.isclose(actual,expected_height,abs_tol=1e-7):
        fail("HEIGHT_BASELINE_DRIFT")
    groups=call("GetGroupsOfElements",{
        "elements":[{"elementId":{"guid":wall_guid}}]}).get("groupGuids")
    if not isinstance(groups,list):
        fail("GROUP_READBACK_MISSING")
    linked=[]
    for row in groups:
        try:
            linked.append(row["groupId"]["guid"].upper())
        except (TypeError,KeyError,AttributeError):
            fail("GROUP_READBACK_MALFORMED")
    if group_guid.upper() not in linked:
        fail("EXPECTED_GROUP_MISSING")
    mode=call("GetSuspendGroupsMode")
    if type(mode.get("suspendGroups")) is not bool:
        fail("SUSPEND_GROUPS_UNKNOWN")
    return {"wallGuid":wall_guid,"groupGuid":group_guid,
            "actualHeight":actual,
            "groupMembership":sorted(set(linked)),
            "suspendGroupsBefore":mode["suspendGroups"],
            "requiresSuspendGroups":not mode["suspendGroups"]}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile",type=Path,required=True)
    parser.add_argument("--wall",required=True)
    parser.add_argument("--group",required=True)
    parser.add_argument("--expected-height",type=float,required=True)
    parser.add_argument("--new-height",type=float,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        cfg=profile_from_path(args.profile)
        dest=args.output
        if (not dest.is_absolute() or dest.exists() or not dest.parent.is_dir()
                or dest.resolve().is_relative_to(Path(cfg["project"]).parent)):
            fail("OUTPUT_MUST_BE_NEW_OUTSIDE_MODEL_DIRECTORY")
        result=preflight(cfg,args.wall,args.group,args.expected_height,
                         args.new_height)
        with dest.open("x",encoding="utf-8",newline="\n") as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
            stream.write("\n")
        print(json.dumps({"status":result["status"],"requiresSuspendGroups":result["requiresSuspendGroups"],
                          "executionPermission":False,"output":str(dest)},ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error":str(exc)},ensure_ascii=False))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
