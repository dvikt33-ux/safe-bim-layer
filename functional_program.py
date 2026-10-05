"""FUNCTIONAL PROGRAM v0: explicit user program, independently of norms/layout.

Consumes a live Stage0 session and inspected, user-approved brief records.
No transport, runtime execution, normative numbers or geometric placement.
"""
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from design_stage0 import Stage0, fingerprint


FLOW = ["VERIFIED STAGE 0", "EXTRACT USER PROGRAM", "NORMALIZE FUNCTIONS",
        "BUILD SPACE PROGRAM", "BUILD RELATIONSHIPS", "IDENTIFY FUNCTIONAL GAPS",
        "RE-AUDIT"]
CATEGORIES = {"USER_REQUIREMENT", "USER_PREFERENCE", "DERIVED_RELATIONSHIP",
              "NORMATIVE_REQUIREMENT_PENDING", "MISSING_FUNCTIONAL_INPUT", "NOT_APPLICABLE"}
RELATION_TYPES = {"REQUIRED_ADJACENCY", "PREFERRED_ADJACENCY", "AVOID_ADJACENCY",
                 "REQUIRED_ACCESS", "VISUAL_CONNECTION", "EXTERNAL_ACCESS",
                 "VERTICAL_CONNECTION", "SEPARATION_REQUIRED"}
ZONES = {"public", "private", "service", "technical", "staff", "circulation", "outdoor/site-related"}
FIELDS = {"function", "quantity", "requestedArea", "preferredFloor", "accessLevel", "privacyLevel",
          "noiseSensitivity", "noiseGeneration", "daylightPreference", "specialEquipment", "functionalZone"}
PREFERENCE_FIELDS = {"preferredFloor", "daylightPreference"}
ALIASES = {
    "спальня": "BEDROOM", "спальни": "BEDROOM", "спален": "BEDROOM", "bedroom": "BEDROOM", "bedrooms": "BEDROOM",
    "кухня": "KITCHEN", "кухни": "KITCHEN", "кухонь": "KITCHEN", "kitchen": "KITCHEN",
    "гостиная": "LIVING_ROOM", "гостиные": "LIVING_ROOM", "living room": "LIVING_ROOM",
    "кабинет": "OFFICE", "кабинета": "OFFICE", "кабинетов": "OFFICE", "office": "OFFICE",
    "гараж": "GARAGE", "гаража": "GARAGE", "гаражей": "GARAGE", "garage": "GARAGE",
    "холл": "HALL", "холла": "HALL", "hall": "HALL", "ванная": "BATHROOM", "bathroom": "BATHROOM",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))


def normalize_function(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("function must be an explicit nonempty label")
    value = value.strip()
    if value.lower() in ALIASES:
        return ALIASES[value.lower()]
    if re.fullmatch(r"[A-Z][A-Z0-9_]*", value):
        return value
    raise ValueError("unsupported function label; supply an explicit stable function code")


def _positive_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate_field(field, value):
    if field == "function":
        return normalize_function(value)
    if field == "quantity":
        if type(value) is not int or value < 1:
            raise ValueError("quantity requires an explicit positive integer")
    elif field == "requestedArea":
        if not isinstance(value, dict) or value.get("unit") != "m2":
            raise ValueError("requested area requires m2 and an explicit value/range")
        if set(value) == {"value", "unit"} and _positive_number(value["value"]):
            pass
        elif set(value) == {"min", "max", "unit"} and all(_positive_number(value[x]) for x in ("min", "max")) and value["min"] <= value["max"]:
            pass
        else:
            raise ValueError("invalid requested area/range")
    elif field == "functionalZone":
        if value not in ZONES:
            raise ValueError("unknown explicitly assigned functional zone")
    elif field == "specialEquipment":
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
            raise ValueError("special equipment requires explicit nonempty descriptions")
        value = sorted(set(value))
    elif field == "preferredFloor":
        if not (type(value) is int or isinstance(value, str) and value.strip()):
            raise ValueError("preferred floor requires an explicit floor identifier")
    elif not isinstance(value, str) or not value.strip():
        raise ValueError("explicit nonempty functional attribute required")
    return deepcopy(value)


def extract_text(text):
    """Bounded explicit grammar; unrecognized lines remain blocking, never vanish.

    One statement per line. No probabilistic extraction or typical room program.
    """
    statements, unresolved = [], []
    functions = "|".join(re.escape(x) for x in sorted(ALIASES, key=len, reverse=True))
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().rstrip(".").strip()
        if not line:
            continue
        home = re.fullmatch(r"Дом для семьи из (\d+) человек(?:, (\d+|два|один|три) этаж(?:а|ей)?)?", line, re.I)
        room = re.fullmatch(r"(\d+)\s+(" + functions + r")(?:\s+(?:по\s+)?(\d+(?:[.,]\d+)?)\s*(?:м2|м²|m2))?", line, re.I)
        if home:
            statements.append({"id": "text-users", "kind": "USER_GROUP", "userId": "family",
                               "quantity": int(home[1]), "label": "family", "textSpan": [line_no, raw]})
            if home[2]:
                floors = {"один": 1, "два": 2, "три": 3}.get(home[2].lower())
                statements.append({"id": "text-floors", "kind": "CONTEXT", "inputId": "floor_count",
                                   "value": floors if floors is not None else int(home[2]), "textSpan": [line_no, raw]})
        elif room:
            function = normalize_function(room[2])
            item = {"id": "text-" + function.lower(), "kind": "SPACE", "spaceId": "space_" + function.lower(),
                    "function": function, "quantity": int(room[1]), "textSpan": [line_no, raw]}
            if room[3]:
                item["requestedArea"] = {"value": float(room[3].replace(",", ".")), "unit": "m2"}
            statements.append(item)
        else:
            unresolved.append({"id": "text-line-" + str(line_no), "text": raw})
    return statements, unresolved


class FunctionalProgram:
    """Re-auditable user program, bound to a Stage0 session rather than a status string."""

    def __init__(self, stage0, sources, project_type_input="purpose"):
        if not isinstance(stage0, Stage0):
            raise TypeError("a Stage0 session with a verified gate is required")
        self._stage0 = stage0
        self._sources = deepcopy(sources)
        self._project_type_input = project_type_input
        self._result = None

    def _refresh_dependency(self):
        if not self._result or not self._result.get("dependencyVerified"):
            return
        current = self._stage0.result()
        if not current or current["status"] != "VERIFIED" or current["contextFingerprint"] != self._result["stage0Fingerprint"]:
            self._result.update(status="INVALIDATED", canProgress=False, invalidationReason="STAGE0_CHANGED_OR_NOT_VERIFIED")

    def result(self):
        self._refresh_dependency()
        return deepcopy(self._result)

    def update_source(self, source):
        replacement = [x for x in self._sources if x.get("id") != source.get("id")] + [deepcopy(source)]
        if fingerprint(sorted(replacement, key=canonical)) != fingerprint(sorted(self._sources, key=canonical)):
            self._sources = replacement
            if self._result:
                self._result.update(status="INVALIDATED", canProgress=False)

    def require_verified(self):
        self._refresh_dependency()
        self._stage0.require_verified()
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"]:
            raise RuntimeError("Functional Program progression blocked")
        if self._result["briefFingerprint"] != fingerprint(sorted(self._sources, key=canonical)):
            raise RuntimeError("Functional Program brief changed")
        return deepcopy(self._result["gateProof"])

    def audit(self):
        self._refresh_dependency()
        previous = self._result
        s0 = self._stage0.result()
        try:
            self._stage0.require_verified()
        except RuntimeError:
            status = "INVALIDATED" if previous and previous["stage0Fingerprint"] else "BLOCKED"
            self._result = self._empty(status, s0)
            self._result["blockers"] = ["STAGE_0_NOT_VERIFIED"]
            return self.result()
        output = self._empty("BLOCKED", s0)
        output["dependencyVerified"] = True
        output["flow"] = list(FLOW)
        known = {x["id"]: x for x in s0["inputs"] if x["status"] in ("CONFIRMED", "DERIVED")}
        project_type = known.get(self._project_type_input)
        output["projectType"] = project_type["value"] if project_type else None
        output["stage0Context"] = deepcopy(known)
        claims, relation_claims, groups, exclusions = [], [], [], []
        space_ids, user_ids = set(), set()
        errors, missing = [], []
        source_ids = set()

        def gap(id, what, why, format, provenance, priority=1):
            missing.append({"inputId": id, "category": "MISSING_FUNCTIONAL_INPUT", "blocking": True,
                            "priority": priority, "WHAT": what, "WHY": why,
                            "REQUIRED_BY": ["FUNCTIONAL_PROGRAM/" + id], "FORMAT": format,
                            "provenance": deepcopy(provenance)})

        for source in sorted(self._sources, key=canonical):
            sid = source.get("id")
            if not sid or sid in source_ids or not source.get("revision") or source.get("kind") not in (
                    "USER_BRIEF", "USER_CORRECTION", "APPROVED_PROJECT_DECISION") or source.get("approved") is not True or source.get("inspected") is not True:
                errors.append({"sourceId": sid, "reason": "unique inspected user-approved versioned source required"})
                continue
            source_ids.add(sid)
            if set(source) - {"id", "revision", "kind", "approved", "inspected", "text", "statements"}:
                errors.append({"sourceId": sid, "reason": "unsupported source fields; normalize the brief explicitly"})
            statements = deepcopy(source.get("statements", []))
            if "text" in source:
                parsed, unresolved = extract_text(source["text"])
                statements += parsed
                for line in unresolved:
                    gap(sid + ":" + line["id"], "Normalize this explicit brief line: " + line["text"],
                        "Unparsed user intent cannot be dropped from the program", "structured statement with source reference",
                        [{"sourceId": sid, "revision": source["revision"], "text": line["text"]}], 0)
            seen_statements = set()
            for st in sorted(statements, key=canonical):
                stid = st.get("id")
                if not stid or stid in seen_statements:
                    errors.append({"sourceId": sid, "reason": "unique stable statement IDs required"})
                    continue
                seen_statements.add(stid)
                prov = {"sourceKind": source["kind"], "sourceId": sid, "revision": source["revision"],
                        "statementId": stid, "verification": "USER_APPROVED", "method": "EXPLICIT_TEXT_GRAMMAR_V0" if "textSpan" in st else "EXPLICIT_STRUCTURED_BRIEF",
                        "supersedes": st.get("supersedes", [])}
                if "textSpan" in st:
                    prov["textSpan"] = deepcopy(st["textSpan"])
                category = st.get("category", "USER_REQUIREMENT")
                if category not in ("USER_REQUIREMENT", "USER_PREFERENCE", "NOT_APPLICABLE") or st.get("assumed") or st.get("basis") in (
                        "GUESSED_VALUE", "TYPICAL_VALUE", "UNAPPROVED_DEFAULT", "PLACEHOLDER", "STATISTICALLY_LIKELY_VALUE"):
                    errors.append({"sourceId": sid, "statementId": stid, "reason": "unapproved assumption or non-user category"})
                    continue
                kind = st.get("kind")
                common = {"id", "kind", "category", "supersedes", "assumed", "basis", "textSpan"}
                allowed = {
                    "SPACE": {"spaceId"} | FIELDS, "SPACE_ATTRIBUTE": {"spaceId", "field", "value"},
                    "RELATIONSHIP": {"type", "from", "to"}, "ACCESS_GROUP": {"via", "members"},
                    "USER_GROUP": {"userId", "label", "quantity"}, "CONTEXT": {"inputId", "value"},
                    "EXCLUDE_FUNCTION": {"function", "reason"}}.get(kind)
                if allowed is None or set(st) - common - allowed:
                    errors.append({"sourceId": sid, "statementId": stid, "reason": "unsupported statement/fields; no norms or geometry accepted"})
                    continue

                def add_claim(target, field, value, cat):
                    normalized = validate_field(field, value) if target.startswith("space:") else deepcopy(value)
                    if field in PREFERENCE_FIELDS:
                        cat = "USER_PREFERENCE"
                    if cat == "NOT_APPLICABLE":
                        raise ValueError("excluded functions require EXCLUDE_FUNCTION")
                    if field in ("function", "quantity") and cat != "USER_REQUIREMENT":
                        raise ValueError("space identity and quantity require an explicit user requirement")
                    claims.append({"target": target, "field": field, "value": normalized, "category": cat,
                                   "claimId": sid + ":" + stid + ":" + field, "provenance": deepcopy(prov)})

                try:
                    if kind in ("SPACE", "SPACE_ATTRIBUTE"):
                        space_id = st.get("spaceId")
                        if not isinstance(space_id, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", space_id):
                            raise ValueError("stable explicit spaceId required")
                        space_ids.add(space_id)
                        if kind == "SPACE":
                            for field in sorted(FIELDS & set(st)):
                                add_claim("space:" + space_id, field, st[field], category)
                        else:
                            if st.get("field") not in FIELDS or "value" not in st:
                                raise ValueError("supported field/value required")
                            add_claim("space:" + space_id, st["field"], st["value"], category)
                    elif kind == "USER_GROUP":
                        uid = st.get("userId")
                        if not isinstance(uid, str) or not uid.strip() or type(st.get("quantity")) is not int or st["quantity"] < 1:
                            raise ValueError("explicit user group ID and positive quantity required")
                        user_ids.add(uid)
                        add_claim("user:" + uid, "quantity", st["quantity"], category)
                        if "label" in st:
                            if not isinstance(st["label"], str) or not st["label"].strip():
                                raise ValueError("explicit user group label required")
                            add_claim("user:" + uid, "label", st["label"], category)
                    elif kind == "CONTEXT":
                        if st.get("inputId") not in known:
                            raise ValueError("CONTEXT must reference a confirmed Stage0 datum")
                        add_claim("context:" + st["inputId"], "value", st["value"], category)
                    elif kind == "RELATIONSHIP":
                        if st.get("type") not in RELATION_TYPES or not all(isinstance(st.get(k), str) and st[k] for k in ("from", "to")):
                            raise ValueError("explicit supported relationship and endpoints required")
                        if category not in ("USER_REQUIREMENT", "USER_PREFERENCE"):
                            raise ValueError("relationship requires an explicit user category")
                        if st["type"] == "PREFERRED_ADJACENCY":
                            category = "USER_PREFERENCE"
                        if category == "USER_PREFERENCE" and st["type"] in ("REQUIRED_ADJACENCY", "REQUIRED_ACCESS", "SEPARATION_REQUIRED"):
                            raise ValueError("preference cannot become a mandatory relationship")
                        relation_claims.append(dict(type=st["type"], **{"from": st["from"], "to": st["to"]},
                                                    category=category, provenance=[prov], claimId=sid + ":" + stid + ":relationship"))
                    elif kind == "ACCESS_GROUP":
                        if category != "USER_REQUIREMENT" or not isinstance(st.get("via"), str) or not st["via"] or not isinstance(st.get("members"), list) or not st["members"] or any(not isinstance(x, str) or not x for x in st["members"]):
                            raise ValueError("explicit shared access instruction with hub and members required")
                        groups.append(dict(via=st["via"], members=sorted(set(st["members"])), provenance=[prov],
                                           claimId=sid + ":" + stid + ":relationship"))
                    else:
                        if category != "NOT_APPLICABLE" or not st.get("reason"):
                            raise ValueError("exclusion requires NOT_APPLICABLE and explicit reason")
                        exclusions.append({"function": normalize_function(st["function"]), "category": category,
                                           "reason": st["reason"], "provenance": [prov]})
                except (ValueError, TypeError) as exc:
                    errors.append({"sourceId": sid, "statementId": stid, "reason": str(exc)})

        # Explicit corrections supersede individual claims, never silently by date.
        all_claims = claims + relation_claims + groups
        superseded = set()
        for x in all_claims:
            p = x["provenance"][0] if isinstance(x["provenance"], list) else x["provenance"]
            if p["sourceKind"] in ("USER_CORRECTION", "APPROVED_PROJECT_DECISION"):
                superseded.update(p["supersedes"])
        claims = [x for x in claims if x["claimId"] not in superseded]
        relation_claims = [x for x in relation_claims if x["claimId"] not in superseded]
        groups = [x for x in groups if x["claimId"] not in superseded]
        resolved, conflicts = {}, []
        keys = sorted({(x["target"], x["field"], x["category"]) for x in claims})
        for target, field, category in keys:
            values = [x for x in claims if (x["target"], x["field"], x["category"]) == (target, field, category)]
            if len({canonical(x["value"]) for x in values}) != 1:
                conflicts.append({"target": target, "field": field, "category": category, "candidates": deepcopy(values)})
                continue
            entry = {"value": values[0]["value"], "source": category, "category": category,
                     "status": "CONFIRMED", "provenance": sorted([x["provenance"] for x in values], key=canonical)}
            if field == "requestedArea":
                entry = {**values[0]["value"], **{k:v for k,v in entry.items() if k != "value"}}
            resolved[(target, field, category)] = entry
            output["userRequirements" if category == "USER_REQUIREMENT" else "userPreferences"].append(
                dict(target=target, field=field, **deepcopy(entry)))

        for sid in sorted(space_ids):
            space = {"spaceId": sid, **{f: None for f in sorted(FIELDS)}, "preferences": {}, "provenance": [],
                     "status": "CONFIRMED", "category": "USER_REQUIREMENT",
                     "normativeMinimum": {"status": "NORMATIVE_REQUIREMENT_PENDING", "category": "NORMATIVE_REQUIREMENT_PENDING"}}
            for field in sorted(FIELDS):
                mandatory = resolved.get(("space:" + sid, field, "USER_REQUIREMENT"))
                preferred = resolved.get(("space:" + sid, field, "USER_PREFERENCE"))
                space[field] = deepcopy(mandatory or (preferred if field in PREFERENCE_FIELDS else None))
                if preferred:
                    space["preferences"][field] = deepcopy(preferred)
                if mandatory or preferred:
                    space["provenance"] += deepcopy((mandatory or preferred)["provenance"])
            for field in ("function", "quantity"):
                if space[field] is None:
                    if not any(x.get("target") == "space:" + sid and x.get("field") == field for x in conflicts):
                        gap("space:" + sid + ":" + field, "Specify " + field + " for " + sid,
                            "This explicitly requested function cannot be counted without its " + field,
                            "positive integer" if field == "quantity" else "explicit function code", space["provenance"])
                    space["status"] = "MISSING_FUNCTIONAL_INPUT"
            output["spaces"].append(space)
            output["normativeRequirementsPending"].append({"spaceId": sid, "requirement": "normativeMinimum",
                "category": "NORMATIVE_REQUIREMENT_PENDING", "status": "NORMATIVE_REQUIREMENT_PENDING",
                "provenance": [{"method": "DEFER_TO_PROJECT_NORMATIVE_BUNDLE", "inputEvidence": space["provenance"]}]})

        for uid in sorted(user_ids):
            fields = {field: deepcopy(rec) for (target,field,cat),rec in resolved.items() if target == "user:" + uid}
            output["users"].append(dict(userId=uid, **fields))
        for (target, field, category), rec in resolved.items():
            if target.startswith("context:") and category == "USER_REQUIREMENT":
                input_id = target.removeprefix("context:")
                if canonical(rec["value"]) != canonical(known[input_id]["value"]):
                    conflicts.append({"target": target, "field": field, "reason": "user brief conflicts with VERIFIED Stage0",
                                      "userEvidence": rec, "stage0Evidence": known[input_id]})
        output["notApplicable"] = sorted(exclusions, key=canonical)
        for excluded in exclusions:
            for space in output["spaces"]:
                if space["function"] and space["function"]["value"] == excluded["function"]:
                    conflicts.append({"target": "space:" + space["spaceId"], "reason": "required and explicitly excluded function",
                                      "requiredEvidence": space["provenance"], "excludedEvidence": excluded["provenance"]})

        for group in groups:
            for member in group["members"]:
                relation_claims.append({"type": "REQUIRED_ACCESS", "from": group["via"], "to": member,
                    "category": "DERIVED_RELATIONSHIP", "derivationRule": "EXPLICIT_ACCESS_GROUP_EXPANSION_V1",
                    "provenance": [{"method": "EXPLICIT_ACCESS_GROUP_EXPANSION_V1", "verification": "TRACEABLE",
                                    "inputEvidence": deepcopy(group["provenance"])}]})
        relations = {}
        for rel in sorted(relation_claims, key=canonical):
            if rel["from"] == rel["to"]:
                errors.append({"reason": "self relationship is not a resolved functional instruction", "relationship": rel})
                continue
            absent = sorted({x for x in (rel["from"], rel["to"]) if x not in space_ids and not (
                rel["type"] == "EXTERNAL_ACCESS" and x == "EXTERIOR")})
            if absent:
                gap("relationship:" + fingerprint([rel["type"], rel["from"], rel["to"]])[:16],
                    "Identify explicitly referenced spaces: " + ", ".join(absent),
                    "A confirmed relationship needs resolved space endpoints", "spaceId/function/quantity or explicit correction",
                    rel["provenance"])
                continue
            symmetric = rel["type"] in ("REQUIRED_ADJACENCY", "PREFERRED_ADJACENCY", "AVOID_ADJACENCY", "VISUAL_CONNECTION", "SEPARATION_REQUIRED")
            endpoints = sorted([rel["from"], rel["to"]]) if symmetric else [rel["from"], rel["to"]]
            key = (rel["type"], *endpoints, rel["category"])
            if key not in relations:
                relations[key] = {k:deepcopy(v) for k,v in rel.items() if k != "claimId"}
                relations[key].update({"from": endpoints[0], "to": endpoints[1], "relationshipId": "rel_" + fingerprint(key)[:20], "status": "CONFIRMED"})
            else:
                relations[key]["provenance"] += deepcopy(rel["provenance"])
        output["relationships"] = sorted(relations.values(), key=canonical)
        output["derivedRelationships"] = [deepcopy(x) for x in output["relationships"] if x["category"] == "DERIVED_RELATIONSHIP"]
        for rel in output["relationships"]:
            if rel["category"] in ("USER_REQUIREMENT", "USER_PREFERENCE"):
                output["userRequirements" if rel["category"] == "USER_REQUIREMENT" else "userPreferences"].append(deepcopy(rel))
            if rel["type"] == "REQUIRED_ADJACENCY" and rel["category"] == "USER_REQUIREMENT":
                opposites = [x for x in output["relationships"] if x["type"] in ("AVOID_ADJACENCY", "SEPARATION_REQUIRED")
                             and x["category"] == "USER_REQUIREMENT" and (x["from"], x["to"]) == (rel["from"], rel["to"])]
                if opposites:
                    conflicts.append({"reason": "required adjacency conflicts with explicit avoidance/separation", "relationships": [rel] + opposites})
        for zone in sorted(ZONES):
            assigned = [x for x in output["spaces"] if x["functionalZone"] and x["functionalZone"]["value"] == zone]
            if assigned:
                output["functionalZones"].append({"zone": zone, "spaceIds": sorted(x["spaceId"] for x in assigned),
                    "category": "USER_REQUIREMENT", "provenance": sorted([p for x in assigned for p in x["functionalZone"]["provenance"]], key=canonical)})
        if not project_type:
            gap("projectType", "Map the verified project type input", "Functional program must be tied to the verified project class",
                "Stage0 input ID containing project type", [{"stage0Fingerprint": output["stage0Fingerprint"]}], 0)
        if not output["spaces"]:
            gap("programScope", "Which spaces/functions are required, and how many of each?",
                "A functional space program cannot be built from household size alone; no room list is assumed",
                "explicit function list with stable IDs and quantities", [{"inspectedSources": sorted(source_ids)}], 0)
        output["missingFunctionalInputs"] = sorted(missing, key=lambda x:(x["priority"], x["inputId"]))
        output["questions"] = [deepcopy(x) for x in output["missingFunctionalInputs"] if x["priority"] == output["missingFunctionalInputs"][0]["priority"]] if missing and not errors and not conflicts else []
        output["conflicts"] = sorted(conflicts, key=canonical)
        if conflicts and not errors:
            output["questions"] = [{"inputId": "conflict:" + fingerprint(c)[:16],
                "category": "MISSING_FUNCTIONAL_INPUT", "blocking": True, "priority": 0,
                "WHAT": "Resolve conflicting user requirements for " + c.get("target", "relationship") +
                    (" / " + c["field"] if "field" in c else ""),
                "WHY": "Competing explicit requirements prevent a verified functional program",
                "REQUIRED_BY": ["FUNCTIONAL_PROGRAM/CONFLICTS"],
                "FORMAT": "USER_CORRECTION with explicit value and superseded claim IDs",
                "provenance": deepcopy(c)} for c in output["conflicts"]]
        output["validationErrors"] = sorted(errors, key=canonical)
        confirmed = output["userRequirements"] + output["userPreferences"] + output["relationships"]
        covered = sum(bool(x["provenance"]) for x in confirmed)
        coverage = 1.0 if not confirmed else covered / len(confirmed)
        provenance_complete = coverage == 1 and all(x["provenance"] and x["status"] == "CONFIRMED" for x in output["spaces"])
        proof = {"stage0Verified": True, "blockingFunctionalInputsResolved": not missing,
                 "conflictsCount": len(conflicts), "validationErrorsCount": len(errors),
                 "provenanceCoverage": coverage, "provenanceComplete": provenance_complete,
                 "inventedNormativeValuesCount": 0, "unapprovedAssumptionsCount": 0,
                 "deterministic": True}
        gate = not missing and not conflicts and not errors and provenance_complete
        output.update(status="VERIFIED" if gate else "BLOCKED" if errors or conflicts else "WAITING_FOR_USER_DATA",
                      canProgress=gate, gateProof=proof, provenanceComplete=provenance_complete)
        if gate:
            output["flow"].append("FUNCTIONAL_PROGRAM VERIFIED")
        for space in output["spaces"]:
            space["identityRequirements"] = {f: deepcopy(space[f]) for f in ("function", "quantity")}
            for field in ("function", "quantity"):
                space[field] = space[field]["value"] if space[field] else None
        output["programFingerprint"] = fingerprint({k:v for k,v in output.items() if k != "programFingerprint"})
        self._result = output
        return self.result()

    def _empty(self, status, stage0):
        return {"stage": "FUNCTIONAL_PROGRAM", "schemaVersion": 0, "status": status,
                "stage0Fingerprint": stage0["contextFingerprint"] if stage0 else None,
                "briefFingerprint": fingerprint(sorted(self._sources, key=canonical)), "projectType": None,
                "users": [], "spaces": [], "functionalZones": [], "relationships": [],
                "userRequirements": [], "userPreferences": [], "derivedRelationships": [],
                "normativeRequirementsPending": [], "missingFunctionalInputs": [], "conflicts": [],
                "notApplicable": [], "questions": [], "provenanceComplete": False, "canProgress": False,
                "dependencyVerified": False}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("stage0-registry", "stage0-sources", "brief", "output"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--answers", type=Path)
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    stage0 = Stage0(load(args.stage0_registry), load(args.stage0_sources))
    stage0.audit()
    engine = FunctionalProgram(stage0, load(args.brief))
    output = engine.audit()
    if args.answers:
        for answer in load(args.answers):
            engine.update_source(answer)
        output = engine.audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if output["canProgress"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
