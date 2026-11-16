"""Read-only, pinned YAML rule evaluation for an independently captured BIM snapshot.

Subset of Archicad-MCP rule vocabulary. No native API calls and no arbitrary code.
Each checked field must be explicitly listed in snapshot coverage; missing coverage
or unread elements are SKIPPED, never silently reported PASS/FAIL.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from threading import Lock

SCHEMA = "APA_MODEL_RULE_SNAPSHOT_V1"
PROFILE_SCHEMA = "APA_RULE_AUDIT_PROFILE_V1"
TYPES = frozenset({"property-required", "classification-required",
                   "layer-compliance", "zone-number-required"})
HEX = re.compile(r"^[0-9a-fA-F]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$")
MAX_RULES = 64
MAX_ELEMENTS = 20000


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path(value, suffixes, limit):
    if not isinstance(value, str):
        raise ValueError("APA_RULE_INVALID_PATH")
    path = Path(value)
    if (not path.is_absolute() or path.suffix.lower() not in suffixes
            or not path.is_file() or path.resolve(strict=True) != path
            or "experiments" not in [p.lower() for p in path.parts]
            or path.stat().st_size > limit):
        raise ValueError("APA_RULE_INPUT_SCOPE_INVALID")
    return path


def _load_yaml(path):
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("APA_RULE_YAML_DEPENDENCY_REQUIRED") from exc
    try:
        result = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (ValueError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError("APA_RULE_YAML_INVALID") from exc
    if not isinstance(result, list) or not 1 <= len(result) <= MAX_RULES:
        raise ValueError("APA_RULE_COUNT_INVALID")
    seen = set()
    for rule in result:
        if not isinstance(rule, dict) or set(rule) - {
                "id", "type", "severity", "tags", "applies_to",
                "property", "system", "allowed"}:
            raise ValueError("APA_RULE_UNSUPPORTED_FIELDS")
        ident, typ = rule.get("id"), rule.get("type")
        if (not isinstance(ident, str) or not IDENT.fullmatch(ident)
                or ident in seen or typ not in TYPES
                or rule.get("severity", "error") not in {"error", "warning"}):
            raise ValueError("APA_RULE_DEFINITION_INVALID")
        seen.add(ident)
        applies = rule.get("applies_to", {})
        if applies != {} and (not isinstance(applies, dict) or
                              set(applies) != {"element_type"} or
                              not isinstance(applies["element_type"], str)):
            raise ValueError("APA_RULE_APPLIES_TO_SCOPE_UNSUPPORTED")
        if typ in {"property-required", "classification-required"}:
            field = "property" if typ == "property-required" else "system"
            if not isinstance(rule.get(field), str) or not rule[field]:
                raise ValueError("APA_RULE_FIELD_REQUIRED")
        if typ == "layer-compliance" and (not isinstance(rule.get("allowed"), list)
                or not rule["allowed"] or
                any(not isinstance(v, str) or not v for v in rule["allowed"])):
            raise ValueError("APA_RULE_LAYER_ALLOWED_REQUIRED")
        if typ == "zone-number-required" and "applies_to" in rule:
            raise ValueError("APA_RULE_ZONE_SCOPE_NOT_SUPPORTED")
    return result


def _load_snapshot(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("APA_RULE_SNAPSHOT_INVALID") from exc
    if (not isinstance(data, dict) or set(data) != {"schema", "elements", "coverage"}
            or data["schema"] != SCHEMA or
            not isinstance(data["elements"], list) or
            len(data["elements"]) > MAX_ELEMENTS or
            not isinstance(data["coverage"], dict) or
            set(data["coverage"]) != {"properties", "classifications", "layers", "zones"}):
        raise ValueError("APA_RULE_SNAPSHOT_SCHEMA_INVALID")
    cover = data["coverage"]
    if (not isinstance(cover["properties"], list)
            or not all(isinstance(v, str) for v in cover["properties"])
            or not isinstance(cover["classifications"], list)
            or not all(isinstance(v, str) for v in cover["classifications"])
            or type(cover["layers"]) is not bool or type(cover["zones"]) is not bool):
        raise ValueError("APA_RULE_COVERAGE_INVALID")
    ids = set()
    for row in data["elements"]:
        if (not isinstance(row, dict) or
                set(row) != {"guid", "element_type", "properties", "classifications",
                             "layer", "zone_number", "unread"} or
                not isinstance(row["guid"], str) or row["guid"] in ids or
                not isinstance(row["element_type"], str) or
                not isinstance(row["properties"], dict) or
                not isinstance(row["classifications"], dict) or
                not isinstance(row["unread"], list) or
                not all(isinstance(v, str) for v in row["unread"])):
            raise ValueError("APA_RULE_ELEMENT_SCHEMA_INVALID")
        ids.add(row["guid"])
    return data


def _missing(value):
    return value is None or value == "" or value == []


def _check(rule, snapshot):
    typ = rule["type"]
    scope = (rule.get("applies_to") or {}).get("element_type")
    if typ == "zone-number-required":
        elements = [row for row in snapshot["elements"] if row["element_type"] == "Zone"]
    else:
        elements = [row for row in snapshot["elements"] if not scope or row["element_type"] == scope]
    coverage = snapshot["coverage"]
    required = {
        "property-required": rule.get("property") in coverage["properties"],
        "classification-required": rule.get("system") in coverage["classifications"],
        "layer-compliance": coverage["layers"],
        "zone-number-required": coverage["zones"],
    }[typ]
    field = {
        "property-required": "property:" + str(rule.get("property")),
        "classification-required": "classification:" + str(rule.get("system")),
        "layer-compliance": "layer",
        "zone-number-required": "zone_number",
    }[typ]
    if not required:
        return ("SKIPPED", [], len(elements), "SOURCE_FIELD_NOT_CAPTURED")
    checked, unread, failed = 0, 0, []
    for element in elements:
        if field in element["unread"]:
            unread += 1
            continue
        checked += 1
        if typ == "property-required":
            invalid = _missing(element["properties"].get(rule["property"]))
        elif typ == "classification-required":
            invalid = _missing(element["classifications"].get(rule["system"]))
        elif typ == "layer-compliance":
            invalid = element["layer"] not in rule["allowed"]
        else:
            invalid = _missing(element["zone_number"])
        if invalid:
            failed.append(element["guid"])
    status = "FAIL" if failed else ("SKIPPED" if not checked or unread else "PASS")
    return status, failed, unread, "PARTIAL_COVERAGE" if unread else "EVALUATED"


class RuleAuditControl:
    def __init__(self, profile):
        self.profile = _path(str(profile), {".json"}, 8192)
        raw = json.loads(self.profile.read_text(encoding="utf-8-sig"))
        if (not isinstance(raw, dict) or set(raw) != {
                "schema", "snapshot", "snapshotSha256", "rules", "rulesSha256"} or
                raw["schema"] != PROFILE_SCHEMA):
            raise ValueError("APA_RULE_PROFILE_INVALID")
        self.snapshot = _path(raw["snapshot"], {".json"}, 16 * 1024 * 1024)
        self.rules = _path(raw["rules"], {".yaml", ".yml"}, 128 * 1024)
        self.hashes = (_digest(self.profile), _digest(self.snapshot), _digest(self.rules))
        if (not isinstance(raw["snapshotSha256"], str) or not HEX.fullmatch(raw["snapshotSha256"])
                or not isinstance(raw["rulesSha256"], str) or not HEX.fullmatch(raw["rulesSha256"])
                or self.hashes[1:] != (raw["snapshotSha256"].lower(), raw["rulesSha256"].lower())):
            raise ValueError("APA_RULE_HASH_MISMATCH")
        self.lock = Lock()

    def _guard(self):
        if self.hashes != (_digest(self.profile), _digest(self.snapshot), _digest(self.rules)):
            raise ValueError("APA_RULE_INPUT_CHANGED")

    def perform(self, operation):
        with self.lock:
            try:
                if operation not in {"status", "audit"}:
                    raise ValueError("APA_RULE_OPERATION_NOT_ALLOWED")
                self._guard()
                if operation == "status":
                    return {"status": "APA_RULE_READY", "snapshotSha256": self.hashes[1],
                            "rulesSha256": self.hashes[2], "modelWrites": 0,
                            "nativeCalls": 0}
                snapshot = _load_snapshot(self.snapshot)
                rules = _load_yaml(self.rules)
                results = []
                for rule in rules:
                    status, failed, unread, reason = _check(rule, snapshot)
                    results.append({"rule": rule["id"], "type": rule["type"],
                                    "severity": rule.get("severity", "error"),
                                    "status": status, "failingGuids": failed[:1000],
                                    "failingCount": len(failed), "unreadCount": unread,
                                    "reason": reason})
                self._guard()
                errors = any(r["status"] == "FAIL" and r["severity"] == "error" for r in results)
                skipped = any(r["status"] == "SKIPPED" for r in results)
                status = "APA_RULE_FAIL" if errors else ("APA_RULE_INCOMPLETE" if skipped else "APA_RULE_PASS")
                return {"status": status, "results": results,
                        "snapshotSha256": self.hashes[1], "rulesSha256": self.hashes[2],
                        "modelWrites": 0, "nativeCalls": 0, "liveModelVerified": False}
            except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
                return {"status": "BLOCKED", "reason": str(exc), "modelWrites": 0}
