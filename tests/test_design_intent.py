from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from design_intent import DesignIntent, GOAL_TYPES
from functional_program import FunctionalProgram
from tests.test_functional_program import stage0, simple_brief, brief
from tests.test_design_stage0 import source, registry, complete


def intent_source(statements=None,id="intent",kind="USER_BRIEF"):
    return dict(id=id,kind=kind,revision="v1",approved=True,inspected=True,statements=statements or [])


def goal(id="cost",type="LOW_COST",priority=1,**fields):
    return dict(id=id,kind="GOAL",goalId=id,type=type,priority=priority,scope=["PROJECT"],source="USER_PREFERENCE",**fields)


def dependencies():
    s0 = stage0()
    fp = FunctionalProgram(s0,[simple_brief()]); fp.audit()
    return s0,fp


def engine(statements=None,deps=None):
    s0,fp = deps or dependencies()
    return DesignIntent(s0,fp,[intent_source(statements if statements is not None else [goal()])])


def equal_tradeoff():
    return [goal("compact","COMPACTNESS"),goal("spacious","SPACIOUSNESS")]


def decision(tradeoff,preferred="compact",**fields):
    return dict(id="tradeoff-answer",kind="TRADEOFF_DECISION",goals=tradeoff["goalIds"],
                goalFingerprints=tradeoff["goalFingerprints"],policy="PREFER_GOAL",preferredGoal=preferred,**fields)


class RequiredScenarios(unittest.TestCase):
    def test_01_stage0_not_verified_blocked(self):
        s0,fp = dependencies()
        s0.update_source(source(purpose="IZHS",floor_count=2))
        result = engine(deps=(s0,fp)).audit()
        self.assertEqual(result["status"],"BLOCKED")
        self.assertEqual(result["goals"],[])

    def test_02_functional_program_not_verified_blocked(self):
        s0,fp = dependencies()
        fp.update_source(brief([],id="program")); fp.audit()
        result = engine(deps=(s0,fp)).audit()
        self.assertEqual(result["status"],"BLOCKED")

    def test_03_explicit_goal_retained(self):
        result = engine().audit()
        self.assertEqual(result["status"],"VERIFIED")
        self.assertEqual(result["goals"][0]["type"],"LOW_COST")
        self.assertEqual(result["goals"][0]["goalId"],"cost")

    def test_04_explicit_priority_retained(self):
        result = engine([goal(priority=3)]).audit()
        self.assertEqual(result["goals"][0]["priority"],3)
        self.assertEqual(result["priorityOrder"],[{"priority":3,"goalIds":["cost"]}])
        self.assertIsNone(result["goals"][0]["weight"])

    def test_05_preference_not_normative_requirement(self):
        result = engine().audit()
        self.assertEqual(result["goals"][0]["source"],"USER_PREFERENCE")
        self.assertEqual(result["goals"][0]["commitment"],"PREFERRED")
        self.assertEqual(result["normativePending"],[])

    def test_06_derived_goal_provenance(self):
        text = "Хочу максимально простой и дешёвый дом без сложных конструкций"
        result = engine([dict(id="simple-cheap",kind="DESIGN_STATEMENT",text=text,priority=1)]).audit()
        self.assertEqual(result["status"],"VERIFIED")
        self.assertEqual({g["type"] for g in result["goals"]},{"LOW_COST","CONSTRUCTION_SIMPLICITY","STRUCTURAL_REGULARITY"})
        for g in result["goals"]:
            self.assertEqual(g["source"],"DERIVED_DESIGN_INTENT")
            self.assertTrue(g["derivationRule"])
            self.assertTrue(g["confidence"])
            self.assertEqual(g["exactInputStatements"],[text])
            self.assertEqual(g["provenance"][0]["exactInputStatements"],[text])

    def test_07_no_goal_invented_from_project_type(self):
        result = engine([]).audit()
        self.assertEqual(result["goals"],[])
        self.assertFalse(result["canProgress"])
        self.assertEqual(len(result["questions"]),1)

    def test_08_equal_priority_tradeoff_missing_decision(self):
        result = engine(equal_tradeoff()).audit()
        self.assertEqual(result["status"],"WAITING_FOR_USER_DATA")
        self.assertEqual(len(result["unresolvedTradeoffs"]),1)
        self.assertEqual(result["missingDesignDecisions"][0]["status"],"MISSING_DESIGN_DECISION")
        self.assertEqual(len(result["questions"]),1)

    def test_09_explicit_priority_resolves_tradeoff(self):
        e = engine([goal("cost","LOW_COST",1),goal("spacious","SPACIOUSNESS",3)])
        result = e.audit()
        self.assertEqual(result["status"],"VERIFIED")
        trade = result["resolvedTradeoffs"][0]
        self.assertEqual(trade["resolutionPolicy"],"PRIORITY_ORDER")
        self.assertEqual(trade["preferredGoal"],"cost")
        self.assertEqual(trade["resolutionProvenance"][0]["derivationRule"],"EXPLICIT_PRIORITY_ORDER_V0")
        e.require_verified()

    def test_10_answer_reaudit_verified(self):
        e = engine(equal_tradeoff())
        blocked = e.audit()
        e.update_source(intent_source([decision(blocked["tradeoffs"][0])],id="answer",kind="USER_CORRECTION"))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        self.assertEqual(e.audit()["status"],"VERIFIED")
        self.assertTrue(e.require_verified()["provenanceComplete"])

    def test_11_stage0_change_invalidates(self):
        deps = dependencies(); e = engine(deps=deps); e.audit()
        deps[0].update_source(source(purpose="IZHS",municipality="new-city",floor_count=2))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        deps[0].audit(); deps[1].audit()
        self.assertEqual(e.result()["status"],"INVALIDATED")
        self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_12_functional_program_change_invalidates(self):
        deps = dependencies(); e = engine(deps=deps); e.audit()
        b = simple_brief(); b["statements"][0]["requestedArea"]["value"] = 20
        deps[1].update_source(b); deps[1].audit()
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_13_design_goal_change_invalidates(self):
        e = engine(); old = e.audit()
        e.update_source(intent_source([goal(priority=2)]))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        with self.assertRaises(RuntimeError): e.require_verified()
        new = e.audit()
        self.assertEqual(new["status"],"VERIFIED")
        self.assertNotEqual(old["designIntentFingerprint"],new["designIntentFingerprint"])

    def test_14_same_input_identical(self):
        first = engine().audit(); second = engine().audit()
        self.assertEqual(json.dumps(first,sort_keys=True),json.dumps(second,sort_keys=True))
        self.assertEqual(first["designIntentFingerprint"],second["designIntentFingerprint"])

    def test_15_full_provenance_coverage(self):
        result = engine([goal("cost","LOW_COST",1),goal("spacious","SPACIOUSNESS",3)]).audit()
        self.assertEqual(result["gateProof"]["provenanceCoverage"],1.0)
        self.assertTrue(result["provenanceComplete"])
        self.assertTrue(all(g["provenance"] for g in result["goals"]))
        self.assertTrue(all(t["resolutionProvenance"] for t in result["resolvedTradeoffs"]))

    def test_16_no_normative_numerical_values(self):
        result = engine([goal(),dict(id="pending",kind="NORMATIVE_PENDING",topic="handled in separate normative bundle")]).audit()
        self.assertEqual(result["status"],"VERIFIED")
        self.assertEqual(result["normativePending"][0]["source"],"NORMATIVE_PENDING")
        self.assertNotIn("value",result["normativePending"][0])
        invalid = dict(id="pending",kind="NORMATIVE_PENDING",topic="minimum",value=18)
        self.assertEqual(engine([goal(),invalid]).audit()["status"],"BLOCKED")

    def test_17_no_geometry_layout_fields_accepted(self):
        for field in ("coordinates","walls","layout","setbacks","normativeMinimum"):
            g = goal(); g[field] = 10
            self.assertEqual(engine([g]).audit()["status"],"BLOCKED")

    def test_18_unrelated_goals_not_added(self):
        result = engine([goal("privacy","PRIVACY")]).audit()
        self.assertEqual([g["type"] for g in result["goals"]],["PRIVACY"])
        self.assertEqual(result["tradeoffs"],[])

    def test_19_custom_user_goal_supported(self):
        result = engine([goal("custom","CUSTOM",description="Keep the family's collection visible")]).audit()
        self.assertEqual(result["status"],"VERIFIED")
        self.assertEqual(result["goals"][0]["description"],"Keep the family's collection visible")

    def test_20_priority_weight_validation_fail_closed(self):
        for field,bad in (("priority",True),("priority",0),("priority",1.5),("priority","1"),
                          ("weight",0),("weight",-1),("weight",True),("weight","1")):
            g = goal(); g[field] = bad
            e = engine([g]); result = e.audit()
            self.assertEqual(result["status"],"BLOCKED")
            with self.assertRaises(RuntimeError): e.require_verified()
        for bad in (float("inf"),float("nan")):
            g = goal(weight=bad)
            e = engine([g]); self.assertEqual(e.audit()["status"],"BLOCKED")
            with self.assertRaises(RuntimeError): e.require_verified()


class BoundaryTests(unittest.TestCase):
    def test_functional_program_unchanged_and_user_requirements_preserved(self):
        deps = dependencies(); before = deps[1].result()
        mandatory = goal("space","SPACIOUSNESS",3); mandatory["source"] = "USER_REQUIREMENT"
        result = engine([goal(),mandatory],deps).audit()
        self.assertEqual(deps[1].result(),before)
        self.assertEqual(result["goals"][1]["commitment"],"MANDATORY")
        self.assertFalse(result["resolvedTradeoffs"][0]["relaxationAuthorized"])

    def test_all_categories_supported_without_automatic_additions(self):
        for type in GOAL_TYPES:
            fields = {"description":"explicit custom goal"} if type == "CUSTOM" else {}
            result = engine([goal(type=type,**fields)]).audit()
            self.assertEqual(result["status"],"VERIFIED")
            self.assertEqual(len(result["goals"]),1)

    def test_missing_priority_and_equal_weights_do_not_resolve(self):
        unranked = goal(); del unranked["priority"]
        result = engine([unranked]).audit()
        self.assertIsNone(result["goals"][0]["priority"])
        self.assertEqual(len(result["questions"]),1)
        pairs = equal_tradeoff(); pairs[0]["weight"] = 5; pairs[1]["weight"] = 1
        self.assertEqual(engine(pairs).audit()["status"],"WAITING_FOR_USER_DATA")

    def test_scope_selective_tradeoffs(self):
        goals = equal_tradeoff(); goals[0]["scope"] = ["space:bedroom_master"]; goals[1]["scope"] = ["space:kitchen"]
        self.assertEqual(engine(goals).audit()["tradeoffs"],[])
        goals[1]["scope"] = ["zone:private"]
        self.assertEqual(len(engine(goals).audit()["tradeoffs"]),1)

    def test_stale_resolution_reapproval_and_resolution_change_invalidate(self):
        e = engine(equal_tradeoff()); first = e.audit()
        e.update_source(intent_source([decision(first["tradeoffs"][0])],id="answer",kind="USER_CORRECTION")); e.audit()
        changed = equal_tradeoff(); changed[0]["weight"] = 2
        e.update_source(intent_source(changed))
        result = e.audit()
        self.assertFalse(result["canProgress"])
        self.assertIn("Re-approve",result["questions"][0]["WHAT"])
        new_decision = decision(result["tradeoffs"][0],preferred="spacious")
        e.update_source(intent_source([new_decision],id="answer",kind="USER_CORRECTION"))
        self.assertEqual(e.result()["status"],"INVALIDATED")
        self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_conflicting_goal_definitions_and_explicit_correction(self):
        s0,fp = dependencies()
        e = DesignIntent(s0,fp,[intent_source([goal()]),intent_source([goal(priority=2)],id="other")])
        self.assertEqual(e.audit()["status"],"BLOCKED")
        correction = goal(priority=2); correction["supersedes"] = ["intent:cost","other:cost"]
        e.update_source(intent_source([correction],id="answer",kind="USER_CORRECTION"))
        self.assertEqual(e.audit()["status"],"VERIFIED")

    def test_approved_decision_sacrificable_target_and_norm_source_boundary(self):
        st = goal("sacrifice","SPACIOUSNESS",3,commitment="SACRIFICABLE",target={"value":30,"unit":"m2"},tolerance={"value":2,"unit":"m2"})
        result = engine([goal(),st]).audit()
        self.assertTrue(result["resolvedTradeoffs"][0]["relaxationAuthorized"])
        g = goal(); g["source"] = "APPROVED_PROJECT_DECISION"
        deps = dependencies()
        self.assertEqual(DesignIntent(*deps,[intent_source([g],kind="APPROVED_PROJECT_DECISION")]).audit()["status"],"VERIFIED")
        g["source"] = "NORMATIVE_PENDING"
        self.assertEqual(engine([g]).audit()["status"],"BLOCKED")

    def test_gate_forgery_and_different_dependency_context_rejected(self):
        e = engine(equal_tradeoff()); output = e.audit(); output.update(status="VERIFIED",canProgress=True)
        with self.assertRaises(RuntimeError): e.require_verified()
        s0,fp = dependencies(); other = stage0()
        other.update_source(source(purpose="IZHS",municipality="other-context",floor_count=2)); other.audit()
        self.assertEqual(DesignIntent(other,fp,[intent_source([goal()])]).audit()["status"],"BLOCKED")

    def test_no_goals_is_explicit_and_unknown_text_not_assumed(self):
        explicit = dict(id="none",kind="NO_DESIGN_GOALS",reason="Client specifies no additional design objectives")
        self.assertEqual(engine([explicit]).audit()["status"],"VERIFIED")
        result = engine([dict(id="text",kind="DESIGN_STATEMENT",text="Хочу красивый дом",priority=1)]).audit()
        self.assertEqual(result["goals"],[])
        self.assertEqual(result["status"],"WAITING_FOR_USER_DATA")

    def test_file_to_file_tradeoff_answer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = [root / x for x in ("registry.json","sources.json","functional.json","intent.json","answers.json","out.json")]
            r,s,f,i,a,o = files
            first = engine(equal_tradeoff()).audit()
            for path,value in ((r,registry()),(s,[complete()]),(f,[simple_brief()]),(i,[intent_source(equal_tradeoff())]),
                               (a,[intent_source([decision(first["tradeoffs"][0])],id="answer",kind="USER_CORRECTION")])):
                path.write_text(json.dumps(value),encoding="utf-8")
            cmd = [sys.executable,str(Path(__file__).resolve().parents[1] / "design_intent.py"),"--stage0-registry",str(r),"--stage0-sources",str(s),"--functional-brief",str(f),"--intent",str(i),"--output",str(o)]
            p = subprocess.run(cmd,capture_output=True,text=True); self.assertEqual(p.returncode,2,p.stderr)
            p = subprocess.run(cmd + ["--answers",str(a)],capture_output=True,text=True); self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(o.read_text())["status"],"VERIFIED")


if __name__ == "__main__": unittest.main()
