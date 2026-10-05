from copy import deepcopy
import unittest

from constraint_compilation import ConstraintCompilation, validate_graph, compilation_fingerprint
from normative_bundle import ProjectNormativeBundle, GlobalRuleLibrary
from project_constraints import ProjectConstraintInput
from tests.test_project_constraints import upstream as prior, source, constraint, material
from tests.test_normative_bundle import library_data, rule, requirement, scope, seal
from tests.test_site_context import site_source, geometry
from tests.test_functional_program import simple_brief
from tests.test_design_intent import intent_source, goal


def domains():
    names = "GEOMETRY AREA DIMENSION COUNT LOCATION ADJACENCY ACCESS ORIENTATION MATERIAL STRUCTURE FIRE DAYLIGHT THERMAL SITE PARKING EQUIPMENT CUSTOM".split()
    project = {
        "BUDGET_LIMIT":("CUSTOM","CLIENT_BUDGET"),"AREA_LIMIT":("AREA","{subject}"),"DIMENSION_LIMIT":("DIMENSION","{subject}"),
        "FLOOR_COUNT_FIXED":("COUNT","FLOOR_COUNT"),"HEIGHT_LIMIT_PROJECT":("DIMENSION","BUILDING_HEIGHT"),
        "MATERIAL_REQUIRED":("MATERIAL","MATERIAL"),"MATERIAL_PROHIBITED":("MATERIAL","MATERIAL"),
        "CONSTRUCTION_SYSTEM_REQUIRED":("STRUCTURE","CONSTRUCTION_SYSTEM"),"CONSTRUCTION_SYSTEM_PROHIBITED":("STRUCTURE","CONSTRUCTION_SYSTEM"),
        "EXISTING_OBJECT_PRESERVE":("SITE","OBJECT:{scopeId}"),"EXISTING_OBJECT_REMOVE_REQUIRED":("SITE","OBJECT:{scopeId}"),
        "SITE_ZONE_REQUIRED":("SITE","ZONE:{scopeId}"),"SITE_ZONE_PROHIBITED":("SITE","ZONE:{scopeId}"),
        "ACCESS_REQUIRED":("ACCESS","ACCESS"),"ORIENTATION_REQUIRED":("ORIENTATION","BUILDING_ORIENTATION"),
        "SPACE_LOCATION_REQUIRED":("LOCATION","SPACE_LOCATION:{scopeId}"),"SPACE_LOCATION_PROHIBITED":("LOCATION","SPACE_LOCATION:{scopeId}"),
        "CAPACITY_FIXED":("COUNT","{subject}"),"PARKING_COUNT_FIXED":("PARKING","PARKING_COUNT"),
        "PHASING_REQUIRED":("CUSTOM","PHASING"),"UTILITY_CONNECTION_FIXED":("EQUIPMENT","UTILITY:{scopeId}"),
        "EQUIPMENT_REQUIRED":("EQUIPMENT","EQUIPMENT"),"EQUIPMENT_PROHIBITED":("EQUIPMENT","EQUIPMENT"),
        "DEMOLITION_LIMIT":("SITE","{subject}"),"CUSTOM":("CUSTOM","{subject}")}
    fields = {"quantity":("COUNT","SPACE_QUANTITY:{scopeId}","count"),"requestedArea":("AREA","SPACE_AREA:{scopeId}","m2"),
        "function":("CUSTOM","SPACE_FUNCTION:{scopeId}","none"),"preferredFloor":("LOCATION","SPACE_LOCATION:{scopeId}","none"),
        "specialEquipment":("EQUIPMENT","EQUIPMENT","none"),"EXISTENCE":("LOCATION","SPACE_EXISTS:{scopeId}","none"),
        "RELATIONSHIP":("ADJACENCY","RELATIONSHIP","none"),"USER_quantity":("COUNT","USER_COUNT:{subject}","count"),"USER_label":("CUSTOM","USER_LABEL:{subject}","none")}
    for f in ("accessLevel","privacyLevel","noiseSensitivity","noiseGeneration","daylightPreference","functionalZone"):
        fields[f] = ("CUSTOM",f.upper()+":{scopeId}","none")
    return dict(id="synthetic-compilation-domains",revision="1",status="VERIFIED",domains={n:"MEMBERSHIP" if n == "EQUIPMENT" else "SINGLE_VALUE" for n in names},
        projectTypes={k:dict(domain=d,subjectTemplate=s,unit="PRESERVE_SOURCE") for k,(d,s) in project.items()},
        functionalFields={k:dict(domain=d,subjectTemplate=s,unit=u) for k,(d,s,u) in fields.items()},
        normativeDomainAliases={"SYNTHETIC_TEST_DOMAIN":"GEOMETRY"},
        subjectAliases={"DIMENSION":{"WIDTH":"BUILDING_WIDTH","DEPTH":"BUILDING_DEPTH"},"AREA":{"REQUESTED_AREA":"SPACE_AREA:{scopeId}"},"COUNT":{"SPACE_QUANTITY":"SPACE_QUANTITY:{scopeId}"}},
        subjectReferences={"SPACE_AREA:":"SPACE","SPACE_LOCATION:":"SPACE","SPACE_EXISTS:":"SPACE","SPACE_QUANTITY:":"SPACE","OBJECT:":"OBJECT"})


def references():
    return dict(id="synthetic-scope-overlap",revision="1",status="VERIFIED",overlaps={"PROJECT":["BUILDING","FLOOR","SPACE","SITE","OBJECT","ZONE","SYSTEM"],"BUILDING":["FLOOR","SPACE"],"SITE":["OBJECT","ZONE"]})


def dependencies(project=None,norm=None):
    us = prior(); pc = ProjectConstraintInput(*us,[source([constraint()] if project is None else project)]); pc.audit()
    data = library_data()
    if norm is not None: data["rules"]["IZHS/GENERAL"] = [norm]
    bundle = ProjectNormativeBundle(*us,pc,GlobalRuleLibrary(data),scope()); bundle.audit()
    return (*us,pc,bundle)


def norm(domain="DIMENSION",subject="BUILDING_WIDTH",value=17,op="gte",unit="synthetic-unit",scope=None):
    r = requirement(value,op,domain); r["subject"] = subject; r["unit"] = unit; r["scope"] = scope or ["BUILDING"]
    return rule(requirement=r)


def width(value=20,op="<=",unit="synthetic-unit",scope=None,binding=True,subject="WIDTH"):
    # Project input's strict physical units stay explicit; synthetic rules use the same supplied unit.
    return constraint("width",type="DIMENSION_LIMIT",value=value,unit="mm" if unit == "synthetic-unit" else unit,operator=op,scope=scope or ["BUILDING"],binding=binding,subject=subject)


def engine(project=None,normative=None,us=None,d=None,r=None):
    return ConstraintCompilation(*(us or dependencies(project,normative)),d or domains(),r or references())


class RequiredScenarios(unittest.TestCase):
    def blocked_upstream(self,index):
        us = dependencies(); us[index]._result["status"] = "INVALIDATED"
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")
    def test_01_stage0_not_verified(self): self.blocked_upstream(0)
    def test_02_functional_not_verified(self): self.blocked_upstream(1)
    def test_03_intent_not_verified(self): self.blocked_upstream(2)
    def test_04_site_not_verified(self): self.blocked_upstream(3)
    def test_05_project_constraints_not_verified(self): self.blocked_upstream(4)
    def test_06_normative_bundle_not_verified(self): self.blocked_upstream(5)

    def test_07_binding_is_mandatory(self):
        r = engine().audit(); self.assertEqual(r["status"],"VERIFIED",r["validationErrors"])
        self.assertTrue(any(c["originType"] == "PROJECT_HARD_CONSTRAINT" for c in r["mandatoryConstraints"]))
    def test_08_nonbinding_not_promoted(self):
        r = engine([constraint(binding=False)]).audit(); self.assertTrue(any(c["originType"] == "PROJECT_NON_BINDING_CONSTRAINT" for c in r["preferences"]))
    def test_09_normative_mandatory(self):
        self.assertTrue(any(c["originType"] == "NORMATIVE_REQUIREMENT" for c in engine().audit()["mandatoryConstraints"]))
    def test_10_intent_preference(self):
        r = engine().audit(); self.assertTrue(any(c["originType"] == "DESIGN_PREFERENCE" for c in r["preferences"]))
    def test_11_site_informational(self):
        self.assertTrue(all(c["strength"] == "INFORMATIONAL" for c in engine().audit()["siteFacts"]))
    def test_12_tree_not_automatically_preserved(self):
        us = prior(); s = site_source(); s["statements"].append(dict(id="tree",kind="OBJECT",objectId="tree",type="TREE",geometry=geometry()))
        us[3].update_source(s); us[3].audit(); pc = ProjectConstraintInput(*us,[]); pc.audit()
        b = ProjectNormativeBundle(*us,pc,GlobalRuleLibrary(library_data()),scope()); b.audit()
        r = engine(us=(*us,pc,b)).audit(); self.assertTrue(any(f["subject"] == "OBJECT:tree" for f in r["siteFacts"]))
        self.assertFalse(any(c["operator"] == "preserve" for c in r["mandatoryConstraints"]))
    def test_13_compatible_lower_bounds(self):
        r = engine([width(11,">=")],norm(value=10,unit="mm")).audit()
        e = next(x for x in r["effectiveConstraints"] if x["subject"] == "BUILDING_WIDTH")
        self.assertEqual(e["lowerBound"]["value"],11); self.assertEqual(len(e["sourceConstraints"]),2)
    def test_14_interval(self):
        r = engine([width(20)],norm(value=10,unit="mm")).audit(); self.assertEqual(r["status"],"VERIFIED")
        e = next(x for x in r["effectiveConstraints"] if x["subject"] == "BUILDING_WIDTH")
        self.assertEqual((e["lowerBound"]["value"],e["upperBound"]["value"]),(10,20))
    def test_15_numeric_conflict(self):
        r = engine([width(9)],norm(value=10,unit="mm")).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["conflicts"])
    def test_16_equality_conflict(self):
        r = engine([width(2,"==")],norm(value=3,op="eq",unit="mm")).audit(); self.assertTrue(r["conflicts"])
    def test_17_require_prohibit(self):
        r = engine([material()],norm("MATERIAL","MATERIAL","CERAMIC_BLOCK","neq","none")).audit(); self.assertTrue(r["conflicts"])
    def test_18_categorical_compatible(self):
        r = engine([material()],norm("MATERIAL","MATERIAL","CERAMIC_BLOCK","eq","none")).audit(); self.assertEqual(r["status"],"VERIFIED")
    def test_19_empty_allowed_set(self):
        c = material(); c.update(value=["A","B"],operator="IN")
        r = engine([c],norm("MATERIAL","MATERIAL",["A","B"],"not_in","none")).audit(); self.assertTrue(r["conflicts"])
    def test_20_distinct_subjects(self):
        r = engine([width(2,subject="DEPTH")],norm(value=3,unit="mm")).audit(); self.assertEqual(r["status"],"VERIFIED")
    def test_21_unrelated_spaces(self):
        r = engine([],norm("AREA","SPACE_AREA:kitchen",10,"lte","m2",["SPACE:living"])).audit()
        self.assertEqual(r["status"],"VERIFIED")
    def test_22_project_overlaps_building(self):
        r = engine([width(2,scope=["PROJECT"])],norm(value=3,unit="mm")).audit(); self.assertTrue(r["conflicts"])
    def test_23_separate_spaces_separate_scopes(self):
        r = engine([width(2,scope=["SPACE:kitchen"])],norm(value=3,unit="mm",scope=["SPACE:bedroom_master"])).audit(); self.assertEqual(r["status"],"VERIFIED")
    def test_24_dangling_space(self):
        r = engine([],norm(scope=["SPACE:phantom"])).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["unresolvedReferences"])
    def test_25_dangling_object(self):
        self.assertEqual(engine([],norm(scope=["OBJECT:phantom"])).audit()["status"],"BLOCKED")
    def test_26_project_provenance(self):
        us = dependencies(); r = engine(us=us).audit(); c = next(c for c in r["mandatoryConstraints"] if c["originType"] == "PROJECT_HARD_CONSTRAINT")
        self.assertEqual(c["provenance"],us[4].result()["constraints"][0]["provenance"])
    def test_27_normative_id_revision(self):
        c = next(c for c in engine().audit()["mandatoryConstraints"] if c["originType"] == "NORMATIVE_REQUIREMENT")
        self.assertEqual((c["sourceRefs"][0]["originalId"],c["sourceRefs"][0]["exactRevision"]),("TEST_RULE_A","1"))
    def test_28_normative_provenance(self):
        us = dependencies(); c = next(c for c in engine(us=us).audit()["mandatoryConstraints"] if c["originType"] == "NORMATIVE_REQUIREMENT")
        self.assertEqual(c["provenance"],us[5].result()["compiledRules"][0]["provenance"])
    def test_29_applicability_preserved(self):
        us = dependencies(); c = next(c for c in engine(us=us).audit()["mandatoryConstraints"] if c["originType"] == "NORMATIVE_REQUIREMENT")
        self.assertEqual(c["applicabilityBasis"],us[5].result()["compiledRules"][0]["applicabilityBasis"])
    def test_30_project_inputs_preserved(self):
        us = dependencies(); c = next(c for c in engine(us=us).audit()["mandatoryConstraints"] if c["originType"] == "NORMATIVE_REQUIREMENT")
        self.assertEqual(c["projectInputsUsed"],us[5].result()["compiledRules"][0]["projectInputsUsed"])
    def test_31_merge_retains_raw(self):
        r = engine([width(11,">=")],norm(value=10,unit="mm")).audit(); self.assertEqual(len([c for c in r["mandatoryConstraints"] if c["subject"] == "BUILDING_WIDTH"]),2)
    def test_32_reverse_traceability(self):
        r = engine().audit(); ids = r["traceabilityIndex"]["byOrigin"]["NORMATIVE_REQUIREMENT:TEST_RULE_A@1"]
        self.assertEqual(r["traceabilityIndex"]["byCompiledConstraintId"][ids[0]][0]["originalId"],"TEST_RULE_A")
    def test_33_graph_source_compiled(self):
        graph = engine().audit()["dependencyGraph"]; self.assertTrue(any(e["type"] == "SUPPORTS" for e in graph["edges"]))
    def test_34_derivation_cycle_rejected(self):
        graph = dict(nodes=[dict(nodeId="a"),dict(nodeId="b")],edges=[dict(fromId="a",toId="b",type="DERIVED_FROM"),dict(fromId="b",toId="a",type="DERIVED_FROM")])
        with self.assertRaisesRegex(ValueError,"cycle"): validate_graph(graph)
    def test_35_operator_tampering_blocked(self):
        us = dependencies(); us[4]._result["constraints"][0]["operator"] = "unsupported"
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")
    def test_36_eval_rejected(self):
        us = dependencies(); us[4]._result["constraints"][0].update(operator="eval",value="__import__('os')")
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")
    def test_37_incompatible_units(self):
        r = engine([width(1,unit="m")],norm(value=1000,unit="mm")).audit(); self.assertTrue(r["unitIssues"]); self.assertEqual(r["status"],"BLOCKED")
    def test_38_no_silent_conversion(self):
        r = engine([width(1,unit="m")],norm(value=1000,unit="mm")).audit(); self.assertEqual(r["unitIssues"][0]["status"],"UNIT_RECONCILIATION_REQUIRED")
    def test_39_conversion_not_implemented(self):
        d = domains(); d["conversions"] = [dict(conversionId="m-to-mm",factor=1000,status="VERIFIED")]
        self.assertEqual(engine(d=d).audit()["status"],"BLOCKED")
    def test_40_deterministic(self):
        e = engine(); r = e.audit(); self.assertEqual(r,e.audit()); self.assertEqual(r["constraintCompilationFingerprint"],compilation_fingerprint(r))
    def test_41_upstream_change_invalidates(self):
        us = dependencies(); e = engine(us=us); e.audit(); b = simple_brief(); b["revision"] = "2"; us[1].update_source(b)
        self.assertEqual(e.result()["status"],"INVALIDATED")
    def test_42_bundle_change_invalidates(self):
        us = dependencies(); e = engine(us=us); e.audit(); sc = scope(); sc["optionalNormativeDomains"] = ["ROOF"]; us[5].update_scope(sc)
        self.assertEqual(e.result()["status"],"INVALIDATED")
    def test_43_project_change_invalidates(self):
        us = dependencies(); e = engine(us=us); e.audit(); us[4].update_source(source([constraint(value=14000000)]))
        self.assertEqual(e.result()["status"],"INVALIDATED")
    def test_44_preference_override(self):
        r = engine([width(9,binding=False)],norm(value=10,unit="mm")).audit(); self.assertEqual(r["status"],"VERIFIED"); self.assertTrue(r["overrides"])
    def test_45_hard_project_norm_blocks(self):
        e = engine([width(9)],norm(value=10,unit="mm")); r = e.audit(); self.assertEqual(r["status"],"BLOCKED")
        with self.assertRaises(RuntimeError): e.planning_input()
    def test_46_functional_hard_conflict(self):
        r = engine([],norm("AREA","SPACE_AREA:kitchen",10,"lte","m2",["SPACE:kitchen"])).audit(); self.assertTrue(r["conflicts"])
    def test_47_optional_preference_no_block(self):
        r = engine([constraint(binding=False)]).audit(); self.assertEqual(r["status"],"VERIFIED")
    def test_48_no_compliance_result(self):
        self.assertFalse({"compliance","actual","compliant"} & engine().audit().keys())
    def test_49_no_layout(self): self.assertNotIn("layout",engine().audit())
    def test_50_no_geometry_generation(self):
        self.assertFalse({"generatedRooms","generatedWalls","generatedGeometry"} & engine().audit().keys())
    def test_51_no_archicad(self): self.assertNotIn("archicadOperations",engine().audit())
    def test_52_no_global_library_reads(self):
        us = dependencies()
        us[5]._library.data = lambda: (_ for _ in ()).throw(AssertionError("global library read"))
        self.assertEqual(engine(us=us).audit()["status"],"VERIFIED")
    def test_53_no_normative_injection(self):
        us = dependencies(); us[5]._result["compiledRules"].append(deepcopy(us[5]._result["compiledRules"][0]))
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")
    def test_54_no_project_injection(self):
        us = dependencies(); us[4]._result["constraints"].append(deepcopy(us[4]._result["constraints"][0]))
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")
    def test_55_planning_only_verified_content(self):
        e = engine(); r = e.audit(); self.assertEqual(e.planning_input()["mandatoryConstraints"],r["mandatoryConstraints"])
    def test_56_planning_fingerprint(self):
        e = engine(); r = e.audit(); self.assertEqual(e.planning_input()["sourceCompilationFingerprint"],r["constraintCompilationFingerprint"])


class Robustness(unittest.TestCase):
    def test_upstream_and_registries_unchanged(self):
        us = dependencies(); before = [u.result() for u in us]; d,r = domains(),references(); originals = deepcopy([d,r])
        engine(us=us,d=d,r=r).audit(); self.assertEqual(before,[u.result() for u in us]); self.assertEqual([d,r],originals)
    def test_each_registry_change_invalidates(self):
        for which in ("domain_registry","reference_registry"):
            e = engine(); e.audit(); changed = domains() if which == "domain_registry" else references(); changed["revision"] = "2"
            e.update_registries(**{which:changed}); self.assertEqual(e.result()["status"],"INVALIDATED")
            with self.assertRaises(RuntimeError): e.planning_input()
            self.assertEqual(e.audit()["status"],"VERIFIED")
    def test_subject_reference_checked(self):
        r = engine([],norm("AREA","SPACE_AREA:phantom",10,"gte","m2")).audit()
        self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["unresolvedReferences"])
    def test_set_location_references_checked(self):
        r = engine([],norm("LOCATION","TEST_LOCATION",["FLOOR:phantom"],"in","none")).audit()
        self.assertEqual(r["status"],"BLOCKED")
    def test_no_implicit_floor_from_count(self):
        self.assertEqual(engine([],norm(scope=["FLOOR:1"])).audit()["status"],"BLOCKED")
    def test_missing_adapter_fails_closed(self):
        d = domains(); del d["functionalFields"]["EXISTENCE"]
        self.assertEqual(engine(d=d).audit()["status"],"BLOCKED")
    def test_membership_multiple_equipment_requirements(self):
        p = constraint(type="EQUIPMENT_REQUIRED",value="confirmed pump",unit="none",operator="REQUIRE")
        r = engine([p]).audit(); self.assertEqual(r["status"],"VERIFIED")
    def test_ordered_phasing_preserved(self):
        p = constraint(type="PHASING_REQUIRED",value=["service","house"],unit="none",operator="REQUIRE")
        r = engine([p]).audit(); self.assertEqual(r["status"],"VERIFIED")
        self.assertEqual(next(c for c in r["mandatoryConstraints"] if c["originType"] == "PROJECT_HARD_CONSTRAINT")["value"],["service","house"])
    def test_blocked_planning_packet_withheld(self):
        r = engine([width(9)],norm(value=10,unit="mm")).audit()
        self.assertEqual(r["planningInput"]["status"],"WITHHELD"); self.assertNotIn("mandatoryConstraints",r["planningInput"])
    def test_copy_cannot_forge_planning_gate(self):
        e = engine([width(9)],norm(value=10,unit="mm")); fake = e.audit(); fake.update(status="VERIFIED",canProgress=True)
        with self.assertRaises(RuntimeError): e.planning_input()
    def test_trace_lookup_original_id(self):
        e = engine(); r = e.audit(); ids = e.lookup_origin("PROJECT_HARD_CONSTRAINT","budget")
        self.assertEqual(len(ids),1); self.assertIn(ids[0],r["traceabilityIndex"]["byCompiledConstraintId"])


if __name__ == "__main__": unittest.main()
