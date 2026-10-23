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

from graph import canonical, configure_stdio

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


def source_class(path):
    parts = set(Path(path).parts)
    if "source-archives" in parts:
        return "ARCHIVED_SOURCE"
    if "runs" in parts:
        return "RESEARCH_RUN"
    if "control" in parts:
        return "PROJECT_CONTROL"
    return "OTHER_DOCUMENT"


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
        conn.execute("CREATE VIRTUAL TABLE sections USING fts5(path UNINDEXED, heading, content, line UNINDEXED, source_sha256 UNINDEXED, source_class UNINDEXED, tokenize='unicode61 remove_diacritics 2')")
        conn.execute("CREATE TABLE provenance (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("CREATE TABLE indexed_sources (path TEXT PRIMARY KEY, size_bytes INTEGER NOT NULL, mtime_ns INTEGER NOT NULL)")
        conn.execute("CREATE TABLE indexed_roots (path TEXT PRIMARY KEY)")
        for root in root_paths:
            conn.execute("INSERT INTO indexed_roots VALUES (?)", (str(Path(root).resolve()),))
        for file in files:
            before_stat = file.stat()
            raw = file.read_bytes()
            after_stat = file.stat()
            if (before_stat.st_size, before_stat.st_mtime_ns) != (after_stat.st_size, after_stat.st_mtime_ns):
                raise ValueError("Source changed during index build")
            conn.execute("INSERT INTO indexed_sources VALUES (?,?,?)",
                         (str(file), after_stat.st_size, after_stat.st_mtime_ns))
            text = raw.decode("utf-8-sig", errors="strict")
            digest = sha(raw)
            for title, line, body in split_sections(text):
                if body.strip() or title not in {"(intro)", "(document)"}:
                    conn.execute("INSERT INTO sections(path,heading,content,line,source_sha256,source_class) VALUES (?,?,?,?,?,?)",
                                 (str(file), title, body, line, digest, source_class(file)))
                    n += 1
        conn.execute("INSERT INTO provenance VALUES (?,?)", ("authority", "DERIVED_READ_ONLY"))
        conn.execute("INSERT INTO provenance VALUES (?,?)", ("schema", "APA_MARKDOWN_SECTION_FTS_V2"))
        conn.commit()
    except Exception:
        conn.close()
        target.unlink(missing_ok=True)
        raise
    conn.close()
    return {"status": "DERIVED_SECTION_INDEX", "files": len(files), "sections": n,
            "index": str(target), "search_backend": "sqlite-fts5"}


def check_index_manifest(conn):
    """Fail closed on unseen added/deleted/stat-changed files before FTS query.

    Only directory names, mtime and size are checked for ALL files, so this
    does not read whole archive on each query; top-K raw bytes remain checked.
    Adversarial same-length/same-mtime changes outside top-K require source
    revision pinning or manual reindex; no total-corpus byte attestation claim.
    """
    stored = {r["path"]: (r["size_bytes"], r["mtime_ns"])
              for r in conn.execute("SELECT path,size_bytes,mtime_ns FROM indexed_sources")}
    roots = [row["path"] for row in conn.execute("SELECT path FROM indexed_roots")]
    if not roots:
        return False
    try:
        paths = list_sources(roots)
        if set(map(str, paths)) != set(stored):
            return False
        for path in paths:
            state = path.stat()
            if (state.st_size, state.st_mtime_ns) != stored[str(path)]:
                return False
    except (OSError, ValueError):
        return False
    return True


def normalized_query(query):
    terms = WORDS.findall(query or "")
    if not 1 <= len(terms) <= 15:
        raise ValueError("Expected 1-15 lexical query terms")
    # Escaping inside quoted phrases protects FTS5 query grammar from injection.
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)


def search(db, query, limit=5, max_snippet=240, selected_class=None, heading_boost=True):
    if limit < 1 or limit > 20 or max_snippet < 40 or max_snippet > 1000:
        raise ValueError("Bounded search requires limit=1..20, max_snippet=40..1000")
    conn = sqlite3.connect("file:" + Path(db).resolve().as_posix() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        meta = dict(conn.execute("SELECT key,value FROM provenance"))
        if meta != {"authority":"DERIVED_READ_ONLY", "schema":"APA_MARKDOWN_SECTION_FTS_V2"}:
            raise ValueError("Unknown or modified index provenance")
        if not check_index_manifest(conn):
            return {"status": "STALE_INDEX", "count": 0, "results": [],
                    "warning": "Directory or source stat changed since indexing; rebuild"}
        q = normalized_query(query)
        rank_sql = "bm25(sections, 0.0, 9.0, 1.0)" if heading_boost else "bm25(sections)"
        allowed = {"ARCHIVED_SOURCE", "RESEARCH_RUN", "PROJECT_CONTROL", "OTHER_DOCUMENT"}
        if selected_class is not None and selected_class not in allowed:
            raise ValueError("Invalid source class")
        if selected_class is None:
            rows = conn.execute(f"""
              SELECT path, heading, content, line, source_sha256, source_class,
                     snippet(sections, 2, '', '', ' … ', 28) AS excerpt,
                     {rank_sql} AS rank
                FROM sections WHERE sections MATCH ?
               ORDER BY rank LIMIT ?
            """, (q, min(500, limit * 30))).fetchall()
        else:
            rows = conn.execute(f"""
              SELECT path, heading, content, line, source_sha256, source_class,
                     snippet(sections, 2, '', '', ' … ', 28) AS excerpt,
                     {rank_sql} AS rank
                FROM sections WHERE sections MATCH ? AND source_class = ?
               ORDER BY rank LIMIT ?
            """, (q, selected_class, min(500, limit * 30))).fetchall()
        # FTS top rows can all belong to ONE giant report. Diversify by
        # document path BEFORE returning and byte-verifying snippets. This
        # preserves relevance order while avoiding wasted context from repeats.
        diverse = []
        seen_docs = set()
        for row in rows:
            if row["path"] not in seen_docs:
                diverse.append(row)
                seen_docs.add(row["path"])
                if len(diverse) == limit:
                    break
        rows = diverse
        # Revalidate only the selected top-K original source bytes.
        checked = {}
        decoded = {}
        stale = []
        tampered = []
        for row in rows:
            location = row["path"]
            if location not in checked:
                src = Path(location)
                raw = src.read_bytes() if src.is_file() else None
                checked[location] = sha(raw) if raw is not None else None
                if raw is not None:
                    decoded[location] = {(heading, line): body for heading, line, body
                                         in split_sections(raw.decode("utf-8-sig"))}
            if checked[location] != row["source_sha256"]:
                stale.append(location)
            elif (source_class(location) != row["source_class"] or
                  decoded.get(location, {}).get((row["heading"], row["line"])) != row["content"]):
                tampered.append(location)
        if stale:
            return {"status": "STALE_INDEX", "count": 0, "results": [],
                    "stale_paths": sorted(set(stale)), "warning": "Source byte hashes mismatch; rebuild"}
        if tampered:
            return {"status": "INDEX_TAMPERED", "count": 0, "results": [],
                    "warning": "Retrieved section text/class does not match source bytes; rebuild trusted cache"}
        results = []
        for row in rows:
            snippet_text = row["excerpt"].strip().replace("\n", " ")
            if len(snippet_text) > max_snippet:
                snippet_text = snippet_text[:max_snippet-1] + "…"
            results.append({
                "path": row["path"], "heading": row["heading"], "line": int(row["line"]),
                "source_class": row["source_class"],
                "source_sha256": row["source_sha256"], "excerpt": snippet_text,
                "relation": "LEXICAL_RETRIEVAL_NOT_VERIFIED_FACT"
            })
        return {"status": "OK", "count": len(results), "results": results,
                "query_type": "LEXICAL_OR_FTS5", "source_class_filter": selected_class,
                "diversity_policy": "ONE_BEST_SECTION_PER_DOCUMENT",
                "ranking": "BM25_HEADING_X9" if heading_boost else "BM25_BASELINE",
                "source_byte_readback": "MATCH_FOR_RETURNED_HITS",
                "source_manifest_check": "PATH_SIZE_MTIME_MATCH",
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
    p.add_argument("--source-class", choices=["ARCHIVED_SOURCE","RESEARCH_RUN","PROJECT_CONTROL","OTHER_DOCUMENT"])
    args = p.parse_args(argv)
    if args.action == "build":
        if not args.root or not args.out:
            p.error("build requires --root and --out")
        result = build(args.root, args.out)
    else:
        if not args.index or not args.query:
            p.error("search requires --index and --query")
        result = search(args.index, args.query, args.limit, args.max_snippet, args.source_class)
    print(canonical(result))


if __name__ == "__main__":
    configure_stdio()
    try:
        main()
    except (OSError, sqlite3.Error, ValueError, UnicodeError) as exc:
        print(canonical({"status": "VALIDATION_ERROR", "reason": str(exc)}), file=sys.stderr)
        sys.exit(2)
