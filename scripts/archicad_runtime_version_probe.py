"""Read-only runtime inventory for installed Archicad 29.2.1 (5101) and Tapir.

This file NEVER calls Create/Modify/Delete/Save/Switch API methods.
Official GetProductInfo and three fixed Tapir reads are the entire surface.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def as_dict(value):
    if isinstance(value, dict):
        return value
    for method in ("to_dict", "dict"):
        fn = getattr(value, method, None)
        if callable(fn):
            maybe = fn()
            if isinstance(maybe, dict):
                return maybe
    data = getattr(value, "__dict__", None)
    return dict(data) if isinstance(data, dict) else {}


def product_info(raw):
    if isinstance(raw, (tuple, list)):
        keys = ("version", "buildNumber", "languageCode")
        return dict(zip(keys, raw))
    d = as_dict(raw)
    return {key: d.get(key) for key in ("version", "buildNumber", "languageCode")}


def tapir_read(connection, command):
    if command not in ("GetProjectInfo", "GetAddOnVersion", "GetStories"):
        raise ValueError("non-read-only or unapproved API command refused")
    result = connection.commands.ExecuteAddOnCommand(
        connection.types.AddOnCommandId("TapirCommand", command), {})
    data = as_dict(result)
    if not data:
        raise ValueError(f"{command}: empty or unexpected response")
    return data


def inventory(connection, *, port, expected_path, expected_name, expected_build=5101):
    project = tapir_read(connection, "GetProjectInfo")
    if (project.get("projectPath") != expected_path or
            project.get("projectName") != expected_name or
            project.get("isUntitled") is True or
            project.get("isTeamwork") is True):
        return {"status": "WRONG_PROJECT", "port": port,
                "expectedProject": expected_path,
                "reportedProject": project.get("projectPath"),
                "writeCommandsCalled": 0}
    try:
        raw_product = connection.commands.GetProductInfo()
        product = product_info(raw_product)
    except (AttributeError, TypeError, ValueError):
        product = {}
    addon = tapir_read(connection, "GetAddOnVersion")
    stories = tapir_read(connection, "GetStories")
    tapir_version = addon.get("version")
    if not isinstance(tapir_version, str) or not tapir_version:
        raise ValueError("GetAddOnVersion did not return a version string")
    build = product.get("buildNumber")
    try:
        build_number = int(build) if build is not None else None
    except (ValueError, TypeError):
        build_number = None
    return {
        "status": "READ_ONLY_VERSION_CHECK",
        "port": port,
        "projectName": expected_name,
        "projectPath": expected_path,
        "archicadProduct": product,
        "expectedInstalledVersion": "29.2.1",
        "expectedBuild": expected_build,
        "buildMatchesUserScreenshot": (build_number == expected_build)
        if build_number is not None else None,
        "tapirAddonVersion": tapir_version,
        "storiesCount": len(stories.get("stories", []))
        if isinstance(stories.get("stories"), list) else None,
        "activeStoryNativeIndex": stories.get("actStory"),
        "readCommandsCalled": [
            "GetProjectInfo", "GetProductInfo (optional)",
            "GetAddOnVersion", "GetStories"
        ],
        "writeCommandsCalled": 0,
        "plnSaved": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--expected-project-name", required=True)
    ap.add_argument("--expected-project-path", required=True)
    args = ap.parse_args(argv)
    try:
        if args.port < 1 or args.port > 65535:
            raise ValueError("invalid port")
        from archicad import ACConnection
        connection = ACConnection.connect(args.port)
        if not connection:
            raise RuntimeError("no Archicad JSON API at selected port")
        report = inventory(connection, port=args.port,
                           expected_name=args.expected_project_name,
                           expected_path=args.expected_project_path)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if report.get("status") == "READ_ONLY_VERSION_CHECK" else 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "errorType": type(exc).__name__,
                          "detail": str(exc), "writeCommandsCalled": 0},
                         ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
