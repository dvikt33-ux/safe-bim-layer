"""Exact additive installed APA update. Stages and validates before applying.

Only two existing function bodies change; the current runtime group wrapper and
one code-owned read are added. Original core remainder, DynamicCommands, sidecars and packages
are preserved. No native connection, APX/PLN write or dependency installation.
"""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

PINNED={
 'scripts/archicad_project_accelerator.py':'c48c3c214d7a33618e11bdbef8d9cbf7a96f21fa411fce23fed8352913639e57',
 'scripts/apa_ac29_dynamic_native_verifiers.py':'d02d160d6c58354a3d800fea6c38c4a008ba6631fb7c975fdc96bd60f9721f06'}
ADDITIONS=['scripts/'+n+'.py' for n in ('apa_ac29_mass_request','apa_ac29_group_strategy',
 'apa_ac29_semantic_operation_selector','apa_ac29_assembly_operations',
 'apa_ac29_native_group_clone_verifier','apa_ac29_native_group_grid',
 'apa_ac29_installed_group_provider','apa_ac29_installed_factory')]
ADDITIONS+=['schemas/accelerator/installed-group-copy.json']


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def function(data,name):
    nodes=[n for n in ast.parse(data).body if isinstance(n,ast.FunctionDef) and n.name==name]
    need(len(nodes)==1,'UNIQUE_FUNCTION_REQUIRED:'+name)
    n=nodes[0];lines=data.splitlines(keepends=True)
    return b''.join(lines[n.lineno-1:n.end_lineno]),n


def replace_function(old,source,name):
    _,node=function(old,name);new,_=function(source,name)
    if old.count(b'\r\n')==old.count(b'\n'):new=new.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    lines=old.splitlines(keepends=True)
    return b''.join(lines[:node.lineno-1])+new+b''.join(lines[node.end_lineno:])


def preflight(root,source):
    root,source=Path(root).resolve(),Path(source).resolve()
    need(root!=source,'INSTALL_SOURCE_TARGET_MUST_DIFFER')
    before={p:(root/p).read_bytes() for p in PINNED}
    need(all(sha(data)==PINNED[p] for p,data in before.items()),'INSTALLED_CORE_HASH_DRIFT_NO_OVERWRITE')
    core='scripts/archicad_project_accelerator.py';ver='scripts/apa_ac29_dynamic_native_verifiers.py'
    new={core:replace_function(before[core],(source/core).read_bytes(),'prepare_auto_optimized_native_task'),
         ver:replace_function(before[ver],(source/ver).read_bytes(),'installed_verifiers')}
    need(not any(isinstance(n,ast.FunctionDef) and n.name=='prepare_current_runtime_group_native_task'
                 for n in ast.parse(before[core]).body),'RUNTIME_WRAPPER_ALREADY_PRESENT')
    wrapper,_=function((source/core).read_bytes(),'prepare_current_runtime_group_native_task')
    new[core]+=b'\n\n'+wrapper+b'\n'
    new[core]+=b"\n# Accepted SDK group membership reader; no mutation allowlist change.\nREADS = READS | frozenset({'GetNativeGroupMembersV1'})\n"
    for name in ADDITIONS:
        data=(source/name).read_bytes()
        if (root/name).exists():
            need((root/name).read_bytes()==data,'EXISTING_MODULE_CHANGED_NO_OVERWRITE:'+name)
        else:new[name]=data
    for name,data in new.items():
        if name.endswith('.py'):compile(data,name,'exec')
    return root,before,new


def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.apa-mass-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def stage(root,source,destination):
    root,before,new=preflight(root,source);dest=Path(destination).resolve()
    need(not dest.exists() and dest.parent.is_dir(),'FRESH_INSTALL_STAGE_REQUIRED')
    dest.mkdir()
    # Copy code/reference sources only. Existing vendor environments are reused.
    for name in ('scripts','schemas','archicad-addon'):
        shutil.copytree(root/name,dest/name,ignore=shutil.ignore_patterns('__pycache__','.apa-*','*.bak'))
    for name,data in new.items():atomic(dest/name,data)
    return dict(status='INSTALLED_MASS_SELECTOR_STAGE_READY',stage=str(dest),nativeWrites=0,
                files={name:dict(beforeSHA256=sha((root/name).read_bytes()) if (root/name).exists() else None,
                                afterSHA256=sha(data)) for name,data in new.items()})


def install(root,source,*,apply=False,smoke=None):
    root,before,new=preflight(root,source)
    report=dict(schema='APA_INSTALLED_MASS_SELECTOR_UPDATE_V1',status='PREFLIGHT_PASS',applied=False,
                files={name:dict(beforeSHA256=sha((root/name).read_bytes()) if (root/name).exists() else None,
                                afterSHA256=sha(data)) for name,data in new.items()},nativeCalls=0,modelWrites=0)
    if not apply:return report
    need(callable(smoke),'EXPLICIT_INSTALLED_SMOKE_REQUIRED')
    backup=root/'runtime-code-backups'/('mass-selector-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    backup.mkdir(parents=True,exist_ok=False)
    for name,row in report['files'].items():
        if row['beforeSHA256'] is not None:
            p=backup/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/name).read_bytes())
    receipt=backup/'receipt.json';report['backup']=str(backup)
    atomic(receipt,(json.dumps(report,indent=2)+'\n').encode())
    changed=[]
    try:
        for name,data in new.items():
            p=root/name;expected=report['files'][name]['beforeSHA256']
            need((sha(p.read_bytes()) if p.exists() else None)==expected,'INSTALLED_STAGE_RACE:'+name)
            atomic(p,data);changed.append(name)
        smoke(root)
        need(all(sha((root/n).read_bytes())==row['afterSHA256'] for n,row in report['files'].items()),'INSTALLED_READBACK_HASH_DRIFT')
    except Exception:
        for name in reversed(changed):
            p=root/name;row=report['files'][name]
            need(sha(p.read_bytes())==row['afterSHA256'],'NO_BLIND_ROLLBACK_FILE_CHANGED:'+name)
            if row['beforeSHA256'] is None:p.unlink()
            else:atomic(p,(backup/name).read_bytes())
        report['status']='ROLLED_BACK_AFTER_FAILED_SMOKE';atomic(receipt,(json.dumps(report,indent=2)+'\n').encode())
        raise
    report.update(status='INSTALLED_MASS_SELECTOR_READBACK_VERIFIED',applied=True)
    atomic(receipt,(json.dumps(report,indent=2)+'\n').encode())
    return report
