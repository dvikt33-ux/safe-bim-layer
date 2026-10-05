from copy import deepcopy
import inspect
import math
import unittest
from unittest.mock import patch

import planning_engine as module
from planning_engine import PlanningEngine, POLICY, shared_boundary, overlap, candidate_fingerprint, intersects_closed, rectangle
from design_stage0 import Stage0, fingerprint
from functional_program import FunctionalProgram
from design_intent import DesignIntent
from site_context import SiteContext
from project_constraints import ProjectConstraintInput
from normative_bundle import ProjectNormativeBundle, GlobalRuleLibrary, text_hash
from constraint_compilation import ConstraintCompilation
from tests.test_design_stage0 import registry, complete
from tests.test_functional_program import brief, space
from tests.test_design_intent import intent_source, goal
from tests.test_site_context import site_source, policy as site_policy, geometry
from tests.test_project_constraints import source, constraint, floor, material
from tests.test_constraint_compilation import domains, references, norm
from tests.test_normative_bundle import library_data, scope, seal


def relation(a,b,type="REQUIRED_ADJACENCY",category="USER_REQUIREMENT"):
    return dict(id=a+"-"+b+"-"+type,kind="RELATIONSHIP",type=type,category=category,**{"from":a,"to":b})


def area(id="area",room="kitchen",value=20,op=">=",binding=True):
    return constraint(id,type="AREA_LIMIT",scope=["SPACE:"+room],subject="REQUESTED_AREA",value=value,operator=op,unit="m2",binding=binding)


def dimension(subject="WIDTH",value=100,op="<=",id=None):
    return constraint(id or subject.lower(),type="DIMENSION_LIMIT",subject=subject,value=value,operator=op,unit="m",scope=["BUILDING"])


def location(room,fid):
    return constraint("location-"+room,type="SPACE_LOCATION_REQUIRED",value="FLOOR:"+fid,operator="REQUIRE",unit="none",scope=["SPACE:"+room])


def fixture(statements=None,project=None,floors=2,goals=None,survey=None,rule=None,policy=None):
    intake=complete();intake["facts"]["floor_count"]["value"]=floors
    s0=Stage0(registry(),[intake]);s0.audit()
    fp=FunctionalProgram(s0,[brief(statements if statements is not None else [space("kitchen","KITCHEN",requestedArea=dict(value=16,unit="m2")),space("living","LIVING_ROOM",requestedArea=dict(value=25,unit="m2"))])]);fp.audit()
    di=DesignIntent(s0,fp,[intent_source(goals if goals is not None else [goal("compact","COMPACTNESS")])]);di.audit()
    site=SiteContext(s0,[survey or site_source()],site_policy());site.audit()
    pc=ProjectConstraintInput(s0,fp,di,site,[source(project or [])]);pc.audit()
    data=library_data();r=rule or norm(value=100,op="lte",unit="m")
    # A real producer receipt pins the explicit synthetic requirement text, never a fabricated VERIFIED result.
    doc=data["sources"]["SYNTHETIC_DOCUMENT@test-r1"]
    text="SYNTHETIC planning test requirement: "+str(r["requirement"])
    h=text_hash(text);doc.update(content=text,sourceHash=h);doc["verifiedLocations"][0].update(text=text,textHash=h,sourceHash=h)
    r["source"]["sourceHash"]=h;seal(r);data["rules"]["IZHS/GENERAL"]=[r]
    lib=GlobalRuleLibrary(data);bundle=ProjectNormativeBundle(s0,fp,di,site,pc,lib,scope());bundle.audit()
    cc=ConstraintCompilation(s0,fp,di,site,pc,bundle,domains(),references());cc.audit()
    e=PlanningEngine(cc,fp,policy)
    e.test_upstream=(s0,fp,di,site,pc,bundle);e.test_library=lib
    return e


def house():
    statements=[space("entry","ENTRANCE",requestedArea=dict(value=6,unit="m2")),
        space("kitchen","KITCHEN",requestedArea=dict(value=16,unit="m2")),
        space("living","LIVING_ROOM",requestedArea=dict(value=25,unit="m2")),
        space("bathroom","BATHROOM",requestedArea=dict(value=5,unit="m2")),
        space("bedroom","BEDROOM",2,requestedArea=dict(value=14,unit="m2")),
        space("bathroom_upper","BATHROOM",requestedArea=dict(value=5,unit="m2")),
        relation("entry","living","REQUIRED_ACCESS"),relation("kitchen","living")]
    project=[floor("floor-1"),floor("floor-2"),dimension(value=20),dimension("DEPTH",15)]
    project += [location(r,"floor-1") for r in ("entry","kitchen","living","bathroom")]
    project += [location(r,"floor-2") for r in ("bedroom","bathroom_upper")]
    # Existing compilation treats FP's EXTERIOR as a space reference and blocks it.
    # Use its existing normative typed adapter with a SPACE:living scope, without a phantom room
    # or modifying upstream. This explicitly synthetic rule requires the same external access.
    return fixture(statements,project,rule=norm("ADJACENCY","RELATIONSHIP:EXTERNAL_ACCESS:living:EXTERIOR","EXTERNAL_ACCESS","eq","none",["SPACE:living"]))


class RequiredScenarios(unittest.TestCase):
    def verified(self,e=None):
        e=e or fixture();r=e.audit();self.assertEqual(r["status"],"VERIFIED",r["generationIssues"] or r["candidateSummaries"])
        self.assertTrue(e.require_verified());return e,r,r["selectedCandidate"]
    def test_01_unverified_compilation_blocks(self):
        e=fixture();e._compilation._result["status"]="BLOCKED";self.assertEqual(e.audit()["status"],"BLOCKED")
    def test_02_planning_input_fingerprint_mismatch(self):
        e=fixture();original=e._compilation.planning_input
        def corrupt():
            v=original();v["sourceCompilationFingerprint"]="fake";return v
        e._compilation.planning_input=corrupt;self.assertEqual(e.audit()["status"],"BLOCKED")
    def test_03_deterministic(self):
        e,r,_=self.verified(house());self.assertEqual(r,e.audit())
    def test_04_no_random_time_fields(self):
        _,r,_=self.verified();text=str(r).lower();self.assertNotIn("timestamp",text);self.assertNotIn("random",text)
    def test_05_single_required_space(self):
        _,_,c=self.verified(fixture([space("single","BEDROOM")]));self.assertEqual([x["spaceId"] for x in c["spaces"]],["single"])
    def test_06_quantity_three(self):
        _,_,c=self.verified(fixture([space("bedroom","BEDROOM",3)]));self.assertEqual({r["spaceId"] for r in c["spaces"]},{"bedroom#1","bedroom#2","bedroom#3"})
    def test_07_no_missing_spaces(self):
        _,_,c=self.verified(house());self.assertEqual(len(c["spaces"]),7)
    def test_08_no_phantom_program_rooms(self):
        _,_,c=self.verified(house());self.assertEqual({r["programSpaceId"] for r in c["spaces"]},{"entry","kitchen","living","bathroom","bedroom","bathroom_upper"});self.assertTrue(all(x["type"] in {"CIRCULATION","VERTICAL_CONNECTION"} for x in c["circulation"]))
    def test_09_stable_instance_ids(self):
        e=fixture([space("bedroom","BEDROOM",3)]);r=e.audit();self.assertEqual([x["spaceId"] for x in r["selectedCandidate"]["spaces"]],[x["spaceId"] for x in e.audit()["selectedCandidate"]["spaces"]])
    def test_10_one_floor(self):
        _,_,c=self.verified(fixture(floors=1));self.assertEqual(c["floors"],[dict(floorId="floor-1")])
    def test_11_two_floors(self):
        _,_,c=self.verified(house());self.assertEqual(c["floors"],[dict(floorId="floor-1"),dict(floorId="floor-2")])
    def test_12_no_extra_floor(self):
        _,_,c=self.verified(fixture(floors=1));self.assertEqual({r["floorId"] for r in c["spaces"]},{"floor-1"})
    def test_13_explicit_floor(self):
        _,_,c=self.verified(house());self.assertTrue(all(r["floorId"]=="floor-2" for r in c["spaces"] if r["programSpaceId"]=="bedroom"))
    def test_14_incompatible_floor_adjacency(self):
        e=fixture([space("a","KITCHEN"),space("b","BEDROOM"),relation("a","b")],[floor("floor-1"),floor("floor-2"),location("a","floor-1"),location("b","floor-2")]);self.assertEqual(e.audit()["status"],"NO_VALID_PLAN_FOUND")
    def test_15_finite_positive(self):
        _,_,c=self.verified(house());self.assertTrue(all(math.isfinite(r[k]) and r[k]>0 for r in c["spaces"] for k in ("width","depth","area")))
    def test_16_rectangles(self):
        _,_,c=self.verified();self.assertTrue(all(r["geometryType"]=="RECTANGLE" and r["unit"]=="m" for r in c["spaces"]))
    def test_17_area_product(self):
        _,_,c=self.verified(house());self.assertTrue(all(abs(r["area"]-r["width"]*r["depth"])<POLICY["numericTolerance"] for r in c["spaces"]))
    def test_18_no_overlaps(self):
        _,_,c=self.verified(house());rs=c["spaces"]+[x for x in c["circulation"] if x["type"]=="CIRCULATION"];self.assertFalse(any(overlap(a,b) for i,a in enumerate(rs) for b in rs[i+1:]))
    def test_19_boundary_touch_allowed(self):
        a=dict(x=0,y=0,width=2,depth=2,floorId="f");b=dict(a,x=2);self.assertFalse(overlap(a,b));self.assertEqual(shared_boundary(a,b),2)
    def test_20_minimum_area(self):
        _,_,c=self.verified(fixture([space("kitchen","KITCHEN")],project=[area(value=20)]));self.assertGreaterEqual(next(r["area"] for r in c["spaces"] if r["spaceId"]=="kitchen"),20)
    def test_21_maximum_area(self):
        _,_,c=self.verified(fixture([space("kitchen","KITCHEN")],[area(value=8,op="<=")]));self.assertLessEqual(c["spaces"][0]["area"],8)
    def test_22_preferred_area_score_only(self):
        e=fixture([space("kitchen","KITCHEN")],[area(value=100,binding=False),area("max",value=10,op="<=")]);_,_,c=self.verified(e);self.assertEqual(c["spaces"][0]["area"],10);self.assertTrue(any(s["kind"]=="REQUESTED_AREA" and s["score"]<0 for s in c["preferenceScores"]))
    def test_23_impossible_area_no_candidate(self):
        r=fixture(project=[area(value=30),area("max",value=10,op="<=")]).audit();self.assertNotEqual(r["status"],"VERIFIED");self.assertIsNone(r["selectedCandidate"])
    def test_24_max_width(self):
        _,_,c=self.verified(fixture(project=[dimension(value=10)]));self.assertLessEqual(c["buildingEnvelope"]["width"],10)
    def test_25_max_depth(self):
        _,_,c=self.verified(fixture(project=[dimension("DEPTH",8)]));self.assertLessEqual(c["buildingEnvelope"]["depth"],8)
    def test_26_envelope_derived(self):
        _,_,c=self.verified();rs=c["spaces"]+[x for x in c["circulation"] if x["type"]=="CIRCULATION"];self.assertAlmostEqual(c["buildingEnvelope"]["width"],max(r["x"]+r["width"] for r in rs));self.assertEqual(c["buildingEnvelope"]["basis"],"GEOMETRY_BOUNDING_BOX")
    def test_27_impossible_envelope(self):
        self.assertEqual(fixture(project=[dimension(value=0.1)]).audit()["status"],"NO_VALID_PLAN_FOUND")
    def test_28_required_adjacency(self):
        _,_,c=self.verified(house());a,b=[next(r for r in c["spaces"] if r["spaceId"]==sid) for sid in ("kitchen","living")];self.assertGreater(shared_boundary(a,b),POLICY["adjacencyEpsilon"])
    def test_29_preferred_adjacency_scored(self):
        _,_,c=self.verified(fixture([space("a","KITCHEN"),space("b","BEDROOM"),relation("a","b","PREFERRED_ADJACENCY")]));self.assertTrue(any(s["kind"]=="PREFERRED_ADJACENCY" and s["raw"]==1 for s in c["preferenceScores"]))
    def test_30_avoid_preference_not_hard(self):
        e=fixture([space("a","KITCHEN"),space("b","BEDROOM"),relation("a","b","AVOID_ADJACENCY","USER_PREFERENCE")]);_,_,c=self.verified(e);self.assertFalse(any(x.get("subject","").startswith("RELATIONSHIP:AVOID") for x in c["constraintChecks"]));self.assertTrue(any(s["kind"]=="AVOID_ADJACENCY" for s in c["preferenceScores"]))
    def test_31_mandatory_separation(self):
        _,_,c=self.verified(fixture([space("a","KITCHEN"),space("b","BEDROOM"),space("c","HALL"),relation("a","b","SEPARATION_REQUIRED")]));self.assertEqual(shared_boundary(*[next(r for r in c["spaces"] if r["spaceId"]==sid) for sid in ("a","b")]),0)
    def test_32_corner_not_adjacent(self):
        a=dict(x=0,y=0,width=2,depth=2,floorId="f");self.assertEqual(shared_boundary(a,dict(a,x=2,y=2)),0)
    def test_33_external_access(self):
        _,_,c=self.verified(house());r=next(r for r in c["spaces"] if r["spaceId"]=="living");self.assertTrue(r["externalAccess"]);self.assertIsNotNone(r["buildingEdge"])
    def test_34_independent_access(self):
        _,_,c=self.verified(house());self.assertTrue(any(l["fromId"]=="entry" and l["type"]=="SPACE_TO_CIRCULATION" for l in c["circulationLinks"]));self.assertTrue(all(x["status"]=="PASS" for x in c["constraintChecks"] if x["subject"].startswith("RELATIONSHIP:REQUIRED_ACCESS")))
    def test_35_vertical_connector(self):
        _,_,c=self.verified(house());self.assertEqual(next(x["floors"] for x in c["circulation"] if x["type"]=="VERTICAL_CONNECTION"),["floor-1","floor-2"])
    def test_36_no_stair_compliance(self):
        _,_,c=self.verified();self.assertEqual(next(x["dimensionalCompliance"] for x in c["circulation"] if x["type"]=="VERTICAL_CONNECTION"),"NOT_EVALUATED")
    def test_37_unsupported_planning_hard_blocks(self):
        r=fixture(rule=norm(subject="STAIR_WIDTH",value=1,unit="m")).audit();self.assertEqual(r["status"],"BLOCKED");self.assertEqual(r["unsupportedMandatoryConstraints"][0]["status"],"UNSUPPORTED_MANDATORY_CONSTRAINT")
    def test_38_material_deferred(self):
        _,_,c=self.verified(fixture(project=[material()]));self.assertEqual(c["deferredConstraints"][0]["constraint"]["domain"],"MATERIAL")
    def test_39_unsupported_preference_nonblocking(self):
        _,r,_=self.verified(fixture(goals=[goal()]));self.assertEqual(r["unsupportedPreferences"][0]["value"],"LOW_COST")
    def test_40_deferred_retained(self):
        e,_,c=self.verified(fixture(project=[material()]));self.assertEqual(c["deferredConstraints"][0]["constraint"],next(x for x in e._compilation.planning_input()["mandatoryConstraints"] if x["domain"]=="MATERIAL"));self.assertTrue(c["deferredConstraints"][0]["downstreamScope"])
    def test_41_site_facts_retained(self):
        e,_,c=self.verified();self.assertEqual(c["siteFacts"],e._compilation.planning_input()["siteFacts"])
    def test_42_tree_not_preserved_implicitly(self):
        s=site_source();s["statements"].append(dict(id="tree",kind="OBJECT",objectId="tree",type="TREE",geometry=geometry()))
        _,_,c=self.verified(fixture(survey=s));self.assertIsNone(c["sitePlacement"]);self.assertFalse(c["deferredConstraints"])
    def test_43_preserved_object_not_intersected(self):
        pc=[constraint("preserve",type="EXISTING_OBJECT_PRESERVE",value="EXISTING_OBJECT",operator="PRESERVE",unit="none",scope=["OBJECT:existing-building"])]
        _,_,c=self.verified(fixture(project=pc));v=c["sitePlacement"];self.assertFalse(intersects_closed((v["x"],v["y"],v["x"]+v["width"],v["y"]+v["depth"]),(5,5,10,10)))
    def test_44_prohibited_zone_not_intersected(self):
        s=site_source();s["statements"].append(dict(id="zone",kind="CONTEXT",featureId="zone",type="LANDSCAPE_FEATURE",description="explicit forbidden area",geometry=geometry("Polygon",[[[0,0],[12,0],[12,12],[0,12],[0,0]]])))
        pc=[constraint("zone-ban",type="SITE_ZONE_PROHIBITED",value="SITE_ZONE",operator="PROHIBIT",unit="none",scope=["ZONE:zone"])]
        _,_,c=self.verified(fixture(project=pc,survey=s));v=c["sitePlacement"];self.assertFalse(intersects_closed((v["x"],v["y"],v["x"]+v["width"],v["y"]+v["depth"]),(0,0,12,12)))
    def test_45_no_invented_setback(self):
        _,_,c=self.verified(fixture(project=[constraint("site",type="CUSTOM",subject="SITE_PLACEMENT",value="REQUIRED",unit="none",operator="REQUIRE")]));self.assertEqual(c["sitePlacement"]["setbacks"],[]);self.assertEqual((c["sitePlacement"]["x"],c["sitePlacement"]["y"]),(0,0))
    def test_46_site_deterministic(self):
        e=fixture(project=[constraint("site",type="CUSTOM",subject="SITE_PLACEMENT",value="REQUIRED",unit="none",operator="REQUIRE")]);r=e.audit();self.assertEqual(r,e.audit());self.assertIsNotNone(r["selectedCandidate"]["sitePlacement"])
    def test_47_hard_not_in_score(self):
        e,_,c=self.verified();hard={x["compiledConstraintId"] for x in e._compilation.planning_input()["mandatoryConstraints"]};self.assertFalse(hard&{x["compiledConstraintId"] for x in c["preferenceScores"]})
    def test_48_score_cannot_rescue_invalid(self):
        e,_,c=self.verified();c["spaces"][0]["width"]=-1;c["score"]=1e20;self.assertEqual(e.audit_candidate(c)["status"],"INVALID_GEOMETRY")
    def test_49_best_valid_selected(self):
        _,r,c=self.verified(house());valid=[x for x in r["candidateSummaries"] if x["status"]=="VALID"];self.assertEqual(c["score"],max(x["score"] for x in valid));self.assertGreater(r["candidatesGenerated"],1)
    def test_50_all_invalid_no_valid_plan(self):
        e=fixture(project=[dimension(value=0.01)]);r=e.audit();self.assertEqual(r["status"],"NO_VALID_PLAN_FOUND");self.assertEqual(r["candidatesValid"],0)
    def test_51_every_decision_provenance(self):
        _,_,c=self.verified(house());self.assertTrue(all(d["basis"] for d in c["decisions"]))
    def test_52_heuristics_labelled(self):
        _,_,c=self.verified();self.assertTrue(all(any(b.get("basisType")=="PLANNER_HEURISTIC" and b.get("policyId") for b in d["basis"]) for d in c["decisions"]))
    def test_53_coverage_one(self):
        e,r,c=self.verified();self.assertEqual(r["constraintCoverage"],1);self.assertEqual(len(c["constraintChecks"]),len(e._compilation.planning_input()["mandatoryConstraints"]));self.assertTrue(all(x["status"]=="PASS" for x in c["constraintChecks"]))
    def test_54_no_direct_library_read(self):
        e=fixture();e.test_library.data=lambda: (_ for _ in ()).throw(AssertionError("planner library read"));self.verified(e)
    def test_55_no_archicad(self):
        sourcecode=inspect.getsource(module);self.assertNotIn("requests",sourcecode);self.assertNotIn("tapir",sourcecode.lower());self.assertNotIn("CreateWalls",sourcecode)
    def test_56_no_upstream_mutation(self):
        e=house();before=[u.result() for u in e.test_upstream]+[e._compilation.result()];self.verified(e);self.assertEqual(before,[u.result() for u in e.test_upstream]+[e._compilation.result()])
    def test_57_compilation_change_invalidates(self):
        e,_,_=self.verified();d=domains();d["revision"]="2";e._compilation.update_registries(domain_registry=d);self.assertEqual(e.result()["status"],"INVALIDATED");self.assertRaises(RuntimeError,e.require_verified)
    def test_58_policy_change_invalidates_recomputes(self):
        e,r,_=self.verified();p=deepcopy(POLICY);p["defaultAspectRatios"]=[2.0];e.update_policy(p);self.assertEqual(e.result()["status"],"INVALIDATED");new=e.audit();self.assertEqual(new["status"],"VERIFIED");self.assertNotEqual(r["plannerPolicyFingerprint"],new["plannerPolicyFingerprint"])
    def test_59_malformed_geometry(self):
        e,_,c=self.verified();del c["spaces"][0]["x"];self.assertEqual(e.audit_candidate(c)["status"],"INVALID_GEOMETRY")
    def test_60_nan_inf(self):
        e,_,c=self.verified()
        for value in (math.nan,math.inf,-math.inf):
            bad=deepcopy(c);bad["spaces"][0]["width"]=value;self.assertEqual(e.audit_candidate(bad)["status"],"INVALID_GEOMETRY")
    def test_61_dangling_relationship(self):
        e,_,c=self.verified(house());c["relationships"][0]["subject"]="RELATIONSHIP:REQUIRED_ACCESS:entry:phantom";self.assertEqual(e.audit_candidate(c)["status"],"INVALID_GEOMETRY")
    def test_62_duplicate_space_ids(self):
        e,_,c=self.verified();c["spaces"][1]["spaceId"]=c["spaces"][0]["spaceId"];self.assertEqual(e.audit_candidate(c)["status"],"INVALID_GEOMETRY")
    def test_63_arbitrary_expression_policy_rejected(self):
        p=deepcopy(POLICY);p["expression"]="__import__('os').system('anything')";self.assertRaises(ValueError,fixture,policy=p)
    def test_64_no_eval(self):
        self.assertNotIn("eval(",inspect.getsource(module));self.assertNotIn("exec(",inspect.getsource(module))
    def test_65_no_shell(self):
        self.assertNotIn("subprocess",inspect.getsource(module));self.assertNotIn("os.system",inspect.getsource(module))
    def test_66_no_external_model(self):
        text=inspect.getsource(module).lower();self.assertNotIn("openai",text);self.assertNotIn("http",text);self.assertNotIn("ollama",text)
    def test_67_limits_enforced(self):
        p=deepcopy(POLICY);p.update(maxCandidates=1,maxGenerationAttempts=3,maxImprovementPasses=1,maxPlacementAttempts=1);_,r,_=self.verified(fixture(policy=p));self.assertLessEqual(r["candidatesGenerated"],1);self.assertLessEqual(r["generationAttempts"],3)
    def test_68_progression_reruns_audit(self):
        e,_,_=self.verified()
        with patch.object(e,"_validate",wraps=e._validate) as checker:
            e.require_verified();self.assertGreater(checker.call_count,0)
    def test_69_copy_or_forgery_cannot_gate(self):
        e,r,_=self.verified();r["selectedCandidate"]["spaces"][0]["x"]=999;self.assertNotEqual(r,e.result());e.require_verified()
        e._result["selectedCandidate"]["spaces"][0]["x"]=999;self.assertRaises(RuntimeError,e.require_verified)
    def test_70_candidate_fingerprint_exact_input_policy(self):
        _,r,c=self.verified();self.assertEqual(c["candidateFingerprint"],candidate_fingerprint(c,r["constraintCompilationFingerprint"],r["plannerPolicyFingerprint"]));self.assertNotEqual(c["candidateFingerprint"],candidate_fingerprint(c,"changed",r["plannerPolicyFingerprint"]))


class Robustness(unittest.TestCase):
    def test_input_content_tamper_with_same_claimed_fingerprint(self):
        e=fixture();original=e._compilation.planning_input
        def changed():
            v=original();v["mandatoryConstraints"]=[];return v
        e._compilation.planning_input=changed;self.assertEqual(e.audit()["status"],"BLOCKED")
    def test_program_content_tamper(self):
        e=fixture();e._program._result["spaces"][0]["quantity"]=999;self.assertEqual(e.audit()["status"],"BLOCKED")
    def test_exact_and_strict_area(self):
        for op,value in (("==",20),(">",20),("<",10)):
            e=fixture([space("kitchen","KITCHEN")],[area(value=value,op=op)]);r=e.audit();self.assertEqual(r["status"],"VERIFIED",r["generationIssues"]);v=r["selectedCandidate"]["spaces"][0]["area"]
            self.assertTrue(abs(v-value)<1e-7 if op=="==" else v>value if op==">" else v<value)
    def test_mandatory_avoid_adjacency(self):
        e=fixture([space("a","KITCHEN"),space("b","BEDROOM"),relation("a","b","AVOID_ADJACENCY")]);r=e.audit();self.assertEqual(r["status"],"VERIFIED");self.assertEqual(shared_boundary(*r["selectedCandidate"]["spaces"]),0)
    def test_vertical_relationship(self):
        e=fixture([space("a","KITCHEN"),space("b","BEDROOM"),relation("a","b","VERTICAL_CONNECTION")],[floor("floor-1"),floor("floor-2"),location("a","floor-1"),location("b","floor-2")]);r=e.audit();self.assertEqual(r["status"],"VERIFIED");self.assertTrue(all(x["status"]=="PASS" for x in r["selectedCandidate"]["constraintChecks"]))
    def test_known_design_goals(self):
        for typ in ("SPACIOUSNESS","STRUCTURAL_REGULARITY","MASONRY_MODULARITY","LOW_COST"):
            r=fixture(goals=[goal("g",typ)]).audit();self.assertEqual(r["status"],"VERIFIED")
            if typ in {"LOW_COST","MASONRY_MODULARITY"}: self.assertEqual(r["unsupportedPreferences"][0]["value"],typ)
            else: self.assertEqual(r["selectedCandidate"]["preferenceScores"][0]["kind"],typ)
    def test_preserved_point(self):
        s=site_source();s["statements"].append(dict(id="tree",kind="OBJECT",objectId="tree",type="TREE",geometry=geometry(coordinates=[1,1])))
        cs=[constraint("tree",type="EXISTING_OBJECT_PRESERVE",value="EXISTING_OBJECT",operator="PRESERVE",unit="none",scope=["OBJECT:tree"])]
        r=fixture(project=cs,survey=s).audit();self.assertEqual(r["status"],"VERIFIED");v=r["selectedCandidate"]["sitePlacement"];self.assertFalse(v["x"]<=1<=v["x"]+v["width"] and v["y"]<=1<=v["y"]+v["depth"])
    def test_nonrectangular_site_blocked(self):
        s=site_source();s["statements"][2]["geometry"]["coordinates"]=[[[0,0],[30,0],[20,20],[0,20],[0,0]]]
        cs=[constraint("site",type="CUSTOM",subject="SITE_PLACEMENT",value="REQUIRED",operator="REQUIRE",unit="none")]
        r=fixture(project=cs,survey=s).audit();self.assertEqual(r["status"],"BLOCKED");self.assertTrue(r["unsupportedMandatoryConstraints"])
    def test_no_silent_unit_conversion(self):
        r=fixture(rule=norm(unit="mm",value=20000,op="lte")).audit();self.assertEqual(r["status"],"BLOCKED");self.assertTrue(r["unsupportedMandatoryConstraints"])
    def test_corridor_link_tamper(self):
        e=fixture();c=e.audit()["selectedCandidate"];c["circulationLinks"][0]["toId"]="phantom";self.assertEqual(e.audit_candidate(c)["status"],"INVALID_GEOMETRY")
    def test_provenance_value_tamper(self):
        e=fixture();c=e.audit()["selectedCandidate"];next(d for d in c["decisions"] if d["decisionId"]=="envelope")["value"]["width"]=99;self.assertEqual(e.audit_candidate(c)["status"],"INVALID_GEOMETRY")
    def test_unsupported_scope_not_silently_checked_elsewhere(self):
        r=fixture(rule=norm("AREA","SPACE_AREA:kitchen",5,"gte","m2",["SPACE:living"])).audit();self.assertEqual(r["status"],"BLOCKED");self.assertTrue(r["unsupportedMandatoryConstraints"])
    def test_nonplanning_normative_domain_retained(self):
        r=fixture(rule=norm("MATERIAL","MATERIAL","CERAMIC_BLOCK","eq","none")).audit();self.assertEqual(r["status"],"VERIFIED");self.assertTrue(r["selectedCandidate"]["deferredConstraints"])
    def test_bad_policy_limits_and_nan_rejected(self):
        for k,v in (("maxCandidates",0),("defaultRoomArea",math.nan),("scoringRegistry",dict(revision="1",weights={"LOW_COST":"eval"}))):
            p=deepcopy(POLICY);p[k]=v;self.assertRaises(ValueError,module.policy_checked,p)
    def test_external_access_false_claim_rejected(self):
        e=house();c=e.audit()["selectedCandidate"];r=next(r for r in c["spaces"] if r["spaceId"]=="living");r["externalAccess"]=False;self.assertEqual(e.audit_candidate(c)["status"],"INVALID_CONSTRAINT")
    def test_geometry_fingerprint_changes_when_coordinates_change(self):
        r=fixture().audit();c=deepcopy(r["selectedCandidate"]);c["spaces"][0]["x"]+=1;self.assertNotEqual(c["candidateFingerprint"],candidate_fingerprint(c,r["constraintCompilationFingerprint"],r["plannerPolicyFingerprint"]))
    def test_missing_numeric_subject_entity_blocks_without_crashing(self):
        r=fixture(rule=norm("AREA","SPACE_AREA",10,"gte","m2")).audit();self.assertEqual(r["status"],"BLOCKED");self.assertTrue(r["unsupportedMandatoryConstraints"])
    def test_unknown_downstream_name_cannot_silently_defer_fire_requirement(self):
        r=norm("FIRE","COMPLEX_FIRE_CALC",1,"eq","none");r["requirement"]["downstreamDomains"]=["UNKNOWN_DOMAIN"];seal(r)
        out=fixture(rule=r).audit();self.assertEqual(out["status"],"BLOCKED");self.assertTrue(out["unsupportedMandatoryConstraints"])
    def test_registered_nonplanning_downstream_scope_deferred(self):
        r=norm("CUSTOM","COST_MODEL",1,"eq","none");r["requirement"]["downstreamDomains"]=["COST_ESTIMATION"];seal(r)
        out=fixture(rule=r).audit();self.assertEqual(out["status"],"VERIFIED");self.assertTrue(out["selectedCandidate"]["deferredConstraints"])


if __name__=="__main__": unittest.main()
