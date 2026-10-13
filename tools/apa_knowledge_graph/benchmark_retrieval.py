#!/usr/bin/env python3
"""Diagnostic self-source retrieval audit: 80+ query/source pairs, no LLM.

Source-anchored heading/title search is NOT independent human-labeled semantic gold.
Reports misses explicitly; never claims perfect natural language query quality.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sqlite3
import statistics
import sys
import time

from graph import canonical
from sections import search

STOP = frozenset(("apa", "архикад", "исследование", "проект", "документы", "работа", "этап",
                  "отчёт", "риск", "итоги", "план", "раздел", "результат", "протокол", "версии"))
WORD = re.compile(r"[^\W_]{3,}", re.UNICODE)


def heading_query(heading):
    words = [w.casefold() for w in WORD.findall(heading)
             if w.casefold() not in STOP and not w.isdigit()]
    # Preserve short anchoring phrases, keep a few prominent words. Single
    # generic words create misleading ranking failures for document-level tests.
    distinct = list(dict.fromkeys(words))
    if len(distinct) < 2:
        return None
    return " ".join(distinct[:4])


def evaluate(db, size=100, k=5):
    if not 80 <= size <= 1000 or not 1 <= k <= 20:
        raise ValueError("Expected size 80..1000 and k 1..20")
    conn = sqlite3.connect("file:" + Path(db).resolve().as_posix() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT path, heading, line, source_class FROM sections ORDER BY path, line").fetchall()
    conn.close()
    seen = set()
    samples = []
    for row in rows:
        path = row["path"]
        if path in seen:
            continue
        q = heading_query(row["heading"])
        if q:
            samples.append((q, path, row["heading"], row["source_class"]))
            seen.add(path)
    if len(samples) < 80:
        raise ValueError("Insufficient independent document/title probes")
    # Uniform sample through the entire sorted corpus avoids prefix bias.
    selected = [samples[i * len(samples) // min(size, len(samples))]
                for i in range(min(size, len(samples)))]
    experiments = {}
    for name, boosted in (("baseline_BM25", False), ("heading_weight_x9", True)):
        results = []
        seconds = []
        for query, expected_path, source_heading, source_class in selected:
            start = time.perf_counter()
            r = search(db, query, limit=k, max_snippet=100,
                       selected_class=source_class, heading_boost=boosted)
            seconds.append(time.perf_counter() - start)
            candidates = [x["path"] for x in r.get("results", [])]
            correct = expected_path in candidates
            results.append({
                "query": query, "expected": expected_path, "class": source_class,
                "source_heading": source_heading, "found": correct,
                "rank": candidates.index(expected_path) + 1 if correct else None,
                "response_status": r.get("status"),
            })
        n = len(results)
        p95 = sorted(seconds)[min(n-1, int(n*.95))]
        experiments[name] = {
            "recall_at_k": round(sum(x["found"] for x in results)/n, 4),
            "error_total": sum(not x["found"] for x in results),
            "errors_or_missing": [x for x in results if not x["found"]][:12],
            "latency_ms_p50": round(statistics.median(seconds)*1000,2),
            "latency_ms_p95": round(p95*1000,2)
        }
    return {
        "schema": "APA_LEXICAL_SELF_SOURCE_DIAGNOSTIC_V2",
        "status": "DIAGNOSTIC_NOT_HUMAN_SEMANTIC_GOLD",
        "sampled_documents": len(selected), "total_candidate_documents": len(samples),
        "retrieval_top_k": k,
        "experiments": experiments,
        "selected_default": "heading_weight_x9",
        "recall_delta": round(experiments["heading_weight_x9"]["recall_at_k"] -
                             experiments["baseline_BM25"]["recall_at_k"], 4),
        "notes": "Same fixed document-heading prompts for both BM25 configurations; not human-reviewed semantics or GPT billing."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--k", type=int, default=5)
    a = p.parse_args()
    print(canonical(evaluate(a.index, a.size, a.k)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(canonical({"status":"BENCHMARK_ERROR","reason":str(exc)}), file=sys.stderr)
        sys.exit(2)
