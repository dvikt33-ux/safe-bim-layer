"""Compare retained observed facts with the explicit acceptance contract."""
import json
from .models import AcceptanceContract, AuditCriterion, Observation, Verdict


def audit(contract: AcceptanceContract, observed: Observation) -> list[AuditCriterion]:
    results = []
    for criterion in contract.criteria:
        fact = observed.facts.get(criterion.check)
        actual, refs = (fact.actual, tuple(fact.evidenceRefs)) if fact else (None, ())
        if fact is None:
            verdict = Verdict.DATA_MISSING
        elif fact.status != 'OBSERVED':
            verdict = Verdict(fact.status)
        elif not refs or any(ref not in observed.evidence or observed.evidence[ref] in (None, {}, [], '') for ref in refs):
            verdict = Verdict.NOT_VERIFIED
        else:
            expected = criterion.expected
            numeric = lambda v: type(v) in (int, float)
            if numeric(actual) and numeric(expected):
                matched = abs(actual - expected) <= criterion.tolerance
            else:
                matched = json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False)
            verdict = Verdict.PASS if matched else Verdict.FAIL
        results.append(AuditCriterion(criterion.id, criterion.required, criterion.expected,
            actual, verdict, refs, criterion.correctable))
    return results
