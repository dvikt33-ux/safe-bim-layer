#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inject reviewed copy/multiply/distribute methods into an EXISTING local APA.

No Archicad model write. Refuses incompatible or locally modified method
definitions instead of overwriting them. Installs into the *explicitly named*
local APA checkout only after an exact byte backup and compile check.

Example:
 python scripts/apa_install_native_copy_features.py \
   --target "C:/.../APA_BDD_NorthPair_20261016_174054" --apply

The source methods come from the current repository's own
scripts/archicad_dynamic_commands.py. The installed SceneWriter and existing
DynamicCommands code are preserved without a branch checkout overwrite.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

METHODS = (
    "copy_existing_many",
    "copy_linear_series",
    "copy_rectangular_array",
    "distribute_evenly_between",
    "distribute_along_polyline",
    "copy_multiple_prototypes",
    "plan_reuse_existing",
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def class_methods(text, *, expect_existing=False):
    tree = ast.parse(text)
    found = next((x for x in tree.body if isinstance(x, ast.ClassDef)
                  and x.name == "DynamicCommands"), None)
    if found is None:
        raise ValueError("EXISTING_APA_DYNAMIC_COMMANDS_CLASS_MISSING")
    funcs = {node.name: node for node in found.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if expect_existing and not {"execute","prepare","execute_batch"}.issubset(funcs):
        raise ValueError("TARGET_APA_LACKS_EXISTING_BATCH_WRITER_METHODS")
    return found, funcs


def inject(source, target):
    src_cls, src_funcs = class_methods(source)
    cls, installed = class_methods(target, expect_existing=True)
    if not set(METHODS).issubset(src_funcs):
        raise ValueError("COPY_FEATURES_NOT_PRESENT_IN_SOURCE_VERSION")

    target_lines = target.splitlines(keepends=True)
    source_lines = source.splitlines(keepends=True)
    insert = []
    added = []
    already = []
    for method in METHODS:
        fn = src_funcs[method]
        if method in installed:
            if ast.dump(fn, include_attributes=False) != ast.dump(
                    installed[method], include_attributes=False):
                raise ValueError("EXISTING_LOCAL_METHOD_DIFFERS_REFUSE_REPLACE:"+method)
            already.append(method)
        else:
            # Include decorators: plan_reuse_existing is @staticmethod.
            start=min([fn.lineno]+[dec.lineno for dec in fn.decorator_list])
            insert.append("".join(source_lines[start-1:fn.end_lineno]))
            added.append(method)

    if not insert:
        return target, added, already
    # All extra methods must remain inside the existing DynamicCommands
    # class. Insert just before its native_facts method, NOT at EOF.
    next_fn = installed.get("native_facts")
    if next_fn is None:
        raise ValueError("TARGET_NATIVE_FACTS_INSERT_ANCHOR_NOT_FOUND")
    n=next_fn.lineno-1
    new="".join(target_lines[:n])+"\n".join(insert)+"\n"+"".join(target_lines[n:])

    # Source adds math/time imports if the target hasn't got them yet.
    for module in ("math","time"):
        check=ast.parse(new)
        imported=any(isinstance(stmt,ast.Import) and
                     any(alias.name==module for alias in stmt.names)
                     for stmt in check.body)
        if not imported:
            anchor="import copy\n"
            if anchor not in new:
                raise ValueError("TARGET_IMPORT_INSERT_ANCHOR_MISSING")
            new=new.replace(anchor,anchor+"import "+module+"\n",1)
    compile(new, "<APA local copy feature deployment>", "exec")
    _, final_methods=class_methods(new,expect_existing=True)
    if not set(METHODS).issubset(final_methods):
        raise ValueError("METHOD_INSTALLATION_INCOMPLETE")
    return new, added, already


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Existing local APA checkout root")
    parser.add_argument("--apply",action="store_true",
                        help="Explicitly modify code, never the Archicad model")
    options=parser.parse_args()

    source_file=Path(__file__).resolve().with_name("archicad_dynamic_commands.py")
    target_file=Path(options.target).resolve()/"scripts"/"archicad_dynamic_commands.py"
    if not target_file.exists() or not source_file.exists():
        raise ValueError("SOURCE_OR_LOCAL_APA_FILE_NOT_FOUND")
    if source_file.resolve()==target_file.resolve():
        raise ValueError("SOURCE_IS_TARGET")
    previous_bytes=target_file.read_bytes()
    crlf=b"\r\n" in previous_bytes
    target_text=previous_bytes.decode("utf-8").replace("\r\n","\n")
    source_text=source_file.read_text(encoding="utf-8")
    updated, added, identical=inject(source_text,target_text)
    output_bytes=updated.replace("\n","\r\n").encode("utf-8") if crlf else updated.encode("utf-8")
    result={"schema":"apa.copy-first.local-install.v1",
            "target":str(target_file),
            "source":str(source_file),
            "previousSHA256":sha(previous_bytes),
            "newSHA256":sha(output_bytes),
            "addedMethods":added,"alreadyMatching":identical,
            "status":"DRY_RUN_SAFE" if not options.apply else "NOT_YET_WRITTEN",
            "archicadModelWrites":0,
            "atUTC":datetime.now(timezone.utc).isoformat()}
    if options.apply and output_bytes!=previous_bytes:
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup=target_file.with_name(target_file.name+"."+stamp+".copyfirst.bak")
        if backup.exists():
            raise ValueError("BACKUP_COLLISION")
        backup.write_bytes(previous_bytes)
        if sha(backup.read_bytes())!=sha(previous_bytes):
            raise ValueError("BACKUP_VERIFICATION_FAILED")
        if sha(target_file.read_bytes())!=sha(previous_bytes):
            raise ValueError("TARGET_CHANGED_DURING_BACKUP")
        temp=target_file.with_name(target_file.name+".copyfirst.tmp")
        if temp.exists():
            raise ValueError("TEMP_INSTALL_FILE_ALREADY_EXISTS")
        temp.write_bytes(output_bytes)
        if sha(temp.read_bytes())!=sha(output_bytes):
            raise ValueError("INSTALL_TEMP_CHECKSUM_FAILED")
        temp.replace(target_file)
        result.update(status="LOCAL_APA_CODE_UPDATED_AND_VERIFIED",backup=str(backup))
    elif options.apply:
        result["status"]="COPY_FEATURES_ALREADY_PRESENT_IDENTICAL"
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    try:sys.exit(main())
    except Exception as error:
        print("COPY_FEATURE_INSTALL_BLOCKED:",type(error).__name__,str(error),
              file=sys.stderr)
        sys.exit(2)
