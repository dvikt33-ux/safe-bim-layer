from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from design_stage0 import Stage0
from functional_program import FunctionalProgram, FLOW, RELATION_TYPES
from tests.test_design_stage0 import registry, complete, source


def stage0(verified=True):
    engine = Stage0(registry(), [complete()] if verified else [])
    engine.audit()
    return engine


def brief(statements=None, text=None, id="program", kind="USER_BRIEF"):
    value = dict(id=id, kind=kind, revision="v1", approved=True, inspected=True)
    if statements is not None:
        value["statements"] = statements
    if text is not None:
        value["text"] = text
    return value


def space(id, function, quantity=1, **fields):
    return dict(id=id + "-intent", kind="SPACE", spaceId=id, function=function, quantity=quantity, **fields)


def simple_brief():
    return brief([space("bedroom_master", "спальня", requestedArea={"value": 18, "unit": "m2"},
                        functionalZone="private", accessLevel="FAMILY", privacyLevel="PRIVATE",
                        noiseSensitivity="HIGH", noiseGeneration="LOW", specialEquipment=["user specified desk"],
                        daylightPreference="morning daylight", preferredFloor="upper"),
                  space("kitchen", "KITCHEN", requestedArea={"min": 12, "max": 16, "unit": "m2"}, functionalZone="service"),
                  space("living", "LIVING_ROOM", functionalZone="public"),
                  space("hall", "HALL", functionalZone="circulation"),
                  dict(id="family", kind="USER_GROUP", userId="family", label="family", quantity=4)])


def engine(sources=None, dependency=None):
    return FunctionalProgram(dependency or stage0(), sources or [simple_brief()])


class RequiredScenarios(unittest.TestCase):
    def test_01_stage0_not_verified_blocked(self):
        program = engine(dependency=stage0(False))
        result = program.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["spaces"], [])
        self.assertEqual(result["questions"], [])
        with self.assertRaises(RuntimeError):
            program.require_verified()

    def test_02_simple_brief_becomes_spaces(self):
        result = engine([brief(text="Дом для семьи из 4 человек, два этажа.\n2 спальни по 18 м2.\n1 кухня 12 м2.\n1 гостиная 25 м2.")]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["flow"], FLOW + ["FUNCTIONAL_PROGRAM VERIFIED"])
        self.assertEqual({x["function"]: x["quantity"] for x in result["spaces"]},
                         {"BEDROOM": 2, "KITCHEN": 1, "LIVING_ROOM": 1})
        self.assertEqual(result["users"][0]["quantity"]["value"], 4)
        self.assertEqual(result["stage0Context"]["floor_count"]["value"], 2)

    def test_03_explicit_area_remains_user_requirement(self):
        result = engine().audit()
        room = next(x for x in result["spaces"] if x["spaceId"] == "bedroom_master")
        self.assertEqual(room["requestedArea"]["value"], 18)
        self.assertEqual(room["requestedArea"]["source"], "USER_REQUIREMENT")
        self.assertEqual(room["requestedArea"]["unit"], "m2")

    def test_04_user_preference_remains_preference(self):
        result = engine().audit()
        room = next(x for x in result["spaces"] if x["spaceId"] == "bedroom_master")
        self.assertEqual(room["daylightPreference"]["source"], "USER_PREFERENCE")
        self.assertEqual(room["preferredFloor"]["source"], "USER_PREFERENCE")
        self.assertFalse(any(x.get("field") in ("preferredFloor", "daylightPreference") for x in result["userRequirements"]))
        self.assertTrue(any(x.get("field") == "daylightPreference" for x in result["userPreferences"]))

    def test_05_normative_minimum_pending(self):
        result = engine().audit()
        self.assertTrue(all(x["normativeMinimum"]["status"] == "NORMATIVE_REQUIREMENT_PENDING" for x in result["spaces"]))
        self.assertEqual(len(result["normativeRequirementsPending"]), len(result["spaces"]))
        self.assertEqual(result["status"], "VERIFIED")

    def test_06_no_invented_normative_number(self):
        result = engine([brief([space("bedroom", "BEDROOM")])]).audit()
        self.assertIsNone(result["spaces"][0]["requestedArea"])
        self.assertNotIn("value", result["spaces"][0]["normativeMinimum"])
        self.assertFalse(any("value" in x or "min" in x or "max" in x for x in result["normativeRequirementsPending"]))
        self.assertEqual(result["gateProof"]["inventedNormativeValuesCount"], 0)

    def test_07_explicit_required_adjacency_retained(self):
        b = simple_brief()
        b["statements"].append(dict(id="kitchen-living", kind="RELATIONSHIP", type="REQUIRED_ADJACENCY", **{"from":"kitchen", "to":"living"}))
        result = engine([b]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        relation = result["relationships"][0]
        self.assertEqual(relation["type"], "REQUIRED_ADJACENCY")
        self.assertEqual(relation["category"], "USER_REQUIREMENT")
        self.assertEqual(relation["provenance"][0]["statementId"], "kitchen-living")

    def test_08_derived_relationship_has_traceable_rule(self):
        b = simple_brief()
        b["statements"].append(dict(id="shared-hall", kind="ACCESS_GROUP", via="hall", members=["bedroom_master", "kitchen"]))
        result = engine([b]).audit()
        self.assertEqual(len(result["derivedRelationships"]), 2)
        for rel in result["derivedRelationships"]:
            self.assertEqual(rel["category"], "DERIVED_RELATIONSHIP")
            self.assertEqual(rel["derivationRule"], "EXPLICIT_ACCESS_GROUP_EXPANSION_V1")
            self.assertEqual(rel["provenance"][0]["inputEvidence"][0]["statementId"], "shared-hall")

    def test_09_conflicting_user_requirements_block_verified(self):
        conflicting = brief([dict(id="other-area", kind="SPACE_ATTRIBUTE", spaceId="bedroom_master", field="requestedArea", value={"value": 20, "unit": "m2"})], id="other")
        program = engine([simple_brief(), conflicting])
        result = program.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["conflicts"][0]["field"], "requestedArea")
        with self.assertRaises(RuntimeError):
            program.require_verified()

    def test_10_missing_functional_datum_minimal_questions(self):
        b = simple_brief()
        del b["statements"][0]["quantity"]
        result = engine([b]).audit()
        self.assertEqual(result["status"], "WAITING_FOR_USER_DATA")
        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(result["questions"][0]["inputId"], "space:bedroom_master:quantity")
        for key in ("WHAT", "WHY", "REQUIRED_BY", "FORMAT", "provenance"):
            self.assertTrue(result["questions"][0][key])

    def test_11_answer_reaudit_verified(self):
        b = simple_brief()
        del b["statements"][0]["quantity"]
        program = engine([b])
        program.audit()
        program.update_source(brief([dict(id="answer-quantity", kind="SPACE_ATTRIBUTE", spaceId="bedroom_master", field="quantity", value=1)], id="answer", kind="USER_CORRECTION"))
        self.assertEqual(program.result()["status"], "INVALIDATED")
        with self.assertRaises(RuntimeError):
            program.require_verified()
        self.assertEqual(program.audit()["status"], "VERIFIED")
        self.assertTrue(program.require_verified()["provenanceComplete"])

    def test_12_material_stage0_change_invalidates(self):
        dependency = stage0()
        program = engine(dependency=dependency)
        old = program.audit()
        dependency.update_source(source(purpose="IZHS", municipality="changed-city", floor_count=2))
        self.assertEqual(program.result()["status"], "INVALIDATED")
        with self.assertRaises(RuntimeError):
            program.require_verified()
        self.assertEqual(program.audit()["status"], "INVALIDATED")
        dependency.audit()
        self.assertEqual(program.result()["status"], "INVALIDATED")
        new = program.audit()
        self.assertEqual(new["status"], "VERIFIED")
        self.assertNotEqual(old["stage0Fingerprint"], new["stage0Fingerprint"])

    def test_13_identical_input_identical_deterministic_program(self):
        b = simple_brief()
        first = engine([b]).audit()
        second = engine([deepcopy(b)]).audit()
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(first["programFingerprint"], second["programFingerprint"])
        b["statements"].reverse()
        reordered = engine([b]).audit()
        for key in ("spaces", "relationships", "userRequirements", "userPreferences", "functionalZones"):
            self.assertEqual(first[key], reordered[key])

    def test_14_no_unrelated_functions_added(self):
        result = engine([brief([space("bedroom", "BEDROOM")])]).audit()
        self.assertEqual([x["function"] for x in result["spaces"]], ["BEDROOM"])
        self.assertEqual(result["relationships"], [])
        self.assertEqual(result["functionalZones"], [])
        minimal = engine([brief(text="Дом для семьи из 4 человек, два этажа.")]).audit()
        self.assertEqual(minimal["spaces"], [])
        self.assertEqual([x["inputId"] for x in minimal["questions"]], ["programScope"])

    def test_15_full_provenance_coverage_for_confirmed_program(self):
        result = engine().audit()
        self.assertEqual(result["gateProof"]["provenanceCoverage"], 1.0)
        self.assertTrue(result["provenanceComplete"])
        for rec in result["userRequirements"] + result["userPreferences"] + result["spaces"]:
            self.assertTrue(rec["provenance"])
        self.assertTrue(all(x["identityRequirements"]["function"]["provenance"] and
                            x["identityRequirements"]["quantity"]["provenance"] for x in result["spaces"]))


class BoundaryTests(unittest.TestCase):
    def test_conflict_question_answer_reaudit(self):
        first = simple_brief()
        other = brief([dict(id="other-area",kind="SPACE_ATTRIBUTE",spaceId="bedroom_master",field="requestedArea",value={"value":20,"unit":"m2"})],id="other")
        program = engine([first,other])
        blocked = program.audit()
        self.assertEqual(len(blocked["questions"]),1)
        self.assertIn("requestedArea",blocked["questions"][0]["WHAT"])
        correction = brief([dict(id="resolved-area",kind="SPACE_ATTRIBUTE",spaceId="bedroom_master",field="requestedArea",value={"value":20,"unit":"m2"},
            supersedes=["program:bedroom_master-intent:requestedArea","other:other-area:requestedArea"])],id="answer",kind="USER_CORRECTION")
        program.update_source(correction)
        verified = program.audit()
        self.assertEqual(verified["status"],"VERIFIED")
        self.assertEqual(verified["conflicts"],[])
        self.assertEqual(verified["questions"],[])

    def test_file_to_file_answer_reaudit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reg, sources, bpath, answers, output = [root / x for x in ("registry.json", "sources.json", "brief.json", "answers.json", "output.json")]
            b = simple_brief()
            del b["statements"][0]["quantity"]
            correction = brief([dict(id="answer-quantity", kind="SPACE_ATTRIBUTE", spaceId="bedroom_master", field="quantity", value=1)], id="answer", kind="USER_CORRECTION")
            for path, value in ((reg,registry()),(sources,[complete()]),(bpath,[b]),(answers,[correction])):
                path.write_text(json.dumps(value), encoding="utf-8")
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / "functional_program.py"), "--stage0-registry",str(reg),"--stage0-sources",str(sources),"--brief",str(bpath),"--output",str(output)]
            process = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(process.returncode, 2, process.stderr)
            self.assertEqual(json.loads(output.read_text())["status"], "WAITING_FOR_USER_DATA")
            process = subprocess.run(cmd + ["--answers",str(answers)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(output.read_text())["status"], "VERIFIED")

    def test_normative_or_geometry_payload_rejected(self):
        for field in ("normativeMinimum", "setback", "coordinates", "walls"):
            b = simple_brief()
            b["statements"][0][field] = 9
            result = engine([b]).audit()
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["validationErrors"])
            self.assertFalse(result["canProgress"])

    def test_preferences_do_not_conflict_with_mandatory_user_area(self):
        b = simple_brief()
        b["statements"].append(dict(id="ideal-area", kind="SPACE_ATTRIBUTE", spaceId="bedroom_master", field="requestedArea", value={"value": 20, "unit": "m2"}, category="USER_PREFERENCE"))
        result = engine([b]).audit()
        room = next(x for x in result["spaces"] if x["spaceId"] == "bedroom_master")
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(room["requestedArea"]["value"], 18)
        self.assertEqual(room["preferences"]["requestedArea"]["value"], 20)

    def test_conflicting_adjacency_blocked(self):
        b = simple_brief()
        for type in ("REQUIRED_ADJACENCY", "AVOID_ADJACENCY"):
            b["statements"].append(dict(id=type.lower(), kind="RELATIONSHIP", type=type, **{"from":"kitchen", "to":"living"}))
        self.assertEqual(engine([b]).audit()["status"], "BLOCKED")

    def test_all_relationship_types_and_explicit_zones_supported(self):
        b = brief([space("a", "CUSTOM_A", functionalZone="staff"), space("b", "CUSTOM_B", functionalZone="outdoor/site-related")])
        for type in sorted(RELATION_TYPES - {"AVOID_ADJACENCY", "SEPARATION_REQUIRED"}):
            b["statements"].append(dict(id=type.lower(), kind="RELATIONSHIP", type=type, **{"from":"a", "to":"EXTERIOR" if type == "EXTERNAL_ACCESS" else "b"}))
        result = engine([b]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual({x["zone"] for x in result["functionalZones"]}, {"staff", "outdoor/site-related"})
        for type in ("AVOID_ADJACENCY", "SEPARATION_REQUIRED"):
            one = brief([space("a", "CUSTOM_A"),space("b","CUSTOM_B"),dict(id="rel", kind="RELATIONSHIP",type=type,**{"from":"a","to":"b"})])
            self.assertEqual(engine([one]).audit()["status"], "VERIFIED")

    def test_unparsed_negative_statement_not_silently_added_or_dropped(self):
        result = engine([brief(text="1 спальня 18 м2.\nНе нужен гараж.")]).audit()
        self.assertEqual([x["function"] for x in result["spaces"]], ["BEDROOM"])
        self.assertEqual(result["status"], "WAITING_FOR_USER_DATA")
        self.assertEqual(len(result["questions"]), 1)

    def test_explicit_correction_with_field_supersession(self):
        b = simple_brief()
        correction = brief([dict(id="area-correction",kind="SPACE_ATTRIBUTE",spaceId="bedroom_master",field="requestedArea",value={"value":20,"unit":"m2"},supersedes=["program:bedroom_master-intent:requestedArea"])], id="answer",kind="USER_CORRECTION")
        result = engine([b,correction]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        room = next(x for x in result["spaces"] if x["spaceId"] == "bedroom_master")
        self.assertEqual(room["requestedArea"]["value"], 20)
        self.assertEqual(room["requestedArea"]["provenance"][0]["supersedes"], ["program:bedroom_master-intent:requestedArea"])

    def test_unapproved_sources_assumptions_and_result_forgery_blocked(self):
        b = simple_brief()
        b["approved"] = False
        e = engine([b])
        result = e.audit()
        self.assertEqual(result["status"], "BLOCKED")
        result.update(status="VERIFIED",canProgress=True)
        with self.assertRaises(RuntimeError):
            e.require_verified()
        b = simple_brief()
        b["statements"][0]["basis"] = "TYPICAL_VALUE"
        self.assertEqual(engine([b]).audit()["status"], "BLOCKED")

    def test_missing_endpoint_generates_precise_blocker(self):
        b = simple_brief()
        b["statements"].append(dict(id="unknown-room",kind="RELATIONSHIP",type="REQUIRED_ACCESS",**{"from":"hall","to":"unprovided_office"}))
        result = engine([b]).audit()
        self.assertEqual(result["status"], "WAITING_FOR_USER_DATA")
        self.assertIn("unprovided_office",result["questions"][0]["WHAT"])
        self.assertFalse(any(x["spaceId"] == "unprovided_office" for x in result["spaces"]))

    def test_user_brief_cannot_override_stage0_silently(self):
        b = simple_brief()
        b["statements"].append(dict(id="new-floors",kind="CONTEXT",inputId="floor_count",value=3))
        result = engine([b]).audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["conflicts"][0]["reason"], "user brief conflicts with VERIFIED Stage0")

    def test_explicit_exclusion_retained_and_conflict_checked(self):
        excluded = dict(id="no-garage",kind="EXCLUDE_FUNCTION",function="GARAGE",category="NOT_APPLICABLE",reason="client excludes a garage")
        b = simple_brief()
        b["statements"].append(excluded)
        result = engine([b]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["notApplicable"][0]["category"], "NOT_APPLICABLE")
        b["statements"].append(space("garage","GARAGE"))
        self.assertEqual(engine([b]).audit()["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
