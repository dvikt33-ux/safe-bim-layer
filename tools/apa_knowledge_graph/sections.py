#!/usr/bin/env python3
"""APA offline Markdown section index using SQLite FTS5; model-token bounded snippets.

A disposable index, NOT source of truth. Works on explicit allowlisted local roots
in repository checkouts. Does not publish licensed/private source text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

from graph import canonical

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
WORDS = re.compile(r"[^\W_]+(?:[-.][^\W_]+)*", re.UNICODE)
ALLOWED = {".md", ".markdown"}
MAX_BYTES = 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def split_sections(text):
    """Preserve real line anchors so readback can expand one selected section."""
    matches = list(HEADING.finditer(text))
    if not matches:
        return [("(document)", 1, text)]
    parts = []
    if matches[0].start() > 0 and text[:matches[0].start()].strip():
        parts.append(("(intro)", 1, text[:matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        line = text.count("\n", 0, m.start()) + 1
        parts.append((m.group(2), line, text[m.end():end]))
    return parts


def list_sources(roots):
    paths = set()
    for root in roots:
        p = Path(root)
        if p.is_symlink():
            raise ValueError("Symlink roots are prohibited")
        if p.is_file():
            candidates = [p]
        elif p.is_dir():
            candidates = p.rglob("*")
        else:
            raise ValueError("Missing source root: " + str(p))
        for item in candidates:
            if item.is_symlink() or not item.is_file() or item.suffix.lower() not in ALLOWED:
                continue
            if item.stat().st_size > MAX_BYTES:
                continue
            paths.add(item.resolve())
    return sorted(paths)


def build(root_paths, output):
    target = Path(output).resolve()
    if target.exists():
        raise ValueError("Refusing to overwrite existing index")
    files = list_sources(root_paths)
    if not files:
        raise ValueError("No allowlisted Markdown source files found")
    if target in files:
        raise ValueError("Index may not replace a source document")
    conn = sqlite3.connect(str(target))
    n = 0
    try:
        conn.execute("CREATE VIRTUAL TABLE sections USING fts5(path UNINDEXED, heading, content, line UNINDEXED, source_sha256 UNINDEXED, tokenize='unicode61 remove_diacritics 2')")
        conn.execute("CREATE TABLE provenance (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        for file in files:
            raw = file.read_bytes()
            text = raw.decode("utf-8-sig", errors="strict")
            digest = sha(raw)
            for title, line, body in split_sections(text):
                if body.strip() or title not in {"(intro)", "(document)"}:
                    conn.execute("INSERT INTO sections(path,heading,content,line,source_sha256) VALUES (?,?,?,?,?)",
                                 (str(file), title, body, line, digest))
                    n += 1
        conn.execute("INSERT INTO provenance VALUES (?,?)", ("authority", "DERIVED_READ_ONLY"))
        conn.execute("INSERT INTO provenance VALUES (?,?)", ("schema", "APA_MARKDOWN_SECTION_FTS_V1"))
        conn.commit()
    except Exception:
        conn.close()
        target.unlink(missing_ok=True)
        raise
    conn.close()
    return {"status": "DERIVED_SECTION_INDEX", "files": len(files), "sections": n,
            "index": str(target), "search_backend": "sqlite-fts5"}


def normalized_query(query):
    terms = WORDS.findall(query or "")
    if not 1 <= len(terms) <= 15:
        raise ValueError("Expected 1-15 lexical query terms")
    # Escaping inside quoted phrases protects FTS5 query grammar from injection.
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)


def search(db, query, limit=5, max_snippet=240):
    if limit < 1 or limit > 20 or max_snippet < 40 or max_snippet > 1000:
        raise ValueError("Bounded search requires limit=1..20, max_snippet=40..1000")
    conn = sqlite3.connect("file:" + Path(db).resolve().as_posix() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        meta = dict(conn.execute("SELECT key,value FROM provenance"))
        if meta != {"authority":"DERIVED_READ_ONLY", "schema":"APA_MARKDOWN_SECTION_FTS_V1"}:
            raise ValueError("Unknown or modified index provenance")
        q = normalized_query(query)
        rows = conn.execute("""
          SELECT path, heading, line, source_sha256,
                 snippet(sections, 2, '', '', ' … ', 28) AS excerpt,
                 bm25(sections) AS rank
            FROM sections WHERE sections MATCH ?
           ORDER BY rank LIMIT ?
        """, (q, limit)).fetchall()
        results = []
        for row in rows:
            snippet_text = row["excerpt"].strip().replace("\n", " ")
            if len(snippet_text) > max_snippet:
                snippet_text = snippet_text[:max_snippet-1] + "…"
            results.append({
                "path": row["path"], "heading": row["heading"], "line": int(row["line"]),
                "source_sha256": row["source_sha256"], "excerpt": snippet_text,
                "relation": "LEXICAL_RETRIEVAL_NOT_VERIFIED_FACT"
            })
        return {"status": "OK", "count": len(results), "results": results,
                "query_type": "LEXICAL_OR_FTS5",
                "warning": "Exact source blob/edition/readback and applicability must be verified before use"}
    finally:
        conn.close()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("build", "search"))
    p.add_argument("--root", type=Path, nargs="+")
    p.add_argument("--out", type=Path)
    p.add_argument("--index", type=Path)
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--max-snippet", type=int, default=240)
    args = p.parse_args(argv)
    if args.action == "build":
        if not args.root or not args.out:
            p.error("build requires --root and --out")
        result = build(args.root, args.out)
    else:
        if not args.index or not args.query:
            p.error("search requires --index and --query")
        result = search(args.index, args.query, args.limit, args.max_snippet)
    print(canonical(result))


if __name__ == "__main__":
    try:
        main()
    except (OSError, sqlite3.Error, ValueError, UnicodeError) as exc:
        print(canonical({"status": "VALIDATION_ERROR", "reason": str(exc)}), file=sys.stderr)
        sys.exit(2)
