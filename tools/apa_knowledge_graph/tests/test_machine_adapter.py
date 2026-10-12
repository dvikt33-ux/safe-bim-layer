"""Pinned machine source and field-impact tests (synthetic fixture, real PR68 CI probe)."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import machine_adapter as M
from graph import build_index


def fixture():
    data = {
        M.ROUTE: {"object_type": "residential.izhs", "route_status": "design_only",
                  "scope": {"exclude_object_classes": ["residential.mkd", "public.*"],
                            "cross_class_fallback":"forbidden"},
                  "compiled_blocks":{"architecture":{"details":[M.BLOCK]}}},
        M.RELEASE: {"explicit_generic_rule_whitelist": [
            {"path":M.RULES,"rule_ids":[M.DEFAULT_RULE]}]},
        M.BLOCK: {"block_id":"IZHS.ROOF.DETAILS","release_status":"design_only",
                  "source_pack_ref":{"primary_rule_file":M.RULES},
                  "normative_closure":{"rule_ids":[M.DEFAULT_RULE]}},
        M.CATALOG: {"implemented_blocks":{"IZHS.ROOF.DETAILS":{
            "file":M.BLOCK,"release_status":"design_only","requires":["IZHS.SHELL.CORE"]}}},
        M.RULES: {"rules":[{"rule_id":M.DEFAULT_RULE,"status":"confirmed",
                           "source_locator":{"document_code":"СП17","table":"A.2"},
                           "derived_values":{"allowed":True,
                                             "required_inputs":["roof_slope","roof_slope_length_m"]}}]}
    }
    files = {path:yaml.safe_dump(value,allow_unicode=True).encode() for path,value in data.items()}
    lock = {"schema":"APA_EXISTING_NORMATIVE_SOURCE_LOCK_V1",
            "repository":"dvikt33-ux/tdk-course-project",
            "commit":"67f17d407d14aebb091daaf79f11c10178b87440",
            "authoritativeUse":False,
            "files":{path:{"sha256":hashlib.sha256(raw).hexdigest(),
                           "gitBlob":M.git_blob_sha(raw)} for path,raw in files.items()}}
    files[M.TDK_LOCK] = json.dumps(lock).encode()
    plan = {"revision":1,
            "tasks":{M.LINK_TASK:{"id":M.LINK_TASK,"title":"Normative adapter","status":"PARTIAL",
                                    "inputs":[],"evidence":[M.LINK_ART],"depends_on":[],"related":[]}},
            "artifacts":{M.LINK_ART:{"id":M.LINK_ART,"uri":"https://github.com/dvikt33-ux/safe-bim-layer/pull/68",
                                   "kind":"CODE","verification":"SOURCE_READ"}}}
    return files,build_index(plan)


class RealSourceLineageTests(unittest.TestCase):
    def setUp(self):
        self.files,self.index = fixture()

    def build(self):
        data,meta,lock = M.parse_verified_sources(self.files)
        return M.compile_trace(data,meta,lock,self.index)

    def test_real_shape_source_lock_and_trace(self):
        card = self.build()
        self.assertEqual(card["readback"],"PR68_PINNED_BLOB_AND_TDK_LOCK_MATCH")
        self.assertEqual(card["required_value_fields"], ["roof_slope","roof_slope_length_m"])
        self.assertEqual(card["linked_apa_task"],M.LINK_TASK)
        self.assertFalse(card["normative_authority"])
        self.assertEqual(card["engineering_acceptance"],"NOT_VERIFIED")
        self.assertEqual(len(card["source_lock_files"]),5)

    def test_rule_input_change_is_recheck_not_calculation(self):
        result = M.change_impact(self.build(),"roof_slope_length_m",10,12)
        self.assertEqual(result["status"],"RECHECK_REQUIRED_NOT_RECOMPUTED")
        self.assertEqual(result["affected"][0]["rule"],M.DEFAULT_RULE)
        self.assertFalse(result["normative_authority"])

    def test_unchanged_does_not_propagate(self):
        self.assertEqual(M.change_impact(self.build(),"roof_slope",15,15)["status"],
                         "NO_VALUE_CHANGE")

    def test_absent_input_is_unknown_globally(self):
        result = M.change_impact(self.build(),"irrelevant_property",1,2)
        self.assertEqual(result["status"],"NOT_IN_SELECTED_RULE_INPUTS")
        self.assertEqual(result["global_impact"],"UNKNOWN")

    def test_source_byte_modification_blocked(self):
        self.files[M.RULES] += b"\n# silent tamper"
        with self.assertRaisesRegex(ValueError,"SOURCE_BYTE_MISMATCH"):
            M.parse_verified_sources(self.files)

    def test_lock_claimed_authoritative_is_rejected(self):
        lock=json.loads(self.files[M.TDK_LOCK]); lock["authoritativeUse"]=True
        self.files[M.TDK_LOCK]=json.dumps(lock).encode()
        with self.assertRaisesRegex(ValueError,"lock or quarantine invalid"):
            M.parse_verified_sources(self.files)

    def test_cross_class_scope_is_blocked(self):
        data,meta,lock = M.parse_verified_sources(self.files)
        data[M.ROUTE]["scope"]["exclude_object_classes"]=[]
        with self.assertRaisesRegex(ValueError,"Cross-class exclusion"):
            M.compile_trace(data,meta,lock,self.index)

    def test_unwhitelisted_rule_is_blocked(self):
        data,meta,lock = M.parse_verified_sources(self.files)
        data[M.RELEASE]["explicit_generic_rule_whitelist"]=[]
        with self.assertRaisesRegex(ValueError,"independent block and release whitelist"):
            M.compile_trace(data,meta,lock,self.index)

    def test_task_provenance_required(self):
        data,meta,lock=M.parse_verified_sources(self.files)
        self.index["tasks"][M.LINK_TASK]["artifacts"]=[]
        with self.assertRaisesRegex(ValueError,"trace is absent"):
            M.compile_trace(data,meta,lock,self.index)

    def test_unknown_commit_rejected(self):
        with self.assertRaisesRegex(ValueError,"Unreviewed PR68 revision"):
            M.parse_verified_sources(self.files,expected_commit="0"*40)

    def test_proxy_token_measurement_is_explicitly_not_billing(self):
        result = M.change_impact(self.build(), "roof_slope_length_m", "10", "12")
        raw_plan = json.dumps({"tasks": self.index["tasks"], "artifacts": self.index["artifacts"]}).encode()
        measured = M.token_benchmark(raw_plan, self.files, result)
        cases = measured["cases"]
        self.assertEqual(measured["tokenizer"], "tiktoken:o200k_base")
        self.assertIn("actual_GPT6_billed_tokens", measured["not_measured"])
        self.assertGreater(cases["naive_plan_and_selected_sources"]["o200k_base_proxy_tokens"],
                           cases["compact_answer_payload"]["o200k_base_proxy_tokens"])
        self.assertGreater(cases["exact_source_closure_raw"]["o200k_base_proxy_tokens"],
                           cases["compact_answer_payload"]["o200k_base_proxy_tokens"])

    def test_github_fetch_refuses_unscoped_files(self):
        with self.assertRaisesRegex(ValueError,"allowlisted"):
            M.fetch_pinned(M.REPO,M.SOURCE_REF,"all-private-pln.json",opener=lambda *_:None)
        with self.assertRaisesRegex(ValueError,"SHA-pinned"):
            M.fetch_pinned(M.REPO,"main",M.RULES,opener=lambda *_:None)


if __name__=="__main__":
    unittest.main()
