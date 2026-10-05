"""SITE / CONTEXT MODEL v0: confirmed physical evidence, independently of norms."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from design_stage0 import Stage0, fingerprint, _derive
from functional_program import canonical

FLOW = ["REQUIRE VERIFIED STAGE 0", "COLLECT SITE SOURCES", "NORMALIZE SITE GEOMETRY",
        "NORMALIZE ORIENTATION", "MAP ACCESS", "MAP EXISTING OBJECTS", "MAP CONTEXT FEATURES",
        "DERIVE SAFE SITE METRICS", "DETECT CONFLICTS / GAPS", "RE-AUDIT"]
ACCESS_TYPES = {"VEHICLE_ACCESS", "PEDESTRIAN_ACCESS", "SERVICE_ACCESS", "EMERGENCY_ACCESS", "EXISTING_ENTRANCE", "POSSIBLE_ACCESS"}
OBJECT_TYPES = {"BUILDING", "STRUCTURE", "ROAD", "PATH", "PARKING", "TREE", "WATER", "UTILITY", "FENCE", "TERRAIN_FEATURE", "OTHER"}
FEATURE_TYPES = {"NEIGHBOURING_BUILDING", "STREET_ROAD", "PEDESTRIAN_ROUTE", "SIGNIFICANT_VIEW", "UNDESIRABLE_VIEW",
                 "NOISE_SOURCE", "LANDSCAPE_FEATURE", "WATER", "MAJOR_VEGETATION", "SITE_ENTRANCE", "ADJACENT_FUNCTIONAL_AREA"}
SOURCE_KINDS = {"PROJECT_FILE", "DRAWING", "COORDINATES", "USER_SITE_OBSERVATION", "APPROVED_DERIVED_GEOMETRY", "USER_CORRECTION"}
CORE = {"siteId", "boundary", "coordinateSystem"}
REQUIREMENTS = CORE | {"orientation", "access", "terrain"} | {"access:" + x for x in ACCESS_TYPES} | {"context:" + x for x in FEATURE_TYPES}


def _id(value):
    return isinstance(value,str) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*",value))


def _number(value):
    return type(value) in (int,float) and math.isfinite(value)


def _point(value):
    if not isinstance(value,list) or len(value) != 2 or not all(_number(x) for x in value):
        raise ValueError("finite explicit XY coordinates required")
    return [float(x) for x in value]


def _geometry(raw):
    if not isinstance(raw,dict) or set(raw) != {"type","coordinates","coordinateSystemId","unit"} or not _id(raw["coordinateSystemId"]) or raw["unit"] not in ("m","mm"):
        raise ValueError("geometry requires type, coordinates, explicit Cartesian CRS ID and m/mm unit")
    kind, coords = raw["type"],raw["coordinates"]
    if kind == "Point":
        coords = _point(coords)
    elif kind == "LineString":
        if not isinstance(coords,list) or len(coords) < 2:
            raise ValueError("line requires at least two explicit points")
        coords = [_point(p) for p in coords]
        if any(a == b for a,b in zip(coords,coords[1:])):
            raise ValueError("zero-length line segment")
    elif kind == "Polygon":
        if not isinstance(coords,list) or len(coords) != 1:
            raise ValueError("v0 supports one explicit polygon ring, no inferred holes")
        ring = [_point(p) for p in coords[0]]
        # Translate for numerical stability; reuse the existing approved validator.
        if not ring:
            raise ValueError("empty polygon")
        shifted = [[p[0]-ring[0][0],p[1]-ring[0][1]] for p in ring]
        _derive("closed_polygon_area",[shifted])
        for a,b,c in zip(ring[-2:-1] + ring[:-1],ring[:-1],ring[1:]):
            u,v = [a[k]-b[k] for k in (0,1)],[c[k]-b[k] for k in (0,1)]
            if u[0]*v[1]-u[1]*v[0] == 0 and u[0]*v[0]+u[1]*v[1] > 0:
                raise ValueError("overlapping adjacent polygon edges")
        # Canonical ring, without changing any physical coordinate or inventing closure.
        vertices = ring[:-1]
        choices = []
        for v in (vertices,list(reversed(vertices))):
            anchor = min(range(len(v)),key=lambda i:v[i])
            choices.append(v[anchor:] + v[:anchor])
        normalized = min(choices)
        coords = [normalized + [normalized[0]]]
    else:
        raise ValueError("unsupported physical geometry type")
    return dict(deepcopy(raw),coordinates=coords)


def _line_length(points):
    return sum(math.dist(a,b) for a,b in zip(points,points[1:]))


class SiteContext:
    """Audited physical site artifact and gate; upstream artifacts are read-only."""
    def __init__(self,stage0,sources,requirements):
        if not isinstance(stage0,Stage0):
            raise TypeError("live Stage0 session required")
        self._stage0,self._sources,self._requirements = stage0,deepcopy(sources),deepcopy(requirements)
        self._result = None
        self._validate_requirements()

    def _validate_requirements(self):
        r = self._requirements
        if not r.get("id") or not r.get("revision") or r.get("approved") is not True or not r.get("downstreamStage") or not isinstance(r.get("requiredInputs"),list):
            raise ValueError("explicit approved versioned downstream input requirements required")
        if any(x not in REQUIREMENTS for x in r["requiredInputs"]) or not CORE <= set(r["requiredInputs"]):
            raise ValueError("site identity, boundary and CRS are core; unknown requirements forbidden")

    def _refresh(self):
        if self._result and self._result.get("dependencyVerified"):
            s0 = self._stage0.result()
            if not s0 or s0["status"] != "VERIFIED" or s0["contextFingerprint"] != self._result["stage0Fingerprint"]:
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="STAGE0_CHANGED_OR_NOT_VERIFIED")

    def result(self):
        self._refresh()
        return deepcopy(self._result)

    def update_source(self,source):
        new = [s for s in self._sources if s.get("id") != source.get("id")] + [deepcopy(source)]
        if fingerprint(sorted(new,key=canonical)) != fingerprint(sorted(self._sources,key=canonical)):
            self._sources = new
            if self._result:
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="SITE_SOURCE_CHANGED")

    def update_requirements(self,requirements):
        candidate = SiteContext(self._stage0,self._sources,requirements)
        if fingerprint(candidate._requirements) != fingerprint(self._requirements):
            self._requirements = candidate._requirements
            if self._result:
                self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="DOWNSTREAM_REQUIREMENTS_CHANGED")

    def require_verified(self):
        self._refresh(); self._stage0.require_verified()
        if not self._result or self._result["status"] != "VERIFIED" or not self._result["canProgress"] or self._result["contextFingerprint"] != fingerprint([self._requirements,sorted(self._sources,key=canonical)]):
            raise RuntimeError("Site Context progression blocked")
        return deepcopy(self._result["gateProof"])

    def audit(self):
        self._refresh()
        bound = bool(self._result and self._result.get("dependencyVerified"))
        s0 = self._stage0.result()
        out = {"stage":"SITE_CONTEXT","schemaVersion":0,"status":"BLOCKED","canProgress":False,"dependencyVerified":False,
               "stage0Fingerprint":s0["contextFingerprint"] if s0 else None,"site":{},"boundary":{},"orientation":{},
               "accessPoints":[],"existingObjects":[],"contextFeatures":[],"terrain":{},"derivedMetrics":[],
               "userSitePreferences":[],"normativeConstraintsPending":[],"missingSiteData":[],"conflicts":[],
               "questions":[],"provenanceComplete":False,"validationErrors":[]}
        try:
            self._stage0.require_verified()
        except RuntimeError:
            out.update(status="INVALIDATED" if bound else "BLOCKED",dependencyVerified=bound,blockers=["STAGE_0_NOT_VERIFIED"])
            self._result = out; return self.result()
        out.update(dependencyVerified=True,flow=list(FLOW))
        try:
            out["contextFingerprint"] = fingerprint([self._requirements,sorted(self._sources,key=canonical)])
        except (ValueError,TypeError):
            out["validationErrors"] = [{"reason":"finite structured source records required"}]
            self._result = out; return self.result()
        candidates,requests = [],[]
        errors,conflicts = out["validationErrors"],out["conflicts"]
        if not isinstance(self._sources,list) or any(not isinstance(s,dict) for s in self._sources):
            out["validationErrors"].append({"reason":"source list of objects required"})
            self._result = out; return self.result()
        seen = set()
        for source in sorted(self._sources,key=canonical):
            sid = source.get("id")
            if not _id(sid) or sid in seen or source.get("kind") not in SOURCE_KINDS or not source.get("revision") or source.get("inspected") is not True or source.get("verification") != "CONFIRMED":
                errors.append({"sourceId":sid,"reason":"unique inspected confirmed versioned site source required"}); continue
            seen.add(sid)
            if set(source) - {"id","kind","revision","inspected","verification","statements","approved","derivationRule","inputEvidence"} or not isinstance(source.get("statements"),list) or any(not isinstance(s,dict) for s in source.get("statements",[])):
                errors.append({"sourceId":sid,"reason":"unsupported source fields/statements"}); continue
            if source["kind"] == "APPROVED_DERIVED_GEOMETRY" and (source.get("approved") is not True or not source.get("derivationRule") or not isinstance(source.get("inputEvidence"),list) or not source["inputEvidence"] or
                    any(not isinstance(e,dict) or not e.get("sourceId") or not e.get("revision") or e.get("verification") != "CONFIRMED" for e in source["inputEvidence"])):
                errors.append({"sourceId":sid,"reason":"derived geometry requires approval, method and confirmed input evidence"}); continue
            seen_st = set()
            for st in sorted(source["statements"],key=canonical):
                stid = st.get("id")
                if not _id(stid) or stid in seen_st:
                    errors.append({"sourceId":sid,"reason":"stable unique statement IDs required"}); continue
                seen_st.add(stid)
                p = {"sourceId":sid,"sourceKind":source["kind"],"revision":source["revision"],"statementId":stid,
                     "verification":"CONFIRMED","method":"EXPLICIT_SITE_RECORD","supersedes":st.get("supersedes",[]),"rawEvidence":deepcopy(st)}
                if source["kind"] == "APPROVED_DERIVED_GEOMETRY":
                    p.update(derivationRule=source["derivationRule"],inputEvidence=deepcopy(source["inputEvidence"]))
                kind = st.get("kind")
                allowed = {"SITE":{"siteId","label"},"COORDINATE_SYSTEM":{"metadata"},"BOUNDARY":{"geometry"},
                    "ORIENTATION":{"northVector","coordinateSystemId","coordinateOrientation"},
                    "ACCESS":{"accessId","type","geometry","description"},"OBJECT":{"objectId","type","geometry","description"},
                    "CONTEXT":{"featureId","type","geometry","description"},"PREFERENCE":{"preferenceId","topic","text","scope"},
                    "ELEVATION_POINT":{"pointId","geometry","elevation","elevationUnit","verticalDatum"},
                    "CONTOUR":{"contourId","geometry","elevation","elevationUnit","verticalDatum"},
                    "MEASUREMENT":{"measurementId","operation","refs"},"NORMATIVE_PENDING":{"topic"}}.get(kind)
                try:
                    if allowed is None or set(st) - allowed - {"id","kind","supersedes"}:
                        raise ValueError("unsupported fields; legal inference, norms and planning geometry forbidden")
                    if not isinstance(p["supersedes"],list) or any(not isinstance(x,str) for x in p["supersedes"]):
                        raise ValueError("explicit superseded source:statement references required")
                    value = {k:deepcopy(v) for k,v in st.items() if k not in ("id","kind","supersedes")}
                    key = kind
                    category = "SITE_FACT"
                    if "geometry" in value:
                        value["geometry"] = _geometry(value["geometry"])
                    if kind == "SITE":
                        if not _id(st.get("siteId")): raise ValueError("stable explicit siteId required")
                    elif kind == "COORDINATE_SYSTEM":
                        cs = st["metadata"]
                        if set(cs) - {"id","kind","unit","axisOrder","orientation","datum"} or not _id(cs.get("id")) or cs.get("kind") not in ("LOCAL_CARTESIAN","PROJECTED_CARTESIAN") or cs.get("unit") not in ("m","mm") or cs.get("axisOrder") != "XY" or not isinstance(cs.get("orientation"),str) or not cs["orientation"]:
                            raise ValueError("explicit planar metric XY coordinate metadata required; geographic degrees unsupported")
                    elif kind == "BOUNDARY":
                        if value["geometry"]["type"] != "Polygon": raise ValueError("confirmed closed polygon boundary required")
                    elif kind == "ORIENTATION":
                        vec = _point(st["northVector"])
                        length = math.hypot(*vec)
                        if not length or not _id(st.get("coordinateSystemId")) or not isinstance(st.get("coordinateOrientation"),str) or not st["coordinateOrientation"]:
                            raise ValueError("explicit nonzero north vector and coordinate orientation metadata required")
                        value["northVector"] = [n/length for n in vec]
                    elif kind in ("ACCESS","OBJECT","CONTEXT"):
                        id_field,types = {"ACCESS":("accessId",ACCESS_TYPES),"OBJECT":("objectId",OBJECT_TYPES),"CONTEXT":("featureId",FEATURE_TYPES)}[kind]
                        if not _id(st.get(id_field)) or st.get("type") not in types:
                            raise ValueError("explicit object/access/context identity and type required")
                        if kind != "CONTEXT" and "geometry" not in value or kind == "CONTEXT" and not value.get("description") and "geometry" not in value:
                            raise ValueError("confirmed geometry or explicit context observation required")
                        if kind == "ACCESS" and value["geometry"]["type"] not in ("Point","LineString"):
                            raise ValueError("access requires confirmed point/entry line")
                        key += ":" + st[id_field]
                        if kind == "OBJECT": value["status"] = "EXISTING"
                        if kind == "ACCESS": value["normativeApproval"] = {"status":"NORMATIVE_CONSTRAINT_PENDING","value":None}
                    elif kind in ("ELEVATION_POINT","CONTOUR"):
                        id_field = "pointId" if kind == "ELEVATION_POINT" else "contourId"
                        if not _id(st.get(id_field)) or not _number(st.get("elevation")) or st.get("elevationUnit") not in ("m","mm") or not isinstance(st.get("verticalDatum"),str) or not st["verticalDatum"] or value["geometry"]["type"] != ("Point" if kind == "ELEVATION_POINT" else "LineString"):
                            raise ValueError("confirmed elevation, vertical datum and point/contour geometry required")
                        key += ":" + st[id_field]
                    elif kind == "PREFERENCE":
                        if not _id(st.get("preferenceId")) or not st.get("topic") or not isinstance(st.get("text"),str) or not st["text"] or not isinstance(st.get("scope"),list) or not st["scope"]:
                            raise ValueError("explicit site preference text, identity and scope required")
                        category = "USER_SITE_PREFERENCE"; key += ":" + st["preferenceId"]
                    elif kind == "MEASUREMENT":
                        if not _id(st.get("measurementId")) or st.get("operation") not in ("DISTANCE","LINE_ORIENTATION","FRONTAGE_LENGTH","SLOPE_DIRECTION") or not isinstance(st.get("refs"),list) or not st["refs"] or any(not isinstance(x,str) for x in st["refs"]):
                            raise ValueError("explicit approved measurement and evidence refs required")
                        requests.append({"value":value,"provenance":[p],"claimId":sid+":"+stid}); continue
                    elif kind == "NORMATIVE_PENDING":
                        if not isinstance(st.get("topic"),str) or not st["topic"]: raise ValueError("pending nonnumerical topic required")
                        category = "NORMATIVE_CONSTRAINT_PENDING"; key += ":" + st["topic"]
                    candidates.append({"key":key,"value":value,"category":category,"provenance":[p],"claimId":sid+":"+stid})
                except (ValueError,KeyError,TypeError,OverflowError) as exc:
                    errors.append({"sourceId":sid,"statementId":stid,"reason":str(exc)})
        superseded = {x for c in candidates+requests for p in c["provenance"] if p["sourceKind"] == "USER_CORRECTION" for x in p["supersedes"]}
        candidates = [c for c in candidates if c["claimId"] not in superseded]
        requests = [c for c in requests if c["claimId"] not in superseded]
        records = {}
        for key in sorted({c["key"] for c in candidates}):
            choices = [c for c in candidates if c["key"] == key]
            if len({canonical(c["value"]) for c in choices}) != 1:
                conflicts.append({"inputId":key,"category":"CONFLICT","candidates":choices}); continue
            records[key] = {**deepcopy(choices[0]["value"]),"category":choices[0]["category"],"verificationStatus":"CONFIRMED",
                            "source":sorted({p["sourceId"] for c in choices for p in c["provenance"]}),
                            "provenance":[p for c in choices for p in c["provenance"]]}
        cs = records.get("COORDINATE_SYSTEM",{}).get("metadata")
        for key,rec in records.items():
            geom = rec.get("geometry")
            if geom and (not cs or geom["coordinateSystemId"] != cs["id"] or geom["unit"] != cs["unit"]):
                errors.append({"inputId":key,"reason":"geometry CRS/unit does not match confirmed coordinate system; no implicit conversion"})
            if key == "ORIENTATION" and (not cs or rec["coordinateSystemId"] != cs["id"] or rec["coordinateOrientation"] != cs["orientation"]):
                conflicts.append({"inputId":key,"category":"CONFLICT","reason":"orientation differs from confirmed coordinate metadata","provenance":rec["provenance"]})
        out["site"] = records.get("SITE",{})
        out["site"]["legalBoundary"] = {"category":"MISSING_SITE_DATA","status":"MISSING_SITE_DATA","value":None}
        out["site"]["ownership"] = {"category":"MISSING_SITE_DATA","status":"MISSING_SITE_DATA","value":None}
        out["boundary"] = records.get("BOUNDARY",{})
        if cs: out["boundary"]["coordinateSystem"] = deepcopy(records["COORDINATE_SYSTEM"])
        out["orientation"] = records.get("ORIENTATION",{"status":"MISSING_SITE_DATA","northVector":None})
        for key,rec in records.items():
            for prefix,field in (("ACCESS:","accessPoints"),("OBJECT:","existingObjects"),("CONTEXT:","contextFeatures"),
                                 ("PREFERENCE:","userSitePreferences"),("NORMATIVE_PENDING:","normativeConstraintsPending")):
                if key.startswith(prefix): out[field].append(deepcopy(rec))
        elevations = [rec for key,rec in records.items() if key.startswith(("ELEVATION_POINT:","CONTOUR:"))]
        datums = {(rec["verticalDatum"],rec["elevationUnit"]) for rec in elevations}
        if len(datums) > 1:
            conflicts.append({"inputId":"terrain","category":"CONFLICT","reason":"incompatible vertical datums","candidates":elevations})
        out["terrain"] = {"status":"CONFIRMED_SAMPLES" if elevations else "TERRAIN_DATA_MISSING",
            "category":"SITE_FACT" if elevations else "MISSING_SITE_DATA","knownElevationPoints":[r for r in elevations if "pointId" in r],
            "contours":[r for r in elevations if "contourId" in r],"minElevation":None,"maxElevation":None,"elevationRange":None,
            "slopeDirection":None,"slopeStatus":"NOT_DERIVED","extent":"OBSERVED_SAMPLES_ONLY" if elevations else "UNKNOWN",
            "provenance":[p for r in elevations for p in r["provenance"]]}

        def metric(id,rule,unit,result,evidence,scope="CONFIRMED_GEOMETRY_ONLY"):
            if any(m["metricId"] == id for m in out["derivedMetrics"]): raise ValueError("duplicate measurement identity")
            m = {"metricId":id,"category":"DERIVED_SITE_METRIC","derivationRule":rule,"unit":unit,"result":result,
                 "scope":scope,"inputEvidence":deepcopy(evidence),"provenance":[{"method":rule,"verification":"TRACEABLE","inputEvidence":deepcopy(evidence)}]}
            # Reject arithmetic overflow/nonfinite results before a metric can enter the gate.
            fingerprint(m); out["derivedMetrics"].append(m)
            return m

        if not errors and not conflicts:
            try:
                boundary = out["boundary"].get("geometry")
                if boundary:
                    ring,unit = boundary["coordinates"][0],boundary["unit"]
                    origin = ring[0]; pts = [[p[0]-origin[0],p[1]-origin[1]] for p in ring]
                    cross = [a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:])]; signed = sum(cross)/2
                    evidence = out["boundary"]["provenance"] + records["COORDINATE_SYSTEM"]["provenance"]
                    metric("site-area","CLOSED_POLYGON_SHOELACE_V0",unit+"2",abs(signed),evidence)
                    metric("site-perimeter","CLOSED_POLYGON_EDGE_LENGTHS_V0",unit,_line_length(ring),evidence)
                    metric("site-bbox","CONFIRMED_POLYGON_EXTENTS_V0",unit,{"min":[min(p[k] for p in ring) for k in (0,1)],"max":[max(p[k] for p in ring) for k in (0,1)]},evidence)
                    centroid = [origin[k]+sum((a[k]+b[k])*c for a,b,c in zip(pts,pts[1:],cross))/(6*signed) for k in (0,1)]
                    metric("site-centroid","SIGNED_POLYGON_CENTROID_V0",unit,centroid,evidence)
                if elevations:
                    low,high = min(r["elevation"] for r in elevations),max(r["elevation"] for r in elevations)
                    out["terrain"].update(minElevation=low,maxElevation=high,elevationRange=high-low)
                    out["terrain"].update(elevationUnit=elevations[0]["elevationUnit"],verticalDatum=elevations[0]["verticalDatum"])
                    metric("elevation-min","CONFIRMED_SAMPLE_ELEVATION_MIN_V0",elevations[0]["elevationUnit"],low,out["terrain"]["provenance"],"OBSERVED_SAMPLES_ONLY")
                    metric("elevation-max","CONFIRMED_SAMPLE_ELEVATION_MAX_V0",elevations[0]["elevationUnit"],high,out["terrain"]["provenance"],"OBSERVED_SAMPLES_ONLY")
                    metric("elevation-range","CONFIRMED_ELEVATION_RANGE_V0",elevations[0]["elevationUnit"],high-low,out["terrain"]["provenance"],"OBSERVED_SAMPLES_ONLY")
                for request in requests:
                    spec = request["value"]; refs = [records.get(ref) for ref in spec["refs"]]
                    if any(r is None or "geometry" not in r for r in refs): raise ValueError("measurement evidence reference is absent/conflicting")
                    evidence = request["provenance"] + [p for r in refs for p in r["provenance"]]
                    op = spec["operation"]; unit = cs["unit"]
                    if op in ("DISTANCE","SLOPE_DIRECTION"):
                        if len(refs) != 2 or any(r["geometry"]["type"] != "Point" for r in refs):
                            raise ValueError("v0 distance/slope requires two confirmed points; no bbox/object proxy")
                        a,b = [r["geometry"]["coordinates"] for r in refs]
                        if op == "DISTANCE":
                            result,rule,scope = math.dist(a,b),"CONFIRMED_POINT_DISTANCE_V0","CONFIRMED_POINTS_ONLY"
                        else:
                            if any("elevation" not in r for r in refs) or a == b or refs[0]["elevation"] == refs[1]["elevation"]:
                                raise ValueError("slope direction needs distinct confirmed points at unequal confirmed elevations")
                            if refs[0]["elevation"] < refs[1]["elevation"]: a,b = b,a
                            result = math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])) % 360
                            rule,unit,scope = "CONFIRMED_DESCENDING_SEGMENT_V0","deg","CONFIRMED_SEGMENT_ONLY_NOT_GLOBAL_TERRAIN"
                            out["terrain"].update(slopeDirection=result,slopeStatus=scope)
                    else:
                        if len(refs) != 1 or refs[0]["geometry"]["type"] != "LineString": raise ValueError("explicit confirmed frontage/oriented line required")
                        points = refs[0]["geometry"]["coordinates"]
                        if op == "FRONTAGE_LENGTH": result,rule = _line_length(points),"EXPLICIT_FRONTAGE_LINE_LENGTH_V0"
                        else:
                            if len(points) != 2: raise ValueError("orientation requires one explicitly directed segment")
                            a,b = points; result = math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])) % 360
                            rule,unit = "CONFIRMED_DIRECTED_LINE_ANGLE_V0","deg"
                        scope = "EXPLICITLY_IDENTIFIED_LINE_ONLY"
                    metric(spec["measurementId"],rule,unit,result,evidence,scope)
            except (ValueError,ZeroDivisionError,OverflowError) as exc:
                errors.append({"reason":"derivation blocked: " + str(exc)})

        required = set(self._requirements["requiredInputs"])
        def available(key):
            if key == "siteId": return "siteId" in out["site"]
            if key == "boundary": return bool(out["boundary"].get("geometry"))
            if key == "coordinateSystem": return bool(cs)
            if key == "orientation": return "provenance" in out["orientation"]
            if key == "access": return bool(out["accessPoints"])
            if key == "terrain": return bool(elevations) and len(datums) == 1
            field,type = key.split(":",1)
            return any(r["type"] == type for r in out["accessPoints" if field == "access" else "contextFeatures"])
        missing_keys = {k for k in required if not available(k)}
        if not elevations: missing_keys.add("terrain")
        if not available("orientation"): missing_keys.add("orientation")
        formats = {"siteId":"stable siteId and confirmed source","boundary":"explicit closed Polygon ring, CRS ID, m/mm",
                   "coordinateSystem":"planar Cartesian CRS metadata, XY, unit and orientation",
                   "orientation":"confirmed northVector in that CRS and coordinate orientation metadata",
                   "terrain":"confirmed XY elevation points/contours, units and vertical datum","access":"confirmed access point/entry line and access type"}
        priority = {"siteId":0,"coordinateSystem":0,"boundary":1,"orientation":2,"terrain":3}
        reasons = {"siteId":"Tie the physical evidence to one identified site", "coordinateSystem":"Prevent mixing coordinate frames, axes or units",
                   "boundary":"Establish confirmed physical extent for site metrics", "orientation":"Relate the site's coordinate frame to confirmed north",
                   "terrain":"The declared downstream task requires observed relief", "access":"Identify the physical access requested by the downstream task"}
        for key in sorted(missing_keys,key=lambda k:(priority.get(k,2),k)):
            out["missingSiteData"].append({"inputId":key,"category":"MISSING_SITE_DATA","blocking":key in required,
                "priority":priority.get(key,2),"WHAT":"Provide confirmed " + key,"WHY":reasons.get(key,"Resolve the explicitly required physical access/context feature") if key in required else "Not observed; no physical condition is assumed",
                "REQUIRED_BY":[self._requirements["downstreamStage"]] if key in required else [],
                "FORMAT":formats.get(key,"confirmed typed access/context record with geometry or explicit observation"),
                "provenance":{"requirementSource":{"id":self._requirements["id"],"revision":self._requirements["revision"]},"inspectedSources":sorted(seen)}})
        blocking = [g for g in out["missingSiteData"] if g["blocking"]]
        out["questions"] = [deepcopy(g) for g in blocking if g["priority"] == blocking[0]["priority"]] if blocking and not errors and not conflicts else []
        if conflicts and not errors:
            out["questions"] = [{"inputId":"conflict:"+fingerprint(c)[:16],"WHAT":"Resolve conflicting " + c["inputId"],
                "WHY":"Physical site evidence disagrees; no source may be silently selected","REQUIRED_BY":[self._requirements["downstreamStage"]],
                "FORMAT":"USER_CORRECTION with explicit superseded source:statement IDs","provenance":deepcopy(c)} for c in conflicts][:1]
        confirmed = list(records.values()); covered = sum(bool(r["provenance"]) for r in confirmed)
        coverage = covered/len(confirmed) if confirmed else 1.0
        traceable = all(m["inputEvidence"] and m["provenance"] and m["unit"] and m["derivationRule"] for m in out["derivedMetrics"])
        gate = not errors and not conflicts and not blocking and coverage == 1.0 and traceable
        out.update(status="VERIFIED" if gate else "BLOCKED" if errors or conflicts else "WAITING_FOR_USER_DATA",canProgress=gate,provenanceComplete=coverage == 1.0)
        out["gateProof"] = {"stage0Verified":True,"requiredSiteIdentityResolved":available("siteId"),"blockingSiteGeometryResolved":available("boundary") and bool(cs),
            "blockingConflictsCount":len(conflicts),"missingBlockingSiteDataCount":len(blocking),"requiredAccessContextResolved":all(available(k) for k in required if k.startswith(("access","context:"))),
            "allDerivedMetricsTraceable":traceable,"provenanceCoverage":coverage,"provenanceComplete":coverage == 1.0,
            "inventedLegalNormativeConstraintsCount":0,"unapprovedAssumptionsCount":0,"validationErrorsCount":len(errors),"deterministic":True}
        if gate: out["flow"].append("SITE_CONTEXT VERIFIED")
        out["siteContextFingerprint"] = fingerprint(out)
        self._result = out; return self.result()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("stage0-registry","stage0-sources","site-sources","requirements","output"):
        parser.add_argument("--"+option,type=Path,required=True)
    parser.add_argument("--answers",type=Path)
    args = parser.parse_args(); load = lambda p:json.loads(p.read_text(encoding="utf-8"))
    s0 = Stage0(load(args.stage0_registry),load(args.stage0_sources)); s0.audit()
    model = SiteContext(s0,load(args.site_sources),load(args.requirements)); out = model.audit()
    if args.answers:
        for answer in load(args.answers): model.update_source(answer)
        out = model.audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return 0 if out["canProgress"] else 2


if __name__ == "__main__": raise SystemExit(main())
