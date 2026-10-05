from copy import deepcopy
import unittest

from normative_bundle import (GlobalRuleLibrary, ProjectNormativeBundle, Applicability, text_hash,
                             rule_audit_hash, LIFECYCLE, SOURCE_STATUS, canonical)
from project_constraints import ProjectConstraintInput
from tests.test_project_constraints import upstream as previous_upstream, source as client_source, constraint
from tests.test_functional_program import stage0, simple_brief
from tests.test_design_intent import intent_source, goal
from tests.test_site_context import site_source


def upstream():
    us = previous_upstream()
    pc = ProjectConstraintInput(*us,[client_source([constraint()])]); pc.audit()
    return (*us,pc)


def condition(cls="IZHS"):
    return {"input":"project.classification","eq":cls}


def requirement(value=17,operator="gte",domain="SYNTHETIC_TEST_DOMAIN",**fields):
    return dict(domain=domain,subject="SYNTHETIC_PROPERTY",operator=operator,value=value,unit="synthetic-unit",
                scope=["BUILDING"],downstreamDomains=["SYNTHETIC_PLANNING"],**fields)


def document():
    text = "SYNTHETIC normative fixture, not a real SP/GOST. TEST_RULE_A requires synthetic property at least 17 synthetic units."
    location = dict(section="synthetic section",paragraph="TEST-PARA-1",table=None,appendix=None)
    h = text_hash(text)
    return dict(documentId="SYNTHETIC_DOCUMENT",documentRevision="test-r1",sourceHash=h,verificationStatus="VERIFIED",
                content=text,synthetic=True,verifiedLocations=[dict(location=location,text=text,textHash=h,sourceHash=h,
                    verificationStatus="VERIFIED",verificationId="synthetic-verification-receipt",evidenceKind="VERIFIED_SOURCE_TEXT")])


def seal(r):
    r["audit"] = dict(status="VERIFIED",auditId="synthetic-rule-audit",ruleFingerprint=rule_audit_hash(r))
    return r


def rule(id="TEST_RULE_A",revision="1",branch="IZHS/GENERAL",**fields):
    doc = document()
    r = dict(ruleId=id,branchId=branch,revision=revision,status="VERIFIED",requirement=requirement(),
        source=dict(documentId=doc["documentId"],documentRevision=doc["documentRevision"],sourceHash=doc["sourceHash"],location=doc["verifiedLocations"][0]["location"],verificationStatus="VERIFIED"),
        applicability=condition(branch.split("/")[0]),supersedes=[],dependencies=[],
        revisionMetadata=dict(state="ACTIVE_REVISION",decisionId="synthetic-revision-decision"))
    r.update(fields)
    return seal(r)


def branch(id="IZHS/GENERAL",domain="GENERAL",required=None,applicabilityId=None):
    return dict(branchId=id,projectClasses=[id.split("/")[0]],domain=domain,status="VERIFIED",
                applicabilityId=applicabilityId or id.split("/")[0],requiredRuleIds=["TEST_RULE_A"] if required is None else required)


def library_data():
    d = document()
    return dict(libraryId="SYNTHETIC_LIBRARY",revision="1",branches=[branch(),branch("MKD/GENERAL")],
        rules={"IZHS/GENERAL":[rule()],"MKD/GENERAL":[rule("TEST_MKD",branch="MKD/GENERAL")]},
        sources={"SYNTHETIC_DOCUMENT@test-r1":d},
        applicabilityRegistry=dict(id="synthetic-applicability",revision="1",status="VERIFIED",
            definitions={"IZHS":condition(),"MKD":condition("MKD")},inputBindings={
                "project.classification":dict(artifact="STAGE0",datumId="purpose",acceptedFormat="verified project class code"),
                "building.floorCount":dict(artifact="STAGE0",datumId="floor_count",acceptedFormat="integer count"),
                "site.terrainRange":dict(artifact="SITE_CONTEXT",path=["terrain","elevationRange"],acceptedFormat="confirmed elevation range in explicit survey unit"),
                "intent.cost":dict(artifact="DESIGN_INTENT",path=["goals","cost","type"],acceptedFormat="explicit design goal code"),
                "client.budget":dict(artifact="PROJECT_CONSTRAINT_INPUT",path=["constraints","budget","value"],acceptedFormat="confirmed budget number RUB")}),
        domainRegistry=dict(id="synthetic-coverage",revision="1",status="VERIFIED",scopes=[
            dict(downstreamStage="SYNTHETIC_PLANNING",projectClasses=["IZHS","MKD"],requiredNormativeDomains=["GENERAL"],optionalNormativeDomains=["ROOF"]) ]))


def scope():
    return dict(downstreamStage="SYNTHETIC_PLANNING",requiredNormativeDomains=["GENERAL"],optionalNormativeDomains=[])


def engine(data=None,us=None,sc=None):
    return ProjectNormativeBundle(*(us or upstream()),GlobalRuleLibrary(library_data() if data is None else data),scope() if sc is None else sc)


def revised_library():
    data = library_data()
    old = data["rules"]["IZHS/GENERAL"][0]
    old["status"] = "SUPERSEDED"; old["revisionMetadata"]["state"] = "SUPERSEDED_REVISION"; seal(old)
    new = rule(revision="2",supersedes=[dict(ruleId="TEST_RULE_A",branchId="IZHS/GENERAL",revision="1")])
    data["rules"]["IZHS/GENERAL"].append(new); data["revision"] = "2"
    return data


class RequiredScenarios(unittest.TestCase):
    def test_01_stage0_not_verified(self):
        us = upstream(); us[0].update_source(dict(id="brief",kind="USER_BRIEF",revision="2",values={}))
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")

    def test_02_functional_not_verified(self):
        us = upstream(); b = simple_brief(); b["revision"] = "2"; us[1].update_source(b)
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")

    def test_03_design_intent_not_verified(self):
        us = upstream(); us[2].update_source(intent_source([goal(priority=2)]))
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")

    def test_04_site_not_verified(self):
        us = upstream(); s = site_source(); s["revision"] = "2"; us[3].update_source(s)
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")

    def test_05_project_constraints_not_verified(self):
        us = upstream(); us[4].update_source(client_source([constraint(value=14000000)]))
        self.assertEqual(engine(us=us).audit()["status"],"BLOCKED")

    def test_06_applicable_verified_included(self):
        e = engine(); r = e.audit(); self.assertEqual(r["status"],"VERIFIED",r)
        self.assertEqual(r["compiledRules"][0]["ruleId"],"TEST_RULE_A"); e.require_verified()

    def test_07_not_applicable_rule_excluded(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"][0]["applicability"] = {"input":"building.floorCount","gt":20}; seal(data["rules"]["IZHS/GENERAL"][0])
        r = engine(data).audit(); self.assertEqual(r["status"],"VERIFIED"); self.assertEqual(r["compiledRules"],[])

    def test_08_unrelated_class_excluded(self):
        r = engine().audit(); self.assertEqual([b["branchId"] for b in r["excludedBranches"]],["MKD/GENERAL"])

    def test_09_only_verified_lifecycle(self):
        for status in LIFECYCLE-{"VERIFIED"}:
            data = library_data(); data["rules"]["IZHS/GENERAL"][0]["status"] = status; seal(data["rules"]["IZHS/GENERAL"][0])
            r = engine(data).audit(); self.assertEqual(r["compiledRules"],[])

    def test_10_source_verified_not_rule_verified(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"][0]["status"] = "SOURCE_VERIFIED"; seal(data["rules"]["IZHS/GENERAL"][0])
        r = engine(data).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertEqual(r["compiledRules"],[])

    def test_11_missing_source_hash(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; del r["source"]["sourceHash"]; seal(r)
        out = engine(data).audit(); self.assertTrue(out["notVerified"]); self.assertEqual(out["status"],"BLOCKED")

    def test_12_missing_exact_location(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; r["source"]["location"]["paragraph"] = None; seal(r)
        out = engine(data).audit(); self.assertEqual(out["compiledRules"],[]); self.assertTrue(out["notVerified"])

    def test_13_source_status_not_verified(self):
        for status in SOURCE_STATUS-{"VERIFIED"}:
            data = library_data(); data["sources"]["SYNTHETIC_DOCUMENT@test-r1"]["verificationStatus"] = status
            self.assertEqual(engine(data).audit()["compiledRules"],[])

    def test_14_applicable_branch_no_rule_gap(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"] = []
        r = engine(data).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["normativeGaps"])

    def test_15_unrelated_missing_branch_no_gap(self):
        data = library_data(); data["rules"]["MKD/GENERAL"] = []
        r = engine(data).audit(); self.assertEqual(r["status"],"VERIFIED"); self.assertEqual(r["normativeGaps"],[])

    def test_16_known_conditional_resolves(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; r["applicability"] = {"all":[condition(),{"input":"building.floorCount","gte":2}]}; seal(r)
        self.assertEqual(engine(data).audit()["status"],"VERIFIED")

    def test_17_missing_applicability_input_unresolved(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; r["applicability"] = {"input":"site.terrainRange","gt":0}; seal(r)
        out = engine(data).audit(); self.assertTrue(out["missingProjectInputs"]); self.assertEqual(out["compiledRules"],[])

    def test_18_blocking_unknown_blocks_gate(self):
        data = library_data(); data["applicabilityRegistry"]["definitions"]["IZHS"] = {"input":"site.terrainRange","exists":True}
        e = engine(data); r = e.audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertEqual(r["conditionalBranches"][0]["status"],"CONDITIONAL")
        with self.assertRaises(RuntimeError): e.require_verified()

    def test_19_optional_unknown_does_not_block(self):
        data = library_data(); data["branches"].append(branch("IZHS/ROOF","ROOF",required=[],applicabilityId="roof"))
        data["applicabilityRegistry"]["definitions"]["roof"] = {"input":"site.terrainRange","exists":True}
        sc = scope(); sc["optionalNormativeDomains"] = ["ROOF"]
        r = engine(data,sc=sc).audit(); self.assertEqual(r["status"],"VERIFIED"); self.assertFalse(r["conditionalBranches"][0]["blocking"])

    def test_20_superseded_revision_excluded(self):
        r = engine(revised_library()).audit(); self.assertEqual(r["status"],"VERIFIED",r)
        self.assertEqual(r["compiledRules"][0]["ruleRevision"],"2"); self.assertTrue(r["supersessionIndex"])

    def test_21_historical_snapshot_reproducible(self):
        e = engine(); old = e.audit(); e.compare_library(GlobalRuleLibrary(revised_library()))
        self.assertEqual(e.snapshot(),old); self.assertEqual(engine().audit(),old)

    def test_22_active_revision_conflict(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"].append(rule(revision="2"))
        r = engine(data).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(any(c["reason"] == "MULTIPLE_ACTIVE_REVISIONS" for c in r["conflicts"]))

    def test_23_applicable_rules_conflict(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"].append(rule("TEST_RULE_B",requirement=requirement(4,"lte")))
        r = engine(data).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(r["conflicts"])
        self.assertEqual(len(r["conflicts"][0]["rules"]),2)

    def test_24_identical_bundle_fingerprint(self):
        e = engine(); r = e.audit(); self.assertEqual(r,e.audit()); self.assertEqual(r["bundleFingerprint"],engine().audit()["bundleFingerprint"])

    def test_25_upstream_fingerprint_invalidation(self):
        us = upstream(); e = engine(us=us); old = e.audit()
        us[4].update_source(client_source([constraint(value=14000000)])); us[4].audit()
        self.assertEqual(e.result()["status"],"INVALIDATED"); self.assertEqual(e.snapshot(),old)
        with self.assertRaises(RuntimeError): e.require_verified()

    def test_26_revision_impact_compare(self):
        e = engine(); e.audit(); impact = e.compare_library(GlobalRuleLibrary(revised_library()))
        self.assertEqual(impact["changedRuleIds"],["TEST_RULE_A"]); self.assertEqual(impact["changedBranches"],["IZHS/GENERAL"])

    def test_27_unrelated_branch_update_unaffected(self):
        e = engine(); before = e.audit(); data = library_data(); data["rules"]["MKD/GENERAL"].append(rule("TEST_MKD_NEW",branch="MKD/GENERAL"))
        impact = e.compare_library(GlobalRuleLibrary(data)); self.assertEqual(impact["status"],"UNCHANGED"); self.assertEqual(e.result(),before)

    def test_28_related_update_reaudit(self):
        e = engine(); e.audit(); self.assertEqual(e.compare_library(GlobalRuleLibrary(revised_library()))["status"],"REQUIRES_REAUDIT")

    def test_29_provenance_full(self):
        e = engine(); e.audit(); self.assertEqual(e.require_verified()["provenanceCoverage"],1)

    def test_30_no_normative_values_invented(self):
        data = library_data(); r = engine(data).audit()
        self.assertEqual(r["compiledRules"][0]["requirement"],data["rules"]["IZHS/GENERAL"][0]["requirement"])

    def test_31_no_compliance_calculation(self):
        r = engine().audit(); self.assertFalse({"actual","compliant","compliance","actualGreaterThanRequired"} & r["compiledRules"][0].keys())

    def test_32_no_bim_layout_generation(self):
        r = engine().audit(); self.assertFalse({"rooms","layout","walls","archicadOperations"} & r.keys())

    def test_33_izhs_excludes_mkd(self):
        r = engine().audit(); self.assertEqual({c["branchId"] for c in r["compiledRules"]},{"IZHS/GENERAL"})

    def test_34_mkd_excludes_izhs(self):
        us = previous_upstream()
        from tests.test_design_stage0 import source
        s = source(purpose="MKD",apartments=["synthetic-apartment"])
        us[0].update_source(s); us[0].audit(); us[1].audit(); us[2].audit(); us[3].audit()
        pc = ProjectConstraintInput(*us,[]); pc.audit()
        data = library_data(); data["branches"][1]["requiredRuleIds"] = ["TEST_MKD"]
        r = engine(data,us=(*us,pc)).audit(); self.assertEqual(r["status"],"VERIFIED",r)
        self.assertEqual({c["branchId"] for c in r["compiledRules"]},{"MKD/GENERAL"})

    def test_35_downstream_scope_restricts_domains(self):
        data = library_data(); data["branches"].append(branch("IZHS/ROOF","ROOF")); data["rules"]["IZHS/ROOF"] = []
        r = engine(data).audit(); self.assertEqual(r["status"],"VERIFIED"); self.assertEqual(r["normativeGaps"],[])
        self.assertTrue(any(b["reason"] == "OUTSIDE_DOWNSTREAM_SCOPE" for b in r["excludedBranches"]))

    def test_36_gap_exact_evidence(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"] = []
        g = engine(data).audit()["normativeGaps"][0]
        self.assertTrue({"gapId","branchId","reason","requiredBy","projectInputs","evidence","blocking"} <= g.keys()); self.assertTrue(g["evidence"])

    def test_37_project_inputs_retained(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; r["applicability"] = {"input":"client.budget","gt":0}; seal(r)
        used = engine(data).audit()["compiledRules"][0]["projectInputsUsed"]
        self.assertEqual({i["input"] for i in used},{"client.budget","project.classification"})

    def test_38_sources_deduplicated_provenance_retained(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"].append(rule("TEST_RULE_B"))
        r = engine(data).audit(); self.assertEqual(r["status"],"VERIFIED"); self.assertEqual(len(r["sourceDocuments"]),1)
        self.assertEqual(len(r["compiledRules"]),2); self.assertTrue(all(c["provenance"] for c in r["compiledRules"]))

    def test_39_no_eval_dsl(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; r["applicability"] = {"eval":"__import__('os').system('forbidden')"}; seal(r)
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_40_malformed_supersession(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]; r["supersedes"] = [dict(ruleId="TEST_RULE_A",revision="0")]; seal(r)
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_41_cyclic_supersession(self):
        data = revised_library(); old,new = data["rules"]["IZHS/GENERAL"]
        old["supersedes"] = [dict(ruleId="TEST_RULE_A",branchId="IZHS/GENERAL",revision="2")]; seal(old)
        r = engine(data).audit(); self.assertEqual(r["status"],"BLOCKED"); self.assertTrue(any("cyclic" in c["reason"] for c in r["conflicts"]))

    def test_42_unknown_branch_status(self):
        data = library_data(); data["branches"][0]["status"] = "MAYBE"
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_43_nonverified_cannot_leak(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"].append(rule("TEST_UNVERIFIED",status="RULE_AUDITED"))
        r = engine(data).audit(); self.assertFalse(any(c["ruleId"] == "TEST_UNVERIFIED" for c in r["compiledRules"]))

    def test_44_exact_rule_revisions(self):
        r = engine(revised_library()).audit()
        self.assertEqual(r["selectedRuleRevisions"],[dict(ruleId="TEST_RULE_A",branchId="IZHS/GENERAL",revision="2")])

    def test_45_library_immutable(self):
        data = library_data(); before = deepcopy(data); lib = GlobalRuleLibrary(data)
        e = ProjectNormativeBundle(*upstream(),lib,scope()); e.audit()
        self.assertEqual(data,before); self.assertEqual(lib.data(),before)
        copy = lib.data(); copy["revision"] = "100"; self.assertEqual(lib.data(),before)

    def test_46_upstream_immutable(self):
        us = upstream(); before = [u.result() for u in us]; engine(us=us).audit()
        self.assertEqual(before,[u.result() for u in us])

    def test_47_compare_does_not_rewrite(self):
        e = engine(); before = e.audit(); e.compare_library(GlobalRuleLibrary(revised_library()))
        self.assertEqual(before,e.snapshot()); self.assertEqual(before,e.result())

    def test_48_new_verified_rule_update_detected(self):
        e = engine(); e.audit(); data = library_data(); data["rules"]["IZHS/GENERAL"].append(rule("TEST_RULE_B"))
        impact = e.compare_library(GlobalRuleLibrary(data)); self.assertEqual(impact["status"],"REQUIRES_REAUDIT"); self.assertEqual(impact["changedRuleIds"],["TEST_RULE_B"])


class Robustness(unittest.TestCase):
    def test_minimum_downstream_scope(self):
        sc = scope(); del sc["optionalNormativeDomains"]
        self.assertEqual(engine(sc=sc).audit()["status"],"VERIFIED")

    def test_count_strict_requirement_interval_conflict(self):
        data = library_data(); a = data["rules"]["IZHS/GENERAL"][0]
        a["requirement"] = requirement(1,"gt"); a["requirement"]["unit"] = "count"; seal(a)
        b = rule("TEST_RULE_B",requirement=requirement(2,"lt")); b["requirement"]["unit"] = "count"; seal(b)
        data["rules"]["IZHS/GENERAL"].append(b)
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_dsl_all_operators_and_no_coercion(self):
        us = upstream(); reg = library_data()["applicabilityRegistry"]
        ap = Applicability(reg,[u.result() for u in us],[u.result()[k] for u,k in zip(us,("contextFingerprint","programFingerprint","designIntentFingerprint","siteContextFingerprint","constraintInputFingerprint"))])
        for expr,result in (({"input":"building.floorCount","eq":2},True),({"input":"building.floorCount","neq":3},True),
            ({"input":"building.floorCount","gt":1},True),({"input":"building.floorCount","gte":2},True),
            ({"input":"building.floorCount","lt":3},True),({"input":"building.floorCount","lte":2},True),
            ({"input":"building.floorCount","in":[2,3]},True),({"input":"building.floorCount","exists":True},True),
            ({"not":{"input":"building.floorCount","eq":3}},True),({"input":"building.floorCount","eq":True},False),
            ({"any":[{"input":"site.terrainRange","gt":0},condition()]},True),
            ({"all":[{"input":"site.terrainRange","gt":0},condition("MKD")]},False)):
            self.assertEqual(ap.evaluate(expr)[0],result)

    def test_no_hidden_executable_predicate_in_short_circuit(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]
        r["applicability"] = {"any":[condition(),{"eval":"unsafe"}]}; seal(r)
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_unrelated_rule_payload_never_parsed(self):
        data = library_data(); data["rules"]["MKD/GENERAL"] = [{"arbitrary":"malformed unrelated draft","eval":"unsafe"}]
        self.assertEqual(engine(data).audit()["status"],"VERIFIED")

    def test_snippet_summary_and_hash_tampering_rejected(self):
        for kind in ("SEARCH_SNIPPET","AI_SUMMARY","UNVERIFIED_PDF"):
            data = library_data(); data["sources"]["SYNTHETIC_DOCUMENT@test-r1"]["verifiedLocations"][0]["evidenceKind"] = kind
            self.assertEqual(engine(data).audit()["status"],"BLOCKED")
        data = library_data(); data["sources"]["SYNTHETIC_DOCUMENT@test-r1"]["content"] += "tampering"
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_stale_rule_audit_receipt_blocked(self):
        data = library_data(); data["rules"]["IZHS/GENERAL"][0]["requirement"]["value"] = 23
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_missing_verified_dependency_does_not_leak(self):
        data = library_data(); r = data["rules"]["IZHS/GENERAL"][0]
        r["dependencies"] = [dict(ruleId="TEST_MISSING",branchId="IZHS/GENERAL",revision="1")]; seal(r)
        out = engine(data).audit(); self.assertEqual(out["status"],"BLOCKED"); self.assertEqual(out["compiledRules"],[])

    def test_valid_exact_dependency_index(self):
        data = library_data(); b = rule("TEST_RULE_B",dependencies=[dict(ruleId="TEST_RULE_A",branchId="IZHS/GENERAL",revision="1")]); data["rules"]["IZHS/GENERAL"].append(b)
        out = engine(data).audit(); self.assertEqual(out["status"],"VERIFIED"); self.assertEqual(len(out["dependencyIndex"]),1)

    def test_dependency_cycle_blocks(self):
        data = library_data(); a = data["rules"]["IZHS/GENERAL"][0]
        a["dependencies"] = [dict(ruleId="TEST_RULE_B",branchId="IZHS/GENERAL",revision="1")]; seal(a)
        data["rules"]["IZHS/GENERAL"].append(rule("TEST_RULE_B",dependencies=[dict(ruleId="TEST_RULE_A",branchId="IZHS/GENERAL",revision="1")]))
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")

    def test_explicit_library_adoption_invalidates_preserves_history(self):
        e = engine(); before = e.audit(); e.adopt_library(GlobalRuleLibrary(revised_library()))
        self.assertEqual(e.result()["status"],"INVALIDATED"); self.assertEqual(e.snapshot(),before)
        with self.assertRaises(RuntimeError): e.require_verified()
        self.assertEqual(e.audit()["status"],"VERIFIED"); self.assertNotEqual(e.snapshot()["snapshotId"],before["snapshotId"])

    def test_source_verification_update_blocked_impact_selective(self):
        e = engine(); before = e.audit(); data = library_data()
        data["sources"]["SYNTHETIC_DOCUMENT@test-r1"]["verificationStatus"] = "NOT_VERIFIED"
        impact = e.compare_library(GlobalRuleLibrary(data))
        self.assertEqual(impact["status"],"BLOCKED_BY_NORMATIVE_CHANGE"); self.assertEqual(impact["changedBranches"],["IZHS/GENERAL"])
        self.assertEqual(impact["affectedBundleRuleIds"],["TEST_RULE_A"]); self.assertEqual(e.result(),before)

    def test_unrelated_registry_revision_increment_not_invalidate(self):
        e = engine(); e.audit(); data = library_data()
        data["applicabilityRegistry"]["revision"] = "2"; data["domainRegistry"]["revision"] = "2"
        data["applicabilityRegistry"]["definitions"]["MKD"] = {"input":"project.classification","neq":"IZHS"}
        self.assertEqual(e.compare_library(GlobalRuleLibrary(data))["status"],"UNCHANGED")

    def test_optional_update_nonblocking(self):
        data = library_data(); data["branches"].append(branch("IZHS/ROOF","ROOF",["TEST_ROOF"]))
        data["rules"]["IZHS/ROOF"] = [rule("TEST_ROOF",branch="IZHS/ROOF",requirement=requirement(domain="TEST_ROOF_DOMAIN"))]
        sc = scope(); sc["optionalNormativeDomains"] = ["ROOF"]; e = engine(data,sc=sc); e.audit()
        data["rules"]["IZHS/ROOF"].append(rule("TEST_ROOF_NEW",branch="IZHS/ROOF",requirement=requirement(domain="TEST_ROOF_DOMAIN")))
        self.assertEqual(e.compare_library(GlobalRuleLibrary(data))["status"],"UPDATE_AVAILABLE_NONBLOCKING")

    def test_required_registry_domain_cannot_be_omitted(self):
        sc = scope(); sc["requiredNormativeDomains"] = []
        self.assertEqual(engine(sc=sc).audit()["status"],"BLOCKED")

    def test_scope_change_invalidates_and_copy_cannot_forge_gate(self):
        e = engine(); old = e.audit(); sc = scope(); sc["optionalNormativeDomains"] = ["ROOF"]; e.update_scope(sc)
        self.assertEqual(e.result()["status"],"INVALIDATED"); self.assertEqual(e.snapshot(),old)
        fake = e.result(); fake.update(status="VERIFIED",canProgress=True)
        with self.assertRaises(RuntimeError): e.require_verified()

    def test_malformed_new_library_compare_fail_closed(self):
        e = engine(); old = e.audit(); data = library_data(); data["applicabilityRegistry"]["inputBindings"] = []
        self.assertEqual(e.compare_library(GlobalRuleLibrary(data))["status"],"BLOCKED_BY_NORMATIVE_CHANGE")
        self.assertEqual(e.snapshot(),old)

    def test_pending_metadata_not_project_fact(self):
        data = library_data(); data["applicabilityRegistry"]["inputBindings"]["client.budget"]["path"] = ["normativePending"]
        r = data["rules"]["IZHS/GENERAL"][0]; r["applicability"] = {"input":"client.budget","exists":True}; seal(r)
        self.assertEqual(engine(data).audit()["status"],"BLOCKED")


if __name__ == "__main__": unittest.main()
