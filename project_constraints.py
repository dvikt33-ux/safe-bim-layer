"""PROJECT CONSTRAINT INPUT v0: offline compilation of explicit nonnormative decisions."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from design_stage0 import Stage0, fingerprint
from functional_program import FunctionalProgram, canonical
from design_intent import DesignIntent
from site_context import SiteContext

FLOW = ["REQUIRE VERIFIED UPSTREAM", "COLLECT CONSTRAINT SOURCES", "NORMALIZE CONSTRAINTS",
        "CLASSIFY HARD / SOFT BOUNDARY", "RESOLVE SCOPE", "NORMALIZE UNITS",
        "DETECT INTERNAL CONFLICTS", "DETECT CROSS-ARTIFACT CONFLICTS",
        "IDENTIFY MISSING DECISIONS", "RE-AUDIT"]
TYPES = set("BUDGET_LIMIT AREA_LIMIT DIMENSION_LIMIT FLOOR_COUNT_FIXED HEIGHT_LIMIT_PROJECT MATERIAL_REQUIRED MATERIAL_PROHIBITED CONSTRUCTION_SYSTEM_REQUIRED CONSTRUCTION_SYSTEM_PROHIBITED EXISTING_OBJECT_PRESERVE EXISTING_OBJECT_REMOVE_REQUIRED SITE_ZONE_PROHIBITED SITE_ZONE_REQUIRED ACCESS_REQUIRED ORIENTATION_REQUIRED SPACE_LOCATION_REQUIRED SPACE_LOCATION_PROHIBITED CAPACITY_FIXED PARKING_COUNT_FIXED PHASING_REQUIRED UTILITY_CONNECTION_FIXED EQUIPMENT_REQUIRED EQUIPMENT_PROHIBITED DEMOLITION_LIMIT CUSTOM".split())
CATEGORIES = set("USER_REQUIREMENT CLIENT_REQUIREMENT APPROVED_PROJECT_DECISION PROJECT_DOCUMENT TECHNICAL_CONDITION DERIVED_PROJECT_CONSTRAINT NORMATIVE_PENDING".split())
OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "IN", "NOT_IN", "PRESERVE", "PROHIBIT", "REQUIRE"}
NUMERIC = {"BUDGET_LIMIT":{"RUB"}, "AREA_LIMIT":{"m2"}, "DIMENSION_LIMIT":{"m","mm"},
           "FLOOR_COUNT_FIXED":{"count"}, "HEIGHT_LIMIT_PROJECT":{"m","mm"}, "CAPACITY_FIXED":{"count"},
           "PARKING_COUNT_FIXED":{"count"}, "ORIENTATION_REQUIRED":{"degrees"}, "DEMOLITION_LIMIT":{"count","m2","percentage"}}
UNITS = {"m", "mm", "m2", "degrees", "count", "RUB", "percentage"}
FAMILY = {"MATERIAL_REQUIRED":"MATERIAL", "MATERIAL_PROHIBITED":"MATERIAL",
          "CONSTRUCTION_SYSTEM_REQUIRED":"CONSTRUCTION_SYSTEM", "CONSTRUCTION_SYSTEM_PROHIBITED":"CONSTRUCTION_SYSTEM",
          "EXISTING_OBJECT_PRESERVE":"EXISTING_OBJECT", "EXISTING_OBJECT_REMOVE_REQUIRED":"EXISTING_OBJECT",
          "SITE_ZONE_REQUIRED":"SITE_ZONE", "SITE_ZONE_PROHIBITED":"SITE_ZONE",
          "SPACE_LOCATION_REQUIRED":"SPACE_LOCATION", "SPACE_LOCATION_PROHIBITED":"SPACE_LOCATION",
          "EQUIPMENT_REQUIRED":"EQUIPMENT", "EQUIPMENT_PROHIBITED":"EQUIPMENT"}
FP_FIELDS = {"SPACE_LOCATION":"preferredFloor", "AREA_LIMIT":"requestedArea", "CAPACITY_FIXED":"quantity"}


def _id(v):
    return isinstance(v,str) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*",v))


def _number(v):
    return type(v) in (int,float) and math.isfinite(v) and v >= 0


def _numeric(c):
    return c["type"] in NUMERIC or c["type"] == "CUSTOM" and c["unit"] in UNITS


def _accept(c,v):
    op,x = c["operator"],c["value"]
    if c["type"] == "EXISTING_OBJECT_REMOVE_REQUIRED": op = "PROHIBIT"
    if op in ("==","REQUIRE","PRESERVE"): return v == x
    if op in ("!=","PROHIBIT"): return v != x
    if op == "IN": return v in x
    if op == "NOT_IN": return v not in x
    return {"<":lambda:v < x,"<=":lambda:v <= x,">":lambda:v > x,">=":lambda:v >= x}[op]()


def _incompatible(group):
    """Check declared domains only; no design feasibility or geometric solving."""
    choices = [{canonical(v) for v in c["value"]} if c["operator"] == "IN" else {canonical(c["value"])}
               for c in group if c["operator"] in ("IN","==","REQUIRE","PRESERVE") and c["type"] != "EXISTING_OBJECT_REMOVE_REQUIRED"]
    if choices:
        return not any(all(_accept(c,json.loads(v)) for c in group) for v in set.union(*choices))
    if not all(_numeric(c) for c in group): return False
    lower,upper = (0,True),(100,True) if group[0]["unit"] == "percentage" else (math.inf,False)
    for c in group:
        op,v = c["operator"],c["value"]
        if op in (">",">="):
            n = (v,op == ">=")
            if n[0] > lower[0] or n[0] == lower[0] and not n[1]: lower = n
        if op in ("<","<="):
            n = (v,op == "<=")
            if n[0] < upper[0] or n[0] == upper[0] and not n[1]: upper = n
    if lower[0] > upper[0] or lower[0] == upper[0] and not (lower[1] and upper[1]): return True
    if lower[0] == upper[0]: return not all(_accept(c,lower[0]) for c in group)
    if group[0]["unit"] == "count":
        lo = math.ceil(lower[0]) + int(not lower[1] and lower[0] == math.ceil(lower[0]))
        hi = math.floor(upper[0]) - int(not upper[1] and upper[0] == math.floor(upper[0])) if math.isfinite(upper[0]) else math.inf
        excluded = set(v for c in group for v in (c["value"] if c["operator"] == "NOT_IN" else [c["value"]]) if c["operator"] in ("!=","NOT_IN"))
        return lo > hi or math.isfinite(hi) and hi-lo+1 <= len({v for v in excluded if lo <= v <= hi})
    return False


class ProjectConstraintInput:
    def __init__(self,stage0,functional_program,design_intent,site_context,sources):
        self._upstream = (stage0,functional_program,design_intent,site_context)
        if not all(isinstance(x,t) for x,t in zip(self._upstream,(Stage0,FunctionalProgram,DesignIntent,SiteContext))):
            raise TypeError("four live upstream sessions required")
        self._sources,self._result = deepcopy(sources),None

    def _dependencies(self):
        results = [x.result() for x in self._upstream]
        keys = ("contextFingerprint","programFingerprint","designIntentFingerprint","siteContextFingerprint")
        return results,[r.get(k) if r else None for r,k in zip(results,keys)]

    def _refresh(self):
        if self._result and self._result.get("dependencyVerified"):
            rs,fs = self._dependencies()
            if fs != self._result["upstreamFingerprints"] or any(not r or r["status"] != "VERIFIED" for r in rs):
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="UPSTREAM_CHANGED_OR_NOT_VERIFIED")

    def result(self):
        self._refresh()
        return deepcopy(self._result)

    def update_source(self,source):
        new = [s for s in self._sources if s.get("id") != source.get("id")] + [deepcopy(source)]
        if canonical(sorted(new,key=canonical)) != canonical(sorted(self._sources,key=canonical)):
            self._sources = new
            if self._result: self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="CONSTRAINT_SOURCE_CHANGED")

    def require_verified(self):
        self._refresh()
        for x in self._upstream: x.require_verified()
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"] or self._result["sourceFingerprint"] != self._source_fingerprint():
            raise RuntimeError("Project Constraint Input progression blocked")
        return deepcopy(self._result["gateProof"])

    def planning_constraints(self):
        self.require_verified()
        return deepcopy(self._result["constraints"] + self._result["derivedConstraints"])

    def _source_fingerprint(self):
        sources = deepcopy(self._sources)
        for s in sources:
            if isinstance(s,dict) and isinstance(s.get("statements"),list): s["statements"] = sorted(s["statements"],key=canonical)
        return fingerprint(sorted(sources,key=canonical))

    def audit(self):
        self._refresh()
        rs,fs = self._dependencies()
        out = dict(stage="PROJECT_CONSTRAINT_INPUT",schemaVersion=0,status="BLOCKED",canProgress=False,
                   dependencyVerified=False,upstreamFingerprints=fs,constraints=[],derivedConstraints=[],
                   nonBindingConstraints=[],overrides=[],conflicts=[],missingConstraintInputs=[],normativePending=[],
                   validationErrors=[],questions=[],supersessions=[],scopeEntities=[],provenanceComplete=False,flow=list(FLOW))
        for k,v in zip(("stage0Fingerprint","functionalProgramFingerprint","designIntentFingerprint","siteContextFingerprint"),fs): out[k] = v
        try:
            for u in self._upstream: u.require_verified()
            s0,fp,di,site = rs
            if any(r["stage0Fingerprint"] != fs[0] for r in (fp,di,site)) or di["functionalProgramFingerprint"] != fs[1]:
                raise RuntimeError("upstream chain does not share audited dependencies")
        except RuntimeError as exc:
            out["validationErrors"].append({"reason":str(exc)})
            self._result = out; return self.result()
        out["dependencyVerified"] = True
        candidates,entities,seen = [],[],set()
        try:
            if not isinstance(self._sources,list): raise ValueError("source list required")
            out["sourceFingerprint"] = self._source_fingerprint()
        except (ValueError,TypeError) as exc:
            out["validationErrors"].append({"reason":str(exc)})
            self._result = out; return self.result()

        def error(reason,**detail): out["validationErrors"].append(dict(reason=reason,**detail))
        def gap(cid,field,p,fmt):
            q = dict(inputId=cid+":"+field,status="MISSING_PROJECT_CONSTRAINT_INPUT",blocking=True,
                     WHAT="Specify "+field+" for declared constraint "+cid,
                     WHY="This explicit project decision cannot be compiled without "+field,
                     REQUIRED_BY={"stage":"PROJECT_CONSTRAINT_INPUT","constraintId":cid},FORMAT=fmt,provenance=[p])
            out["missingConstraintInputs"].append(q); out["questions"].append(deepcopy(q))

        for src in sorted(self._sources,key=canonical):
            try:
                if not isinstance(src,dict) or set(src)-{"id","revision","category","approved","inspected","verification","basis","statements"}:
                    raise ValueError("strict structured source record required")
                sid = src.get("id")
                if not _id(sid) or sid in seen or not isinstance(src.get("revision"),str) or not src["revision"]: raise ValueError("unique source ID and revision required")
                seen.add(sid)
                if src.get("category") not in CATEGORIES-{"DERIVED_PROJECT_CONSTRAINT"} or src.get("approved") is not True or src.get("inspected") is not True or src.get("verification") != "CONFIRMED":
                    raise ValueError("explicit approved inspected confirmed source required")
                if src["category"] != "NORMATIVE_PENDING" and src.get("basis") != "NON_NORMATIVE": raise ValueError("explicit NON_NORMATIVE basis required; document type alone is insufficient")
                if not isinstance(src.get("statements"),list): raise ValueError("structured statements required; arbitrary text/expression parsing unsupported")
            except (ValueError,TypeError) as exc:
                error(str(exc)); continue
            stids = set()
            for st in sorted(src["statements"],key=canonical):
                try:
                    if not isinstance(st,dict) or not _id(st.get("id")) or st["id"] in stids: raise ValueError("unique statement ID required")
                    stids.add(st["id"])
                    p = dict(sourceId=sid,sourceRevision=src["revision"],statementId=st["id"],sourceCategory=src["category"],
                             rawEvidence=deepcopy(st),evidenceFingerprint=fingerprint(st),basis=src.get("basis"),
                             approved=True,inspected=True,verification="CONFIRMED")
                    claim = sid+":"+st["id"]
                    if src["category"] == "NORMATIVE_PENDING":
                        if set(st) != {"id","topic"} or not isinstance(st["topic"],str) or not st["topic"].strip(): raise ValueError("normative pending accepts topic only, no active values")
                        out["normativePending"].append(dict(status="NORMATIVE_PENDING",topic=st["topic"],provenance=[p])); continue
                    if st.get("kind") == "SCOPE_ENTITY":
                        if set(st) != {"id","kind","entityType","entityId"} or st["entityType"] not in ("FLOOR","SYSTEM") or not _id(st["entityId"]): raise ValueError("explicit FLOOR/SYSTEM identity required")
                        entities.append(dict(scope=st["entityType"]+":"+st["entityId"],provenance=[p])); continue
                    derived = st.get("kind") == "DIMENSION_ENVELOPE"
                    allowed = {"id","kind","constraintId","type","scope","operator","value","unit","binding","subject","supersedes"}
                    if derived: allowed = {"id","kind","constraintId","scope","binding","width","depth","unit","exactInputStatement","derivationRule","supersedes"}
                    if set(st)-allowed or st.get("kind") not in ("CONSTRAINT","DIMENSION_ENVELOPE"): raise ValueError("unknown statement fields/kind; expressions, assumptions and normative payloads forbidden")
                    cid = st.get("constraintId")
                    if not _id(cid): raise ValueError("explicit constraintId required")
                    required = ("scope","binding","width","depth","unit","exactInputStatement","derivationRule") if derived else ("type","scope","operator","value","unit","binding")
                    missing = [k for k in required if k not in st or st[k] is None or st[k] == ""]
                    if missing:
                        for field in missing: gap(cid,field,p,"explicit "+field+" for "+str(st.get("type","DIMENSION_ENVELOPE"))+"; unit="+str(st.get("unit","must be specified")))
                        continue
                    if type(st["binding"]) is not bool: raise ValueError("binding must be explicit boolean; no preference promotion")
                    if not isinstance(st["scope"],list) or not st["scope"] or any(not isinstance(s,str) for s in st["scope"]): raise ValueError("nonempty explicit scope list required")
                    refs = st.get("supersedes",[])
                    if not isinstance(refs,list) or any(not isinstance(ref,dict) or set(ref) != {"claimId","evidenceFingerprint"} or not isinstance(ref["claimId"],str) or not isinstance(ref["evidenceFingerprint"],str) for ref in refs):
                        raise ValueError("supersession requires exact claimId and evidenceFingerprint records")
                    if derived:
                        text = f"Дом максимум {st['width']} × {st['depth']} {st['unit']}"
                        if st["derivationRule"] != "EXPLICIT_DIMENSION_ENVELOPE_V0" or st["exactInputStatement"] != text or st["unit"] not in ("m","mm") or not all(_number(st[k]) and st[k] > 0 for k in ("width","depth")):
                            raise ValueError("dimension derivation requires exact approved bounded statement and positive explicit dimensions")
                        generated = [dict(constraintId=cid+"-"+axis.lower(),type="DIMENSION_LIMIT",operator="<=",value=st[key],unit=st["unit"],subject=axis) for key,axis in (("width","WIDTH"),("depth","DEPTH"))]
                    else: generated = [{k:deepcopy(st[k]) for k in ("constraintId","type","operator","value","unit","subject") if k in st}]
                    for c in generated:
                        self._validate(c)
                        c.update(status="ACTIVE" if st["binding"] else "NON_BINDING",scope=sorted(set(st["scope"])),binding=st["binding"],
                                 sourceCategory="DERIVED_PROJECT_CONSTRAINT" if derived else src["category"],provenance=[p],claimId=claim,
                                 supersedes=deepcopy(st.get("supersedes",[])))
                        if derived: c.update(derivationRule=st["derivationRule"],exactInputStatement=st["exactInputStatement"],inputEvidence=[p])
                        candidates.append(c)
                except (ValueError,TypeError,KeyError,OverflowError) as exc: error(str(exc),sourceId=sid,statementId=st.get("id") if isinstance(st,dict) else None)

        claims = {c["claimId"]:c for c in candidates}
        removed = set()
        for c in candidates:
            ss = c["supersedes"]
            if not isinstance(ss,list): error("supersedes must be explicit evidence-bound list"); continue
            if ss and c["provenance"][0]["sourceCategory"] != "APPROVED_PROJECT_DECISION": error("supersession requires approved project decision"); continue
            for ref in ss:
                old = claims.get(ref.get("claimId")) if isinstance(ref,dict) else None
                if not old or set(ref) != {"claimId","evidenceFingerprint"} or old["claimId"] == c["claimId"] or ref["evidenceFingerprint"] != old["provenance"][0]["evidenceFingerprint"]:
                    error("supersession reference missing, stale or self-referential"); continue
                removed.add(old["claimId"])
                out["supersessions"].append(dict(by=c["claimId"],**ref))
        if any(c["claimId"] in removed and c["supersedes"] for c in candidates): error("chained or cyclic supersession unsupported in v0; submit one explicit final correction")
        candidates = [c for c in candidates if c["claimId"] not in removed]
        out["scopeEntities"] = sorted(entities,key=canonical)
        spaces = {s["spaceId"] for s in fp["spaces"]}
        scopes = {"PROJECT","SITE","BUILDING"} | {"SPACE:"+s for s in spaces} | {e["scope"] for e in entities}
        scopes |= {"OBJECT:"+o["objectId"] for o in site["existingObjects"]} | {"ZONE:"+z["zone"] for z in fp["functionalZones"]}
        site_zones = {"ZONE:"+f["featureId"] for f in site["contextFeatures"] if f.get("geometry",{}).get("type") == "Polygon"}
        scopes |= site_zones
        locations = {s for s in scopes if s.startswith(("FLOOR:","ZONE:"))}
        for c in candidates:
            for s in c["scope"]:
                if s not in scopes: error("dangling scope: "+s,constraintId=c["constraintId"])
            family = FAMILY.get(c["type"],c["type"])
            if c["type"] == "FLOOR_COUNT_FIXED" and any(s not in {"PROJECT","BUILDING"} for s in c["scope"]): error("floor count applies to explicit project/building only")
            if family == "SPACE_LOCATION" and (not all(s.startswith("SPACE:") for s in c["scope"]) or any(v not in locations for v in (c["value"] if c["operator"] in ("IN","NOT_IN") else [c["value"]]))): error("explicit existing SPACE and FLOOR/ZONE location required",constraintId=c["constraintId"])
            if family == "EXISTING_OBJECT" and (not all(s.startswith("OBJECT:") for s in c["scope"]) or c["value"] != "EXISTING_OBJECT"): error("object preserve/remove requires OBJECT scope and EXISTING_OBJECT value")
            if family == "SITE_ZONE" and not all(s in site_zones for s in c["scope"]): error("site zone requires confirmed polygon context feature in Site Context")
            if c["type"] == "ACCESS_REQUIRED" and any(v not in {a["accessId"] for a in site["accessPoints"]} for v in (c["value"] if c["operator"] == "IN" else [c["value"]])): error("access reference absent in verified Site Context")
        for cid in sorted({c["constraintId"] for c in candidates}):
            same = [c for c in candidates if c["constraintId"] == cid]
            if len(same) > 1: error("duplicate constraintId; use separate IDs and explicit supersession",constraintId=cid)
        hard = [c for c in candidates if c["binding"]]
        for groupkey in sorted({(FAMILY.get(c["type"],c["type"]),c.get("subject"),s) for c in hard for s in c["scope"]},key=canonical):
            family,subject,scope = groupkey
            # PROJECT decisions apply to declared narrower targets; BUILDING to explicit floor/space targets.
            group = [c for c in hard if FAMILY.get(c["type"],c["type"]) == family and c.get("subject") == subject and
                     (scope in c["scope"] or "PROJECT" in c["scope"] or "BUILDING" in c["scope"] and scope.startswith(("FLOOR:","SPACE:")))]
            if len({c["unit"] for c in group}) > 1:
                error("mixed units in same constraint domain; explicit conversion rule required",domain=list(groupkey)); continue
            if _incompatible(group): out["conflicts"].append(dict(category="CONFLICT",domain=list(groupkey),candidates=deepcopy(group),blocking=True))
        for c in hard:
            family = FAMILY.get(c["type"],c["type"])
            if c["type"] == "FLOOR_COUNT_FIXED":
                entry = fp.get("stage0Context",{}).get("floor_count")
                if entry and not _accept(c,entry["value"]): out["conflicts"].append(dict(category="CONFLICT",constraintId=c["constraintId"],upstream="STAGE0.floor_count",inputEvidence=deepcopy(entry),blocking=True))
            for scope in c["scope"]:
                if scope.startswith("SPACE:") and family == "EQUIPMENT" and c["type"] == "EQUIPMENT_PROHIBITED":
                    space = next((s for s in fp["spaces"] if s["spaceId"] == scope[6:]),None)
                    equipment = space.get("specialEquipment") if space else None
                    if equipment and any(not _accept(c,v) for v in equipment["value"]):
                        out["conflicts"].append(dict(category="CONFLICT",constraintId=c["constraintId"],upstream="FUNCTIONAL_PROGRAM.specialEquipment",inputEvidence=deepcopy(equipment),blocking=True))
                if not scope.startswith("SPACE:") or family not in FP_FIELDS: continue
                if c["type"] == "CAPACITY_FIXED" and c.get("subject") != "SPACE_QUANTITY": continue
                if c["type"] == "AREA_LIMIT" and c.get("subject") != "REQUESTED_AREA": continue
                field = FP_FIELDS[family]
                for collection in ("userRequirements","userPreferences"):
                    for req in fp[collection]:
                        if req.get("target") != "space:"+scope[6:] or req.get("field") != field: continue
                        if field == "requestedArea":
                            upstream_constraints = [dict(type="AREA_LIMIT",unit="m2",operator="==",value=req["value"])] if "value" in req else [dict(type="AREA_LIMIT",unit="m2",operator=op,value=req[key]) for op,key in ((">=","min"),("<=","max"))]
                            contradicts = _incompatible([c]+upstream_constraints)
                        else:
                            v = req["value"]
                            if field == "preferredFloor": v = "FLOOR:"+str(v)
                            contradicts = not _accept(c,v)
                        if contradicts:
                            record = dict(constraintId=c["constraintId"],upstream="FUNCTIONAL_PROGRAM",inputEvidence=deepcopy(req),scope=scope)
                            if collection == "userRequirements": out["conflicts"].append(dict(category="CONFLICT",blocking=True,**record))
                            else: out["overrides"].append(dict(status="PREFERENCE_OVERRIDDEN",reason="explicit binding project constraint has priority",**record))
        for c in candidates:
            key = "nonBindingConstraints" if not c["binding"] else "derivedConstraints" if c["sourceCategory"] == "DERIVED_PROJECT_CONSTRAINT" else "constraints"
            out[key].append(c)
        records = candidates + entities + out["normativePending"]
        out["provenanceComplete"] = all(r["provenance"] for r in records)
        out["gateProof"] = dict(stage0Verified=True,functionalProgramVerified=True,designIntentVerified=True,siteContextVerified=True,
            allBindingConstraintsValid=not out["validationErrors"],allScopesResolved=not out["validationErrors"],
            allReferencedEntitiesExist=not out["validationErrors"],allRequiredUnitsValid=not out["validationErrors"],
            conflictsCount=len(out["conflicts"]),blockingMissingInputsCount=len(out["missingConstraintInputs"]),
            derivedConstraintsTraceable=all(c.get("derivationRule") and c.get("inputEvidence") for c in out["derivedConstraints"]),
            provenanceComplete=out["provenanceComplete"],provenanceCoverage=1.0 if out["provenanceComplete"] else 0.0,
            inventedNormativeConstraintsCount=0,unapprovedAssumptionsCount=0,deterministic=True)
        out["canProgress"] = not (out["validationErrors"] or out["conflicts"] or out["missingConstraintInputs"]) and out["provenanceComplete"]
        if out["canProgress"]: out["status"] = "VERIFIED"; out["flow"].append("PROJECT_CONSTRAINT_INPUT VERIFIED")
        for key in ("constraints","derivedConstraints","nonBindingConstraints","overrides","conflicts","missingConstraintInputs","normativePending","validationErrors","questions","supersessions"):
            out[key] = sorted(out[key],key=canonical)
        out["constraintInputFingerprint"] = fingerprint(out)
        self._result = out
        return self.result()

    @staticmethod
    def _validate(c):
        typ,op,v,unit = c.get("type"),c.get("operator"),c.get("value"),c.get("unit")
        if typ not in TYPES or op not in OPERATORS: raise ValueError("invalid constraint type/operator")
        if _numeric(c):
            if unit not in NUMERIC.get(typ,UNITS) or op not in {"==","!=","<","<=",">",">=","IN","NOT_IN"}: raise ValueError("invalid numeric operator/unit")
            vs = v if op in ("IN","NOT_IN") else [v]
            if not isinstance(vs,list) or not vs or any(not _number(x) or unit == "count" and type(x) is not int or unit == "percentage" and x > 100 for x in vs): raise ValueError("finite nonnegative numeric values; count integers, percentage 0..100 required")
            if typ in {"DIMENSION_LIMIT","AREA_LIMIT","CAPACITY_FIXED","DEMOLITION_LIMIT","CUSTOM"} and not _id(c.get("subject")): raise ValueError("explicit measurement subject required; no width/depth or gross/net assumptions")
            if typ in {"FLOOR_COUNT_FIXED","PARKING_COUNT_FIXED","CAPACITY_FIXED"} and op != "==": raise ValueError("FIXED requires ==")
        else:
            if unit != "none" and not (typ == "CUSTOM" and unit in UNITS): raise ValueError("categorical unit must be explicit none")
            values = v if op in ("IN","NOT_IN") or typ == "PHASING_REQUIRED" else [v]
            if not isinstance(values,list) or not values or any(not isinstance(x,str) or not x.strip() for x in values): raise ValueError("explicit categorical labels required; no executable expressions")
            if typ == "PHASING_REQUIRED" and (not isinstance(v,list) or len(v) != len(set(v))): raise ValueError("explicit ordered unique phase labels required")
            if op in {"<","<=",">",">="}: raise ValueError("ordering of categorical labels unsupported")
            if typ.endswith("_PROHIBITED") or typ == "SITE_ZONE_PROHIBITED":
                if op not in {"PROHIBIT","!=","NOT_IN"}: raise ValueError("prohibited type requires prohibition operator")
            if typ.endswith("_REQUIRED") and op not in {"REQUIRE","==","IN"}: raise ValueError("required type requires requirement operator")
            if typ == "EXISTING_OBJECT_PRESERVE" and op != "PRESERVE": raise ValueError("preserve type requires PRESERVE")
            if typ in {"EXISTING_OBJECT_PRESERVE","EXISTING_OBJECT_REMOVE_REQUIRED","SITE_ZONE_PROHIBITED","SITE_ZONE_REQUIRED"} and (not isinstance(v,str) or v != FAMILY[typ]): raise ValueError("explicit EXISTING_OBJECT or SITE_ZONE subject value required")
            if typ == "CUSTOM" and not _id(c.get("subject")): raise ValueError("CUSTOM requires explicit nonnormative subject")


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    for opt in ("stage0-registry","stage0-sources","functional-brief","intent","site-sources","site-requirements","constraint-sources","output"):
        p.add_argument("--"+opt,type=Path,required=True)
    p.add_argument("--answers",type=Path)
    args = p.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    s0 = Stage0(load(args.stage0_registry),load(args.stage0_sources)); s0.audit()
    fp = FunctionalProgram(s0,load(args.functional_brief)); fp.audit()
    di = DesignIntent(s0,fp,load(args.intent)); di.audit()
    site = SiteContext(s0,load(args.site_sources),load(args.site_requirements)); site.audit()
    model = ProjectConstraintInput(s0,fp,di,site,load(args.constraint_sources)); out = model.audit()
    if args.answers:
        for answer in load(args.answers): model.update_source(answer)
        out = model.audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return 0 if out["canProgress"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
