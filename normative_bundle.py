"""PROJECT NORMATIVE BUNDLE v0. Offline selection, evidence and immutable snapshots."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from design_stage0 import Stage0, fingerprint
from functional_program import FunctionalProgram, canonical
from design_intent import DesignIntent
from site_context import SiteContext
from project_constraints import ProjectConstraintInput

FLOW = ["REQUIRE VERIFIED UPSTREAM", "READ PROJECT CLASSIFICATION", "DISCOVER NORMATIVE BRANCHES",
        "FILTER BY APPLICABILITY", "RESOLVE CONDITIONAL APPLICABILITY", "SELECT VERIFIED RULE REVISIONS",
        "VERIFY SOURCE TRACEABILITY", "VERIFY SUPERSESSION STATE", "DETECT NORMATIVE GAPS",
        "DETECT RULE CONFLICTS", "FREEZE PROJECT SNAPSHOT", "BUILD IMPACT INDEX", "RE-AUDIT"]
LIFECYCLE = {"COLLECTED","SOURCE_VERIFIED","RULE_PARSED","RULE_AUDITED","VERIFIED","SUPERSEDED","RETIRED"}
SOURCE_STATUS = {"VERIFIED","NOT_VERIFIED","SUPERSEDED","CONFLICT","MISSING_SOURCE"}
OPS = {"eq","neq","gt","gte","lt","lte","in","exists"}
FP_KEYS = ("contextFingerprint","programFingerprint","designIntentFingerprint","siteContextFingerprint","constraintInputFingerprint")
OUT_KEYS = ("stage0Fingerprint","functionalProgramFingerprint","designIntentFingerprint","siteContextFingerprint","constraintInputFingerprint")
ARTIFACTS = ("STAGE0","FUNCTIONAL_PROGRAM","DESIGN_INTENT","SITE_CONTEXT","PROJECT_CONSTRAINT_INPUT")


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rule_audit_hash(rule):
    return fingerprint({k:v for k,v in rule.items() if k != "audit"})


def _label(v):
    return isinstance(v,str) and bool(v.strip())


def _scalar(v):
    return isinstance(v,(str,bool)) or type(v) in (int,float) and math.isfinite(v)


def _numeric(v):
    return type(v) in (int,float) and math.isfinite(v)


def _eq(a,b):
    return a == b and (type(a) is type(b) or _numeric(a) and _numeric(b))


def _ref(rule):
    return {k:rule[k] for k in ("branchId","ruleId","revision")}


def _key(ref):
    if not isinstance(ref,dict) or set(ref) != {"branchId","ruleId","revision"} or not all(_label(v) for v in ref.values()):
        raise ValueError("exact branchId/ruleId/revision reference required")
    return canonical(ref)


def _scope_value(scope):
    scope = deepcopy(scope)
    if isinstance(scope,dict): scope.setdefault("optionalNormativeDomains",[])
    return scope


class GlobalRuleLibrary:
    """A copied library revision, never a project artifact and never mutated by selection."""
    def __init__(self,data):
        self._data = deepcopy(data)
        self._fingerprint = fingerprint(self._data)

    @property
    def library_fingerprint(self): return self._fingerprint

    def data(self): return deepcopy(self._data)


def _path(data,path):
    for part in path:
        if isinstance(data,dict): data = data.get(part)
        elif isinstance(data,list) and type(part) is int: data = data[part] if 0 <= part < len(data) else None
        elif isinstance(data,list) and isinstance(part,str):
            matches = [v for v in data if isinstance(v,dict) and part in [v.get(k) for k in ("spaceId","goalId","objectId","featureId","accessId","constraintId")]]
            data = matches[0] if len(matches) == 1 else None
        else: return None
        if data is None: return None
    return deepcopy(data)


class Applicability:
    """Three-valued bounded DSL over registered verified fact adapters; no eval."""
    def __init__(self,registry,upstream,fingerprints):
        self.registry,self.upstream,self.fingerprints = registry,upstream,fingerprints

    def fact(self,id):
        bindings = self.registry.get("inputBindings",{})
        b = bindings.get(id)
        if not isinstance(b,dict) or not _label(b.get("acceptedFormat")) or b.get("artifact") not in ARTIFACTS:
            raise ValueError("registered typed input binding required: "+str(id))
        i = ARTIFACTS.index(b["artifact"])
        raw = None
        if i == 0:
            if set(b) != {"artifact","datumId","acceptedFormat"}: raise ValueError("Stage0 binding needs explicit datumId")
            raw = next((v for v in self.upstream[0]["inputs"] if v["id"] == b["datumId"]),None)
            value = raw.get("value") if raw and raw["status"] in ("CONFIRMED","DERIVED") else None
        else:
            path = b.get("path")
            if set(b) != {"artifact","path","acceptedFormat"} or not isinstance(path,list) or not path or any(not isinstance(x,str) and type(x) is not int for x in path): raise ValueError("explicit declarative artifact field path required")
            if any(isinstance(x,str) and ("normative" in x.lower() or x in {"gateProof","validationErrors","conflicts","questions"}) for x in path): raise ValueError("applicability cannot consume pending norms or audit metadata as project facts")
            allowed = {1:{"projectType","spaces","users","functionalZones","relationships","userRequirements","userPreferences","stage0Context"},
                       2:{"goals"},3:{"site","boundary","orientation","accessPoints","existingObjects","contextFeatures","terrain","derivedMetrics","userSitePreferences"},
                       4:{"constraints","derivedConstraints","nonBindingConstraints"}}
            if path[0] not in allowed[i]: raise ValueError("registered project-fact field required; artifact metadata is not an applicability fact")
            value = _path(self.upstream[i],path)
            raw = {"path":path,"value":value}
        return dict(input=id,value=value,known=value is not None,artifact=b["artifact"],artifactFingerprint=self.fingerprints[i],
                    acceptedFormat=b["acceptedFormat"],inputEvidence=raw)

    @staticmethod
    def validate(expr,depth=0):
        if depth > 32 or not isinstance(expr,dict): raise ValueError("bounded declarative applicability required")
        if set(expr) in ({"all"},{"any"}):
            children = next(iter(expr.values()))
            if not isinstance(children,list) or not children or len(children) > 128: raise ValueError("bounded nonempty all/any required")
            for child in children: Applicability.validate(child,depth+1)
        elif set(expr) == {"not"}: Applicability.validate(expr["not"],depth+1)
        else:
            if set(expr)-OPS != {"input"} or len(expr) != 2 or not _label(expr.get("input")): raise ValueError("unsupported applicability DSL; executable expressions forbidden")
            op = next(k for k in expr if k != "input"); v = expr[op]
            if op == "exists" and type(v) is not bool or op == "in" and (not isinstance(v,list) or not v or not all(_scalar(x) for x in v)) or op not in {"exists","in"} and not _scalar(v):
                raise ValueError("explicit typed finite applicability literal required")

    def evaluate(self,expr,depth=0):
        if depth > 32 or not isinstance(expr,dict): raise ValueError("bounded declarative applicability object required")
        if set(expr) in ({"all"},{"any"}):
            op = next(iter(expr)); children = expr[op]
            if not isinstance(children,list) or not children or len(children) > 128: raise ValueError("nonempty bounded all/any list required")
            values,used,missing = [],[],[]
            for child in children:
                result,inputs,unknown = self.evaluate(child,depth+1)
                values.append(result); used += inputs; missing += unknown
                if op == "all" and result is False or op == "any" and result is True:
                    return result,used,[]  # known proof closes the condition without asking irrelevant facts
            result = None if None in values else all(values) if op == "all" else any(values)
            return result,used,missing if result is None else []
        if set(expr) == {"not"}:
            r,u,m = self.evaluate(expr["not"],depth+1)
            return None if r is None else not r,u,m
        if set(expr)-OPS != {"input"} or len(expr) != 2 or not _label(expr.get("input")):
            raise ValueError("only input with one eq/neq/gt/gte/lt/lte/in/exists predicate is supported")
        op = next(k for k in expr if k != "input"); expected = expr[op]
        if op == "exists":
            if type(expected) is not bool: raise ValueError("exists requires boolean")
        elif op == "in":
            if not isinstance(expected,list) or not expected or not all(_scalar(v) for v in expected): raise ValueError("in requires explicit scalar alternatives")
        elif not _scalar(expected): raise ValueError("literal finite scalar predicate required")
        fact = self.fact(expr["input"])
        if not fact["known"]: return None,[fact],[fact]
        v = fact["value"]
        if op == "exists": return expected,[fact],[]
        if not _scalar(v): raise ValueError("scalar project fact required for comparison")
        if op in {"gt","gte","lt","lte"}:
            if not _numeric(v) or not _numeric(expected): raise ValueError("ordered applicability comparisons require finite numeric facts")
            r = {"gt":lambda:v>expected,"gte":lambda:v>=expected,"lt":lambda:v<expected,"lte":lambda:v<=expected}[op]()
        elif op == "in": r = any(_eq(v,x) for x in expected)
        else: r = _eq(v,expected) if op == "eq" else not _eq(v,expected)
        return r,[fact],[]


def _requirement(req):
    fields = {"domain","subject","scope","operator","value","unit","downstreamDomains"}
    if not isinstance(req,dict) or set(req) != fields or not all(_label(req[k]) for k in ("domain","subject","unit")):
        raise ValueError("explicit machine-readable requirement domain/subject/unit required")
    if not isinstance(req["scope"],list) or not req["scope"] or not all(_label(x) for x in req["scope"]): raise ValueError("explicit requirement scope required")
    if not isinstance(req["downstreamDomains"],list) or not req["downstreamDomains"] or not all(_label(x) for x in req["downstreamDomains"]): raise ValueError("explicit downstream dependency domains required")
    op,v = req["operator"],req["value"]
    if op not in {"eq","neq","gt","gte","lt","lte","in","not_in"}: raise ValueError("unsupported requirement operator; expressions not supported")
    if op in ("in","not_in"):
        if not isinstance(v,list) or not v or not all(_scalar(x) for x in v): raise ValueError("explicit scalar requirement set required")
    elif not _scalar(v): raise ValueError("explicit finite requirement literal required")
    if op in {"gt","gte","lt","lte"} and not _numeric(v): raise ValueError("numeric ordered requirement required")


def _satisfies(req,value):
    op,x = req["operator"],req["value"]
    if op == "eq": return _eq(value,x)
    if op == "neq": return not _eq(value,x)
    if op == "in": return any(_eq(value,v) for v in x)
    if op == "not_in": return not any(_eq(value,v) for v in x)
    if not _numeric(value): return False
    return {"gt":lambda:value>x,"gte":lambda:value>=x,"lt":lambda:value<x,"lte":lambda:value<=x}[op]()


def _contradiction(reqs):
    finite = [r["value"] if r["operator"] == "in" else [r["value"]] for r in reqs if r["operator"] in {"eq","in"}]
    if finite: return not any(all(_satisfies(r,x) for r in reqs) for values in finite for x in values)
    lower,upper = (-math.inf,False),(math.inf,False)
    for r in reqs:
        op,v = r["operator"],r["value"]
        if op in {"gt","gte"} and (v > lower[0] or v == lower[0] and op == "gt"): lower = v,op == "gte"
        if op in {"lt","lte"} and (v < upper[0] or v == upper[0] and op == "lt"): upper = v,op == "lte"
    if lower[0] > upper[0] or lower[0] == upper[0] and not (lower[1] and upper[1]): return True
    if reqs[0]["unit"] == "count":
        lo = math.ceil(lower[0])+int(not lower[1] and lower[0] == math.ceil(lower[0])) if math.isfinite(lower[0]) else -math.inf
        hi = math.floor(upper[0])-int(not upper[1] and upper[0] == math.floor(upper[0])) if math.isfinite(upper[0]) else math.inf
        if lo > hi: return True
    return lower[0] == upper[0] and not all(_satisfies(r,lower[0]) for r in reqs)


class ProjectNormativeBundle:
    def __init__(self,stage0,functional_program,design_intent,site_context,constraint_input,library,scope):
        self._upstream = (stage0,functional_program,design_intent,site_context,constraint_input)
        if not all(isinstance(x,t) for x,t in zip(self._upstream,(Stage0,FunctionalProgram,DesignIntent,SiteContext,ProjectConstraintInput))):
            raise TypeError("five live verified upstream sessions required")
        if not isinstance(library,GlobalRuleLibrary): raise TypeError("separate GlobalRuleLibrary revision required")
        self._library,self._scope,self._result,self._frozen = library,_scope_value(scope),None,None

    def _dependencies(self):
        rs = [x.result() for x in self._upstream]
        return rs,[r.get(k) if r else None for r,k in zip(rs,FP_KEYS)]

    def _refresh(self):
        if self._result and self._result.get("dependencyVerified"):
            rs,fs = self._dependencies()
            if fs != self._result["upstreamFingerprints"] or any(not r or r["status"] != "VERIFIED" for r in rs):
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="UPSTREAM_CHANGED_OR_NOT_VERIFIED")

    def result(self):
        self._refresh(); return deepcopy(self._result)

    def snapshot(self):
        """Historical frozen evidence; does not grant a live progression gate."""
        return deepcopy(self._frozen)

    def require_verified(self):
        self._refresh()
        for u in self._upstream: u.require_verified()
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"]:
            raise RuntimeError("Project Normative Bundle progression blocked")
        return deepcopy(self._result["gateProof"])

    def update_scope(self,scope):
        scope = _scope_value(scope)
        if fingerprint(scope) != fingerprint(self._scope):
            self._scope = deepcopy(scope)
            if self._result: self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="DOWNSTREAM_SCOPE_CHANGED")

    def adopt_library(self,library):
        impact = self.compare_library(library)
        if impact["status"] != "UNCHANGED":
            self._library = library
            if self._result: self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="EXPLICIT_LIBRARY_REFRESH_REQUIRES_REAUDIT")
        return impact

    def audit(self):
        self._refresh()
        rs,fs = self._dependencies()
        out = dict(stage="PROJECT_NORMATIVE_BUNDLE",schemaVersion=0,status="BLOCKED",canProgress=False,dependencyVerified=False,
                   upstreamFingerprints=fs,projectClassification={},applicableBranches=[],excludedBranches=[],conditionalBranches=[],
                   compiledRules=[],normativeGaps=[],conflicts=[],notVerified=[],sourceDocuments=[],dependencyIndex=[],impactIndex=[],
                   missingProjectInputs=[],supersessionIndex=[],ruleApplicability=[],validationErrors=[],provenanceComplete=False,flow=list(FLOW),
                   downstreamScope=deepcopy(self._scope),libraryFingerprint=self._library.library_fingerprint,
                   createdFromLibraryFingerprint=self._library.library_fingerprint)
        for k,v in zip(OUT_KEYS,fs): out[k] = v
        try:
            for u in self._upstream: u.require_verified()
            for r in rs[1:]:
                if r["stage0Fingerprint"] != fs[0]: raise ValueError("incoherent Stage0 dependency chain")
            if rs[2]["functionalProgramFingerprint"] != fs[1] or rs[4]["upstreamFingerprints"] != fs[:4]: raise ValueError("incoherent upstream dependency chain")
            out["dependencyVerified"] = True
            data = self._library.data()
            if not isinstance(data,dict) or set(data) != {"libraryId","revision","branches","rules","sources","applicabilityRegistry","domainRegistry"} or not all(_label(data[k]) for k in ("libraryId","revision")): raise ValueError("versioned separate library registries required")
            ar,dr = data["applicabilityRegistry"],data["domainRegistry"]
            for r in (ar,dr):
                if not isinstance(r,dict) or r.get("status") != "VERIFIED" or not _label(r.get("id")) or not _label(r.get("revision")): raise ValueError("verified versioned applicability/domain registries required")
            if not isinstance(ar.get("definitions"),dict) or not isinstance(ar.get("inputBindings"),dict) or not isinstance(dr.get("scopes"),list) or any(not isinstance(x,dict) for x in dr["scopes"]): raise ValueError("structured applicability and domain registries required")
            if not isinstance(data["branches"],list) or not isinstance(data["rules"],dict) or not isinstance(data["sources"],dict): raise ValueError("branch inventory and keyed rule/source registries required")
            ap = Applicability(ar,rs,fs)
            classification = ap.fact("project.classification")
            if not classification["known"] or not _label(classification["value"]) or classification["value"] != rs[1]["projectType"]: raise ValueError("verified project classification unresolved or inconsistent")
            cls = classification["value"]
            out["projectClassification"] = classification
            scope = self._scope
            if not isinstance(scope,dict) or set(scope) != {"downstreamStage","requiredNormativeDomains","optionalNormativeDomains"}: raise ValueError("explicit downstream stage and required/optional domains required")
            if not _label(scope["downstreamStage"]) or any(not isinstance(scope[k],list) or any(not _label(x) for x in scope[k]) or len(scope[k]) != len(set(scope[k])) for k in ("requiredNormativeDomains","optionalNormativeDomains")): raise ValueError("unique declared normative domain lists required")
            specs = [x for x in dr["scopes"] if x["downstreamStage"] == scope["downstreamStage"] and cls in x["projectClasses"]]
            if len(specs) != 1: raise ValueError("exact versioned downstream domain coverage specification required")
            spec = specs[0]
            if set(spec) != {"downstreamStage","projectClasses","requiredNormativeDomains","optionalNormativeDomains"} or any(not isinstance(spec[k],list) or any(not _label(v) for v in spec[k]) for k in ("projectClasses","requiredNormativeDomains","optionalNormativeDomains")):
                raise ValueError("explicit typed domain coverage specification required")
            if set(scope["requiredNormativeDomains"]) != set(spec["requiredNormativeDomains"]) or not set(scope["optionalNormativeDomains"]) <= set(spec["optionalNormativeDomains"]): raise ValueError("downstream scope cannot silently omit required registry domains")
            domains = set(scope["requiredNormativeDomains"]+scope["optionalNormativeDomains"])
            out["projectFingerprint"] = fingerprint(fs)
            out["domainRegistryEvidence"] = dict(id=dr["id"],revision=dr["revision"],scopeSpecification=deepcopy(spec))
        except (ValueError,RuntimeError,TypeError,KeyError) as exc:
            out["validationErrors"].append({"reason":str(exc)})
            self._result = out; return self.result()

        def gap(branch,reason,blocking,evidence=None,inputs=None,rule=None):
            g = dict(branchId=branch,status="NORMATIVE_GAP",blocking=blocking,reason=reason,
                     requiredBy=[scope["downstreamStage"]],projectInputs=inputs or [],evidence=evidence or [])
            if rule: g["ruleReference"] = rule
            g["gapId"] = "gap-"+fingerprint(g)[:24]; out["normativeGaps"].append(g)

        def evaluate(expr,branch,blocking,rule=None):
            try:
                Applicability.validate(expr)
                state,used,missing = ap.evaluate(expr)
                basis = dict(definition=deepcopy(expr),status="APPLICABLE" if state is True else "NOT_APPLICABLE" if state is False else "CONDITIONAL",
                             projectInputsUsed=sorted({canonical(x):x for x in used}.values(),key=canonical))
                if state is None:
                    for m in missing:
                        q = dict(WHAT="Provide verified project fact "+m["input"],WHY="Resolve applicability; no normative value is requested",
                                 REQUIRED_BY=[scope["downstreamStage"]],ACCEPTED_FORMAT=m["acceptedFormat"],input=m["input"],
                                 affectedBranch=branch,affectedRule=rule,blocking=blocking,provenance=[m])
                        out["missingProjectInputs"].append(q)
                    gap(branch,"UNRESOLVED_APPLICABILITY",blocking,[basis],missing,rule)
                return state,basis
            except (ValueError,TypeError,KeyError,OverflowError) as exc:
                rec = dict(branchId=branch,status="NOT_VERIFIED",reason=str(exc),ruleReference=rule)
                out["notVerified"].append(rec); gap(branch,"INVALID_APPLICABILITY",blocking,[rec],rule=rule)
                return None,rec

        branches,seen,coverage = [],set(),set()
        for b in sorted(data["branches"],key=canonical):
            try:
                if not isinstance(b,dict) or not _label(b.get("branchId")) or not isinstance(b.get("projectClasses"),list) or not b["projectClasses"] or any(not _label(x) for x in b["projectClasses"]): raise ValueError("explicit branch identity/class routing required")
                bid = b["branchId"]
                if bid in seen: raise ValueError("duplicate branchId")
                seen.add(bid)
                if b.get("status") not in {"VERIFIED","NOT_VERIFIED","CONFLICT","RETIRED"}: raise ValueError("unknown branch status")
                if cls not in b["projectClasses"]:
                    out["excludedBranches"].append(dict(branchId=bid,status="NOT_APPLICABLE",reason="UNRELATED_PROJECT_CLASS",projectInputsUsed=[classification])); continue
                if b.get("domain") not in domains:
                    out["excludedBranches"].append(dict(branchId=bid,status="NOT_APPLICABLE",reason="OUTSIDE_DOWNSTREAM_SCOPE",domain=b.get("domain"))); continue
                blocking = b["domain"] in scope["requiredNormativeDomains"]
                coverage.add(b["domain"])
                if b["status"] != "VERIFIED": gap(bid,"BRANCH_NOT_VERIFIED",blocking,[b]); continue
                if set(b) != {"branchId","projectClasses","domain","status","applicabilityId","requiredRuleIds"} or not isinstance(b["requiredRuleIds"],list) or any(not _label(x) for x in b["requiredRuleIds"]): raise ValueError("verified branch requires applicability and expected rule inventory")
                definition = ar["definitions"][b["applicabilityId"]]
                state,basis = evaluate(definition,bid,blocking)
                br = dict(branchId=bid,domain=b["domain"],blocking=blocking,applicabilityBasis=basis,requiredRuleIds=b["requiredRuleIds"])
                if state is False: out["excludedBranches"].append(dict(status="NOT_APPLICABLE",reason="PROVEN_NOT_APPLICABLE",**br)); continue
                if state is None: out["conditionalBranches"].append(dict(status="CONDITIONAL",**br)); continue
                out["applicableBranches"].append(dict(status="APPLICABLE",**br)); branches.append((b,br))
            except (ValueError,TypeError,KeyError) as exc:
                out["validationErrors"].append(dict(reason=str(exc),branchId=b.get("branchId") if isinstance(b,dict) else None))
        for domain in sorted(set(scope["requiredNormativeDomains"])-coverage): gap(domain,"REQUIRED_DOMAIN_HAS_NO_PROJECT_BRANCH",True,[out["domainRegistryEvidence"]])

        candidates,rule_by_key,rule_bases = [],{},{}
        for b,br in branches:
            bid,blocking = b["branchId"],br["blocking"]
            rules = data["rules"].get(bid,[])
            if not isinstance(rules,list): gap(bid,"MALFORMED_RULE_INVENTORY",blocking); continue
            if not rules: gap(bid,"APPLICABLE_BRANCH_HAS_NO_RULE",blocking,[br]); continue
            present = {r.get("ruleId") for r in rules if isinstance(r,dict) and isinstance(r.get("ruleId"),str)}
            for rid in sorted(set(b["requiredRuleIds"])-present): gap(bid,"REQUIRED_RULE_MISSING",blocking,[br],rule={"ruleId":rid})
            local = []
            for r in sorted(rules,key=canonical):
                try:
                    required = {"ruleId","branchId","revision","status","requirement","source","applicability","supersedes","dependencies","revisionMetadata","audit"}
                    if not isinstance(r,dict) or set(r) != required or r["branchId"] != bid or r["status"] not in LIFECYCLE: raise ValueError("complete rule identity/lifecycle/revision metadata required")
                    key = _key(_ref(r))
                    if key in rule_by_key: raise ValueError("duplicate exact rule revision")
                    rm = r["revisionMetadata"]
                    if not isinstance(rm,dict) or set(rm) != {"state","decisionId"} or rm["state"] not in {"ACTIVE_REVISION","SUPERSEDED_REVISION","RETIRED_REVISION"} or not _label(rm["decisionId"]): raise ValueError("explicit revision state and decision evidence required")
                    if not isinstance(r["supersedes"],list) or not isinstance(r["dependencies"],list): raise ValueError("explicit supersession/dependency references required")
                    for ref in r["supersedes"]+r["dependencies"]: _key(ref)
                    rule_by_key[key] = r; local.append(r)
                except (ValueError,TypeError,KeyError) as exc:
                    rec = dict(branchId=bid,status="NOT_VERIFIED",reason=str(exc),rawEvidence=deepcopy(r))
                    out["notVerified"].append(rec); gap(bid,"MALFORMED_RULE",blocking,[rec])
            # Revision state is checked before any active candidate can become production.
            if not any(r["revisionMetadata"]["state"] == "ACTIVE_REVISION" and r["status"] not in {"SUPERSEDED","RETIRED"} for r in local):
                gap(bid,"NO_ACTIVE_RULE_REVISION",blocking,[br])
            for r in local:
                key = _key(_ref(r)); rm = r["revisionMetadata"]
                for ref in r["supersedes"]:
                    old = rule_by_key.get(_key(ref))
                    if not old or ref["ruleId"] != r["ruleId"] or ref["branchId"] != bid or old["revisionMetadata"]["state"] != "SUPERSEDED_REVISION":
                        out["conflicts"].append(dict(status="CONFLICT",reason="MALFORMED_OR_UNRESOLVED_SUPERSESSION",newRevision=_ref(r),oldRevision=ref,provenance=[r,old]))
                    out["supersessionIndex"].append(dict(replacingRevision=_ref(r),replacementState=rm["state"],supersededRevision=ref,decisionId=rm["decisionId"]))
                if rm["state"] != "ACTIVE_REVISION" or r["status"] in {"SUPERSEDED","RETIRED"}:
                    out["notVerified"].append(dict(ruleReference=_ref(r),status=r["status"],reason=rm["state"])); continue
                state,basis = evaluate(r["applicability"],bid,blocking,_ref(r)); rule_bases[key] = basis
                out["ruleApplicability"].append(dict(ruleReference=_ref(r),applicabilityBasis=basis,status=basis["status"]))
                if state is not True: continue
                if r["status"] != "VERIFIED":
                    rec = dict(ruleReference=_ref(r),status="NOT_VERIFIED",reason="RULE_LIFECYCLE_"+r["status"],applicabilityBasis=basis)
                    out["notVerified"].append(rec); gap(bid,"APPLICABLE_RULE_NOT_VERIFIED",blocking,[rec],rule=_ref(r)); continue
                try:
                    if r["audit"].get("status") != "VERIFIED" or not _label(r["audit"].get("auditId")) or r["audit"].get("ruleFingerprint") != rule_audit_hash(r): raise ValueError("exact parsed rule audit receipt missing/stale")
                    _requirement(r["requirement"])
                    doc,location = self._source_chain(data,r)
                    compiled = dict(ruleId=r["ruleId"],ruleRevision=r["revision"],branchId=bid,requirement=deepcopy(r["requirement"]),
                        applicabilityBasis=[br["applicabilityBasis"],basis],projectInputsUsed=sorted({canonical(x):x for x in br["applicabilityBasis"]["projectInputsUsed"]+basis["projectInputsUsed"]}.values(),key=canonical),
                        sourceDocument=doc["documentId"],sourceRevision=doc["documentRevision"],sourceHash=doc["sourceHash"],
                        sourceLocation=deepcopy(r["source"]["location"]),sourceVerification="VERIFIED",dependencies=deepcopy(r["dependencies"]),
                        provenance=[dict(ruleReference=_ref(r),ruleAudit=deepcopy(r["audit"]),sourceEvidence=deepcopy(location),revisionMetadata=deepcopy(rm))])
                    candidates.append(compiled)
                    out["sourceDocuments"].append(deepcopy(doc))
                except (ValueError,TypeError,KeyError) as exc:
                    rec = dict(ruleReference=_ref(r),status="NOT_VERIFIED",reason=str(exc),sourceEvidence=deepcopy(r["source"]),applicabilityBasis=basis)
                    out["notVerified"].append(rec); gap(bid,"SOURCE_OR_RULE_TRACEABILITY_INCOMPLETE",blocking,[rec],rule=_ref(r))

        # Fail closed on cycles even if revision metadata attempts to hide them.
        def visit(key,trail):
            if key in trail: raise ValueError("cyclic supersession graph")
            for ref in rule_by_key[key]["supersedes"]:
                target = _key(ref)
                if target in rule_by_key: visit(target,trail|{key})
        try:
            for key in rule_by_key: visit(key,set())
        except (ValueError,RecursionError) as exc: out["conflicts"].append(dict(status="CONFLICT",reason=str(exc),graph=deepcopy(out["supersessionIndex"])))
        for rid in sorted({r["ruleId"] for r in rule_by_key.values()}):
            active = [r for r in rule_by_key.values() if r["ruleId"] == rid and r["revisionMetadata"]["state"] == "ACTIVE_REVISION"]
            if len(active) > 1: out["conflicts"].append(dict(status="CONFLICT",reason="MULTIPLE_ACTIVE_REVISIONS",ruleId=rid,revisions=[_ref(r) for r in active],sourceProvenance=[r["source"] for r in active],applicabilityBasis=[rule_bases.get(_key(_ref(r))) for r in active]))
        compiled_keys = {canonical(dict(branchId=c["branchId"],ruleId=c["ruleId"],revision=c["ruleRevision"])) for c in candidates}
        missing_deps = set()
        for c in candidates:
            for ref in c["dependencies"]:
                out["dependencyIndex"].append(dict(ruleId=c["ruleId"],ruleRevision=c["ruleRevision"],dependency=ref))
                if _key(ref) not in compiled_keys:
                    missing_deps.add((c["branchId"],c["ruleId"],c["ruleRevision"]))
                    gap(c["branchId"],"DEPENDENCY_NOT_APPLICABLE_VERIFIED_ACTIVE",True,[ref],rule={"ruleId":c["ruleId"],"revision":c["ruleRevision"]})
        depmap = {canonical(dict(branchId=c["branchId"],ruleId=c["ruleId"],revision=c["ruleRevision"])):c for c in candidates}
        def dependency_visit(key,trail):
            if key in trail: raise ValueError("cyclic rule dependency graph")
            for ref in depmap[key]["dependencies"]:
                target = _key(ref)
                if target in depmap: dependency_visit(target,trail|{key})
        try:
            for key in depmap: dependency_visit(key,set())
        except (ValueError,RecursionError) as exc:
            out["conflicts"].append(dict(status="CONFLICT",reason=str(exc),graph=deepcopy(out["dependencyIndex"])))
        # Remove consumers transitively; a dependency gap cannot leak a production rule.
        while missing_deps:
            rejected = {canonical(dict(branchId=b,ruleId=r,revision=v)) for b,r,v in missing_deps}
            remaining = [c for c in candidates if (c["branchId"],c["ruleId"],c["ruleRevision"]) not in missing_deps]
            missing_deps = {(c["branchId"],c["ruleId"],c["ruleRevision"]) for c in remaining if any(_key(ref) in rejected for ref in c["dependencies"])}
            candidates = remaining
        out["compiledRules"] = candidates
        for b,br in branches:
            for rid in b["requiredRuleIds"]:
                if not any(c["ruleId"] == rid and c["branchId"] == b["branchId"] for c in candidates):
                    states = [rule_bases.get(_key(_ref(r)),{}).get("status") for r in rule_by_key.values() if r["branchId"] == b["branchId"] and r["ruleId"] == rid and r["revisionMetadata"]["state"] == "ACTIVE_REVISION"]
                    if not states or any(s != "NOT_APPLICABLE" for s in states): gap(b["branchId"],"REQUIRED_RULE_NOT_COMPILED",br["blocking"],[br],rule={"ruleId":rid})
        self._rule_conflicts(out)
        used_docs = {(c["sourceDocument"],c["sourceRevision"]) for c in candidates}
        out["sourceDocuments"] = sorted({canonical(d):d for d in out["sourceDocuments"] if (d["documentId"],d["documentRevision"]) in used_docs}.values(),key=canonical)
        out["applicabilityFingerprint"] = fingerprint([ar,out["applicableBranches"],out["excludedBranches"],out["conditionalBranches"],rule_bases])
        out["selectedRuleRevisions"] = sorted([dict(ruleId=c["ruleId"],revision=c["ruleRevision"],branchId=c["branchId"]) for c in candidates],key=canonical)
        out["sourceHashes"] = sorted({c["sourceHash"] for c in candidates})
        for c in candidates:
            out["impactIndex"].append(dict(ruleId=c["ruleId"],ruleRevision=c["ruleRevision"],branchId=c["branchId"],
                projectInputs=[i["input"] for i in c["projectInputsUsed"]],sourceDocument=c["sourceDocument"],sourceRevision=c["sourceRevision"],
                downstreamDomains=c["requirement"]["downstreamDomains"],dependentRuleIds=[x["ruleId"] for x in candidates if any(ref["ruleId"] == c["ruleId"] for ref in x["dependencies"])]))
        out["provenanceComplete"] = all(c["provenance"] and c["applicabilityBasis"] and c["projectInputsUsed"] for c in candidates)
        blocking = sum(g["blocking"] for g in out["normativeGaps"])
        proof = dict(allRequiredUpstreamVerified=True,projectClassificationResolved=True,requiredNormativeBranchesResolved=not blocking,
                     allProductionRulesVerified=True,allSourceChainsComplete=out["provenanceComplete"],allActiveRevisionsResolved=not out["conflicts"],
                     blockingConditionalCount=sum(b["blocking"] for b in out["conditionalBranches"])+sum(g["blocking"] and g["reason"] == "UNRESOLVED_APPLICABILITY" and "ruleReference" in g for g in out["normativeGaps"]),
                     blockingNormativeGapCount=blocking,conflictCount=len(out["conflicts"]),provenanceComplete=out["provenanceComplete"],
                     provenanceCoverage=1.0 if out["provenanceComplete"] else 0.0,inventedNormativeDataCount=0,hiddenAssumptionsCount=0,deterministicSnapshot=True)
        out["gateProof"] = proof
        out["canProgress"] = not (blocking or out["conflicts"] or out["validationErrors"]) and out["provenanceComplete"]
        if out["canProgress"]: out["status"] = "VERIFIED"; out["flow"].append("PROJECT_NORMATIVE_BUNDLE VERIFIED")
        for k in ("applicableBranches","excludedBranches","conditionalBranches","compiledRules","normativeGaps","conflicts","notVerified","dependencyIndex","impactIndex","missingProjectInputs","supersessionIndex","ruleApplicability","validationErrors"):
            out[k] = sorted({canonical(v):v for v in out[k]}.values(),key=canonical)
        out["snapshotId"] = "snapshot-"+fingerprint(out)
        out["bundleId"] = "bundle-"+fingerprint([out["projectFingerprint"],scope])
        out["normativeBundleFingerprint"] = fingerprint(out)
        out["bundleFingerprint"] = out["normativeBundleFingerprint"]
        self._result = out
        if out["canProgress"]: self._frozen = deepcopy(out)
        return self.result()

    @staticmethod
    def _source_chain(data,rule):
        src = rule["source"]
        if not isinstance(src,dict) or set(src) != {"documentId","documentRevision","sourceHash","location","verificationStatus"} or src["verificationStatus"] != "VERIFIED" or not all(_label(src[k]) for k in ("documentId","documentRevision","sourceHash")): raise ValueError("rule source must have exact verified document revision/hash")
        loc = src["location"]
        if not isinstance(loc,dict) or set(loc) != {"section","paragraph","table","appendix"} or not any(_label(loc[k]) for k in ("paragraph","table","appendix")): raise ValueError("exact paragraph/table/appendix required; section alone insufficient")
        doc = data["sources"].get(src["documentId"]+"@"+src["documentRevision"])
        if not isinstance(doc,dict) or doc.get("verificationStatus") not in SOURCE_STATUS or doc["verificationStatus"] != "VERIFIED": raise ValueError("SOURCE_NOT_VERIFIED_OR_MISSING")
        if doc.get("documentId") != src["documentId"] or doc.get("documentRevision") != src["documentRevision"] or doc.get("sourceHash") != src["sourceHash"] or not isinstance(doc.get("content"),str) or text_hash(doc["content"]) != src["sourceHash"]:
            raise ValueError("source content/revision/hash mismatch")
        records = [e for e in doc.get("verifiedLocations",[]) if isinstance(e,dict) and e.get("location") == loc]
        if len(records) != 1: raise ValueError("exact located verified text evidence missing/ambiguous")
        ev = records[0]
        if ev.get("verificationStatus") != "VERIFIED" or ev.get("evidenceKind") != "VERIFIED_SOURCE_TEXT" or not _label(ev.get("verificationId")) or not _label(ev.get("text")) or ev["text"] not in doc["content"] or ev.get("textHash") != text_hash(ev["text"]) or ev.get("sourceHash") != src["sourceHash"]:
            raise ValueError("actually verified located source text required; filename/snippet/AI summary insufficient")
        return doc,ev

    @staticmethod
    def _rule_conflicts(out):
        rules = out["compiledRules"]
        domains = {(c["requirement"]["domain"],c["requirement"]["subject"],s) for c in rules for s in c["requirement"]["scope"]}
        for domain,subject,scope in sorted(domains):
            group = [c for c in rules if c["requirement"]["domain"] == domain and c["requirement"]["subject"] == subject and (scope in c["requirement"]["scope"] or "PROJECT" in c["requirement"]["scope"])]
            if len(group) < 2: continue
            mixed = len({c["requirement"]["unit"] for c in group}) > 1
            if mixed or _contradiction([c["requirement"] for c in group]):
                out["conflicts"].append(dict(status="CONFLICT",reason="INCOMPARABLE_UNITS" if mixed else "INCOMPATIBLE_APPLICABLE_REQUIREMENTS",conflictDomain=dict(domain=domain,subject=subject,scope=scope),rules=deepcopy(group)))

    def compare_library(self,new_library):
        if not isinstance(new_library,GlobalRuleLibrary): raise TypeError("GlobalRuleLibrary revision required")
        if not self._frozen: raise RuntimeError("verified historical bundle required for impact comparison")
        try: return self._compare_library(new_library)
        except (ValueError,TypeError,KeyError,AttributeError,RecursionError,OverflowError) as exc:
            impact = dict(status="BLOCKED_BY_NORMATIVE_CHANGE",oldSnapshotId=self._frozen["snapshotId"],
                newLibraryFingerprint=new_library.library_fingerprint,changedRuleIds=[],changedBranches=[],
                affectedProjectInputs=[],affectedBundleRuleIds=[c["ruleId"] for c in self._frozen["compiledRules"]],
                downstreamDomains=sorted({d for i in self._frozen["impactIndex"] for d in i["downstreamDomains"]}),
                reason="MALFORMED_NEW_LIBRARY: "+str(exc),historicalSnapshotUnchanged=True)
            impact["changeId"] = "change-"+fingerprint(impact)
            return impact

    def _compare_library(self,new_library):
        """Read-only compare: never adopts the new revision or rewrites a historical bundle."""
        if not isinstance(new_library,GlobalRuleLibrary): raise TypeError("GlobalRuleLibrary revision required")
        old = self._frozen
        if not old: raise RuntimeError("verified historical bundle required for impact comparison")
        current,new = self._library.data(),new_library.data()
        candidate = ProjectNormativeBundle(*self._upstream,new_library,self._scope).audit()
        linked = {b["branchId"] for b in old["applicableBranches"]+old["conditionalBranches"]}
        linked |= {b["branchId"] for b in candidate["applicableBranches"]+candidate["conditionalBranches"]}
        # Domain and class routing can make a previously absent branch required.
        cls = old["projectClassification"]["value"]
        domains = set(self._scope["requiredNormativeDomains"]+self._scope["optionalNormativeDomains"])
        for data in (current,new):
            linked |= {b["branchId"] for b in data.get("branches",[]) if isinstance(b,dict) and cls in b.get("projectClasses",[]) and b.get("domain") in domains}
        def signature(data):
            bs = [b for b in data.get("branches",[]) if b.get("branchId") in linked]
            rs = {bid:data.get("rules",{}).get(bid,[]) for bid in sorted(linked)}
            srcs = {r["source"]["documentId"]+"@"+r["source"]["documentRevision"] for rows in rs.values() if isinstance(rows,list) for r in rows if isinstance(r,dict) and isinstance(r.get("source"),dict) and "documentId" in r["source"] and "documentRevision" in r["source"]}
            ar = data.get("applicabilityRegistry",{})
            defs = {b.get("applicabilityId"):ar.get("definitions",{}).get(b.get("applicabilityId")) for b in bs}
            expressions = list(defs.values())+[r.get("applicability") for rows in rs.values() if isinstance(rows,list) for r in rows if isinstance(r,dict)]
            def inputs(e):
                if isinstance(e,dict): return ({e["input"]} if isinstance(e.get("input"),str) else set()) | set().union(*(inputs(v) for v in e.values()))
                if isinstance(e,list): return set().union(*(inputs(v) for v in e))
                return set()
            refs = set().union(*(inputs(e) for e in expressions)) | {"project.classification"}
            dr = data.get("domainRegistry",{})
            specifications = [s for s in dr.get("scopes",[]) if s.get("downstreamStage") == self._scope["downstreamStage"] and cls in s.get("projectClasses",[])]
            result = dict(branches=bs,rules=rs,sources={s:data.get("sources",{}).get(s) for s in sorted(srcs)},
                        applicability=dict(id=ar.get("id"),status=ar.get("status"),definitions=defs,inputBindings={r:ar.get("inputBindings",{}).get(r) for r in sorted(refs)}),
                        domainRegistry=dict(id=dr.get("id"),status=dr.get("status"),specifications=specifications))
            per_branch = {}
            for bid in linked:
                rows = rs[bid]; metadata = [b for b in bs if b["branchId"] == bid]
                exprs = [defs.get(b.get("applicabilityId")) for b in metadata]+[r.get("applicability") for r in rows if isinstance(r,dict)] if isinstance(rows,list) else []
                ids = set().union(*(inputs(e) for e in exprs)) | {"project.classification"}
                docs = {r["source"]["documentId"]+"@"+r["source"]["documentRevision"] for r in rows if isinstance(r,dict) and isinstance(r.get("source"),dict) and all(_label(r["source"].get(k)) for k in ("documentId","documentRevision"))} if isinstance(rows,list) else set()
                per_branch[bid] = dict(metadata=metadata,rules=rows,sourceEvidence={s:result["sources"].get(s) for s in docs},
                    definitions=exprs,bindings={id:ar.get("inputBindings",{}).get(id) for id in ids})
            result["perBranch"] = per_branch
            return result
        try:
            before,after = signature(current),signature(new)
        except (ValueError,TypeError,KeyError,AttributeError,RecursionError):
            # Invalid new registries cannot grant UNCHANGED or crash into a success path.
            result = dict(status="BLOCKED_BY_NORMATIVE_CHANGE",oldSnapshotId=old["snapshotId"],newLibraryFingerprint=new_library.library_fingerprint,
                changedRuleIds=[],changedBranches=sorted(linked),affectedProjectInputs=[],affectedBundleRuleIds=[c["ruleId"] for c in old["compiledRules"]],
                downstreamDomains=sorted({d for i in old["impactIndex"] for d in i["downstreamDomains"]}),candidateStatus=candidate["status"],
                reason="MALFORMED_NEW_LIBRARY_METADATA",candidateErrors=candidate["validationErrors"],historicalSnapshotUnchanged=True)
            result["changeId"] = "change-"+fingerprint(result)
            return result
        changed = []
        for bid in sorted(linked):
            if fingerprint(before["perBranch"].get(bid)) != fingerprint(after["perBranch"].get(bid)): changed.append(bid)
        registry_change = before["domainRegistry"] != after["domainRegistry"] or before["applicability"]["id"] != after["applicability"]["id"] or before["applicability"]["status"] != after["applicability"]["status"]
        if registry_change: changed = sorted(linked)
        if not changed and not registry_change: status = "UNCHANGED"
        elif candidate["status"] != "VERIFIED": status = "BLOCKED_BY_NORMATIVE_CHANGE"
        else:
            required = {b["branchId"] for b in old["applicableBranches"] if b["blocking"]}
            required |= {b["branchId"] for b in candidate["applicableBranches"] if b["blocking"]}
            status = "REQUIRES_REAUDIT" if set(changed) & required or registry_change else "UPDATE_AVAILABLE_NONBLOCKING"
        changed_ids = set()
        for bid in changed:
            old_rules = {canonical([r.get("ruleId"),r.get("revision")]):r for r in before["rules"][bid] if isinstance(r,dict)} if isinstance(before["rules"][bid],list) else {}
            new_rules = {canonical([r.get("ruleId"),r.get("revision")]):r for r in after["rules"][bid] if isinstance(r,dict)} if isinstance(after["rules"][bid],list) else {}
            changed_ids |= {json.loads(k)[0] for k in old_rules.keys()|new_rules.keys() if _label(json.loads(k)[0]) and old_rules.get(k) != new_rules.get(k)}
        affected_old = [i for i in old["impactIndex"] if i["branchId"] in changed or i["ruleId"] in changed_ids]
        affected = affected_old+[i for i in candidate["impactIndex"] if i["branchId"] in changed or i["ruleId"] in changed_ids]
        impact = dict(status=status,oldSnapshotId=old["snapshotId"],newLibraryFingerprint=new_library.library_fingerprint,
                      changedRuleIds=sorted(changed_ids),changedBranches=changed,affectedBundleRuleIds=sorted({i["ruleId"] for i in affected_old}),
                      affectedProjectInputs=sorted({p for i in affected for p in i["projectInputs"]}),downstreamDomains=sorted({d for i in affected for d in i["downstreamDomains"]}),
                      candidateStatus=candidate["status"],candidateGaps=candidate["normativeGaps"],candidateConflicts=candidate["conflicts"],
                      supersededRuleRevisions=candidate["supersessionIndex"],historicalSnapshotUnchanged=True)
        impact["changeId"] = "change-"+fingerprint(impact)
        return impact


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    for opt in ("stage0-registry","stage0-sources","functional-brief","intent","site-sources","site-requirements","constraint-sources","library","scope","output"):
        p.add_argument("--"+opt,type=Path,required=True)
    p.add_argument("--compare-library",type=Path)
    a = p.parse_args(); load = lambda path:json.loads(path.read_text(encoding="utf-8"))
    s0 = Stage0(load(a.stage0_registry),load(a.stage0_sources)); s0.audit()
    fp = FunctionalProgram(s0,load(a.functional_brief)); fp.audit()
    di = DesignIntent(s0,fp,load(a.intent)); di.audit()
    site = SiteContext(s0,load(a.site_sources),load(a.site_requirements)); site.audit()
    constraints = ProjectConstraintInput(s0,fp,di,site,load(a.constraint_sources)); constraints.audit()
    model = ProjectNormativeBundle(s0,fp,di,site,constraints,GlobalRuleLibrary(load(a.library)),load(a.scope)); out = model.audit()
    if a.compare_library and out["status"] == "VERIFIED": out = model.compare_library(GlobalRuleLibrary(load(a.compare_library)))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return 0 if out["status"] in {"VERIFIED","UNCHANGED","UPDATE_AVAILABLE_NONBLOCKING","REQUIRES_REAUDIT"} else 2


if __name__ == "__main__": raise SystemExit(main())
