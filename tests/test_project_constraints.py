from copy import deepcopy
import unittest

from project_constraints import ProjectConstraintInput, TYPES, OPERATORS
from design_stage0 import fingerprint
from functional_program import FunctionalProgram, canonical
from tests.test_design_intent import dependencies, engine as intent_engine, intent_source, goal
from tests.test_functional_program import simple_brief
from tests.test_site_context import SiteContext, site_source, policy


def upstream():
    s0,fp = dependencies()
    di = intent_engine(deps=(s0,fp)); di.audit()
    site = SiteContext(s0,[site_source()],policy()); site.audit()
    return s0,fp,di,site


def source(statements=None,id="client",category="CLIENT_REQUIREMENT"):
    return dict(id=id,revision="v1",category=category,approved=True,inspected=True,
                verification="CONFIRMED",basis="NON_NORMATIVE",statements=statements or [])


def constraint(id="budget",type="BUDGET_LIMIT",value=15000000,unit="RUB",operator="<=",scope=None,binding=True,**fields):
    return dict(id=id,kind="CONSTRAINT",constraintId=id,type=type,value=value,unit=unit,operator=operator,
                scope=scope or ["PROJECT"],binding=binding,**fields)


def material(id="material",prohibit=False):
    return constraint(id,type="MATERIAL_PROHIBITED" if prohibit else "MATERIAL_REQUIRED",value="CERAMIC_BLOCK",
                      unit="none",operator="PROHIBIT" if prohibit else "REQUIRE")


def floor(id="ground"):
    return dict(id=id,kind="SCOPE_ENTITY",entityType="FLOOR",entityId=id)


def location(prohibit=False,space="bedroom_master"):
    return constraint("location",type="SPACE_LOCATION_PROHIBITED" if prohibit else "SPACE_LOCATION_REQUIRED",
                      value="FLOOR:ground",unit="none",operator="PROHIBIT" if prohibit else "REQUIRE",scope=["SPACE:"+space])


def envelope():
    return dict(id="envelope",kind="DIMENSION_ENVELOPE",constraintId="envelope",scope=["BUILDING"],binding=True,
                width=12,depth=10,unit="m",exactInputStatement="Дом максимум 12 × 10 m",derivationRule="EXPLICIT_DIMENSION_ENVELOPE_V0")


def engine(statements=None,deps=None,sources=None):
    return ProjectConstraintInput(*(deps or upstream()),sources if sources is not None else [source([constraint()] if statements is None else statements)])


class RequiredScenarios(unittest.TestCase):
    def test_01_stage0_not_verified(self):
        us = upstream(); us[0].update_source(dict(id="brief",revision="v2",kind="USER_BRIEF",values={}))
        self.assertEqual(engine(deps=us).audit()["status"],"BLOCKED")

    def test_02_functional_not_verified(self):
        us = upstream(); us[1].update_source(dict(id="program",kind="USER_BRIEF",revision="v2",approved=True,inspected=True,statements=[]))
        self.assertEqual(engine(deps=us).audit()["status"],"BLOCKED")

    def test_03_intent_not_verified(self):
        us = upstream(); us[2].update_source(intent_source([],id="intent"))
        self.assertEqual(engine(deps=us).audit()["status"],"BLOCKED")

    def test_04_site_not_verified(self):
        us = upstream(); changed = site_source(); changed["revision"] = "v2"; us[3].update_source(changed)
        self.assertEqual(engine(deps=us).audit()["status"],"BLOCKED")

    def test_05_explicit_hard_retained(self):
        e = engine(); r = e.audit(); self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(r["constraints"][0]["value"],15000000); self.assertTrue(e.planning_constraints()[0]["binding"])

    def test_06_nonbinding_remains_nonbinding(self):
        e = engine([constraint(binding=False)]); r = e.audit()
        self.assertEqual(r["status"],"VERIFIED"); self.assertFalse(r["nonBindingConstraints"][0]["binding"])
        self.assertEqual(e.planning_constraints(),[])

    def test_07_budget_unit(self):
        self.assertEqual(engine().audit()["constraints"][0]["unit"],"RUB")

    def test_08_fixed_floor_count(self):
        r = engine([constraint(type="FLOOR_COUNT_FIXED",value=2,unit="count",operator="==")]).audit()
        self.assertEqual(r["status"],"VERIFIED"); self.assertEqual(r["constraints"][0]["value"],2)

    def test_09_required_material(self):
        self.assertEqual(engine([material()]).audit()["constraints"][0]["type"],"MATERIAL_REQUIRED")

    def test_10_prohibited_material(self):
        self.assertEqual(engine([material(prohibit=True)]).audit()["constraints"][0]["type"],"MATERIAL_PROHIBITED")

    def test_11_same_material_conflict(self):
        e = engine([material(),material("ban",True)]); r = e.audit()
        self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["conflicts"])
        with self.assertRaises(RuntimeError): e.require_verified()

    def test_12_numeric_bound_conflict(self):
        cs = [constraint("max",type="AREA_LIMIT",value=150,unit="m2",subject="TOTAL"),
              constraint("min",type="AREA_LIMIT",value=200,unit="m2",operator=">=",subject="TOTAL")]
        r = engine(cs).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["conflicts"])

    def test_13_space_scope_resolved(self):
        r = engine([floor(),location()]).audit(); self.assertEqual(r["status"],"VERIFIED")

    def test_14_unknown_space_blocked(self):
        r = engine([floor(),location(space="phantom")]).audit(); self.assertEqual(r["status"],"BLOCKED")

    def test_15_site_object_scope(self):
        r = engine([constraint(type="EXISTING_OBJECT_PRESERVE",operator="PRESERVE",value="EXISTING_OBJECT",unit="none",scope=["OBJECT:existing-building"])]).audit()
        self.assertEqual(r["status"],"VERIFIED")

    def test_16_unknown_object_blocked(self):
        r = engine([constraint(type="EXISTING_OBJECT_PRESERVE",operator="PRESERVE",value="EXISTING_OBJECT",unit="none",scope=["OBJECT:phantom"])]).audit()
        self.assertEqual(r["status"],"BLOCKED")

    def test_17_dimension_derivation_traceable(self):
        r = engine([envelope()]).audit(); self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual({c["subject"]:c["value"] for c in r["derivedConstraints"]},{"WIDTH":12,"DEPTH":10})
        for c in r["derivedConstraints"]:
            self.assertEqual(c["exactInputStatement"],envelope()["exactInputStatement"]); self.assertTrue(c["inputEvidence"]); self.assertTrue(c["provenance"])

    def test_18_no_project_type_invention(self):
        r = engine([]).audit(); self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(r["constraints"]+r["derivedConstraints"],[])

    def test_19_normative_pending_inactive(self):
        s = source([dict(id="norm",topic="future normative review")],category="NORMATIVE_PENDING")
        r = engine(sources=[s]).audit(); self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(r["constraints"],[]); self.assertTrue(r["normativePending"])

    def test_20_explicit_supersession_reaudit(self):
        old = material("old"); new = material("new",True); e = engine([old,new]); self.assertEqual(e.audit()["status"],"BLOCKED")
        answer = material("answer",True); answer["supersedes"] = [dict(claimId="client:old",evidenceFingerprint=fingerprint(old)),dict(claimId="client:new",evidenceFingerprint=fingerprint(new))]
        e.update_source(source([answer],id="correction",category="APPROVED_PROJECT_DECISION"))
        self.assertEqual(e.result()["status"],"INVALIDATED"); self.assertEqual(e.audit()["status"],"VERIFIED"); e.require_verified()

    def test_21_each_upstream_change_invalidates(self):
        for index in range(4):
            us = upstream(); e = engine(deps=us); e.audit()
            if index == 0:
                from tests.test_design_stage0 import complete
                changed = complete(); changed["revision"] = "v2"; us[0].update_source(changed)
            elif index == 1:
                changed = simple_brief(); changed["revision"] = "v2"; us[1].update_source(changed)
            elif index == 2: us[2].update_source(intent_source([goal(priority=2)]))
            else:
                changed = site_source(); changed["revision"] = "v2"; us[3].update_source(changed)
            us[index].audit()
            self.assertEqual(e.result()["status"],"INVALIDATED")
            with self.assertRaises(RuntimeError): e.require_verified()

    def test_22_source_change_invalidates(self):
        e = engine(); e.audit(); s = source([constraint(value=14000000)]); e.update_source(s)
        self.assertEqual(e.result()["status"],"INVALIDATED"); self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_23_deterministic(self):
        e = engine([constraint(),material()]); first = e.audit()
        self.assertEqual(canonical(first),canonical(e.audit()))
        self.assertEqual(canonical(first),canonical(engine([material(),constraint()]).audit()))

    def test_24_provenance_full(self):
        e = engine([constraint(),envelope()]); e.audit(); self.assertEqual(e.require_verified()["provenanceCoverage"],1)

    def test_25_no_layout_generation(self):
        r = engine().audit()
        self.assertFalse({"rooms","walls","layout","placement"} & set(r))

    def test_26_no_normative_values(self):
        s = source([constraint()]); s["basis"] = "NORMATIVE"
        self.assertEqual(engine(sources=[s]).audit()["status"],"BLOCKED")
        r = engine([]).audit(); self.assertEqual(r["gateProof"]["inventedNormativeConstraintsCount"],0)

    def test_27_invalid_unit(self):
        self.assertEqual(engine([constraint(unit="USD")]).audit()["status"],"BLOCKED")

    def test_28_invalid_operator(self):
        self.assertEqual(engine([constraint(operator="evaluate")]).audit()["status"],"BLOCKED")

    def test_29_no_silent_binding_promotion(self):
        c = constraint(); del c["binding"]
        r = engine([c]).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertEqual(r["constraints"],[])
        self.assertEqual(len(r["questions"]),1)

    def test_30_hard_overrides_preference_recorded(self):
        r = engine([floor(),location()]).audit(); self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(len(r["overrides"]),1); self.assertEqual(r["overrides"][0]["inputEvidence"]["value"],"upper")

    def test_31_hard_requirement_conflict(self):
        # Existing FP requestedArea is a USER_REQUIREMENT; preferredFloor is always a preference.
        r = engine([constraint(type="AREA_LIMIT",value=10,unit="m2",scope=["SPACE:kitchen"],subject="REQUESTED_AREA")]).audit()
        self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["conflicts"])
        r = engine([floor(),location(True,"kitchen"),dict(location(space="kitchen"),id="required",constraintId="required")]).audit()
        self.assertTrue(r["conflicts"])

    def test_32_no_eval_support(self):
        for field in ("expression","eval","formula"):
            c = constraint(); c[field] = "__import__('os').system('echo forbidden')"
            self.assertEqual(engine([c]).audit()["status"],"BLOCKED")


class Robustness(unittest.TestCase):
    def test_all_25_categories(self):
        us = upstream()
        s = site_source()
        from tests.test_site_context import geometry
        s["statements"].append(dict(id="garden",kind="CONTEXT",featureId="garden",type="LANDSCAPE_FEATURE",geometry=geometry("Polygon",[[[0,0],[2,0],[2,2],[0,2],[0,0]]])))
        us[3].update_source(s); us[3].audit()
        fixtures = {
            "BUDGET_LIMIT":(15000000,"RUB","<=",["PROJECT"],{}),
            "AREA_LIMIT":(150,"m2","<=",["BUILDING"],{"subject":"TOTAL"}),
            "DIMENSION_LIMIT":(12,"m","<=",["BUILDING"],{"subject":"WIDTH"}),
            "FLOOR_COUNT_FIXED":(2,"count","==",["BUILDING"],{}),
            "HEIGHT_LIMIT_PROJECT":(8,"m","<=",["BUILDING"],{}),
            "MATERIAL_REQUIRED":("CERAMIC_BLOCK","none","REQUIRE",["BUILDING"],{}),
            "MATERIAL_PROHIBITED":("CERAMIC_BLOCK","none","PROHIBIT",["BUILDING"],{}),
            "CONSTRUCTION_SYSTEM_REQUIRED":("MASONRY","none","REQUIRE",["BUILDING"],{}),
            "CONSTRUCTION_SYSTEM_PROHIBITED":("MASONRY","none","PROHIBIT",["BUILDING"],{}),
            "EXISTING_OBJECT_PRESERVE":("EXISTING_OBJECT","none","PRESERVE",["OBJECT:existing-building"],{}),
            "EXISTING_OBJECT_REMOVE_REQUIRED":("EXISTING_OBJECT","none","REQUIRE",["OBJECT:existing-building"],{}),
            "SITE_ZONE_PROHIBITED":("SITE_ZONE","none","PROHIBIT",["ZONE:garden"],{}),
            "SITE_ZONE_REQUIRED":("SITE_ZONE","none","REQUIRE",["ZONE:garden"],{}),
            "ACCESS_REQUIRED":("driveway","none","REQUIRE",["SITE"],{}),
            "ORIENTATION_REQUIRED":(90,"degrees","==",["BUILDING"],{}),
            "SPACE_LOCATION_REQUIRED":("FLOOR:ground","none","REQUIRE",["SPACE:living"],{}),
            "SPACE_LOCATION_PROHIBITED":("FLOOR:ground","none","PROHIBIT",["SPACE:living"],{}),
            "CAPACITY_FIXED":(1,"count","==",["SPACE:kitchen"],{"subject":"SPACE_QUANTITY"}),
            "PARKING_COUNT_FIXED":(2,"count","==",["SITE"],{}),
            "PHASING_REQUIRED":(["service","house"],"none","REQUIRE",["PROJECT"],{}),
            "UTILITY_CONNECTION_FIXED":("approved-feed-1","none","==",["SYSTEM:water"],{}),
            "EQUIPMENT_REQUIRED":("pump","none","REQUIRE",["SYSTEM:water"],{}),
            "EQUIPMENT_PROHIBITED":("pump","none","PROHIBIT",["SYSTEM:water"],{}),
            "DEMOLITION_LIMIT":(0,"percentage","<=",["SITE"],{"subject":"SITE_OBJECT_SHARE"}),
            "CUSTOM":("client-red","none","==",["BUILDING"],{"subject":"CLIENT_COLOR"}),
        }
        self.assertEqual(set(fixtures),TYPES)
        for typ,(v,u,op,scope,fields) in fixtures.items():
            with self.subTest(type=typ):
                decl = [floor(),dict(id="water",kind="SCOPE_ENTITY",entityType="SYSTEM",entityId="water")]
                r = engine(decl+[constraint(type=typ,value=v,unit=u,operator=op,scope=scope,**fields)],deps=us).audit()
                self.assertEqual(r["status"],"VERIFIED",r["validationErrors"])

    def test_all_operators_and_strict_bounds(self):
        for op in ("==","!=","<","<=",">",">=","IN","NOT_IN"):
            r = engine([constraint(operator=op,value=[10,20] if op in ("IN","NOT_IN") else 10)]).audit()
            self.assertEqual(r["status"],"VERIFIED")
        r = engine([constraint("max",value=10,operator="<"),constraint("min",value=10,operator=">=")]).audit()
        self.assertTrue(r["conflicts"])

    def test_preserve_remove_conflict(self):
        cs = [constraint("keep",type="EXISTING_OBJECT_PRESERVE",value="EXISTING_OBJECT",unit="none",operator="PRESERVE",scope=["OBJECT:existing-building"]),
              constraint("remove",type="EXISTING_OBJECT_REMOVE_REQUIRED",value="EXISTING_OBJECT",unit="none",operator="REQUIRE",scope=["OBJECT:existing-building"])]
        self.assertTrue(engine(cs).audit()["conflicts"])

    def test_global_material_constraint_overlaps_building(self):
        c = material("ban",True); c["scope"] = ["BUILDING"]
        self.assertTrue(engine([material(),c]).audit()["conflicts"])

    def test_all_material_input_changes_invalidate(self):
        changes = {"value":14000000,"unit":"count","operator":">=","scope":["SITE"],"binding":False,"supersedes":[]}
        for field,v in changes.items():
            e = engine(); e.audit(); c = constraint(); c[field] = v
            e.update_source(source([c])); self.assertEqual(e.result()["status"],"INVALIDATED")

    def test_missing_answer_reaudit_verified(self):
        c = constraint(); del c["value"]
        e = engine([c]); self.assertEqual(e.audit()["status"],"BLOCKED")
        e.update_source(source([constraint()])); self.assertEqual(e.audit()["status"],"VERIFIED"); e.require_verified()

    def test_equipment_hard_requirement_conflict(self):
        c = constraint(type="EQUIPMENT_PROHIBITED",value="user specified desk",unit="none",operator="PROHIBIT",scope=["SPACE:bedroom_master"])
        self.assertTrue(engine([c]).audit()["conflicts"])

    def test_invalid_records_fail_closed(self):
        for fields in ({"value":True},{"unit":[]},{"type":{}},{"supersedes":[{"claimId":[],"evidenceFingerprint":"x"}]},{"scope":[{}]}):
            c = constraint(); c.update(fields)
            self.assertEqual(engine([c]).audit()["status"],"BLOCKED")

    def test_missing_budget_one_precise_question(self):
        c = constraint(); del c["value"]
        r = engine([c]).audit(); self.assertEqual(len(r["questions"]),1)
        self.assertEqual(r["questions"][0]["inputId"],"budget:value")
        self.assertTrue({"WHAT","WHY","REQUIRED_BY","FORMAT","provenance"} <= r["questions"][0].keys())

    def test_no_upstream_mutation(self):
        us = upstream(); before = [x.result() for x in us]
        engine([floor(),location(),constraint()],deps=us).audit()
        self.assertEqual(before,[x.result() for x in us])

    def test_count_conflict_and_integer_open_interval(self):
        r = engine([constraint("two",type="FLOOR_COUNT_FIXED",value=2,unit="count",operator="=="),constraint("three",type="FLOOR_COUNT_FIXED",value=3,unit="count",operator="==")]).audit()
        self.assertTrue(r["conflicts"])

    def test_mixed_units_no_silent_conversion(self):
        r = engine([constraint("m",type="DIMENSION_LIMIT",unit="m",value=12,subject="WIDTH"),constraint("mm",type="DIMENSION_LIMIT",unit="mm",value=12000,subject="WIDTH")]).audit()
        self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["validationErrors"])

    def test_stale_supersession_blocked(self):
        c = constraint("new"); c["supersedes"] = [dict(claimId="client:budget",evidenceFingerprint="old")]
        r = engine(sources=[source([constraint()]),source([c],id="correction",category="APPROVED_PROJECT_DECISION")]).audit()
        self.assertEqual(r["status"],"BLOCKED")

    def test_material_revision_no_precedence(self):
        s = source([material("other",True)],id="other"); s["revision"] = "v99"
        self.assertTrue(engine(sources=[source([material()]),s]).audit()["conflicts"])

    def test_result_copy_cannot_forge_gate(self):
        e = engine([constraint(unit="bad")]); r = e.audit(); r.update(status="VERIFIED",canProgress=True)
        with self.assertRaises(RuntimeError): e.planning_constraints()


if __name__ == "__main__": unittest.main()
