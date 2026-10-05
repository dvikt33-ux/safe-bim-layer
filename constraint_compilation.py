"""CONSTRAINT COMPILATION v0: declarative inputs for planning, no solving/compliance."""
from copy import deepcopy
import json
import math
from pathlib import Path

from design_stage0 import Stage0, fingerprint
from functional_program import FunctionalProgram, canonical
from design_intent import DesignIntent
from site_context import SiteContext
from project_constraints import ProjectConstraintInput
from normative_bundle import ProjectNormativeBundle

FLOW = ["REQUIRE VERIFIED UPSTREAM","IMPORT PROJECT CONSTRAINTS","IMPORT NORMATIVE RULE REQUIREMENTS",
        "NORMALIZE CONSTRAINT DOMAINS","NORMALIZE SUBJECTS","NORMALIZE SCOPES","NORMALIZE OPERATORS",
        "PRESERVE UNITS","BUILD SOURCE PRECEDENCE MODEL","MERGE COMPATIBLE CONSTRAINTS",
        "DETECT CONTRADICTIONS","BUILD DEPENDENCY GRAPH","BUILD TRACEABILITY GRAPH",
        "BUILD PLANNING INPUT SET","RE-AUDIT"]
FP_KEYS = ("contextFingerprint","programFingerprint","designIntentFingerprint","siteContextFingerprint","constraintInputFingerprint","normativeBundleFingerprint")
OUT_KEYS = ("stage0Fingerprint","functionalProgramFingerprint","designIntentFingerprint","siteContextFingerprint","constraintInputFingerprint","normativeBundleFingerprint")
OPS = {"eq","neq","gt","gte","lt","lte","in","not_in","require","prohibit","preserve"}
PROJECT_OPS = {"==":"eq","!=":"neq",">":"gt",">=":"gte","<":"lt","<=":"lte","IN":"in","NOT_IN":"not_in","REQUIRE":"require","PROHIBIT":"prohibit","PRESERVE":"preserve"}


def _label(v): return isinstance(v,str) and bool(v.strip())
def _number(v): return type(v) in (int,float) and math.isfinite(v)
def _scalar(v): return isinstance(v,(str,bool)) or _number(v)
def _equal(a,b): return a == b and (type(a) is type(b) or _number(a) and _number(b))


def compilation_fingerprint(out):
    payload = deepcopy(out); payload.pop("constraintCompilationFingerprint",None)
    payload.get("planningInput",{}).pop("sourceCompilationFingerprint",None)
    return fingerprint(payload)


def _accept(c,v):
    op,x = c["operator"],c["value"]
    if op in {"eq","require","preserve"}: return _equal(v,x)
    if op in {"neq","prohibit"}: return not _equal(v,x)
    if op in {"in","not_in"}: return any(_equal(v,y) for y in x) == (op == "in")
    if not _number(v): return False
    return {"gt":lambda:v>x,"gte":lambda:v>=x,"lt":lambda:v<x,"lte":lambda:v<=x}[op]()


def logical_group(records,mode):
    """Intersect declared bounds/sets only; never evaluate actual project geometry."""
    lower,upper = None,None
    for c in records:
        op,v = c["operator"],c["value"]
        if op in {"gt","gte"} and (lower is None or v > lower["value"] or v == lower["value"] and op == "gt"): lower = c
        if op in {"lt","lte"} and (upper is None or v < upper["value"] or v == upper["value"] and op == "lt"): upper = c
    positive = [c for c in records if c["operator"] in {"eq","in"} or mode == "SINGLE_VALUE" and c["operator"] in {"require","preserve"}]
    conflict,allowed = False,None
    if positive:
        universe = [v for c in positive for v in (c["value"] if c["operator"] == "in" else [c["value"]])]
        checked = records if mode == "SINGLE_VALUE" else [c for c in records if c["operator"] not in {"require","preserve"}]
        allowed = sorted({canonical(v):v for v in universe if all(_accept(c,v) for c in checked)}.values(),key=canonical)
        conflict = not allowed
    required = [c["value"] for c in records if c["operator"] in {"require","preserve"}]
    prohibitions = [c for c in records if c["operator"] in {"prohibit","not_in","neq"}]
    if mode == "MEMBERSHIP":
        conflict |= any(not all(_accept(c,v) for c in prohibitions) or allowed is not None and not any(_equal(v,a) for a in allowed) for v in required)
    if lower and upper:
        conflict |= lower["value"] > upper["value"] or lower["value"] == upper["value"] and (lower["operator"] == "gt" or upper["operator"] == "lt")
        if records[0]["unit"] == "count":
            lo = math.ceil(lower["value"])+int(lower["operator"] == "gt" and lower["value"] == math.ceil(lower["value"]))
            hi = math.floor(upper["value"])-int(upper["operator"] == "lt" and upper["value"] == math.floor(upper["value"]))
            conflict |= lo > hi
        if lower["value"] == upper["value"]: conflict |= not all(_accept(c,lower["value"]) for c in records)
    return dict(conflict=bool(conflict),lowerBound=deepcopy(lower),upperBound=deepcopy(upper),allowedValues=allowed,
                requiredValues=sorted({canonical(v):v for v in required}.values(),key=canonical),
                exclusions=[deepcopy(c) for c in prohibitions])


class ConstraintCompilation:
    def __init__(self,stage0,functional_program,design_intent,site_context,constraint_input,normative_bundle,domain_registry,reference_registry):
        self._upstream = (stage0,functional_program,design_intent,site_context,constraint_input,normative_bundle)
        if not all(isinstance(x,t) for x,t in zip(self._upstream,(Stage0,FunctionalProgram,DesignIntent,SiteContext,ProjectConstraintInput,ProjectNormativeBundle))):
            raise TypeError("six live upstream sessions required; no injected constraint records")
        self._domains,self._references = deepcopy(domain_registry),deepcopy(reference_registry)
        self._result = None

    def _deps(self):
        rs = [u.result() for u in self._upstream]
        return rs,[r.get(k) if r else None for r,k in zip(rs,FP_KEYS)]

    def _refresh(self):
        if self._result and self._result.get("dependencyVerified"):
            rs,fs = self._deps()
            if fs != self._result["upstreamFingerprints"] or any(not r or r["status"] != "VERIFIED" for r in rs):
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="UPSTREAM_CHANGED_OR_NOT_VERIFIED")
                self._result["planningInput"] = {"status":"WITHHELD"}

    def result(self): self._refresh(); return deepcopy(self._result)

    def update_registries(self,domain_registry=None,reference_registry=None):
        d = self._domains if domain_registry is None else deepcopy(domain_registry)
        r = self._references if reference_registry is None else deepcopy(reference_registry)
        if fingerprint([d,r]) != fingerprint([self._domains,self._references]):
            self._domains,self._references = d,r
            if self._result:
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="REGISTRY_CHANGED")
                self._result["planningInput"] = {"status":"WITHHELD"}

    def require_verified(self):
        self._refresh()
        for u in self._upstream: u.require_verified()
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"] or self._result["constraintCompilationFingerprint"] != compilation_fingerprint(self._result):
            raise RuntimeError("Constraint Compilation progression blocked")
        return deepcopy(self._result["gateProof"])

    def planning_input(self):
        self.require_verified(); return deepcopy(self._result["planningInput"])

    def lookup_origin(self,origin_type,original_id):
        self._refresh()
        if not self._result: return []
        return deepcopy(self._result["traceabilityIndex"]["byOriginalId"].get(origin_type,{}).get(original_id,[]))

    def _registries(self):
        d,r = self._domains,self._references
        for reg in (d,r):
            if not isinstance(reg,dict) or reg.get("status") != "VERIFIED" or not _label(reg.get("id")) or not _label(reg.get("revision")): raise ValueError("VERIFIED versioned domain/reference registries required")
        if set(d) != {"id","revision","status","domains","projectTypes","functionalFields","normativeDomainAliases","subjectAliases","subjectReferences"} or set(r) != {"id","revision","status","overlaps"}: raise ValueError("strict declarative registries required; no expressions or conversions")
        if not isinstance(d["domains"],dict) or not d["domains"] or any(not _label(k) or v not in {"SINGLE_VALUE","MEMBERSHIP"} for k,v in d["domains"].items()): raise ValueError("explicit domain comparison semantics required")
        for k in ("projectTypes","functionalFields","normativeDomainAliases","subjectAliases"):
            if not isinstance(d[k],dict): raise ValueError("declarative mapping dictionaries required")
        for collection in ("projectTypes","functionalFields"):
            for spec in d[collection].values():
                if not isinstance(spec,dict) or set(spec) != {"domain","subjectTemplate","unit"} or spec["domain"] not in d["domains"] or not _label(spec["unit"]) or not _label(spec["subjectTemplate"]): raise ValueError("strict registered declarative adapter required")
        if "EXISTENCE" not in d["functionalFields"]: raise ValueError("explicit existence adapter required")
        if any(not isinstance(v,dict) or any(not _label(a) or not _label(b) for a,b in v.items()) for v in d["subjectAliases"].values()) or any(not _label(a) or b not in d["domains"] for a,b in d["normativeDomainAliases"].items()): raise ValueError("explicit domain/subject aliases required")
        if not isinstance(d["subjectReferences"],dict) or any(not _label(k) or v not in {"SPACE","OBJECT","FLOOR","ZONE","SYSTEM","ACCESS"} for k,v in d["subjectReferences"].items()): raise ValueError("explicit subject reference prefixes required")
        if not isinstance(r["overlaps"],dict) or any(not isinstance(v,list) or any(x not in {"PROJECT","SITE","BUILDING","FLOOR","SPACE","ZONE","OBJECT","SYSTEM"} for x in v) for v in r["overlaps"].values()): raise ValueError("bounded scope overlap registry required")

    def _covers(self,broad,narrow):
        if broad == narrow: return True
        if ":" in broad: return False
        return narrow.split(":")[0] in self._references["overlaps"].get(broad,[])

    def _subject(self,spec,raw,scopes):
        if not isinstance(spec,dict) or set(spec) != {"domain","subjectTemplate","unit"} or spec["domain"] not in self._domains["domains"] or not _label(spec["subjectTemplate"]): raise ValueError("explicit registered adapter required")
        token = spec["subjectTemplate"]
        if "{subject}" in token:
            if not _label(raw): raise ValueError("explicit source subject required")
            token = token.replace("{subject}",raw)
        token = self._domains["subjectAliases"].get(spec["domain"],{}).get(token,token)
        if "{scopeId}" in token:
            if len(scopes) != 1 or ":" not in scopes[0]: raise ValueError("adapter requires one explicit entity scope")
            token = token.replace("{scopeId}",scopes[0].split(":",1)[1])
        if "{" in token or "}" in token: raise ValueError("unsupported subject template; no arbitrary expressions")
        return token

    def audit(self):
        self._refresh(); rs,fs = self._deps()
        out = dict(stage="CONSTRAINT_COMPILATION",schemaVersion=0,status="BLOCKED",canProgress=False,dependencyVerified=False,
            upstreamFingerprints=fs,mandatoryConstraints=[],effectiveConstraints=[],preferences=[],siteFacts=[],conflicts=[],unitIssues=[],
            unresolvedReferences=[],validationErrors=[],overrides=[],dependencyGraph={"nodes":[],"edges":[]},
            traceabilityIndex={"byCompiledConstraintId":{},"byOrigin":{},"byOriginalId":{}},planningInput={"status":"WITHHELD"},provenanceCoverage=0.0,flow=list(FLOW),
            conversionPolicy="NO_CONVERSION_V0",domainRegistryFingerprint=fingerprint(self._domains),referenceRegistryFingerprint=fingerprint(self._references),
            sourcePrecedenceModel={"mandatoryOrigins":"NO_AUTOMATIC_PRIORITY", "preferencePolicy":"MANDATORY_OVERRIDES_PREFERENCE_WITH_EVIDENCE"})
        for k,v in zip(OUT_KEYS,fs): out[k] = v
        try:
            for u in self._upstream: u.require_verified()
            self._registries()
            for i in range(1,6):
                if rs[i]["stage0Fingerprint"] != fs[0]: raise ValueError("incoherent Stage0 chain")
            if rs[2]["functionalProgramFingerprint"] != fs[1] or rs[4]["upstreamFingerprints"] != fs[:4] or rs[5]["upstreamFingerprints"] != fs[:5]: raise ValueError("incoherent upstream fingerprints")
            if fingerprint({k:v for k,v in rs[4].items() if k != "constraintInputFingerprint"}) != fs[4]: raise ValueError("project constraint artifact integrity mismatch")
            if rs[5] != self._upstream[5].snapshot(): raise ValueError("normative bundle content absent from pinned verified snapshot")
            out["dependencyVerified"] = True
        except (RuntimeError,ValueError,TypeError,KeyError) as exc:
            out["validationErrors"].append(dict(reason=str(exc))); self._result = out; return self.result()
        s0,fp,di,site,pc,bundle = rs
        refs = {"PROJECT","SITE","BUILDING"} | {"SPACE:"+s["spaceId"] for s in fp["spaces"]} | {e["scope"] for e in pc["scopeEntities"]}
        refs |= {"OBJECT:"+o["objectId"] for o in site["existingObjects"]} | {"ZONE:"+z["zone"] for z in fp["functionalZones"]}
        refs |= {"ZONE:"+f["featureId"] for f in site["contextFeatures"] if f.get("geometry",{}).get("type") == "Polygon"}
        value_refs = refs | {"ACCESS:"+a["accessId"] for a in site["accessPoints"]}
        nodes,edges = {},[]
        artifact_ids = {}
        for name,fpvalue in zip(OUT_KEYS,fs):
            id = "upstream-"+fingerprint([name,fpvalue]); artifact_ids[name] = id
            nodes[id] = dict(nodeId=id,type="UPSTREAM_INPUT",artifact=name,fingerprint=fpvalue)

        def source_ref(artifact,origin,id,revision,evidence):
            return dict(originType=origin,upstreamArtifact=artifact,artifactFingerprint=out[artifact],originalId=id,
                        exactRevision=revision,sourceEvidence=deepcopy(evidence))

        def add(domain,subject,scope,op,value,unit,strength,origin,source,basis=None,used=None,dependencies=None):
            try:
                if domain not in self._domains["domains"] or not _label(subject) or op not in OPS or not _label(unit): raise ValueError("unknown domain/subject/operator/unit")
                if op in {"in","not_in"}:
                    if not isinstance(value,list) or not value or not all(_scalar(v) for v in value): raise ValueError("explicit nonempty finite scalar set required")
                elif not _scalar(value):
                    phasing = isinstance(value,list) and bool(value) and all(_label(v) for v in value) and any(p.get("rawEvidence",{}).get("type") == "PHASING_REQUIRED" for p in source["sourceEvidence"])
                    if not phasing or op != "require": raise ValueError("finite scalar or explicitly confirmed ordered phasing labels required; functions/expressions forbidden")
                if op in {"gt","gte","lt","lte"} and not _number(value): raise ValueError("numeric bound required")
                if not isinstance(scope,list) or not scope or any(not _label(s) for s in scope): raise ValueError("explicit scope required")
                c = dict(domain=domain,subject=subject,scope=sorted(set(scope)),operator=op,value=deepcopy(value),unit=unit,
                    strength=strength,originType=origin,sourceRefs=[source],applicabilityBasis=deepcopy(basis or []),
                    projectInputsUsed=deepcopy(used or []),dependencies=deepcopy(dependencies or []),provenance=deepcopy(source["sourceEvidence"]))
                c["normalizationBasis"] = dict(domainRegistryId=self._domains["id"],domainRegistryRevision=self._domains["revision"],
                    domainRegistryFingerprint=out["domainRegistryFingerprint"],referenceRegistryId=self._references["id"],referenceRegistryRevision=self._references["revision"],unitPolicy="PRESERVE_NO_CONVERSION")
                if not c["provenance"]: raise ValueError("source provenance required")
                for s in c["scope"]:
                    if s not in refs: out["unresolvedReferences"].append(dict(status="DANGLING_REFERENCE",reference=s,sourceRef=source,blocking=strength == "MANDATORY"))
                for v in value if op in {"in","not_in"} else [value]:
                    if isinstance(v,str) and v.startswith(("FLOOR:","SPACE:","ZONE:","OBJECT:","SYSTEM:","ACCESS:")) and v not in value_refs:
                        out["unresolvedReferences"].append(dict(status="DANGLING_REFERENCE",reference=v,sourceRef=source,blocking=strength == "MANDATORY"))
                for prefix,kind in self._domains["subjectReferences"].items():
                    if subject.startswith(prefix):
                        ref = kind+":"+subject[len(prefix):]
                        if ref not in value_refs: out["unresolvedReferences"].append(dict(status="DANGLING_SUBJECT_REFERENCE",reference=ref,sourceRef=source,blocking=strength == "MANDATORY"))
                c["compiledConstraintId"] = "constraint-"+fingerprint(c)
                target = "mandatoryConstraints" if strength == "MANDATORY" else "preferences"
                out[target].append(c)
                sid = "source-"+fingerprint(source)
                nodes[sid] = dict(nodeId=sid,type="NORMATIVE_RULE" if origin == "NORMATIVE_REQUIREMENT" else "PROJECT_CONSTRAINT" if origin.startswith("PROJECT_") else "FUNCTIONAL_REQUIREMENT" if origin == "FUNCTIONAL_REQUIREMENT" else "PLANNING_PREFERENCE",sourceRef=source)
                cid = c["compiledConstraintId"]; nodes[cid] = dict(nodeId=cid,type="COMPILED_CONSTRAINT",strength=strength)
                edges.extend([dict(fromId=cid,toId=sid,type="DERIVED_FROM"),dict(fromId=sid,toId=cid,type="SUPPORTS"),dict(fromId=sid,toId=artifact_ids[source["upstreamArtifact"]],type="DERIVED_FROM")])
                for scopeid in c["scope"]:
                    nid = "scope-"+fingerprint(scopeid); nodes[nid] = dict(nodeId=nid,type="UPSTREAM_INPUT",scopeReference=scopeid,resolved=scopeid in refs)
                    edges.append(dict(fromId=cid,toId=nid,type="APPLIES_TO"))
                    kind = scopeid.split(":")[0]
                    scope_artifact = "functionalProgramFingerprint" if kind == "SPACE" or kind == "ZONE" and any(z["zone"] == scopeid.split(":",1)[1] for z in fp["functionalZones"]) else "siteContextFingerprint" if kind in {"SITE","OBJECT","ZONE"} else "constraintInputFingerprint" if kind in {"FLOOR","SYSTEM"} else "stage0Fingerprint"
                    edges.append(dict(fromId=nid,toId=artifact_ids[scope_artifact],type="DERIVED_FROM"))
                out["traceabilityIndex"]["byCompiledConstraintId"][cid] = [source]
                key = origin+":"+source["originalId"]+"@"+str(source["exactRevision"])
                out["traceabilityIndex"]["byOrigin"].setdefault(key,[]).append(cid)
                out["traceabilityIndex"]["byOriginalId"].setdefault(origin,{}).setdefault(source["originalId"],[]).append(cid)
                return c,sid
            except (ValueError,TypeError,KeyError) as exc: out["validationErrors"].append(dict(reason=str(exc),sourceRef=source)); return None,None

        for p in pc["constraints"]+pc["derivedConstraints"]+pc["nonBindingConstraints"]:
            origin = "PROJECT_HARD_CONSTRAINT" if p["binding"] else "PROJECT_NON_BINDING_CONSTRAINT"
            src = source_ref("constraintInputFingerprint",origin,p["constraintId"],sorted({x["sourceRevision"] for x in p["provenance"]}),p["provenance"])
            try:
                spec = self._domains["projectTypes"][p["type"]]
                operator = PROJECT_OPS[p["operator"]]
                if p["type"] == "EXISTING_OBJECT_REMOVE_REQUIRED": operator = "prohibit"
                groups = [[s] for s in p["scope"]] if "{scopeId}" in spec["subjectTemplate"] else [p["scope"]]
                for scopes in groups:
                    subject = self._subject(spec,p.get("subject"),scopes)
                    add(spec["domain"],subject,scopes,operator,p["value"],p["unit"],"MANDATORY" if p["binding"] else "PREFERENCE",origin,src,dependencies=p.get("inputEvidence",[]))
            except (ValueError,TypeError,KeyError) as exc: out["validationErrors"].append(dict(reason=str(exc),sourceRef=src))
        norm_nodes = {}
        for rule in bundle["compiledRules"]:
            r = rule["requirement"]
            src = source_ref("normativeBundleFingerprint","NORMATIVE_REQUIREMENT",rule["ruleId"],rule["ruleRevision"],rule["provenance"])
            src.update(branchId=rule["branchId"],originalRequirement=deepcopy(r),sourceDocument=rule["sourceDocument"],sourceRevision=rule["sourceRevision"],sourceHash=rule["sourceHash"],sourceLocation=deepcopy(rule["sourceLocation"]))
            domain = self._domains["normativeDomainAliases"].get(r["domain"],r["domain"])
            subject = self._domains["subjectAliases"].get(domain,{}).get(r["subject"],r["subject"])
            c,nid = add(domain,subject,r["scope"],r["operator"],r["value"],r["unit"],"MANDATORY","NORMATIVE_REQUIREMENT",src,rule["applicabilityBasis"],rule["projectInputsUsed"],rule["dependencies"])
            if c: norm_nodes[canonical(dict(ruleId=rule["ruleId"],revision=rule["ruleRevision"],branchId=rule["branchId"]))] = nid
        for c in out["mandatoryConstraints"]:
            if c["originType"] == "NORMATIVE_REQUIREMENT":
                sr = c["sourceRefs"][0]; sid = "source-"+fingerprint(sr)
                for dep in c["dependencies"]:
                    target = norm_nodes.get(canonical(dep))
                    if not target: out["unresolvedReferences"].append(dict(reference=dep,status="MISSING_RULE_DEPENDENCY",blocking=True))
                    else: edges.append(dict(fromId=sid,toId=target,type="DEPENDS_ON"))

        for collection,strength in (("userRequirements","MANDATORY"),("userPreferences","PREFERENCE")):
            for index,req in enumerate(fp[collection]):
                src = source_ref("functionalProgramFingerprint","FUNCTIONAL_REQUIREMENT",req.get("target",req.get("from","relationship"))+":"+req.get("field",req.get("type","record"))+":"+str(index),fp["briefFingerprint"],req["provenance"])
                try:
                    if "field" in req and req["target"].startswith("space:"):
                        scopes = ["SPACE:"+req["target"][6:]]; field = req["field"]
                        spec = self._domains["functionalFields"][field]; subject = self._subject(spec,None,scopes)
                        if field == "requestedArea":
                            values = [("eq",req["value"])] if "value" in req else [("gte",req["min"]),("lte",req["max"])]
                            for op,v in values: add(spec["domain"],subject,scopes,op,v,req["unit"],strength,"FUNCTIONAL_REQUIREMENT",src)
                        elif field == "specialEquipment":
                            for v in req["value"]: add(spec["domain"],subject,scopes,"require",v,spec["unit"],strength,"FUNCTIONAL_REQUIREMENT",src)
                        else: add(spec["domain"],subject,scopes,"require" if field == "function" else "eq",req["value"],spec["unit"],strength,"FUNCTIONAL_REQUIREMENT",src)
                    elif "type" in req and "from" in req:
                        spec = self._domains["functionalFields"]["RELATIONSHIP"]
                        scopes = ["SPACE:"+req["from"],"SPACE:"+req["to"]]
                        add(spec["domain"],"RELATIONSHIP:"+req["type"]+":"+req["from"]+":"+req["to"],scopes,"require",req["type"],spec["unit"],strength,"FUNCTIONAL_REQUIREMENT",src)
                    elif req.get("target","").startswith("user:"):
                        spec = self._domains["functionalFields"]["USER_"+req["field"]]
                        add(spec["domain"],self._subject(spec,req["target"][5:],["PROJECT"]),["PROJECT"],"eq",req["value"],spec["unit"],strength,"FUNCTIONAL_REQUIREMENT",src)
                    elif req.get("target","").startswith("context:"): pass  # classification/context is already a gated factual dependency
                    else: raise ValueError("unsupported functional requirement shape; cannot silently drop it")
                except (ValueError,TypeError,KeyError) as exc: out["validationErrors"].append(dict(reason=str(exc),sourceRef=src))
        for space in fp["spaces"]:
            spec = self._domains["functionalFields"]["EXISTENCE"]
            scopes = ["SPACE:"+space["spaceId"]]; src = source_ref("functionalProgramFingerprint","FUNCTIONAL_REQUIREMENT","SPACE_EXISTS:"+space["spaceId"],fp["briefFingerprint"],space["provenance"])
            add(spec["domain"],self._subject(spec,None,scopes),scopes,"require",True,spec["unit"],"MANDATORY","FUNCTIONAL_REQUIREMENT",src)
        for g in di["goals"]:
            scopes = [s.upper() if s == "SITE" else s.replace("space:","SPACE:").replace("zone:","ZONE:") for s in g["scope"]]
            src = source_ref("designIntentFingerprint","DESIGN_PREFERENCE",g["goalId"],di["sourceFingerprint"],g["provenance"])
            c,_ = add("CUSTOM","GOAL:"+g["goalId"],scopes,"require",g["type"],"none","MANDATORY" if g["commitment"] == "MANDATORY" else "PREFERENCE","DESIGN_PREFERENCE",src)
            if c: c["goalMetadata"] = {k:deepcopy(g.get(k)) for k in ("priority","weight","commitment","target","tolerance")}

        site_records = [("SITE",site["site"]),("BOUNDARY",site["boundary"]),("ORIENTATION",site["orientation"])]
        site_records += [("OBJECT:"+o["objectId"],o) for o in site["existingObjects"]]+[("ACCESS:"+a["accessId"],a) for a in site["accessPoints"]]+[("CONTEXT:"+f["featureId"],f) for f in site["contextFeatures"]]+[("METRIC:"+m["metricId"],m) for m in site["derivedMetrics"]]
        site_records += [("TERRAIN",site["terrain"])]
        for key,rec in site_records:
            if not rec: continue
            fact = dict(factId="fact-"+fingerprint([key,fs[3]]),subject=key,strength="INFORMATIONAL",originType="SITE_FACT_DEPENDENCY",scope=["SITE"],
                        value=deepcopy(rec),sourceRefs=[dict(upstreamArtifact="siteContextFingerprint",artifactFingerprint=fs[3],originalId=key)],provenance=deepcopy(rec.get("provenance",[])))
            if not fact["provenance"] and key == "TERRAIN": fact["provenance"] = [dict(method="EXPLICIT_SITE_TERRAIN_STATUS",siteContextFingerprint=fs[3],status=rec["status"])]
            out["siteFacts"].append(fact); fid = fact["factId"]; nodes[fid] = dict(nodeId=fid,type="SITE_FACT",sourceRef=fact["sourceRefs"][0])
            edges.append(dict(fromId=fid,toId=artifact_ids["siteContextFingerprint"],type="DERIVED_FROM"))

        fact_nodes = {f["subject"]:f["factId"] for f in out["siteFacts"]}
        input_artifacts = dict(zip(("STAGE0","FUNCTIONAL_PROGRAM","DESIGN_INTENT","SITE_CONTEXT","PROJECT_CONSTRAINT_INPUT"),OUT_KEYS[:5]))
        for c in out["mandatoryConstraints"]+out["preferences"]:
            for s in c["scope"]:
                if s in fact_nodes: edges.append(dict(fromId=c["compiledConstraintId"],toId=fact_nodes[s],type="DEPENDS_ON"))
            for used in c["projectInputsUsed"]:
                name = input_artifacts.get(used.get("artifact"))
                if name:
                    iid = "input-"+fingerprint(used); nodes[iid] = dict(nodeId=iid,type="UPSTREAM_INPUT",evidence=deepcopy(used))
                    edges.extend([dict(fromId=c["compiledConstraintId"],toId=iid,type="DEPENDS_ON"),dict(fromId=iid,toId=artifact_ids[name],type="DERIVED_FROM")])

        mandatory = out["mandatoryConstraints"]
        groups = {(c["domain"],c["subject"],s) for c in mandatory for s in c["scope"]}
        for domain,subject,scope in sorted(groups):
            group = [c for c in mandatory if c["domain"] == domain and c["subject"] == subject and any(self._covers(s,scope) for s in c["scope"])]
            units = {c["unit"] for c in group}
            if len(units) != 1:
                out["unitIssues"].append(dict(status="UNIT_RECONCILIATION_REQUIRED",domain=domain,subject=subject,scope=[scope],units=sorted(units),sourceConstraints=deepcopy(group),blocking=True)); continue
            result = logical_group(group,self._domains["domains"][domain])
            if result["conflict"]:
                out["conflicts"].append(dict(status="CONFLICT",reason="INCOMPATIBLE_MANDATORY_DECLARATIONS",domain=domain,subject=subject,scope=[scope],exactBounds=result,sourceConstraints=deepcopy(group)))
                for a,b in zip(group,group[1:]): edges.append(dict(fromId=a["compiledConstraintId"],toId=b["compiledConstraintId"],type="CONFLICTS_WITH"))
            else:
                effective = dict(domain=domain,subject=subject,scope=[scope],unit=group[0]["unit"],strength="MANDATORY",sourceConstraints=[c["compiledConstraintId"] for c in group],**{k:v for k,v in result.items() if k != "conflict"})
                effective["effectiveConstraintId"] = "effective-"+fingerprint(effective); out["effectiveConstraints"].append(effective)
                for bound in (result["lowerBound"],result["upperBound"]):
                    if bound:
                        for weaker in group:
                            if weaker["operator"] in ({"gt","gte"} if bound["operator"] in {"gt","gte"} else {"lt","lte"}) and weaker != bound:
                                edges.append(dict(fromId=bound["compiledConstraintId"],toId=weaker["compiledConstraintId"],type="NARROWS"))
        for pref in out["preferences"]:
            relevant = [c for c in mandatory if c["domain"] == pref["domain"] and c["subject"] == pref["subject"] and any(self._covers(a,b) or self._covers(b,a) for a in pref["scope"] for b in c["scope"])]
            if any(c["unit"] != pref["unit"] for c in relevant):
                out["unitIssues"].append(dict(status="UNIT_RECONCILIATION_REQUIRED",subject=pref["subject"],sourceConstraints=[pref]+relevant,blocking=False)); continue
            if relevant and logical_group(relevant+[pref],self._domains["domains"][pref["domain"]])["conflict"]:
                override = dict(status="PREFERENCE_OVERRIDDEN",preferenceId=pref["compiledConstraintId"],mandatoryConstraintIds=[c["compiledConstraintId"] for c in relevant],preferenceEvidence=deepcopy(pref),reason="mandatory declaration overrides optional preference")
                out["overrides"].append(override)
                for c in relevant: edges.append(dict(fromId=c["compiledConstraintId"],toId=pref["compiledConstraintId"],type="OVERRIDES_PREFERENCE"))
        out["dependencyGraph"] = dict(nodes=sorted(nodes.values(),key=canonical),edges=sorted({canonical(e):e for e in edges}.values(),key=canonical))
        try: validate_graph(out["dependencyGraph"])
        except ValueError as exc: out["validationErrors"].append(dict(reason=str(exc)))
        records = mandatory+out["preferences"]+out["siteFacts"]
        out["provenanceCoverage"] = sum(bool(r["provenance"]) for r in records)/len(records) if records else 1.0
        blocked = bool(out["conflicts"] or out["validationErrors"] or any(x["blocking"] for x in out["unitIssues"]+out["unresolvedReferences"]) or out["provenanceCoverage"] != 1)
        out["gateProof"] = dict(allUpstreamVerified=True,fingerprintChainCoherent=True,allMandatoryScopesResolved=not any(x["blocking"] for x in out["unresolvedReferences"]),
            allNormativeOriginsFromBundle=True,allProjectOriginsFromVerifiedInputs=True,allRequiredUnitsCompatible=not any(x["blocking"] for x in out["unitIssues"]),
            conflictsCount=len(out["conflicts"]),provenanceCoverage=out["provenanceCoverage"],dependencyGraphValid=not out["validationErrors"],
            inventedConstraintsCount=0,silentPreferencePromotionsCount=0,complianceClaimsCount=0,deterministic=True)
        for k in ("mandatoryConstraints","effectiveConstraints","preferences","siteFacts","conflicts","unitIssues","unresolvedReferences","validationErrors","overrides"): out[k] = sorted(out[k],key=canonical)
        if not blocked:
            out.update(status="VERIFIED",canProgress=True); out["flow"].append("CONSTRAINT_COMPILATION VERIFIED")
            out["planningInput"] = dict(mandatoryConstraints=deepcopy(out["mandatoryConstraints"]),effectiveConstraints=deepcopy(out["effectiveConstraints"]),preferences=deepcopy(out["preferences"]),siteFacts=deepcopy(out["siteFacts"]),functionalProgramRef=fs[1],designIntentRef=fs[2])
        out["constraintCompilationFingerprint"] = compilation_fingerprint(out)
        out["planningInput"]["sourceCompilationFingerprint"] = out["constraintCompilationFingerprint"]
        self._result = out; return self.result()


def validate_graph(graph):
    ids = {n["nodeId"] for n in graph["nodes"]}
    if len(ids) != len(graph["nodes"]) or any(e["fromId"] not in ids or e["toId"] not in ids for e in graph["edges"]): raise ValueError("invalid graph node/edge references")
    derivations = {id:[] for id in ids}
    for e in graph["edges"]:
        if e["type"] in {"DERIVED_FROM","DEPENDS_ON"}: derivations[e["fromId"]].append(e["toId"])
    def visit(id,path):
        if id in path: raise ValueError("provenance derivation cycle")
        for target in derivations[id]: visit(target,path|{id})
    try:
        for id in ids: visit(id,set())
    except RecursionError: raise ValueError("unbounded provenance derivation graph") from None
