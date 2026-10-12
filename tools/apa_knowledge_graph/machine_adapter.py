#!/usr/bin/env python3
"""Read-only, SHA-pinned adapter: existing TDK roof source -> APA trace/impact cards.

NEVER a normative evaluator. Does not synthesize a calculator, imply compliance,
or write to project, source library, plan or GitHub. Uses existing PR68 source lock,
route, whitelist, compiled block, and machine rules, not a duplicate norm corpus.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml

from graph import canonical

REPO = "dvikt33-ux/safe-bim-layer"
SOURCE_REF = "29aa06a6e9bbef0d991bea922e1ad4101ab29bdd"
TDK_PREFIX = "vendor/tdk-normative-roof/"
TDK_LOCK = "SOURCE_LOCK.json"
MACHINE = "01_Normative_Base/_Machine/"
ROUTE = MACHINE + "routes/objects/residential.izhs.yaml"
RELEASE = MACHINE + "audit/IZHS_CENTRAL_RUSSIA_RELEASE_SET_2026-10-03.yaml"
BLOCK = "04_Code_Generation/blocks/residential.izhs/IZHS.ROOF.DETAILS.yaml"
CATALOG = "04_Code_Generation/block_catalog/residential.izhs.yaml"
RULES = MACHINE + "rules/roofing_2026.yaml"
ALLOWED_FILES = (TDK_LOCK, ROUTE, RELEASE, BLOCK, CATALOG, RULES)
DEFAULT_RULE = "ROOF-VENT-CHANNEL-TABLE-A2-001"
LINK_TASK = "APA-P70.A02.S02"
LINK_ART = "ART-P70-A02-S02-PR68-20261012"


def git_blob_sha(raw):
    return hashlib.sha1(("blob " + str(len(raw)) + "\0").encode("ascii") + raw).hexdigest()


def fetch_pinned(repository, commit, path, token=None, opener=urlopen):
    """Fetch GitHub content pinned to a full commit; never branch HEAD."""
    if repository != REPO or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Must request exact allowed repository and SHA-pinned commit")
    if path not in ALLOWED_FILES:
        raise ValueError("File not allowlisted for scoped normative retrieval")
    uri = (f"https://api.github.com/repos/{repository}/contents/"
           f"{quote(TDK_PREFIX + path, safe='/')}?ref={commit}")
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "APA-knowledge-impact-read-only",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(uri, headers=headers)
    with opener(req, timeout=25) as response:
        encoded = json.load(response)
    if not isinstance(encoded, dict) or encoded.get("encoding") != "base64":
        raise ValueError("GitHub contents response lacked base64 content")
    raw = base64.b64decode(encoded["content"], validate=False)
    if git_blob_sha(raw) != encoded.get("sha"):
        raise ValueError("GITHUB_BLOB_MISMATCH: exact file bytes do not match reported SHA")
    return raw


def parse_verified_sources(raw_files, expected_commit=SOURCE_REF):
    """Verify lock before interpreting any YAML. Verified means SOURCE BYTES only."""
    if set(raw_files) != set(ALLOWED_FILES):
        raise ValueError("Source-set mismatch; require exact six-file minimum closure")
    lock = json.loads(raw_files[TDK_LOCK].decode("utf-8"))
    if (lock.get("schema") != "APA_EXISTING_NORMATIVE_SOURCE_LOCK_V1" or
            lock.get("commit") != "67f17d407d14aebb091daaf79f11c10178b87440" or
            lock.get("authoritativeUse") is not False or
            lock.get("repository") != "dvikt33-ux/tdk-course-project"):
        raise ValueError("Normative source lock or quarantine invalid")
    meta = {}
    for name in ALLOWED_FILES[1:]:
        exact = lock.get("files", {}).get(name)
        if not isinstance(exact, dict):
            raise ValueError("Source not in existing 28-file SOURCE_LOCK: " + name)
        raw = raw_files[name]
        digest = hashlib.sha256(raw).hexdigest()
        blob = git_blob_sha(raw)
        if digest != exact.get("sha256") or blob != exact.get("gitBlob"):
            raise ValueError("SOURCE_BYTE_MISMATCH:" + name)
        meta[name] = {"sha256": digest, "git_blob": blob, "source_path": TDK_PREFIX + name}
    data = {name: yaml.safe_load(raw_files[name].decode("utf-8")) for name in ALLOWED_FILES[1:]}
    if any(not isinstance(d, dict) for d in data.values()):
        raise ValueError("Invalid YAML document root")
    if expected_commit != SOURCE_REF:
        raise ValueError("Unreviewed PR68 revision; no implicit automatic source upgrade")
    return data, meta, lock


def compile_trace(data, meta, lock, index, rule_id=DEFAULT_RULE):
    """Build a minimal *structural* dependency chain from genuine source bytes."""
    if index.get("schema") != "APA_KNOWLEDGE_GRAPH_INDEX_V1":
        raise ValueError("Invalid APA index")
    task = index.get("tasks", {}).get(LINK_TASK)
    artifact = index.get("artifacts", {}).get(LINK_ART)
    if not task or not artifact or LINK_ART not in task.get("artifacts", []):
        raise ValueError("APA task-to-PR68 trace is absent in canonical indexed plan")
    uri = str(artifact.get("uri") or "")
    if not uri.endswith("/pull/68"):
        raise ValueError("Unexpected APA task evidence target for PR68")
    route, release, block, catalog, rules = (data[k] for k in (ROUTE, RELEASE, BLOCK, CATALOG, RULES))
    if route.get("object_type") != "residential.izhs" or route.get("route_status") != "design_only":
        raise ValueError("Unexpected source route or release state")
    if "residential.mkd" not in route.get("scope", {}).get("exclude_object_classes", []):
        raise ValueError("Cross-class exclusion missing")
    if route.get("scope", {}).get("cross_class_fallback") != "forbidden":
        raise ValueError("Cross-class fallback must remain forbidden")
    selected = route.get("compiled_blocks", {}).get("architecture", {}).get("details", [])
    if BLOCK not in selected or block.get("block_id") != "IZHS.ROOF.DETAILS":
        raise ValueError("Roof block missing from exact IZHS route")
    entry = catalog.get("implemented_blocks", {}).get("IZHS.ROOF.DETAILS", {})
    if entry.get("file") != BLOCK or entry.get("release_status") != "design_only":
        raise ValueError("Compiled catalog not aligned with source block")
    if block.get("release_status") != "design_only":
        raise ValueError("Block unexpectedly promoted")
    if block.get("source_pack_ref", {}).get("primary_rule_file") != RULES:
        raise ValueError("Block rule file mismatch")
    whitelist = []
    for group in release.get("explicit_generic_rule_whitelist", []):
        if group.get("path") == RULES:
            whitelist = group.get("rule_ids", [])
    if rule_id not in whitelist or rule_id not in block.get("normative_closure", {}).get("rule_ids", []):
        raise ValueError("Rule absent from the independent block and release whitelist")
    selected_rules = [r for r in rules.get("rules", []) if r.get("rule_id") == rule_id]
    if len(selected_rules) != 1 or selected_rules[0].get("status") != "confirmed":
        raise ValueError("Rule not unique or unconfirmed in source inventory")
    rule = selected_rules[0]
    required = rule.get("derived_values", {}).get("required_inputs", [])
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        raise ValueError("Missing or duplicate parametric inputs")
    if rule.get("derived_values", {}).get("allowed") is not True:
        raise ValueError("Rule is not permitted to declare derived values")
    if rule.get("source_locator", {}).get("table") != "A.2":
        raise ValueError("Unexpected rule locator")
    if not isinstance(index.get("plan_sha256"), str):
        raise ValueError("Unpinned APA plan")
    return {
        "schema": "APA_REAL_SOURCE_DEPENDENCY_CHAIN_V1",
        "readback": "PR68_PINNED_BLOB_AND_TDK_LOCK_MATCH",
        "source_commit": SOURCE_REF,
        "upstream_tdk_commit": lock["commit"],
        "plan_sha256": index["plan_sha256"],
        "project_class": "residential.izhs",
        "source_rule_id": rule_id,
        "locator": rule["source_locator"],
        "rule_status_in_source": rule["status"],
        "required_value_fields": sorted(required),
        "compiled_block": block["block_id"],
        "compiled_block_requires": entry.get("requires", []),
        "linked_apa_task": LINK_TASK,
        "linked_apa_evidence_artifact": LINK_ART,
        "evidence_url": uri,
        "source_lock_files": {k: meta[k] for k in (ROUTE, RELEASE, BLOCK, CATALOG, RULES)},
        "source_release": "DESIGN_ONLY_QUARANTINED",
        "normative_authority": False,
        "engineering_acceptance": "NOT_VERIFIED",
        "lineage_kind": "VERIFIED_SOURCE_STRUCTURAL_DEPENDENCY_NOT_ENGINEERING_CALCULATION"
    }


def change_impact(chain, changed_field, before, after):
    if chain.get("schema") != "APA_REAL_SOURCE_DEPENDENCY_CHAIN_V1":
        raise ValueError("Unrecognized chain")
    if before == after:
        return {"status": "NO_VALUE_CHANGE", "source_field": changed_field, "affected": []}
    if changed_field in chain["required_value_fields"]:
        return {
            "status": "RECHECK_REQUIRED_NOT_RECOMPUTED", "source_field": changed_field,
            "affected": [{"rule": chain["source_rule_id"], "compiled_block": chain["compiled_block"],
                          "task_id": chain["linked_apa_task"],
                          "relation": "DECLARED_REQUIRED_INPUT"}],
            "normative_authority": False, "engineering_acceptance": "NOT_VERIFIED",
            "reason": "Exact machine rule declares this input; calculator and binding not approved"
        }
    return {
        "status": "NOT_IN_SELECTED_RULE_INPUTS", "source_field": changed_field,
        "affected": [], "global_impact": "UNKNOWN",
        "reason": "Absence in this rule does not exclude effects in other rules or documents"
    }


def token_benchmark(raw_plan, raw_files, impact):
    """Count tokenizer proxy; NOT GPT-6 billing, correctness, tool schemas or prompt cache."""
    try:
        import tiktoken
    except ImportError as exc:
        raise ValueError("Token proxy needs separate tiktoken benchmark dependency") from exc
    enc = tiktoken.get_encoding("o200k_base")
    contexts = {
        "naive_plan_and_selected_sources": (raw_plan.decode("utf-8") + "\\n" +
                                            "\\n".join(raw_files[k].decode("utf-8") for k in ALLOWED_FILES)),
        "exact_source_closure_raw": "\\n".join(raw_files[k].decode("utf-8") for k in ALLOWED_FILES),
        "compact_answer_payload": canonical(impact)
    }
    measurements = {k: {"utf8_bytes": len(v.encode("utf-8")),
                        "o200k_base_proxy_tokens": len(enc.encode(v))}
                    for k,v in contexts.items()}
    return {"status": "MEASURED_TOKENIZER_PROXY",
            "tokenizer": "tiktoken:o200k_base",
            "not_measured": ["actual_GPT6_billed_tokens", "tool_schema_tokens", "hidden_reasoning_tokens",
                             "retry_calls", "embedding_index_cost", "answer_quality"],
            "cases": measurements,
            "interpretation": "Same known input chain; NOT candidate-engine head-to-head"}


def run(index_path, output_path=None, rule_id=DEFAULT_RULE, plan_path=None,
        changed_field=None, before=None, after=None):
    index = json.loads(Path(index_path).read_text(encoding="utf-8"))
    token = os.environ.get("GITHUB_TOKEN")
    files = {p: fetch_pinned(REPO, SOURCE_REF, p, token=token) for p in ALLOWED_FILES}
    data, meta, lock = parse_verified_sources(files)
    report = compile_trace(data, meta, lock, index, rule_id)
    impact = None
    if changed_field is not None:
        if before is None or after is None:
            raise ValueError("Change simulation requires both values")
        impact = change_impact(report, changed_field, before, after)
    if plan_path is not None:
        if impact is None:
            raise ValueError("Token proxy requires a specified change scenario")
        original_plan = Path(plan_path).read_bytes()
        supplied = json.loads(original_plan)
        from graph import fingerprint
        if fingerprint(supplied) != index["plan_sha256"]:
            raise ValueError("BENCHMARK_PLAN_STALE: benchmark plan does not match index")
        report["token_budget_audit"] = token_benchmark(original_plan, files, impact)
    if output_path:
        out = Path(output_path)
        if out.exists():
            raise ValueError("Output exists; never overwrite derived snapshots")
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(canonical({"status": "SOURCE_CHAIN_WRITTEN", "path": str(out),
                         "verified_file_count": len(files), "rule": rule_id,
                         "normative_authority": False}))
    else:
        print(canonical(report))
    if impact is not None:
        print(canonical(impact))
    if plan_path is not None:
        print(canonical(report["token_budget_audit"]))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--rule", default=DEFAULT_RULE)
    parser.add_argument("--benchmark-plan", type=Path,
                        help="Run tokenizer proxy against unchanged canonical plan and same exact sources")
    parser.add_argument("--change-field")
    parser.add_argument("--before")
    parser.add_argument("--after")
    a = parser.parse_args()
    run(a.index, a.out, a.rule, a.benchmark_plan,
        a.change_field, a.before, a.after)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, yaml.YAMLError) as exc:
        print(canonical({"status":"VALIDATION_ERROR","reason":str(exc)}), file=sys.stderr)
        sys.exit(2)
