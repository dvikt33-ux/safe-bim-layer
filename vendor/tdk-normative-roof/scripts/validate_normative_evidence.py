#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

RULES_DIR = Path("01_Normative_Base/_Machine/rules")
ALLOWED_CONTENT_ACCESS = {"partial_text", "full_text"}
ALLOWED_SOURCE_TIERS = {"A1_primary_legal_system", "A2_one_hop_from_A1"}
LOCATOR_KEYS = {"section", "article", "clause", "subclause", "term", "table", "appendix", "paragraph", "page_or_anchor"}
TABLE_RULE_TYPES = {"formula", "minimum", "maximum", "requirement", "prohibition"}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def validate_confirmed(rule, path):
    errors = []
    rid = rule.get("rule_id", "<missing-rule-id>")

    locator = rule.get("source_locator")
    if not isinstance(locator, dict) or not any(nonempty(locator.get(k)) for k in LOCATOR_KEYS):
        errors.append("missing exact source_locator")

    if not nonempty(rule.get("evidence_note")):
        errors.append("missing evidence_note")

    if not nonempty(rule.get("verifier")):
        errors.append("missing verifier")

    if rule.get("confidence") != "source_exact":
        errors.append("confidence must be source_exact")

    verification = rule.get("verification")
    if not isinstance(verification, dict):
        errors.append("missing verification block")
    else:
        if verification.get("text_opened") is not True:
            errors.append("verification.text_opened must be true")
        if verification.get("locator_read") is not True:
            errors.append("verification.locator_read must be true")
        if verification.get("content_access") not in ALLOWED_CONTENT_ACCESS:
            errors.append("verification.content_access must be partial_text or full_text")
        if verification.get("source_tier") not in ALLOWED_SOURCE_TIERS:
            errors.append("verification.source_tier must be A1 or A2")
        if not nonempty(verification.get("source_url")):
            errors.append("missing verification.source_url")
        if not nonempty(verification.get("checked_at")):
            errors.append("missing verification.checked_at")

        if isinstance(locator, dict) and nonempty(locator.get("table")) and rule.get("rule_type") in TABLE_RULE_TYPES:
            ctx = verification.get("table_context")
            if not isinstance(ctx, dict):
                errors.append("table-based confirmed rule missing verification.table_context")
            else:
                for key in ("row", "column", "unit", "conditions"):
                    if not nonempty(ctx.get(key)):
                        errors.append(f"table_context.{key} is required")

    return [(path, rid, e) for e in errors]


def main():
    if not RULES_DIR.exists():
        print(f"ERROR: rules directory not found: {RULES_DIR}")
        return 2

    failures = []
    files = sorted(RULES_DIR.glob("*.yaml"))
    for path in files:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            failures.append((path, "<file>", f"YAML parse error: {exc}"))
            continue

        rules = data.get("rules", [])
        if not isinstance(rules, list):
            failures.append((path, "<file>", "top-level 'rules' must be a list"))
            continue

        for rule in rules:
            if not isinstance(rule, dict):
                failures.append((path, "<unknown>", "rule entry must be a mapping"))
                continue
            if rule.get("status") == "confirmed":
                failures.extend(validate_confirmed(rule, path))

    if failures:
        print("NORMATIVE EVIDENCE GATE: FAIL")
        print(f"Found {len(failures)} evidence violations in confirmed rules.\n")
        for path, rid, message in failures:
            print(f"{path}: {rid}: {message}")
        print("\nA confirmed rule is not authoritative until every violation is resolved from the actually opened source text.")
        return 1

    print(f"NORMATIVE EVIDENCE GATE: PASS ({len(files)} rule files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
