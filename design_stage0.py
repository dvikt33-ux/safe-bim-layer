"""Offline Stage 0 intake audit; no transport, BIM calls or downstream execution.

The caller supplies a complete source inventory and an approved requirement
registry. This module routes those requirements; it does not author norms.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path


CONTRACT = json.loads((Path(__file__).parent / "docs" /
                       "project_intake_stage0_contract.v1.json").read_text(encoding="utf-8"))
FLOW = ["COLLECT", "CLASSIFY", "APPLICABILITY", "REQUIRED INPUT MATRIX",
        "MAP KNOWN DATA", "DERIVE", "CONFLICTS/GAPS",
        "REQUIRED_USER_INPUT_PACKAGE", "RE-AUDIT"]
OWNERS = {"SYSTEM_CAN_FIND", "SYSTEM_CAN_DERIVE", "USER_CLIENT_SURVEYOR_MUST_PROVIDE"}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode("utf-8")).hexdigest()


def _valid(value, spec):
    kind = spec["type"]
    valid = {"number": lambda: type(value) in (int, float) and math.isfinite(value),
             "integer": lambda: type(value) is int,
             "string": lambda: isinstance(value, str) and bool(value.strip()),
             "boolean": lambda: type(value) is bool,
             "array": lambda: isinstance(value, list) and bool(value),
             "object": lambda: isinstance(value, dict) and bool(value)}[kind]()
    if not valid:
        return False
    if "enum" in spec and value not in spec["enum"]:
        return False
    if kind in ("number", "integer"):
        return ("minimum" not in spec or value >= spec["minimum"]) and (
            "maximum" not in spec or value <= spec["maximum"])
    return True


def _derive(method, values):
    """Small deterministic allowlist. Registry declares output units explicitly."""
    if method == "count":
        if len(values) != 1 or not isinstance(values[0], list):
            raise ValueError("count requires one inventory")
        return len(values[0])
    if method == "sum":
        if not values or any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
            raise ValueError("sum requires finite numbers")
        return sum(values)
    if method == "closed_polygon_area":
        if len(values) != 1:
            raise ValueError("area requires one polygon")
        p = values[0]
        if not isinstance(p, list) or len(p) < 4 or p[0] != p[-1]:
            raise ValueError("polygon must be explicitly closed")
        if any(not isinstance(x, list) or len(x) != 2 or
               any(type(n) not in (int, float) or not math.isfinite(n) for n in x) for x in p):
            raise ValueError("polygon requires finite 2D coordinates")
        # Reject degenerate and intersecting polygons; shoelace alone is unsafe.
        def cross(a, b, c):
            return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        def intersects(a, b, c, d):
            def on(a, b, c):
                return cross(a, b, c) == 0 and all(min(a[k], b[k]) <= c[k] <= max(a[k], b[k]) for k in (0, 1))
            return (cross(a,b,c)*cross(a,b,d) < 0 and cross(c,d,a)*cross(c,d,b) < 0) or any(
                (on(a,b,c), on(a,b,d), on(c,d,a), on(c,d,b)))
        n = len(p)-1
        if len({tuple(x) for x in p[:-1]}) != n:
            raise ValueError("repeated polygon vertices")
        for i in range(n):
            for j in range(i+1, n):
                if j == i+1 or (i == 0 and j == n-1):
                    continue
                if intersects(p[i], p[i+1], p[j], p[j+1]):
                    raise ValueError("self intersecting polygon")
        area = abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]))) / 2
        if area <= 0:
            raise ValueError("degenerate polygon")
        return area
    raise ValueError("unapproved derivation")


class Stage0:
    """Mutable intake session. Every data/policy update revokes its verified gate."""

    def __init__(self, registry, sources):
        self._registry = deepcopy(registry)
        self._sources = deepcopy(sources)
        self._result = None
        self._validate_registry()

    def _validate_registry(self):
        r = self._registry
        if not r.get("id") or not r.get("revision") or r.get("approved") is not True:
            raise ValueError("approved versioned requirement registry required")
        inputs = r.get("inputs", [])
        ids = [x["id"] for x in inputs]
        if len(ids) != len(set(ids)) or not r.get("classificationInputs"):
            raise ValueError("unique inputs and explicit classification required")
        if any(x not in ids for x in r["classificationInputs"]):
            raise ValueError("classification input is absent")
        if any(not x["blocking"] for x in inputs if x["id"] in r["classificationInputs"]):
            raise ValueError("classification inputs must block progression")
        branches = r.get("branches", [])
        bids = [b["id"] for b in branches]
        if not branches or len(bids) != len(set(bids)):
            raise ValueError("explicit unique applicability branches required")
        for b in branches:
            if not b.get("requiredBy") or not b.get("reason") or type(b.get("blocking")) is not bool:
                raise ValueError("branch dependency metadata required")
            if b.get("when") and (b["when"]["input"] not in ids or "equals" not in b["when"]):
                raise ValueError("unknown applicability input")
        for s in inputs:
            for key in ("name", "type", "acceptedFormats", "requiredBy", "reason", "sourceKinds", "priority", "owner"):
                if not s.get(key):
                    raise ValueError("missing requirement metadata: " + key)
            if s["type"] not in ("number", "integer", "string", "boolean", "array", "object"):
                raise ValueError("unsupported input type")
            if type(s.get("blocking")) is not bool or s["owner"] not in OWNERS:
                raise ValueError("blocking flag and acquisition owner required")
            if s["priority"] not in CONTRACT["questionPriority"] or any(
                    k not in CONTRACT["sourceClasses"] for k in s["sourceKinds"]):
                raise ValueError("unknown priority/source class")
            if any(b not in bids for b in s.get("branches", [])):
                raise ValueError("unknown requirement branch")
            d = s.get("derivation")
            if s["owner"] == "SYSTEM_CAN_DERIVE" and not d:
                raise ValueError("system derivation owner requires an approved method")
            if d and (d.get("method") not in ("count", "sum", "closed_polygon_area") or
                      not d.get("inputs") or not d.get("unit") or not d.get("inputUnits") or
                      len(d["inputs"]) != len(d["inputUnits"]) or any(x not in ids for x in d["inputs"])):
                raise ValueError("approved derivation/dependencies/units required")

    def update_source(self, source):
        """Explicit corrections may supersede specific evidence IDs, never by date alone."""
        old = self._sources
        new = [x for x in old if x["id"] != source["id"]] + [deepcopy(source)]
        if fingerprint(old) != fingerprint(new):
            self._sources = new
            if self._result:
                self._result["status"] = "INVALIDATED"
                self._result["canProgress"] = False
                self._result["invalidatedDependencies"] = sorted({v for x in self._result["inputs"]
                    if x["blocking"] and x["status"] != "NOT_APPLICABLE" for v in x["requiredBy"]})

    def result(self):
        return deepcopy(self._result)

    def update_registry(self, registry):
        candidate = Stage0(registry, self._sources)
        if fingerprint(candidate._registry) != fingerprint(self._registry):
            self._registry = candidate._registry
            if self._result:
                self._result.update(status="INVALIDATED", canProgress=False,
                                    invalidatedDependencies=["APPLICABILITY", "REQUIRED_INPUT_MATRIX"])

    def require_verified(self):
        """Read-only permission gate; cannot launch any later stage."""
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"]:
            raise RuntimeError("Stage 0 progression blocked")
        if self._result["contextFingerprint"] != fingerprint([self._registry, self._sources]):
            raise RuntimeError("Stage 0 context changed")
        return deepcopy(self._result["gateProof"])

    def audit(self):
        r = self._registry
        specs = {x["id"]: x for x in r["inputs"]}
        candidates = {k: [] for k in specs}
        collection_errors = []
        unapproved_assumptions = 0
        seen = set()
        for source in self._sources:
            sid = source.get("id")
            if not sid or sid in seen or source.get("kind") not in CONTRACT["sourceClasses"] or not source.get("revision"):
                collection_errors.append("Invalid/duplicate source identity")
                continue
            seen.add(sid)
            if source.get("inspected") is not True:
                collection_errors.append("Source not inspected: " + sid)
                continue
            for k, fact in source.get("facts", {}).items():
                if k not in specs:
                    continue
                evidence = {"sourceKind": source["kind"], "sourceId": sid,
                            "revision": source["revision"], "method": fact.get("method"),
                            "verification": fact.get("verification"), "evidenceId": sid + ":" + k,
                            "supersedes": fact.get("supersedes", [])}
                assumption = fact.get("assumed") is True or fact.get("basis") in CONTRACT[
                    "progressionGate"]["forbidSilentFallbacks"] or fact.get("verification") == "ASSUMED"
                unapproved_assumptions += int(assumption)
                ok = (source["kind"] in specs[k]["sourceKinds"] and fact.get("verification") == "VERIFIED"
                      and bool(fact.get("method")) and _valid(fact.get("value"), specs[k])
                      and fact.get("unit") == specs[k].get("unit") and not assumption)
                candidates[k].append({"value": fact.get("value"), "accepted": ok, "provenance": evidence})
        records = {}
        for k, spec in specs.items():
            c = candidates[k]
            approved = [x for x in c if x["accepted"]]
            superseded = {eid for x in approved if x["provenance"]["sourceKind"] in
                          ("USER_CORRECTION", "APPROVED_PROJECT_DECISION")
                          for eid in x["provenance"]["supersedes"]}
            approved = [x for x in approved if x["provenance"]["evidenceId"] not in superseded]
            vals = {fingerprint(x["value"]) for x in approved}
            status = "CONFLICT" if len(vals) > 1 else "CONFIRMED" if vals else (
                "MISSING_REQUIRED" if spec["blocking"] else "MISSING_OPTIONAL")
            records[k] = dict(deepcopy(spec), status=status,
                              value=deepcopy(approved[0]["value"]) if len(vals) == 1 else None,
                              provenance=[x["provenance"] for x in c],
                              conflictingValues=deepcopy(approved) if len(vals) > 1 else [],
                              derivable=bool(spec.get("derivation")))
        def route():
            matrix = []
            required = set(r["classificationInputs"])
            for b in r["branches"]:
                cond = b.get("when")
                rec = records[cond["input"]] if cond else None
                status = ("APPLICABLE" if cond is None else "UNKNOWN" if rec["status"] not in ("CONFIRMED", "DERIVED")
                          else "APPLICABLE" if rec["value"] == cond["equals"] else "NOT_APPLICABLE")
                if cond:
                    required.add(cond["input"])
                matrix.append({"branchId": b["id"], "status": status, "blocking": b["blocking"],
                    "basis": deepcopy(cond), "evidence": deepcopy(rec["provenance"]) if rec else [
                        {"sourceId": r["id"], "revision": r["revision"], "verification": "VERIFIED"}],
                    "unresolvedConditions": [cond["input"]] if status == "UNKNOWN" else []})
                if cond and b["blocking"]:
                    rec["blocking"] = True
                    rec["requiredBy"] = sorted(set(rec["requiredBy"] + b["requiredBy"]))
                    if b["reason"] not in rec["reason"]:
                        rec["reason"] += "; " + b["reason"]
                    if rec["status"] == "MISSING_OPTIONAL":
                        rec["status"] = "MISSING_REQUIRED"
                if status == "APPLICABLE":
                    required.update(k for k,s in specs.items() if b["id"] in s.get("branches", []))
            required.update(k for k,s in specs.items() if not s.get("branches") and not s.get("evidenceOnly"))
            return matrix, required

        applicability, active = route()
        reaudit_passes = 0
        # Re-audit classification, applicability and newly activated requirements
        # after derivation. A finite registry bounds the number of routing changes.
        while True:
            changed = False
            for k in sorted(active):
                rec, d = records[k], specs[k].get("derivation")
                if rec["status"] not in ("MISSING_REQUIRED", "MISSING_OPTIONAL") or not d:
                    continue
                deps = [records[dep] for dep in d["inputs"]]
                if any(x["status"] != "CONFIRMED" for x in deps):
                    continue
                rec["status"] = "UNKNOWN_BUT_DERIVABLE"
                try:
                    if [x.get("unit") for x in deps] != d["inputUnits"] or rec.get("unit") != d["unit"]:
                        raise ValueError("derivation unit mismatch")
                    value = _derive(d["method"], [x["value"] for x in deps])
                    if not _valid(value, specs[k]):
                        raise ValueError("derived result outside accepted format/range")
                    rec.update(status="DERIVED", value=value, derivationMethod=d["method"])
                    rec["provenance"].append({"sourceKind": "SAFE_BIM_STATE", "sourceId": r["id"],
                        "revision": r["revision"], "method": d["method"], "unit": d["unit"], "result": value,
                        "verification": "VERIFIED", "inputEvidence": [deepcopy(x["provenance"]) for x in deps]})
                except (ValueError, TypeError, OverflowError) as exc:
                    rec["derivationError"] = str(exc)
                changed = True
            reaudit_passes += 1
            applicability, next_active = route()
            if next_active == active and not changed:
                break
            active = next_active
        classification_ok = all(records[k]["status"] in ("CONFIRMED", "DERIVED") for k in r["classificationInputs"])
        for k, rec in records.items():
            if k not in active:
                rec["status"] = "NOT_APPLICABLE"
                rec["value"] = None
        ordered = sorted((records[k] for k in active), key=lambda x: (
            CONTRACT["questionPriority"].index(x["priority"]), x["id"]))
        package = []
        for rec in ordered:
            if not rec["blocking"] or rec["status"] not in ("MISSING_REQUIRED", "CONFLICT", "UNKNOWN_BUT_DERIVABLE"):
                continue
            owner = "USER_CLIENT_SURVEYOR_MUST_PROVIDE" if rec["status"] == "CONFLICT" else (
                "SYSTEM_CAN_DERIVE" if rec["status"] == "UNKNOWN_BUT_DERIVABLE" else rec["owner"])
            package.append({"inputId": rec["id"], "status": rec["status"], "priority": rec["priority"],
                "question": ("Resolve conflicting values for " if rec["status"] == "CONFLICT" else "Provide ") +
                    rec["name"] + "; accepted format: " + ", ".join(rec["acceptedFormats"]) +
                    ("; units: " + rec["unit"] if rec.get("unit") else ""),
                "why": rec["reason"], "requiredBy": rec["requiredBy"], "acceptedFormats": rec["acceptedFormats"],
                "WHAT": rec["name"], "WHY": rec["reason"], "REQUIRED_BY": rec["requiredBy"],
                "FORMAT": {"type": rec["type"], "acceptedFormats": rec["acceptedFormats"], "unit": rec.get("unit")},
                "canDeriveAutomatically": rec["derivable"], "derivationMethod": rec.get("derivation"),
                "conflictingValues": rec["conflictingValues"],
                "resolutionOwner": owner, "provenance": {"requirement": {"sourceId": r["id"], "revision": r["revision"]},
                    "inspectedSources": sorted(seen), "evidence": rec["provenance"]}})
        user = [x for x in package if x["resolutionOwner"] == "USER_CLIENT_SURVEYOR_MUST_PROVIDE"]
        questions = [x for x in user if x["priority"] == user[0]["priority"]] if user and not collection_errors else []
        blocking = [x for x in ordered if x["blocking"]]
        proof = {"projectClassification": "VERIFIED" if classification_ok else "NOT_VERIFIED",
                 "applicabilityMatrixComplete": not any(x["status"] == "UNKNOWN" and x["blocking"] for x in applicability),
                 "requiredInputMatrixComplete": True,
                 "missingRequiredCount": sum(x["status"] == "MISSING_REQUIRED" for x in ordered),
                 "unresolvedConflictCount": sum(x["status"] == "CONFLICT" for x in ordered),
                 "blockingUnknownDerivableCount": sum(x["status"] == "UNKNOWN_BUT_DERIVABLE" for x in blocking),
                 "unapprovedAssumptionCount": unapproved_assumptions,
                 "provenanceCompleteForBlockingInputs": all(x["status"] in ("CONFIRMED", "DERIVED") and
                     any(p["verification"] == "VERIFIED" for p in x["provenance"]) for x in blocking),
                 "collectionComplete": not collection_errors}
        gate = all(proof.get(k) == v for k,v in CONTRACT["progressionGate"]["conditions"].items()) and proof["collectionComplete"]
        self._result = {"stage": CONTRACT["stage"], "status": "VERIFIED" if gate else "WAITING_FOR_USER_DATA",
            "flow": FLOW + (["VERIFIED"] if gate else []), "canProgress": gate, "gateProof": proof,
            "reAudit": {"passes": reaudit_passes, "routingStable": True},
            "contextFingerprint": fingerprint([r, self._sources]),
            "projectClassification": {"status": proof["projectClassification"],
                "inputs": {k: deepcopy(records[k]) for k in r["classificationInputs"]}},
            "applicabilityMatrix": applicability, "inputs": ordered,
            "missingRequired": [x["id"] for x in ordered if x["status"] == "MISSING_REQUIRED"],
            "missingOptional": [x["id"] for x in ordered if x["status"] == "MISSING_OPTIONAL"],
            "conflicts": [x["id"] for x in ordered if x["status"] == "CONFLICT"],
            "derived": [x["id"] for x in ordered if x["status"] == "DERIVED"],
            "REQUIRED_USER_INPUT_PACKAGE": package, "questions": questions,
            "provenanceComplete": proof["provenanceCompleteForBlockingInputs"], "collectionErrors": collection_errors}
        return self.result()


def main():
    """File-to-file end-to-end entry point, including answer ingestion and re-audit."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--answers", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    engine = Stage0(load(args.registry), load(args.sources))
    result = engine.audit()
    if args.answers:
        for answer in load(args.answers):
            engine.update_source(answer)
        result = engine.audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if result["canProgress"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
