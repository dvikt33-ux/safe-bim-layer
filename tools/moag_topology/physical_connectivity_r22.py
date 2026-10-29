#!/usr/bin/env python3
"""R22: immutable evidence graph, qualified incidences and sourced identity quotient.

Components are undirected evidence components, never a navigable floor plan.
The existing R15 adapters provide all constraint solving; this module only
prepares evidence and graph projections. Identity tokens are not XYZ.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import csv
from itertools import combinations
from pathlib import Path
import shutil

import solver_r11 as r11
import integrated_spatial_r15 as r15
import identity_alternatives_r18 as r18
import contextual_crosswalk_r21 as r21
from assemble_evidence_graph_r06 import Components

BASE_COMMIT = "d3620e4d6721ae0b0430522d5a7423fe46a3028c"
REVIEW = r11.SYNTH / "r22/source_review.json"
HALLS = ("M-L1-CH-001", "M-L1-AH-OLD-001")
REPAIRS = {"RT015-G": "MOAG-G-0057", "RT024-F": "M-L1-AH-OLD-001"}
EPISODE_ONLY = {"RT031-F", "RT031-G"}
SCOPES = {"L1-SEALED": "SECTOR_OR_EPISODE_GATE_NOT_SHARED_PORTAL",
          "L1-OLD-FREIGHT-HANGAR": "CARGO_SCOPE_OR_CORRIDOR_NOT_SHARED_ROOM"}


def query(a, left, right, kind, name):
    return r18.query({"tokens": a["reference_tokens"]}, left, right, kind, name)


def snapshot(graph, edges, identities=()):
    """Keep all original IDs in memberships, quotient only explicit identities."""
    physical = {n["id"] for n in graph["nodes"] if n["layer"] == "PHYSICAL_INDEX"}
    ids = [n["id"] for n in graph["nodes"]]
    counts = {}
    for name, predicate in (
        ("direct_access", lambda e: e.get("proves_direct_access", False)),
        ("physical_qualitative", lambda e: e.get("joins_approved_evidence_component", False)
         and e["from"] in physical and e["to"] in physical),
        ("route_evidence", lambda e: e.get("joins_approved_evidence_component", False))):
        selected = [e for e in edges if predicate(e)]
        uf = Components(ids, physical)
        for left, right in identities:
            uf.union(left, right)
        for e in selected:
            uf.union(e["from"], e["to"])
        groups = sorted([sorted(set(g) & physical) for g in uf.groups() if set(g) & physical])
        counts[name] = {"edges": len(selected), "components": len(groups),
                        "physical_index_memberships": groups,
                        "meaning": "UNDIRECTED_EVIDENCE_COMPONENT_NOT_TRAVERSABLE_PLAN"}
    identity = Components(sorted(physical), physical)
    for left, right in identities:
        identity.union(left, right)
    return {"physical_source_indices": len(physical),
            "physical_identity_classes": len(identity.groups()),
            "identity_classes": identity.groups(), "projections": counts}


def audit_occurrences(a21, graph, review):
    visits = {e["from"].split("::")[-1]: e for e in graph["edges"]
              if e["id"].startswith("VISIT::")}
    rows = []
    for old in a21["all_30_legacy_uses"]:
        x = deepcopy(old)
        sid = x["stage_id"]
        actual = visits.get(sid, {}).get("to")
        x["original_R09_anchor"] = actual
        x["source_review"] = review["occurrence_contexts"][sid]
        x["effective_specific_referent"] = REPAIRS.get(sid, actual)
        x["contextual_scope_anchor"] = None
        if x["original_legacy_alias"] in SCOPES:
            x["relation_type"] = SCOPES[x["original_legacy_alias"]]
            x["contextual_scope_anchor"] = actual
            x["effective_specific_referent"] = None
        elif sid in EPISODE_ONLY:
            x["relation_type"] = "SAME_EPISODE_HANGAR_GLOBAL_INDEX_UNKNOWN"
            x["effective_specific_referent"] = None
        elif actual is None:
            x["relation_type"] = "UNRESOLVED_OBJECT_NO_FORCED_ANCHOR"
        else:
            x["relation_type"] = "SOURCED_OCCURRENCE_REFERENCE_NOT_DIRECT_ACCESS"
        x["R09_incidence_action"] = ("REANCHOR_IN_PROJECTION" if sid in REPAIRS else
            "CONTEXT_ONLY_NO_GLOBAL_IDENTITY" if sid in EPISODE_ONLY else "PRESERVE")
        rows.append(x)
    dependent = {"stage_id": "RT031-G", "original_R09_anchor": visits["RT031-G"]["to"],
        "effective_specific_referent": None, "relation_type": "SAME_EPISODE_AS_RT031-F",
        "sources": [r21.source("P-376")],
        "reason": "R21 F=G requires reviewing G too; neither is proved to be the first boat hangar",
        "R09_incidence_action": "CONTEXT_ONLY_NO_GLOBAL_IDENTITY"}
    return rows, dependent


def qualified_edges(graph):
    edges, dispositions = [], []
    for original in graph["edges"]:
        e = deepcopy(original)
        disposition = "RETAIN_ORIGINAL_TYPED_EVIDENCE"
        if e["id"].startswith("VISIT::"):
            sid = e["from"].split("::")[-1]
            if sid in REPAIRS:
                e["to"] = REPAIRS[sid]
                disposition = "SOURCE_CORRECTED_OCCURRENCE_REFERENCE"
            elif sid in EPISODE_ONLY:
                # Keep the record and its original scope; exclude its global
                # hangar membership from the approved connectivity projection.
                e["joins_approved_evidence_component"] = False
                disposition = "LEGACY_CONTEXT_RETAINED_GLOBAL_IDENTITY_UNPROVEN"
        edges.append(e)
        dispositions.append({"edge_id": e["id"], "action": disposition,
                             "original": original, "qualified": e})
    return edges, dispositions


def uncertainty(graph, a21, ident):
    rows = []
    for e in graph["edges"]:
        if not e.get("joins_approved_evidence_component") and (
                "HYPOTH" in e["layer"] or e["layer"] == "R08_HYPOTHESIS_NOT_A_PHYSICAL_LINK"):
            rows.append({"id": e["id"], "objects": [e["from"], e["to"]],
                "relation_type": e["layer"], "source_record": e,
                "certainty": "HYPOTHESIS_ONLY", "alternatives": ["exists", "does_not_exist", "different_route"],
                "confirm_if": "Direct station-specific text identifies endpoints and connection",
                "refute_if": "Direct source separates endpoints or contradicts the proposed path"})
    pairs = []
    for p in ident["not_yet_decidable"] + a21["unresolved_cross_episode_pairs"]:
        x = deepcopy(p)
        resolved = {x["a"], x["b"]} in (
            {"MOAG-G-0057", "M-L1-AH-OLD-001"}, {"MOAG-G-0057", "RT024-F"})
        x.update({"R22_status": "PROVEN_DIFFERENT_VIA_R20_AND_R22" if resolved else "UNRESOLVED",
            "alternatives": ["same", "different"],
            "confirm_if": "Explicit cross-episode reference identifies this particular object",
            "refute_if": "Explicit source establishes different objects; hall equality alone is insufficient",
            "source_context_nodes": [n for n in graph["nodes"] if n["id"] in (p["a"], p["b"])
                                     or n.get("step_id") in (p["a"], p["b"])],
            "source_role": "Original indexed node and route page provenance; unresolved relation is not a new fact"})
        pairs.append(x)
    def retain_uncertain(records, kind):
        return [{"original_record": deepcopy(x), "relation_type": kind,
            "certainty": "KNOWN_ELEMENT_UNRESOLVED_GEOMETRY",
            "alternatives": ["intermediate corridors or rooms with unknown geometry",
                             "another source-compatible path geometry", "endpoints still unlocated"],
            "confirm_if": "Explicit source establishes endpoints and complete intermediate path",
            "refute_if": "Source contradicts the candidate endpoints or connection type"} for x in records]
    return {"hypothetical_edges": rows, "identity_candidate_rows": pairs,
        "unresolved_identity_pairs": [x for x in pairs if x["R22_status"] == "UNRESOLVED"],
        "documented_gaps": retain_uncertain(graph["gap_placeholders"], "DOCUMENTED_GAP_NO_CONFIRMED_PATH"),
        "unlocated_intervals": retain_uncertain(graph["witnessed_route_steps_with_unresolved_intermediate_geometry"], "OBSERVED_PATH_UNKNOWN_INTERMEDIATE_GEOMETRY"),
        "unlocated_fixed_elements": deepcopy(graph["unlocated_fixed_element_options"]),
        "layout_alternatives": deepcopy(graph["layout_alternative_groups"]),
        "symmetry_scenarios": deepcopy(graph["conceptual_symmetry_and_nonsymmetry_patterns"]),
        "sector_and_gate_rule": "11 SEALED occurrences are not 11 distinct gates or one proved gate",
        "gate_alternatives": {"objects": [x["stage_id"] for x in a21["all_30_legacy_uses"]
                                              if x["original_legacy_alias"] == "L1-SEALED"],
            "sources": ["B1-074", "B1-100", "B1-105", "B1-108", "B1-113", "B2-012", "B2-013", "B2-017"],
            "relation_type": "EPISODE_GATE_IDENTITY_UNKNOWN", "certainty": "PARTIAL_CONTEXT",
            "alternatives": ["same repaired double gate in multiple episodes", "multiple gates in the sector"],
            "confirm_if": "Text follows the same gate continuously or names its unique landmark",
            "refute_if": "Source identifies another gate or incompatible location"}}


def build():
    m, a21, history, ident = r21.build()
    review = r11.read(REVIEW)
    graph = r11.inputs()[-1]
    tokens = dict(a21["reference_tokens"])
    tokens[HALLS[0]] = len(m["variables"])
    m["variables"].append({"name": "R22::IDENTITY::" + HALLS[0], "domain": [0, 22], "interval": True})
    # Existing refined physical index and the R20 round-hall occurrence.
    for left, right, cid, sources, family in (
        (HALLS[0], "RT015-I", "R22-ROUND-INDEX-REFERENT", [r21.source("P-219")], "r22_index_referent"),
        (HALLS[0], HALLS[1], "R22-SAME-ROUND-AND-OLD-HALL", [review["new_identity_evidence"],
            r21.source("P-219"), r21.source("P-313")], "r22_cross_episode_identity")):
        m["constraints"].append({"id": cid, "rows": [
            r15.row([(tokens[left], 1), (tokens[right], -1)]),
            r15.row([(tokens[right], 1), (tokens[left], -1)])],
            "sources": sources, "status": "SOURCE_IDENTITY_NO_XYZ_OR_PORTAL",
            "any_of": False, "family": family})
    occurrences, dependent = audit_occurrences(a21, graph, review)
    edges, dispositions = qualified_edges(graph)
    baseline = snapshot(graph, graph["edges"])
    after21 = snapshot(graph, edges)
    after22 = snapshot(graph, edges, [HALLS])
    a = {"schema": "MOAG-R22-PHYSICAL-CONNECTIVITY/1", "base_commit": BASE_COMMIT,
        "R09_fingerprint": r11.digest(graph), "reference_tokens": tokens,
        "all_30_uses": occurrences, "dependent_occurrence": dependent,
        "original_nodes": graph["nodes"], "original_edges": graph["edges"],
        "edge_dispositions": dispositions, "baseline_R21_raw": baseline,
        "R21_source_qualified": after21, "R22_source_qualified_identity_quotient": after22,
        "new_confirmed_physical_unions": [{"a": HALLS[0], "b": HALLS[1],
             "source": review["new_identity_evidence"], "inference": "Explicit recollection of Emma's earlier visit",
             "not_implied": ["same individual stair", "same individual control room", "same XYZ", "new door"]}],
        "uncertainty": uncertainty(graph, a21, ident),
        "protected_model": {"r13": r11.digest(m["r13"]), "r14": r11.digest(m["r14"]),
                            "R05_profiles": r11.digest(r11.inputs()[2])},
        "geometry_policy": {"global_levels": [1, 2, 3], "new_metric_constraints": 0,
            "scenario_volumes": 12, "bound_visits": 25, "unbound_visits": 353,
            "new_physical_rooms": 0, "new_portals": 0,
            "equivalent_hall_profiles": "NONADDITIVE_ALTERNATIVE_REPRESENTATIONS_PENDING_R23",
            "local_strata": "R12 preserved, not new global levels"}}
    def delta(before, after):
        result = {}
        for name in before["projections"]:
            def connected_pairs(s):
                return {tuple(p) for g in s["projections"][name]["physical_index_memberships"]
                        for p in combinations(g, 2)}
            old, new = connected_pairs(before), connected_pairs(after)
            result[name] = {"newly_co_component_pairs": sorted(new - old),
                            "no_longer_co_component_pairs": sorted(old - new),
                            "pair_relation": "EVIDENCE_REACHABILITY_NOT_IDENTITY_OR_DOOR"}
        return result
    a["component_partition_changes"] = {"apply_R21": delta(baseline, after21),
                                        "new_R22_identity": delta(after21, after22)}
    validate(m, a)
    return m, a


def validate(m, a):
    r15.validate(m)
    graph = r11.inputs()[-1]
    if a["original_nodes"] != graph["nodes"] or a["original_edges"] != graph["edges"]:
        raise ValueError("R22_ORIGINAL_GRAPH_LOST")
    if r11.digest(graph) != a["R09_fingerprint"]:
        raise ValueError("R22_R09_CHANGED")
    expected, dispositions = qualified_edges(graph)
    if dispositions != a["edge_dispositions"]:
        raise ValueError("R22_UNSOURCED_EDGE_CHANGE")
    for key, edges, identities in (("baseline_R21_raw", graph["edges"], ()),
            ("R21_source_qualified", expected, ()),
            ("R22_source_qualified_identity_quotient", expected, (HALLS,))):
        if a[key] != snapshot(graph, edges, identities):
            raise ValueError("R22_UNSOURCED_COMPONENT_OR_IDENTITY")
    if Counter(x["original_legacy_alias"] for x in a["all_30_uses"]) != r21.EXPECTED:
        raise ValueError("R22_AUDIT_OCCURRENCES_LOST")
    if len(m["r14"]["steps"]) != 378 or len(m["unbound_route_steps"]) != 353:
        raise ValueError("R22_ROUTE_STAGES_LOST")
    for section in ("r13", "r14"):
        if r11.digest(m[section]) != a["protected_model"][section]:
            raise ValueError("R22_METRIC_MODEL_CHANGED")
    cs = {c["id"]: c for c in m["constraints"]}
    t = a["reference_tokens"]
    for left, right, cid in ((HALLS[0], "RT015-I", "R22-ROUND-INDEX-REFERENT"),
                             (*HALLS, "R22-SAME-ROUND-AND-OLD-HALL")):
        c = cs[cid]
        if c["rows"] != [r15.row([(t[left], 1), (t[right], -1)]),
                         r15.row([(t[right], 1), (t[left], -1)])] or c["any_of"] or not c["sources"]:
            raise ValueError("R22_IDENTITY_PROOF_CHANGED")
    return True


def experiment(out, exe):
    out.mkdir(parents=True, exist_ok=True)
    m, a = build()
    r11.write(out / "connectivity-audit.json", a)
    r11.write(out / "joint-model.json", m)
    with (out / "corrected-route-crosswalk.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["stage_id", "original_legacy_alias", "episode_book_page", "original_R14_stable_anchor",
                  "original_R09_anchor", "effective_specific_referent", "contextual_scope_anchor",
                  "relation_type", "R09_incidence_action"]
        writer = csv.DictWriter(f, fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(a["all_30_uses"])
    cp = r15.cp_solve(m)
    mz = r15.mzn_solve(m, exe, out, "r22-sat")
    if cp["status"] != "SAT" or mz["status"] != "SAT":
        raise RuntimeError("R22_BASE_NOT_SAT")
    replay = r15.mzn_solve(m, exe, out, "python-witness", fixed=cp["witness"])
    if replay["status"] != "SAT":
        raise RuntimeError("R22_WITNESS_NOT_REPLAYED")
    conflicts = []
    for left, right, kind, label in ((HALLS[0], HALLS[1], "different", "false-hall-split"),
            (HALLS[1], "MOAG-G-0057", "same", "false-sleeping-hall-merge"),
            ("M-L1-FH-001", "M-L1-FH-002", "same", "false-independent-hangars-merge")):
        q = query(a, left, right, kind, "R22-TEST-" + label)
        z = r15.cp_solve(m, [q]); zm = r15.mzn_solve(m, exe, out, label, [q])
        ids = {c["id"] for c in z["unsat_core"]}
        if z["status"] != "INFEASIBLE" or zm["status"] != "INFEASIBLE" or q["id"] not in ids:
            raise RuntimeError("R22_CONFLICT_NOT_PROVEN: " + label)
        core = r15.cp_solve(m, [q], active=ids)
        cm = r15.mzn_solve(m, exe, out, label + "-core", [q], active=ids)
        if core["status"] != "INFEASIBLE" or cm["status"] != "INFEASIBLE":
            raise RuntimeError("R22_CORE_NOT_REPLAYED")
        absent = None
        if label != "false-independent-hangars-merge":
            absent = r15.cp_solve(m, [q], exclude_families=("r22_cross_episode_identity",))["status"]
            if absent != "SAT" or "R22-SAME-ROUND-AND-OLD-HALL" not in ids:
                raise RuntimeError("R22_NEW_PROOF_NOT_CAUSAL")
        conflicts.append({"test": label, "python": z["status"], "minizinc": zm["status"],
            "without_new_source": absent, "core_replayed_both": True, "unsat_core": z["unsat_core"]})
    alternatives = []
    for i, p in enumerate(a["uncertainty"]["unresolved_identity_pairs"]):
        for kind in ("same", "different"):
            q = query(a, p["a"], p["b"], kind, f"R22-OPEN-{i}-{kind}")
            z = r15.cp_solve(m, [q]); zm = r15.mzn_solve(m, exe, out, f"open-{i}-{kind}", [q])
            if z["status"] != "SAT" or zm["status"] != "SAT":
                raise RuntimeError("R22_UNPROVEN_IDENTITY_PROMOTED")
            rep = r15.mzn_solve(m, exe, out, f"replay-open-{i}-{kind}", [q], fixed=z["witness"])
            if rep["status"] != "SAT":
                raise RuntimeError("R22_ALTERNATIVE_REPLAY_FAILED")
            alternatives.append({"a": p["a"], "b": p["b"], "kind": kind,
                "python": "SAT", "minizinc": "SAT", "witness_replayed": True})
    result = {"schema": "MOAG-R22-REAL-SOLVER-RESULTS/1", "base_commit": BASE_COMMIT,
        "python_cp_sat": cp["status"], "minizinc_cp_sat": mz["status"],
        "full_witness_replayed": True, "conflicts": conflicts, "alternatives": alternatives,
        "new_physical_unions": 1, "unresolved_identity_pairs": len(alternatives) // 2,
        "hypothetical_edges": len(a["uncertainty"]["hypothetical_edges"]),
        "snapshots": {k: {"indices": a[k]["physical_source_indices"],
            "identity_classes": a[k]["physical_identity_classes"],
            "components": {n: v["components"] for n, v in a[k]["projections"].items()}}
            for k in ("baseline_R21_raw", "R21_source_qualified", "R22_source_qualified_identity_quotient")},
        "routes": 52, "occurrences": 378, "bound": 25, "unbound": 353,
        "new_portals": 0, "new_metric_constraints": 0, "archicad_write": False}
    validate(m, a)
    r11.write(out / "results.json", result)
    print(result["snapshots"])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    portable = next((r11.ROOT / ".runtime/minizinc").glob("*/bin/minizinc.exe"), None)
    portable = portable or next((r11.ROOT / ".runtime/minizinc").glob("*/bin/minizinc"), None)
    p.add_argument("--minizinc", type=Path, default=shutil.which("minizinc") or portable)
    z = p.parse_args()
    if z.minizinc is None:
        p.error("Official MiniZinc cp-sat executable required")
    experiment(z.out, z.minizinc)


if __name__ == "__main__":
    main()
