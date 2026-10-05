from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from design_stage0 import Stage0, FLOW


def requirement(id, name, kind="string", unit=None, branches=None, blocking=True,
                priority="SITE_GEOMETRY_BLOCKER", **extra):
    return dict(id=id, name=name, type=kind, unit=unit, branches=branches or [],
                blocking=blocking, priority=priority, acceptedFormats=[kind],
                requiredBy=["STAGE_0/" + id], reason="Verified " + name + " is needed to resolve this dependency",
                sourceKinds=["USER_BRIEF", "PROJECT_FILE", "USER_CORRECTION"],
                owner="USER_CLIENT_SURVEYOR_MUST_PROVIDE", **extra)


def registry():
    # Synthetic routing registry, not a normative base or a universal questionnaire.
    result = {"id": "fixture-intake", "revision": "v1", "approved": True,
            "classificationInputs": ["purpose"],
            "branches": [dict(id=b, when={"input": "purpose", "equals": b}, blocking=True,
                              requiredBy=["STAGE_0/route"], reason="Select the supplied project branch")
                         for b in ("IZHS", "MKD", "INDUSTRIAL", "RETAIL")],
            "inputs": [requirement("purpose", "Project purpose", priority="CLASSIFICATION_BLOCKER"),
                       requirement("municipality", "Municipality and jurisdiction", branches=["IZHS"]),
                       requirement("floor_count", "Verified storey count", "integer", "count", ["IZHS"],
                                   minimum=1),
                       requirement("apartments", "Apartment schedule", "array", branches=["MKD"]),
                       requirement("process", "Industrial process", branches=["INDUSTRIAL"]),
                       requirement("customers", "Retail occupancy", "integer", "persons", ["RETAIL"])]}
    result["inputs"][0].update(reason="Select the project branch and exclude unrelated building classes",
        requiredBy=["STAGE_0/CLASSIFY", "STAGE_0/APPLICABILITY"], enum=["IZHS", "MKD", "INDUSTRIAL", "RETAIL"])
    result["inputs"][1].update(reason="Route the project to its jurisdiction; building geometry cannot establish municipality",
        requiredBy=["STAGE_0/APPLICABILITY/jurisdiction"], acceptedFormats=["municipality, region and country or approved site document"])
    result["inputs"][2].update(reason="Establish the storey classification from a verified inventory or explicit project brief",
        requiredBy=["STAGE_0/CLASSIFY/storeys"], acceptedFormats=["positive integer or verified storey inventory"])
    return result


def source(id="brief", **facts):
    return {"id": id, "kind": "USER_BRIEF", "revision": "v1", "inspected": True,
            "facts": {k: {"value": v, "unit": "count" if k == "floor_count" else None,
                          "method": "explicit supplied record", "verification": "VERIFIED"}
                      for k,v in facts.items()}}


def complete():
    return source(purpose="IZHS", municipality="fixture-city", floor_count=2)


class RequiredScenarios(unittest.TestCase):
    def test_01_all_known_verified_without_questions(self):
        engine = Stage0(registry(), [complete()])
        result = engine.audit()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["questions"], [])
        self.assertEqual(result["flow"], FLOW + ["VERIFIED"])
        self.assertEqual(engine.require_verified()["missingRequiredCount"], 0)

    def test_02_derivable_data_is_derived(self):
        r = registry()
        r["inputs"][2]["derivation"] = {"method": "count", "inputs": ["inventory"],
                                       "inputUnits": ["storey-records"], "unit": "count"}
        r["inputs"].append(requirement("inventory", "Verified storey inventory", "array", "storey-records",
                                       evidenceOnly=True))
        s = complete()
        del s["facts"]["floor_count"]
        s["facts"]["inventory"] = {"value": ["ground", "first"], "unit": "storey-records",
                                    "method": "confirmed inventory", "verification": "VERIFIED"}
        result = Stage0(r, [s]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["derived"], ["floor_count"])
        self.assertEqual(result["questions"], [])
        rec = next(x for x in result["inputs"] if x["id"] == "floor_count")
        self.assertEqual(rec["value"], 2)
        self.assertTrue(rec["provenance"][-1]["inputEvidence"])

    def test_03_one_missing_required_one_exact_question(self):
        s = complete()
        del s["facts"]["municipality"]
        result = Stage0(registry(), [s]).audit()
        self.assertEqual(result["missingRequired"], ["municipality"])
        self.assertEqual([x["inputId"] for x in result["questions"]], ["municipality"])
        self.assertFalse(result["canProgress"])

    def test_04_conflict_blocked(self):
        e = Stage0(registry(), [complete(), source("drawing", floor_count=3)])
        result = e.audit()
        self.assertEqual(result["conflicts"], ["floor_count"])
        with self.assertRaises(RuntimeError):
            e.require_verified()

    def test_05_selective_izhs_applicability(self):
        result = Stage0(registry(), [complete()]).audit()
        self.assertEqual([x["branchId"] for x in result["applicabilityMatrix"]
                          if x["status"] == "APPLICABLE"], ["IZHS"])
        self.assertNotIn("apartments", [x["id"] for x in result["inputs"]])
        self.assertNotIn("process", result["missingRequired"])

    def test_06_blocking_unknown_applicability(self):
        r = registry()
        r["inputs"].append(requirement("protected", "Protected zone evidence", "boolean", blocking=False,
                                       priority="REGULATORY_APPLICABILITY_BLOCKER"))
        r["branches"].append(dict(id="PROTECTED_ZONE", when={"input": "protected", "equals": True},
                                  blocking=True, reason="Resolve supplied protected-zone route",
                                  requiredBy=["STAGE_0/protected-zone"]))
        e = Stage0(r, [complete()])
        result = e.audit()
        self.assertFalse(result["gateProof"]["applicabilityMatrixComplete"])
        self.assertEqual(result["questions"][0]["inputId"], "protected")
        with self.assertRaises(RuntimeError):
            e.require_verified()

    def test_07_user_answer_reaudit_verified(self):
        s = complete()
        del s["facts"]["municipality"]
        e = Stage0(registry(), [s])
        self.assertEqual(e.audit()["status"], "WAITING_FOR_USER_DATA")
        answer = source("answer-1", municipality="fixture-city")
        answer["kind"] = "USER_CORRECTION"
        e.update_source(answer)
        self.assertEqual(e.result()["status"], "INVALIDATED")
        self.assertEqual(e.audit()["status"], "VERIFIED")
        self.assertTrue(e.require_verified()["provenanceCompleteForBlockingInputs"])

    def test_08_material_change_invalidates(self):
        e = Stage0(registry(), [complete()])
        e.audit()
        e.require_verified()
        e.update_source(source(purpose="MKD", municipality="fixture-city", floor_count=2))
        self.assertEqual(e.result()["status"], "INVALIDATED")
        with self.assertRaises(RuntimeError):
            e.require_verified()
        self.assertEqual(e.audit()["missingRequired"], ["apartments"])

    def test_09_no_exhaustive_questionnaire(self):
        s = complete()
        del s["facts"]["purpose"]
        del s["facts"]["floor_count"]
        result = Stage0(registry(), [s]).audit()
        self.assertEqual([x["inputId"] for x in result["questions"]], ["purpose"])
        self.assertEqual(len(result["REQUIRED_USER_INPUT_PACKAGE"]), 1)
        self.assertNotIn("customers", result["missingRequired"])

    def test_10_every_question_has_what_why_required_by_format(self):
        result = Stage0(registry(), [source(purpose="IZHS")]).audit()
        self.assertEqual(len(result["questions"]), 2)
        for q in result["questions"]:
            for key in ("WHAT", "WHY", "REQUIRED_BY", "FORMAT", "provenance"):
                self.assertTrue(q[key])
            self.assertIn("canDeriveAutomatically", q)
            self.assertEqual(q["resolutionOwner"], "USER_CLIENT_SURVEYOR_MUST_PROVIDE")


class FailClosedTests(unittest.TestCase):
    def test_file_to_file_cli_answer_reaudit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            r, s, a, out = [root / x for x in ("registry.json", "sources.json", "answers.json", "output.json")]
            data = complete()
            del data["facts"]["municipality"]
            answer = source("answer", municipality="fixture-city")
            answer["kind"] = "USER_CORRECTION"
            for path, value in ((r, registry()), (s, [data]), (a, [answer])):
                path.write_text(json.dumps(value), encoding="utf-8")
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / "design_stage0.py"),
                   "--registry", str(r), "--sources", str(s), "--output", str(out)]
            missing = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2, missing.stderr)
            self.assertEqual(len(json.loads(out.read_text())["questions"]), 1)
            verified = subprocess.run(cmd + ["--answers", str(a)], capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            result = json.loads(out.read_text())
            self.assertEqual(result["status"], "VERIFIED")
            self.assertEqual(result["questions"], [])

    def test_declared_typical_value_cannot_pass_as_verified(self):
        s = complete()
        s["facts"]["floor_count"]["basis"] = "TYPICAL_VALUE"
        result = Stage0(registry(), [s]).audit()
        self.assertEqual(result["gateProof"]["unapprovedAssumptionCount"], 1)
        self.assertFalse(result["canProgress"])

    def test_derived_applicability_reaudits_new_required_inputs(self):
        r = registry()
        r["inputs"][2]["derivation"] = {"method": "count", "inputs": ["inventory"],
                                       "inputUnits": ["storey-records"], "unit": "count"}
        r["inputs"].append(requirement("inventory", "Verified storey inventory", "array", "storey-records",
                                       evidenceOnly=True))
        r["branches"].append(dict(id="TWO_STOREYS", when={"input": "floor_count", "equals": 2},
                                  blocking=True, reason="Fixture two storey branch", requiredBy=["STAGE_0/route"]))
        r["inputs"].append(requirement("two_storey_input", "Branch specific evidence", branches=["TWO_STOREYS"]))
        s = complete()
        del s["facts"]["floor_count"]
        s["facts"]["inventory"] = {"value": ["ground", "first"], "unit": "storey-records",
                                    "method": "confirmed inventory", "verification": "VERIFIED"}
        e = Stage0(r, [s])
        result = e.audit()
        self.assertTrue(result["gateProof"]["applicabilityMatrixComplete"])
        self.assertEqual(result["missingRequired"], ["two_storey_input"])
        self.assertGreater(result["reAudit"]["passes"], 1)
        e.update_source(source("answer", two_storey_input="accepted evidence"))
        self.assertEqual(e.audit()["status"], "VERIFIED")

    def test_uninspected_source_blocks_and_suppresses_questions(self):
        s = complete()
        s["inspected"] = False
        result = Stage0(registry(), [s]).audit()
        self.assertFalse(result["canProgress"])
        self.assertEqual(result["questions"], [])

    def test_wrong_units_or_unverified_values_never_confirmed(self):
        for field, bad in (("unit", "m"), ("verification", "ASSUMED"), ("value", True)):
            s = complete()
            s["facts"]["floor_count"][field] = bad
            result = Stage0(registry(), [s]).audit()
            self.assertIn("floor_count", result["missingRequired"])
            self.assertFalse(result["canProgress"])

    def test_explicit_supersession_resolves_conflict(self):
        e = Stage0(registry(), [complete(), source("old-drawing", floor_count=3)])
        self.assertIn("floor_count", e.audit()["conflicts"])
        correction = source("correction", floor_count=2)
        correction["kind"] = "USER_CORRECTION"
        correction["facts"]["floor_count"]["supersedes"] = ["brief:floor_count", "old-drawing:floor_count"]
        e.update_source(correction)
        self.assertEqual(e.audit()["status"], "VERIFIED")

    def test_nonblocking_optional_gap_does_not_block(self):
        r = registry()
        r["inputs"].append(requirement("preference", "Optional finish", blocking=False,
                                       priority="OPTIONAL_PREFERENCE"))
        result = Stage0(r, [complete()]).audit()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["missingOptional"], ["preference"])
        self.assertEqual(result["questions"], [])

    def test_find_derive_provide_are_separate(self):
        r = registry()
        r["inputs"][1]["owner"] = "SYSTEM_CAN_FIND"
        result = Stage0(r, [source(purpose="IZHS")]).audit()
        items = {x["inputId"]: x for x in result["REQUIRED_USER_INPUT_PACKAGE"]}
        self.assertEqual(items["municipality"]["resolutionOwner"], "SYSTEM_CAN_FIND")
        self.assertEqual([x["inputId"] for x in result["questions"]], ["floor_count"])

    def test_registry_change_revokes_gate(self):
        e = Stage0(registry(), [complete()])
        e.audit()
        r = registry()
        r["revision"] = "v2"
        e.update_registry(r)
        self.assertEqual(e.result()["status"], "INVALIDATED")
        with self.assertRaises(RuntimeError):
            e.require_verified()

    def test_mutating_return_value_cannot_forge_gate(self):
        e = Stage0(registry(), [])
        output = e.audit()
        output.update(status="VERIFIED", canProgress=True)
        with self.assertRaises(RuntimeError):
            e.require_verified()

    def test_unapproved_registry_rejected(self):
        r = registry()
        r["approved"] = False
        with self.assertRaises(ValueError):
            Stage0(r, [complete()])

    def test_polygon_derived_and_self_intersection_blocked(self):
        r = registry()
        r["inputs"].append(requirement("polygon", "Accepted survey polygon", "array", "m", evidenceOnly=True))
        r["inputs"].append(requirement("plot_area", "Plot area", "number", "m2", ["IZHS"], minimum=1,
            derivation={"method": "closed_polygon_area", "inputs": ["polygon"], "inputUnits": ["m"], "unit": "m2"}))
        for p, verified in (([[0,0],[2,0],[2,2],[0,2],[0,0]], True),
                            ([[0,0],[3,3],[3,0],[0,2],[0,0]], False)):
            s = complete()
            s["facts"]["polygon"] = {"value": p, "unit": "m", "method": "accepted survey",
                                      "verification": "VERIFIED"}
            result = Stage0(r, [s]).audit()
            self.assertEqual(result["canProgress"], verified)
            if not verified:
                self.assertEqual(result["gateProof"]["blockingUnknownDerivableCount"], 1)
                self.assertEqual(result["REQUIRED_USER_INPUT_PACKAGE"][0]["resolutionOwner"], "SYSTEM_CAN_DERIVE")


if __name__ == "__main__":
    unittest.main()
