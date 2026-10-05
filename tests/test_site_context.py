from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from site_context import SiteContext, ACCESS_TYPES, OBJECT_TYPES, FEATURE_TYPES
from tests.test_functional_program import stage0
from tests.test_design_stage0 import source as intake_source, registry, complete
from tests.test_design_intent import dependencies, engine as intent_engine


def geometry(type="Point",coordinates=None,unit="m",crs="site-grid"):
    if coordinates is None: coordinates = [0,5]
    return dict(type=type,coordinates=coordinates,unit=unit,coordinateSystemId=crs)


def source(statements=None,id="survey",kind="COORDINATES"):
    return dict(id=id,kind=kind,revision="v1",inspected=True,verification="CONFIRMED",statements=statements or [])


def policy(*extra):
    return dict(id="site-inputs",revision="v1",approved=True,downstreamStage="CURRENT_SITE_INTAKE",
                requiredInputs=["siteId","coordinateSystem","boundary","orientation","access:VEHICLE_ACCESS",*extra])


def site_source():
    return source([
        dict(id="identity",kind="SITE",siteId="test-site",label="synthetic acceptance site"),
        dict(id="crs",kind="COORDINATE_SYSTEM",metadata=dict(id="site-grid",kind="LOCAL_CARTESIAN",unit="m",axisOrder="XY",orientation="survey-grid",datum="survey-frame")),
        dict(id="boundary",kind="BOUNDARY",geometry=geometry("Polygon",[[[0,0],[30,0],[30,20],[0,20],[0,0]]])),
        dict(id="north",kind="ORIENTATION",northVector=[0,1],coordinateSystemId="site-grid",coordinateOrientation="survey-grid"),
        dict(id="vehicle",kind="ACCESS",accessId="driveway",type="VEHICLE_ACCESS",geometry=geometry(),description="confirmed entry"),
        dict(id="building",kind="OBJECT",objectId="existing-building",type="BUILDING",geometry=geometry("Polygon",[[[5,5],[10,5],[10,10],[5,10],[5,5]]])),
        dict(id="noise",kind="CONTEXT",featureId="road-noise",type="NOISE_SOURCE",description="confirmed road along western boundary"),
        dict(id="view",kind="PREFERENCE",preferenceId="view",topic="VIEW",text="user prefers a view towards the garden",scope=["SITE"]),
    ])


def elevations():
    return [dict(id="e"+str(i),kind="ELEVATION_POINT",pointId="e"+str(i),geometry=geometry(coordinates=p),elevation=z,
                 elevationUnit="m",verticalDatum="survey-benchmark") for i,(p,z) in enumerate((([0,0],100),([30,0],102),([0,20],101)),1)]


def engine(sources=None,s0=None,requirements=None):
    return SiteContext(s0 or stage0(),[site_source()] if sources is None else sources,requirements or policy())


def metric(result,id): return next(m for m in result["derivedMetrics"] if m["metricId"] == id)


class RequiredScenarios(unittest.TestCase):
    def test_01_stage0_not_verified_blocked(self):
        e = engine(s0=stage0(False)); r = e.audit()
        self.assertEqual(r["status"],"BLOCKED")
        self.assertEqual(r["derivedMetrics"],[])
        with self.assertRaises(RuntimeError): e.require_verified()

    def test_02_explicit_boundary_retained(self):
        r = engine().audit()
        self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(r["site"]["siteId"],"test-site")
        self.assertEqual(r["boundary"]["verificationStatus"],"CONFIRMED")
        self.assertEqual(r["boundary"]["provenance"][0]["rawEvidence"]["geometry"],site_source()["statements"][2]["geometry"])
        self.assertEqual(r["boundary"]["coordinateSystem"]["metadata"]["id"],"site-grid")

    def test_03_closed_polygon_derived_area(self):
        r = engine().audit(); m = metric(r,"site-area")
        self.assertEqual(m["result"],600)
        self.assertEqual(m["category"],"DERIVED_SITE_METRIC")
        self.assertEqual(m["unit"],"m2")
        self.assertTrue(m["derivationRule"])

    def test_04_open_invalid_polygon_blocked(self):
        for ring in ([[0,0],[30,0],[30,20],[0,20]],[[0,0],[30,20],[30,0],[0,20],[0,0]]):
            s = site_source(); s["statements"][2]["geometry"]["coordinates"] = [ring]
            e = engine([s]); r = e.audit()
            self.assertEqual(r["status"],"BLOCKED")
            with self.assertRaises(RuntimeError): e.require_verified()

    def test_05_orientation_retained_with_provenance(self):
        r = engine().audit()
        self.assertEqual(r["orientation"]["northVector"],[0,1])
        self.assertEqual(r["orientation"]["provenance"][0]["statementId"],"north")

    def test_06_no_guessed_north(self):
        s = site_source(); s["statements"] = [st for st in s["statements"] if st["kind"] != "ORIENTATION"]
        r = engine([s]).audit()
        self.assertEqual(r["orientation"]["northVector"],None)
        self.assertEqual([q["inputId"] for q in r["questions"]],["orientation"])

    def test_07_explicit_vehicle_access_retained(self):
        r = engine().audit(); a = r["accessPoints"][0]
        self.assertEqual(a["type"],"VEHICLE_ACCESS")
        self.assertEqual(a["accessId"],"driveway")
        self.assertTrue(a["provenance"])

    def test_08_possible_access_not_normative_approval(self):
        s = site_source(); s["statements"][4]["type"] = "POSSIBLE_ACCESS"
        p = policy(); p["requiredInputs"].remove("access:VEHICLE_ACCESS"); p["requiredInputs"].append("access")
        r = engine([s],requirements=p).audit()
        self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(r["accessPoints"][0]["normativeApproval"],{"status":"NORMATIVE_CONSTRAINT_PENDING","value":None})
        self.assertEqual(r["accessPoints"][0]["type"],"POSSIBLE_ACCESS")

    def test_09_existing_building_retained(self):
        r = engine().audit(); obj = r["existingObjects"][0]
        self.assertEqual(obj["type"],"BUILDING"); self.assertEqual(obj["status"],"EXISTING")
        self.assertTrue(obj["geometry"]); self.assertTrue(obj["provenance"])

    def test_10_noise_source_site_fact(self):
        r = engine().audit(); fact = r["contextFeatures"][0]
        self.assertEqual(fact["type"],"NOISE_SOURCE"); self.assertEqual(fact["category"],"SITE_FACT")
        self.assertIn("western boundary",fact["description"])

    def test_11_view_preference_not_site_fact(self):
        r = engine().audit(); pref = r["userSitePreferences"][0]
        self.assertEqual(pref["category"],"USER_SITE_PREFERENCE")
        self.assertFalse(any(x["type"] == "SIGNIFICANT_VIEW" for x in r["contextFeatures"]))

    def test_12_unknown_terrain_explicit_not_flat(self):
        r = engine().audit(); t = r["terrain"]
        self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(t["status"],"TERRAIN_DATA_MISSING")
        for field in ("minElevation","maxElevation","elevationRange","slopeDirection"): self.assertIsNone(t[field])
        self.assertFalse(next(x for x in r["missingSiteData"] if x["inputId"] == "terrain")["blocking"])

    def test_13_confirmed_elevation_range(self):
        s = site_source(); s["statements"] += elevations()
        r = engine([s]).audit(); t = r["terrain"]
        self.assertEqual(t["elevationRange"],2)
        self.assertEqual(t["minElevation"],100); self.assertEqual(t["maxElevation"],102)
        self.assertEqual(metric(r,"elevation-range")["scope"],"OBSERVED_SAMPLES_ONLY")

    def test_14_no_setbacks_fire_distances(self):
        r = engine().audit()
        self.assertFalse(any(m["metricId"] in ("setback","fire-distance","buildable-envelope") for m in r["derivedMetrics"]))
        self.assertEqual(r["gateProof"]["inventedLegalNormativeConstraintsCount"],0)

    def test_15_conflicting_boundaries_conflict(self):
        conflicting = source([dict(id="other-boundary",kind="BOUNDARY",geometry=geometry("Polygon",[[[0,0],[40,0],[40,20],[0,20],[0,0]]]))],id="drawing",kind="DRAWING")
        r = engine([site_source(),conflicting]).audit()
        self.assertEqual(r["status"],"BLOCKED")
        self.assertEqual(r["conflicts"][0]["inputId"],"BOUNDARY")
        self.assertEqual(r["conflicts"][0]["category"],"CONFLICT")

    def test_16_user_correction_reaudit_verified(self):
        other = source([dict(id="other",kind="BOUNDARY",geometry=geometry("Polygon",[[[0,0],[40,0],[40,20],[0,20],[0,0]]]))],id="drawing",kind="DRAWING")
        e = engine([site_source(),other]); e.audit()
        st = deepcopy(other["statements"][0]); st["supersedes"] = ["survey:boundary","drawing:other"]
        e.update_source(source([st],id="answer",kind="USER_CORRECTION"))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        self.assertEqual(e.audit()["status"],"VERIFIED")
        self.assertEqual(e.require_verified()["blockingConflictsCount"],0)

    def test_17_stage0_change_invalidates(self):
        dependency = stage0(); e = engine(s0=dependency); e.audit()
        dependency.update_source(intake_source(purpose="IZHS",municipality="other-city",floor_count=2))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        dependency.audit(); self.assertEqual(e.result()["status"],"INVALIDATED")
        self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_18_site_source_change_invalidates(self):
        e = engine(); e.audit(); changed = site_source(); changed["revision"] = "v2"
        e.update_source(changed)
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_19_identical_input_deterministic(self):
        first,second = engine().audit(),engine().audit()
        self.assertEqual(json.dumps(first,sort_keys=True),json.dumps(second,sort_keys=True))
        self.assertEqual(first["siteContextFingerprint"],second["siteContextFingerprint"])

    def test_20_provenance_coverage_full(self):
        r = engine().audit()
        self.assertEqual(r["gateProof"]["provenanceCoverage"],1)
        for field in ("site","boundary","orientation"): self.assertTrue(r[field]["provenance"])
        self.assertTrue(r["gateProof"]["allDerivedMetricsTraceable"])

    def test_21_unrelated_context_not_added(self):
        r = engine().audit()
        self.assertEqual([f["type"] for f in r["contextFeatures"]],["NOISE_SOURCE"])
        self.assertFalse(any(x["inputId"].startswith("context:") for x in r["missingSiteData"]))

    def test_22_legal_ownership_not_inferred(self):
        r = engine().audit()
        for field in ("ownership","legalBoundary"):
            self.assertIsNone(r["site"][field]["value"])
            self.assertEqual(r["site"][field]["category"],"MISSING_SITE_DATA")

    def test_23_no_layout_room_wall_generation(self):
        for field in ("layout","rooms","walls","buildableEnvelope","setbacks"):
            s = site_source(); s["statements"][2][field] = 10
            self.assertEqual(engine([s]).audit()["status"],"BLOCKED")

    def test_24_metric_units_input_evidence(self):
        r = engine().audit()
        for m in r["derivedMetrics"]:
            self.assertTrue(m["unit"]); self.assertTrue(m["inputEvidence"]); self.assertTrue(m["provenance"])
            self.assertTrue(all(p["sourceId"] == "survey" for p in m["inputEvidence"]))


class BoundaryTests(unittest.TestCase):
    def test_selective_requirements_no_geology_questionnaire(self):
        r = engine(requirements=policy("terrain","context:SIGNIFICANT_VIEW")).audit()
        self.assertEqual(r["status"],"WAITING_FOR_USER_DATA")
        self.assertEqual([q["inputId"] for q in r["questions"]],["context:SIGNIFICANT_VIEW"])
        self.assertFalse(any("geology" in q["inputId"] for q in r["questions"]))
        for q in r["questions"]:
            for field in ("WHAT","WHY","REQUIRED_BY","FORMAT","provenance"): self.assertTrue(q[field])

    def test_distance_line_frontage_and_segment_slope(self):
        s = site_source(); s["statements"] += elevations() + [
            dict(id="line",kind="OBJECT",objectId="frontage-line",type="FENCE",geometry=geometry("LineString",[[0,0],[30,0]])),
            dict(id="distance",kind="MEASUREMENT",measurementId="distance",operation="DISTANCE",refs=["ELEVATION_POINT:e1","ELEVATION_POINT:e2"]),
            dict(id="orientation",kind="MEASUREMENT",measurementId="line-angle",operation="LINE_ORIENTATION",refs=["OBJECT:frontage-line"]),
            dict(id="frontage",kind="MEASUREMENT",measurementId="frontage",operation="FRONTAGE_LENGTH",refs=["OBJECT:frontage-line"]),
            dict(id="slope",kind="MEASUREMENT",measurementId="slope",operation="SLOPE_DIRECTION",refs=["ELEVATION_POINT:e1","ELEVATION_POINT:e2"])]
        r = engine([s]).audit()
        self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(metric(r,"distance")["result"],30); self.assertEqual(metric(r,"frontage")["result"],30)
        self.assertEqual(metric(r,"line-angle")["result"],0)
        self.assertEqual(metric(r,"slope")["result"],180)
        self.assertIn("NOT_GLOBAL_TERRAIN",r["terrain"]["slopeStatus"])
        self.assertEqual(metric(r,"site-centroid")["result"],[15,10])
        self.assertEqual(metric(r,"site-perimeter")["result"],100)

    def test_coordinate_units_orientation_and_vertical_datums_fail_closed(self):
        for field,value in (("coordinateSystemId","wrong-crs"),("unit","mm")):
            s = site_source(); s["statements"][2]["geometry"][field] = value
            self.assertEqual(engine([s]).audit()["status"],"BLOCKED")
        s = site_source(); s["statements"][3]["coordinateOrientation"] = "not-survey-grid"
        self.assertTrue(engine([s]).audit()["conflicts"])
        s = site_source(); s["statements"] += elevations(); s["statements"][-1]["verticalDatum"] = "different-datum"
        self.assertEqual(engine([s]).audit()["status"],"BLOCKED")
        s = site_source(); s["statements"][1]["metadata"]["kind"] = "GEOGRAPHIC"
        self.assertEqual(engine([s]).audit()["status"],"BLOCKED")

    def test_equivalent_polygon_ring_has_no_false_conflict(self):
        other = source([dict(id="boundary",kind="BOUNDARY",geometry=geometry("Polygon",[[[30,20],[30,0],[0,0],[0,20],[30,20]]]))],id="drawing",kind="DRAWING")
        r = engine([site_source(),other]).audit()
        self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(len(r["boundary"]["provenance"]),2)

    def test_all_access_objects_context_types_and_contours(self):
        s = site_source()
        for type in sorted(ACCESS_TYPES): s["statements"].append(dict(id="a-"+type,kind="ACCESS",accessId="a-"+type,type=type,geometry=geometry()))
        for type in sorted(OBJECT_TYPES): s["statements"].append(dict(id="o-"+type,kind="OBJECT",objectId="o-"+type,type=type,geometry=geometry()))
        for type in sorted(FEATURE_TYPES): s["statements"].append(dict(id="c-"+type,kind="CONTEXT",featureId="c-"+type,type=type,description="explicit confirmed fixture observation"))
        s["statements"].append(dict(id="contour",kind="CONTOUR",contourId="contour",geometry=geometry("LineString",[[0,0],[30,0]]),elevation=100,elevationUnit="m",verticalDatum="benchmark"))
        self.assertEqual(engine([s]).audit()["status"],"VERIFIED")

    def test_other_artifacts_unchanged_and_gate_forgery_blocked(self):
        deps = dependencies(); intent = intent_engine(deps=deps); intent.audit()
        before_fp,before_intent = deps[1].result(),intent.result()
        e = engine(s0=deps[0]); e.audit()
        self.assertEqual(deps[1].result(),before_fp); self.assertEqual(intent.result(),before_intent)
        missing = engine([]); forged = missing.audit(); forged.update(status="VERIFIED",canProgress=True)
        with self.assertRaises(RuntimeError): missing.require_verified()

    def test_nonfinite_unconfirmed_sources_and_approved_derived_geometry(self):
        s = site_source(); s["verification"] = "UNVERIFIED"
        self.assertEqual(engine([s]).audit()["status"],"BLOCKED")
        s = site_source(); s["statements"][2]["geometry"]["coordinates"][0][0][0] = float("nan")
        self.assertEqual(engine([s]).audit()["status"],"BLOCKED")
        s = site_source(); s["kind"] = "APPROVED_DERIVED_GEOMETRY"
        self.assertEqual(engine([s]).audit()["status"],"BLOCKED")
        s.update(approved=True,derivationRule="caller-approved-extraction",inputEvidence=[{"sourceId":"survey-original","revision":"v1","verification":"CONFIRMED"}])
        self.assertEqual(engine([s]).audit()["status"],"VERIFIED")

    def test_mm_geometry_preserves_units_and_policy_change_invalidates(self):
        s = site_source(); s["statements"][1]["metadata"]["unit"] = "mm"
        for st in s["statements"]:
            if "geometry" in st: st["geometry"]["unit"] = "mm"
        r = engine([s]).audit(); self.assertEqual(metric(r,"site-area")["unit"],"mm2")
        e = engine(); e.audit(); e.update_requirements(policy("terrain"))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        self.assertEqual(e.audit()["status"],"WAITING_FOR_USER_DATA")

    def test_file_to_file_north_answer_reaudit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); r,s,req,site,a,o = [root/x for x in ("registry.json","sources.json","req.json","site.json","answer.json","out.json")]
            missing = site_source(); north = missing["statements"].pop(3)
            for path,value in ((r,registry()),(s,[complete()]),(req,policy()),(site,[missing]),(a,[source([north],id="answer",kind="USER_CORRECTION")])):
                path.write_text(json.dumps(value),encoding="utf-8")
            cmd = [sys.executable,str(Path(__file__).resolve().parents[1]/"site_context.py"),"--stage0-registry",str(r),"--stage0-sources",str(s),"--requirements",str(req),"--site-sources",str(site),"--output",str(o)]
            p = subprocess.run(cmd,capture_output=True,text=True); self.assertEqual(p.returncode,2,p.stderr)
            p = subprocess.run(cmd+["--answers",str(a)],capture_output=True,text=True); self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(o.read_text())["status"],"VERIFIED")


if __name__ == "__main__": unittest.main()
