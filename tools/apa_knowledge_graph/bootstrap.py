#!/usr/bin/env python3
"""Safe one-command APA read-only local knowledge cache installer/bootstrap.

Creates derived local cache only, never changes original GitHub files, PLN/APX or
authoritative PROJECT_PLAN.json. Supports Windows LOCALAPPDATA and POSIX caches.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from graph import build_index, canonical, configure_stdio
from sections import build as build_sections, check_index_manifest


def default_cache():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "APA" / "Knowledge"
    return Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")) / "apa" / "knowledge"


def checkout_root(repo_root):
    base = Path(repo_root).resolve(strict=True)
    plan = base / "docs" / "research" / "apa-results" / "control" / "PROJECT_PLAN.json"
    docs = base / "docs" / "research" / "apa-results"
    if not plan.is_file() or not docs.is_dir():
        raise ValueError("Expected APA checkout with canonical PROJECT_PLAN.json and research docs")
    if plan.is_symlink() or docs.is_symlink():
        raise ValueError("Refusing symlinked plan/doc root")
    return base, plan, docs


def setup(repo_root, cache_dir=None, rebuild=True):
    root, plan_path, docs = checkout_root(repo_root)
    cache = Path(cache_dir or default_cache()).resolve()
    if cache == root or cache.is_relative_to(root):
        raise ValueError("Cache must be outside checkout; no source tree writes")
    cache.mkdir(parents=True, exist_ok=True)
    index_path = cache / "apa-graph.json"
    sections_path = cache / "apa-sections.sqlite"
    # Atomic per-artifact replace, and fail-closed gateway hash checks.
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    index = build_index(plan)
    with tempfile.TemporaryDirectory(prefix="apa-index-", dir=str(cache)) as d:
        p = Path(d)
        staged_graph = p / "graph.json"
        staged_sections = p / "sections.sqlite"
        staged_graph.write_text(json.dumps(index, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        stat = build_sections([docs], staged_sections)
        # Verify manifest without materializing whole corpus in model context.
        db = sqlite3.connect(staged_sections)
        db.row_factory = sqlite3.Row
        if not check_index_manifest(db):
            db.close()
            raise ValueError("STALE_DURING_BOOTSTRAP: documents changed while indexing")
        db.close()
        os.replace(staged_graph, index_path)
        os.replace(staged_sections, sections_path)
    cmd = [str(Path(sys.executable).resolve()),
           str((Path(__file__).resolve().parent / "mcp_adapter.py")),
           "--plan", str(plan_path), "--index", str(index_path),
           "--sections", str(sections_path), "--repo-root", str(root)]
    return {"status": "LOCAL_DERIVED_CACHE_READY", "plan_revision": index.get("plan_revision"),
            "task_count": len(index["tasks"]), "artifact_count": len(index["artifacts"]),
            "document_count": stat["files"], "section_count": stat["sections"],
            "cache": str(cache), "plan": str(plan_path), "index": str(index_path),
            "sections": str(sections_path),
            "optional_local_mcp_command": cmd,
            "warning": "MCP subprocess is NOT automatically registered in ChatGPT; official host integration needed. Cache is disposable, no original sources touched."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--cache-dir", type=Path)
    a = p.parse_args(argv)
    print(canonical(setup(a.repo_root, a.cache_dir)))


if __name__ == "__main__":
    configure_stdio()
    try:
        main()
    except (OSError, ValueError, sqlite3.Error) as e:
        print(canonical({"status": "SETUP_FAILED", "reason": str(e)}), file=sys.stderr)
        sys.exit(2)
