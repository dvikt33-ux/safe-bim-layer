"""Opt-in APA AC29 V2 IFC/DXF routes through the EXISTING certified router.

No native Archicad calls, no PLN or APX writes, no modification of the installed
V1 six commands and no automatic attachment to already-running sessions.
Source draft: installation/execution acceptance must be performed separately.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import apa_external_analytics_entrypoint as V1
import apa_high_density_readonly_v2 as Pack


def route_once(command, a, output):
    Pack.require(command in Pack.COMMANDS, "V2_COMMAND_NOT_REVIEWED")
    action, suffix = Pack.COMMANDS[command]
    src = Pack.input_file(a, suffix)
    dest = Pack.output_file(output, src)
    old_vendor_factory, schema = V1.verified_session()

    # V1 registers its original six commands first; V2 is only an opt-in add-on.
    router = old_vendor_factory.native_command_router(
        schema, include_functional_modules=False)
    before = {name for name in router.catalog["commands"]
              if name.startswith("AddOn.APAExternalReadOnly.")}
    Pack.require(len(before) == 6, "V1_ORIGINAL_SIX_COMMANDS_MISSING")
    registered = Pack.register(router)
    keys = registered["commands"]
    Pack.require(len(keys) == 12 and
                 all(name in router.catalog["commands"] for name in keys),
                 "V2_REGISTERED_SET_INCOMPLETE")
    after = {name for name in router.catalog["commands"]
             if name.startswith("AddOn.APAExternalReadOnly.")}
    Pack.require(before == after, "V1_CATALOG_CHANGED_BY_V2")

    key = "AddOn." + Pack.NAMESPACE + "." + command
    Pack.require(router.operation_kind(key) == "READ_ONLY" and
                 router.catalog["commands"][key].get("api") == "local-python",
                 "V2_ROUTER_PERMISSION_INVALID")
    ticket = router.prepare(key, {"a": str(src), "output": str(dest)})
    Pack.require(ticket.get("nativeWritePermission") is False and
                 ticket.get("effect") == "READ_ONLY",
                 "V2_NATIVE_WRITE_PERMISSION_DETECTED")
    evidence = router.read(None, ticket, reviewed_read_only=True)
    Pack.require(evidence.get("schema") == "APA_HIGH_DENSITY_READONLY_V2" and
                 evidence.get("action") == action and
                 evidence.get("modelWrites") == 0 and
                 evidence.get("nativeCalls") == 0 and dest.is_file(),
                 "V2_ROUTER_EVIDENCE_INCOMPLETE")
    # An in-memory router response is not proof of what actually reached disk.
    # Re-read the new report and independently bind both source and adapter.
    actual = json.loads(dest.read_text(encoding="utf-8-sig"))
    Pack.require(actual == evidence and
                 actual.get("sources") == [
                     {"name": src.name, "sha256": Pack.digest(src)}] and
                 actual.get("adapterSha256") == Pack.digest(Pack.__file__),
                 "V2_ROUTER_EVIDENCE_SHA_OR_READBACK_MISMATCH")
    return {"schema": "APA_AC29_HIGH_DENSITY_ROUTED_V2",
            "status": "READ_ONLY_REPORT_CREATED_NOT_BIM_ACCEPTED",
            "command": key, "output": str(dest),
            "evidenceSha256": Pack.digest(dest),
            "newReadOnlyCommandsRegistered": len(keys),
            "originalV1CommandsUnchanged": len(after),
            "nativeCalls": 0, "plnWrites": 0}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--command", required=True, choices=sorted(Pack.COMMANDS))
    p.add_argument("--a", required=True, help="existing .ifc or .dxf")
    p.add_argument("--output", required=True, help="new .json outside stable APA")
    args = p.parse_args(argv)
    print(json.dumps(route_once(args.command, args.a, args.output),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_STATUS: HIGH_DENSITY_V2_ROUTER_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
