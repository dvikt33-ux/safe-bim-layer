"""Check all three IFC vendor operations via installed original APA router.

Creates two disposable IFC4 walls and an IDS under TemporaryDirectory,
routes to the installed (receipt-hash-verified) external adapter using the
existing DynamicCommands.prepare/read interface. Never opens a PLN.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import apa_external_router_activation as Activation

TESTS = Path(__file__).resolve().parents[1] / "tests"


def check(yes, message):
    if not yes:
        raise ValueError(message)


def main():
    sys.path.insert(0, str(TESTS))
    from apa_external_ifc_vendor_smoke import create_ifc, ids

    router, original = Activation.load_router()
    provider = Activation.register_installed(router)
    observed = {}
    with tempfile.TemporaryDirectory(prefix="apa-installed-ifc-route-") as folder:
        temp = Path(folder)
        arch = temp / "architecture.ifc"
        mep = temp / "services.ifc"
        first = create_ifc(arch, "Temporary Architecture Wall")
        second = create_ifc(mep, "Temporary Services Wall")
        check(first != second, "DUPLICATED_IFC_ROOT_GUID")
        ids_file = temp / "wall-name.ids"
        rules = ids.Ids(title="APA IFC demo criterion")
        rule = ids.Specification(name="Walls have Name", ifcVersion=["IFC4"])
        rule.applicability.append(ids.Entity(name="IFCWALL"))
        rule.requirements.append(ids.Attribute(name="Name"))
        rules.specifications.append(rule)
        rules.to_xml(str(ids_file))
        tasks = [
            ("IFCClash", {"a": str(arch), "b": str(mep),
                          "output": str(temp / "clash.json")}),
            ("IDSValidate", {"a": str(arch), "ids": str(ids_file),
                             "output": str(temp / "ids.json")}),
            ("IFCQuantities", {"a": str(arch),
                               "output": str(temp / "quantities.json")})
        ]
        for command, params in tasks:
            report = Activation.run_read(router, command, params)
            value = report["result"]
            check(report["modelWrites"] == 0 and report["nativeCalls"] == 0,
                  "NATIVE_WRITE_OR_CALL_DETECTED")
            if command == "IFCQuantities":
                qto = value["result"]
                check(qto["schema"] == "APA_QUANTIFIED_IFC_EXCHANGE_V1"
                      and len(qto["elements"]) == 1
                      and qto["elements"][0]["ifcId"] == first,
                      "INSTALLED_IFC_QTO_DIFFERENT_RESULT")
                observed[command] = {"status": "SOURCE_IFC_QTO_ROUTER_PASS",
                                      "ifcElementCount": len(qto["elements"])}
            else:
                expected = "ifcclash" if command == "IFCClash" else "ifctester"
                check(value["vendor"] == expected, "UNEXPECTED_VENDOR:" + command)
                observed[command] = {"status": "SOURCE_IFC_VENDOR_ROUTER_PASS",
                                      "vendor": value["vendor"]}
                if command == "IFCClash":
                    out = value.get("vendorOutput")
                    if isinstance(out, list) and out and isinstance(out[0], dict):
                        clashes = out[0].get("clashes")
                        observed[command]["clashCount"] = len(clashes) if isinstance(clashes,dict) else None
    check(len(provider["commands"]) == 6, "SIX_READ_ONLY_COMMANDS_REQUIRED")
    print(json.dumps({"schema": "APA_AC29_LOCAL_INSTALLED_IFC_ROUTE_V1",
                      "status": "REAL_VENDOR_IFC_READ_ONLY_ROUTE_PASS",
                      "existingCatalogCommands": original,
                      "registeredCount": 6,
                      "observedRuns": observed,
                      "nativeCalls": 0, "plnWrites": 0,
                      "model": "TEMPORARY_IFC4_ONLY_NOT_USER_PROJECT",
                      "autoRegistrationAcrossExistingProcesses": False},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("APA_STATUS: LOCAL_IFC_ROUTE_PROBE_BLOCKED")
        print("ERROR:", type(error).__name__ + ": " + str(error))
        sys.exit(2)
