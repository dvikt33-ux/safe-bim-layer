"""DESIGN INTENT / PROJECT GOALS v0. Offline optimization intent, never norms/layout."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from design_stage0 import Stage0, fingerprint
from functional_program import FunctionalProgram, canonical

FLOW = ["REQUIRE VERIFIED STAGE 0", "REQUIRE VERIFIED FUNCTIONAL PROGRAM", "COLLECT DESIGN INTENT",
        "NORMALIZE GOALS", "CLASSIFY GOALS", "ASSIGN PRIORITIES", "BUILD TRADEOFF MATRIX",
        "DETECT CONFLICTS", "IDENTIFY MISSING DECISIONS", "RE-AUDIT"]
GOAL_TYPES = {"COMPACTNESS", "SPACIOUSNESS", "MINIMIZE_CIRCULATION", "PRIVACY", "OPEN_PLAN",
    "SITE_CONNECTION", "DAYLIGHT_PREFERENCE", "VIEW_PRIORITY", "LOW_COST", "LOW_OPERATING_COST",
    "CONSTRUCTION_SIMPLICITY", "STRUCTURAL_REGULARITY", "MASONRY_MODULARITY", "FLEXIBILITY",
    "FUTURE_EXPANSION", "ACCESSIBILITY_PREFERENCE", "ACOUSTIC_COMFORT", "ENERGY_EFFICIENCY_PREFERENCE",
    "AESTHETIC_DIRECTION", "CUSTOM"}
SOURCES = {"USER_REQUIREMENT", "USER_PREFERENCE", "APPROVED_PROJECT_DECISION", "DERIVED_DESIGN_INTENT", "NORMATIVE_PENDING"}
# Potential optimization tensions only: no numeric thresholds or feasibility claims.
TRADEOFF_PAIRS = {frozenset(pair) for pair in (
    ("SPACIOUSNESS", "LOW_COST"), ("OPEN_PLAN", "ACOUSTIC_COMFORT"),
    ("DAYLIGHT_PREFERENCE", "LOW_COST"), ("FUTURE_EXPANSION", "COMPACTNESS"),
    ("PRIVACY", "OPEN_PLAN"), ("COMPACTNESS", "SPACIOUSNESS"))}
DERIVATION_RULE = "EXPLICIT_SIMPLE_LOW_COST_NO_COMPLEX_STRUCTURES_V0"
DERIVATION_TEXT = "хочу максимально простой и дешёвый дом без сложных конструкций"


def _number(value, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (value > 0 if positive else value >= 0)


def _id(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value))


class DesignIntent:
    def __init__(self, stage0, functional_program, sources):
        if not isinstance(stage0, Stage0) or not isinstance(functional_program, FunctionalProgram):
            raise TypeError("live Stage0 and FunctionalProgram sessions required")
        self._stage0, self._functional = stage0, functional_program
        self._sources = deepcopy(sources)
        self._result = None

    def _refresh(self):
        if not self._result or not self._result.get("dependencyVerified"):
            return
        s0, fp = self._stage0.result(), self._functional.result()
        if not s0 or not fp or s0["status"] != "VERIFIED" or fp["status"] != "VERIFIED" or (
                s0["contextFingerprint"] != self._result["stage0Fingerprint"] or
                fp["programFingerprint"] != self._result["functionalProgramFingerprint"]):
            self._result.update(status="INVALIDATED", canProgress=False, invalidationReason="UPSTREAM_CHANGED_OR_NOT_VERIFIED")

    def result(self):
        self._refresh()
        return deepcopy(self._result)

    def update_source(self, source):
        new = [x for x in self._sources if x.get("id") != source.get("id")] + [deepcopy(source)]
        if fingerprint(sorted(new, key=canonical)) != fingerprint(sorted(self._sources, key=canonical)):
            self._sources = new
            if self._result:
                self._result.update(status="INVALIDATED", canProgress=False, invalidationReason="INTENT_SOURCE_CHANGED")

    def require_verified(self):
        self._refresh()
        self._stage0.require_verified()
        self._functional.require_verified()
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"] or (
                self._result["sourceFingerprint"] != fingerprint(sorted(self._sources, key=canonical))):
            raise RuntimeError("Design Intent progression blocked")
        return deepcopy(self._result["gateProof"])

    def audit(self):
        self._refresh()
        previously_bound = bool(self._result and self._result.get("dependencyVerified"))
        s0, fp = self._stage0.result(), self._functional.result()
        out = self._empty(s0, fp)
        try:
            self._stage0.require_verified()
            self._functional.require_verified()
            if fp["stage0Fingerprint"] != s0["contextFingerprint"]:
                raise RuntimeError("Functional Program belongs to a different Stage0 context")
        except RuntimeError as exc:
            out.update(status="INVALIDATED" if previously_bound else "BLOCKED", blockers=[str(exc)],dependencyVerified=previously_bound)
            self._result = out
            return self.result()
        out.update(dependencyVerified=True, flow=list(FLOW))
        if out["sourceFingerprint"] is None or not isinstance(self._sources,list) or any(not isinstance(s,dict) for s in self._sources):
            out["validationErrors"] = [{"reason":"finite JSON source records required"}]
            out["designIntentFingerprint"] = fingerprint(out)
            self._result = out
            return self.result()
        errors, conflicts, candidates, decisions, missing = [], [], [], [], []
        no_goals = []
        seen = set()

        def gap(id, what, why, evidence, priority=1, **details):
            missing.append({"decisionId": id, "status": "MISSING_DESIGN_DECISION", "blocking": True,
                "priority": priority, "WHAT": what, "WHY": why, "REQUIRED_BY": ["DESIGN_INTENT/" + id],
                "FORMAT": "approved explicit goal/priority or context-bound tradeoff decision",
                "provenance": deepcopy(evidence), **deepcopy(details)})

        for source in sorted(self._sources, key=canonical):
            sid = source.get("id")
            if not _id(sid) or sid in seen or not source.get("revision") or source.get("kind") not in (
                    "USER_BRIEF", "USER_CORRECTION", "APPROVED_PROJECT_DECISION") or source.get("approved") is not True or source.get("inspected") is not True:
                errors.append({"sourceId": sid, "reason": "unique inspected user-approved source/revision required"})
                continue
            seen.add(sid)
            if set(source) - {"id", "kind", "revision", "approved", "inspected", "statements"}:
                errors.append({"sourceId": sid, "reason": "unsupported source fields"})
            if not isinstance(source.get("statements",[]),list) or any(not isinstance(s,dict) for s in source.get("statements",[])):
                errors.append({"sourceId":sid,"reason":"statement records must be a list of objects"})
                continue
            statement_ids = set()
            for st in sorted(source.get("statements", []), key=canonical):
                stid = st.get("id")
                if not _id(stid) or stid in statement_ids:
                    errors.append({"sourceId": sid, "reason": "stable unique statement IDs required"})
                    continue
                statement_ids.add(stid)
                if not isinstance(st.get("supersedes",[]),list) or any(not isinstance(x,str) or not x for x in st.get("supersedes",[])):
                    errors.append({"sourceId":sid,"statementId":stid,"reason":"explicit superseded statement references required"})
                    continue
                p = {"sourceId": sid, "sourceKind": source["kind"], "revision": source["revision"], "statementId": stid,
                     "verification": "USER_APPROVED", "method": "EXPLICIT_USER_INTENT", "supersedes": st.get("supersedes", [])}
                kind = st.get("kind")
                common = {"id", "kind", "supersedes"}
                allowed = {"GOAL": {"goalId", "type", "status", "priority", "weight", "scope", "target", "tolerance", "source", "commitment", "description"},
                    "DESIGN_STATEMENT": {"text", "priority", "priorities"},
                    "TRADEOFF_DECISION": {"goals", "policy", "preferredGoal", "goalFingerprints", "overridePriorityOrder"},
                    "NORMATIVE_PENDING": {"topic"}, "NO_DESIGN_GOALS": {"reason"}}.get(kind)
                if allowed is None or set(st) - allowed - common:
                    errors.append({"sourceId": sid, "statementId": stid, "reason": "unsupported intent fields; no norms, assumptions or geometry accepted"})
                    continue
                if kind == "NORMATIVE_PENDING":
                    if not isinstance(st.get("topic"), str) or not st["topic"].strip():
                        errors.append({"sourceId": sid, "statementId": stid, "reason": "pending topic label required"})
                    else:
                        out["normativePending"].append({"source": "NORMATIVE_PENDING", "status": "NORMATIVE_PENDING", "topic": st["topic"], "provenance": [p]})
                    continue
                if kind == "NO_DESIGN_GOALS":
                    if not isinstance(st.get("reason"), str) or not st["reason"].strip():
                        errors.append({"sourceId": sid, "reason": "explicit no-goals decision requires a reason"})
                    else:
                        no_goals.append(p)
                    continue
                if kind == "TRADEOFF_DECISION":
                    ids, bindings = st.get("goals"), st.get("goalFingerprints")
                    if not isinstance(ids,list) or len(ids) != 2 or any(not _id(x) for x in ids) or len(set(ids)) != 2 or (
                        not isinstance(bindings,dict) or set(bindings) != set(ids) or
                        any(not isinstance(x,str) or not re.fullmatch(r"[0-9a-f]{64}",x) for x in bindings.values())):
                        errors.append({"sourceId":sid,"statementId":stid,"reason":"two goal IDs and their exact fingerprints required"})
                        continue
                    decisions.append(dict(deepcopy(st), provenance=[p], claimId=sid + ":" + stid))
                    continue
                goal_specs = []
                if kind == "DESIGN_STATEMENT":
                    text = st.get("text")
                    if not isinstance(text, str) or text.strip().rstrip(".! ").lower().replace("дешевый", "дешёвый") != DERIVATION_TEXT:
                        gap(sid + ":" + stid, "Normalize the exact design statement into explicit goals",
                            "The bounded derivation rule cannot interpret this statement safely", [p], 0)
                        continue
                    types = ["LOW_COST", "CONSTRUCTION_SIMPLICITY", "STRUCTURAL_REGULARITY"]
                    if not isinstance(st.get("priorities",{}),dict) or set(st.get("priorities", {})) - set(types) or ("priority" in st and "priorities" in st):
                        errors.append({"sourceId": sid, "reason": "unambiguous explicit priorities for derived goals required"})
                        continue
                    for type in types:
                        gp = dict(deepcopy(p), method=DERIVATION_RULE, exactInputStatements=[text],
                                  derivationRule=DERIVATION_RULE, confidence="EXACT_RULE_MATCH")
                        goal_specs.append(({"goalId": stid + "-" + type.lower().replace("_", "-"), "type": type,
                            "source": "DERIVED_DESIGN_INTENT", "scope": ["PROJECT"],
                            "priority": st.get("priorities", {}).get(type, st.get("priority")), "commitment": "PREFERRED"}, gp))
                else:
                    goal_specs.append((st, p))
                for goal_spec, gp in goal_specs:
                    try:
                        goal = self._goal(goal_spec, gp, source["kind"], kind == "DESIGN_STATEMENT")
                        candidates.append({"goal": goal, "claimId": sid + ":" + stid})
                    except ValueError as exc:
                        errors.append({"sourceId": sid, "statementId": stid, "reason": str(exc)})

        superseded = {ref for x in candidates + decisions for p in (x["goal"]["provenance"] if "goal" in x else x["provenance"])
                      if p["sourceKind"] in ("USER_CORRECTION", "APPROVED_PROJECT_DECISION") for ref in p["supersedes"]}
        candidates = [x for x in candidates if x["claimId"] not in superseded]
        decisions = [x for x in decisions if x["claimId"] not in superseded]
        for gid in sorted({x["goal"]["goalId"] for x in candidates}):
            entries = [x["goal"] for x in candidates if x["goal"]["goalId"] == gid]
            signatures = {canonical({k:v for k,v in g.items() if k != "provenance"}) for g in entries}
            if len(signatures) > 1:
                conflicts.append({"goalId": gid, "reason": "conflicting explicit goal definitions", "candidates": entries})
                continue
            goal = deepcopy(entries[0])
            goal["provenance"] = sorted([p for g in entries for p in g["provenance"]], key=canonical)
            goal["goalFingerprint"] = fingerprint(goal)
            out["goals"].append(goal)
        active = [g for g in out["goals"] if g["status"] == "ACTIVE"]
        if active and no_goals:
            conflicts.append({"reason": "active goals conflict with explicit no-goals decision", "provenance": no_goals})
        if not active and not no_goals and not errors and not conflicts:
            gap("intentScope", "Specify design goals, or explicitly approve no additional design goals",
                "Project type does not establish the user's tastes or priorities", [{"inspectedSources": sorted(seen)}], 0)
        if no_goals:
            out["noGoalsDecision"] = sorted(no_goals, key=canonical)
        spaces = {s["spaceId"] for s in fp["spaces"]}
        zones = {z["zone"]: set(z["spaceIds"]) for z in fp["functionalZones"]}
        for goal in active:
            unknown = [s for s in goal["scope"] if s not in ("PROJECT", "SITE") and not (
                s.startswith("space:") and s[6:] in spaces or s.startswith("zone:") and s[5:] in zones)]
            if unknown:
                gap("scope:" + goal["goalId"], "Resolve goal scope: " + ", ".join(unknown),
                    "Intent must reference the verified functional program", goal["provenance"], 0)
        unranked = [g for g in active if g["priority"] is None]
        if unranked:
            gap("goalPriorities", "Assign explicit priorities to: " + ", ".join(g["goalId"] for g in unranked),
                "No user priority or weight may be guessed", [p for g in unranked for p in g["provenance"]], 0)
        out["priorityOrder"] = [{"priority": n, "goalIds": sorted(g["goalId"] for g in active if g["priority"] == n)}
                                for n in sorted({g["priority"] for g in active if g["priority"] is not None})]

        def scope_set(goal):
            result = set()
            for s in goal["scope"]:
                if s == "PROJECT":
                    return {"*"}
                result |= zones.get(s[5:], set()) if s.startswith("zone:") else {s[6:] if s.startswith("space:") else s}
            return result

        used_decisions = set()
        for i, a in enumerate(active):
            for b in active[i+1:]:
                sa, sb = scope_set(a), scope_set(b)
                if frozenset((a["type"], b["type"])) not in TRADEOFF_PAIRS or not ("*" in sa or "*" in sb or sa & sb):
                    continue
                ids = sorted([a["goalId"], b["goalId"]])
                bindings = {g["goalId"]: g["goalFingerprint"] for g in (a,b)}
                trade = {"tradeoffId": "tradeoff-" + fingerprint(ids)[:20], "goalIds": ids,
                    "goalFingerprints": bindings, "status": "POTENTIAL_TRADEOFF", "blocking": True,
                    "ruleId": "POTENTIAL_" + "_VS_".join(sorted([a["type"],b["type"]])) + "_V0",
                    "resolutionPolicy": None, "preferredGoal": None, "relaxationAuthorized": False,
                    "provenance": [p for g in (a,b) for p in g["provenance"]], "mandatoryGoalsPreserved": True}
                matching = [d for d in decisions if sorted(d.get("goals", [])) == ids]
                valid = []
                for d in matching:
                    used_decisions.add(d["claimId"])
                    if d.get("goalFingerprints") != bindings:
                        gap("reapprove:" + trade["tradeoffId"], "Re-approve the tradeoff decision against current goals",
                            "A goal/source/priority change invalidates a decision bound to older goals", d["provenance"], 0, goalFingerprints=bindings)
                        continue
                    policy = d.get("policy")
                    if policy not in ("PREFER_GOAL", "KEEP_BOTH") or (policy == "PREFER_GOAL" and d.get("preferredGoal") not in ids) or (
                            policy == "KEEP_BOTH" and d.get("preferredGoal") is not None):
                        errors.append({"reason": "explicit supported tradeoff policy/goal required", "decision": d})
                        continue
                    if "overridePriorityOrder" in d and type(d["overridePriorityOrder"]) is not bool:
                        errors.append({"reason": "priority override must be explicit boolean", "decision": d})
                        continue
                    if policy == "PREFER_GOAL" and all(g["priority"] is not None for g in (a,b)) and a["priority"] != b["priority"]:
                        ranked = min((a,b), key=lambda g:g["priority"])["goalId"]
                        if ranked != d["preferredGoal"] and d.get("overridePriorityOrder") is not True:
                            conflicts.append({"reason": "tradeoff decision contradicts explicit priority order", "decision": d})
                            continue
                    valid.append(d)
                if len({canonical([d["policy"], d.get("preferredGoal")]) for d in valid}) > 1:
                    conflicts.append({"reason": "conflicting tradeoff resolutions", "decisions": valid})
                elif valid and len(valid) == len(matching):
                    trade.update(resolutionPolicy="EXPLICIT_USER_DECISION", decisionPolicy=valid[0]["policy"],
                                 preferredGoal=valid[0].get("preferredGoal"), resolutionProvenance=[p for d in valid for p in d["provenance"]])
                elif not matching and a["priority"] is not None and b["priority"] is not None and a["priority"] != b["priority"]:
                    trade.update(resolutionPolicy="PRIORITY_ORDER", preferredGoal=min((a,b),key=lambda g:g["priority"])["goalId"],
                        resolutionProvenance=[{"derivationRule":"EXPLICIT_PRIORITY_ORDER_V0", "source":"DERIVED_DESIGN_INTENT",
                            "inputEvidence":[{"goalId":g["goalId"],"priority":g["priority"],"provenance":g["provenance"]} for g in (a,b)]}])
                if trade["preferredGoal"]:
                    lower = next(g for g in (a,b) if g["goalId"] != trade["preferredGoal"])
                    trade["relaxationAuthorized"] = lower["commitment"] == "SACRIFICABLE"
                if trade["resolutionPolicy"]:
                    out["resolvedTradeoffs"].append(deepcopy(trade))
                else:
                    out["unresolvedTradeoffs"].append(deepcopy(trade))
                    if not unranked and not matching:
                        gap(trade["tradeoffId"], "Which criterion is more important: " + " or ".join(ids) + "?",
                            "Equal-priority potentially conflicting goals have no approved resolution policy", trade["provenance"],
                            goalIds=ids, goalFingerprints=bindings)
                out["tradeoffs"].append(trade)
        for d in decisions:
            if d["claimId"] not in used_decisions:
                errors.append({"reason":"decision does not identify a current applicable tradeoff", "decision":d})
        out["missingDesignDecisions"] = sorted(missing, key=lambda x:(x["priority"],x["decisionId"]))
        out["questions"] = [deepcopy(x) for x in out["missingDesignDecisions"] if x["priority"] == out["missingDesignDecisions"][0]["priority"]][:1] if missing and not errors and not conflicts else []
        out["conflicts"], out["validationErrors"] = sorted(conflicts,key=canonical), sorted(errors,key=canonical)
        coverage = 1.0 if not out["goals"] else sum(bool(g["provenance"]) for g in out["goals"]) / len(out["goals"])
        provenance_complete = coverage == 1.0 and all(t["provenance"] and t.get("resolutionProvenance") for t in out["resolvedTradeoffs"])
        gate = not missing and not conflicts and not errors and not out["unresolvedTradeoffs"] and provenance_complete
        proof = {"stage0Verified": True, "functionalProgramVerified": True, "blockingDesignGoalsValid": not errors,
                 "conflictsCount": len(conflicts), "unresolvedBlockingTradeoffsCount": len(out["unresolvedTradeoffs"]),
                 "missingBlockingDesignDecisionsCount": len(missing), "provenanceCoverage":coverage,
                 "provenanceComplete":provenance_complete, "inventedNormativeValuesCount":0,
                 "unapprovedAssumptionsCount":0, "deterministic":True}
        out.update(status="VERIFIED" if gate else "BLOCKED" if errors or conflicts else "WAITING_FOR_USER_DATA",
                   canProgress=gate, gateProof=proof, provenanceComplete=provenance_complete)
        if gate:
            out["flow"].append("DESIGN_INTENT VERIFIED")
        out["designIntentFingerprint"] = fingerprint(out)
        self._result = out
        return self.result()

    @staticmethod
    def _goal(st, p, source_kind, derived):
        gid, goal_type = st.get("goalId"), st.get("type")
        if not _id(gid) or goal_type not in GOAL_TYPES:
            raise ValueError("stable goalId and supported explicit goal type required")
        source = st.get("source")
        if source not in SOURCES - {"NORMATIVE_PENDING"} or (source == "DERIVED_DESIGN_INTENT" and not derived):
            raise ValueError("explicit user source or traceable approved derivation required")
        if source == "APPROVED_PROJECT_DECISION" and source_kind != "APPROVED_PROJECT_DECISION":
            raise ValueError("approved project decision must have matching source evidence")
        status = st.get("status", "ACTIVE")
        if status not in ("ACTIVE", "INACTIVE"):
            raise ValueError("unsupported goal status")
        priority, weight = st.get("priority"), st.get("weight")
        if priority is not None and (type(priority) is not int or priority < 1):
            raise ValueError("priority must be an explicit positive integer")
        if weight is not None and not _number(weight, positive=True):
            raise ValueError("optional weight must be finite and positive")
        scope = st.get("scope")
        if not isinstance(scope,list) or not scope or any(not isinstance(x,str) or not x.strip() for x in scope):
            raise ValueError("explicit nonempty scope required")
        commitment = st.get("commitment", "MANDATORY" if source == "USER_REQUIREMENT" else "PREFERRED")
        if commitment not in ("MANDATORY","PREFERRED","SACRIFICABLE") or source == "USER_REQUIREMENT" and commitment != "MANDATORY" or source == "USER_PREFERENCE" and commitment == "MANDATORY":
            raise ValueError("commitment cannot silently change user requirement/preference")
        if goal_type == "CUSTOM" and (not isinstance(st.get("description"),str) or not st["description"].strip()):
            raise ValueError("CUSTOM requires the user's explicit description")
        for field in ("target","tolerance"):
            value = st.get(field)
            if value is not None and (not isinstance(value,dict) or set(value) != {"value","unit"} or
                                     not _number(value["value"]) or not isinstance(value["unit"],str) or not value["unit"].strip()):
                raise ValueError("user target/tolerance requires an explicit finite value and unit; no geometry/norm fields")
        result = {"goalId":gid,"type":goal_type,"status":status,"priority":priority,"weight":weight,
                  "scope":sorted(set(scope)),"target":deepcopy(st.get("target")),"tolerance":deepcopy(st.get("tolerance")),
                  "source":source,"commitment":commitment,"provenance":[deepcopy(p)]}
        if "description" in st:
            result["description"] = st["description"]
        if derived:
            result.update(derivationRule=DERIVATION_RULE,confidence="EXACT_RULE_MATCH",exactInputStatements=p["exactInputStatements"])
        return result

    def _empty(self,s0,fp):
        try:
            source_fingerprint = fingerprint(sorted(self._sources,key=canonical))
        except (ValueError,TypeError):
            source_fingerprint = None
        return {"stage":"DESIGN_INTENT","schemaVersion":0,"status":"BLOCKED", "dependencyVerified":False,
            "stage0Fingerprint":s0["contextFingerprint"] if s0 else None,
            "functionalProgramFingerprint":fp.get("programFingerprint") if fp else None,
            "sourceFingerprint":source_fingerprint,"goals":[],"priorityOrder":[],
            "tradeoffs":[],"resolvedTradeoffs":[],"unresolvedTradeoffs":[],"missingDesignDecisions":[],
            "conflicts":[],"normativePending":[],"questions":[],"provenanceComplete":False,"canProgress":False}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("stage0-registry","stage0-sources","functional-brief","intent","output"):
        parser.add_argument("--" + option,type=Path,required=True)
    parser.add_argument("--answers",type=Path)
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    s0 = Stage0(load(args.stage0_registry),load(args.stage0_sources)); s0.audit()
    fp = FunctionalProgram(s0,load(args.functional_brief)); fp.audit()
    intent = DesignIntent(s0,fp,load(args.intent)); out = intent.audit()
    if args.answers:
        for answer in load(args.answers):
            intent.update_source(answer)
        out = intent.audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False) + "\n",encoding="utf-8")
    return 0 if out["canProgress"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
