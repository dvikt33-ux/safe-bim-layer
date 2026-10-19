"""Exact S13 -> accepted native-copy registry update, with staged rollback.

No packages, APX, PLN, new dispatcher or native command calls in this updater.
Only original DynamicCommands.scope, installed_verifiers, one READS addition
and the missing accepted caller modules change. Every other byte is retained.
"""
import ast,json
from pathlib import Path
from datetime import datetime,timezone
import uuid
from apa_install_mass_selector import need,sha,atomic,replace_function

PINNED={
 'scripts/archicad_project_accelerator.py':'30793c9538feacd11e86c6e6d688869f0506afb6e0ec19f74d50cdc143a26e03',
 'scripts/archicad_dynamic_commands.py':'4da6f9b8b359f8ef75b880a2bcead254a553c9a760ba0b32f546d176129c5353',
 'scripts/apa_ac29_dynamic_native_verifiers.py':'aef2feaa27c78c4a47180c48958165bad42677f7fce699c81f8d422e95d5d4af'}
ADD=['scripts/'+n+'.py' for n in ('apa_ac29_copy_batch_oneshot','apa_ac29_group_batch_oneshot',
 'apa_ac29_hotlink_batch_geometry','apa_ac29_hotlink_batch_oneshot','apa_ac29_hotlink_batch_verifier',
 'apa_ac29_hotlink_native_verifiers','apa_ac29_hotlink_oneshot','apa_ac29_native_copy_verifier','apa_ac29_save_isolation')]


def replace_scope(old,source):
    def node(data):
        classes=[n for n in ast.parse(data).body if isinstance(n,ast.ClassDef) and n.name=='DynamicCommands']
        need(len(classes)==1,'COPY_UPDATE_UNIQUE_EXISTING_DYNAMIC_CLASS')
        methods=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name=='scope']
        need(len(methods)==1 and not methods[0].decorator_list,'COPY_UPDATE_UNIQUE_PLAIN_SCOPE_METHOD')
        return methods[0]
    a,b=node(old),node(source);lines=old.splitlines(keepends=True);replacement=b''.join(source.splitlines(keepends=True)[b.lineno-1:b.end_lineno])
    if old.count(b'\r\n')==old.count(b'\n'):replacement=replacement.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    return b''.join(lines[:a.lineno-1])+replacement+b''.join(lines[a.end_lineno:])


def preflight(root,source):
    root,source=Path(root).resolve(),Path(source).resolve()
    before={n:(root/n).read_bytes() for n in PINNED}
    need(all(sha(b)==PINNED[n] for n,b in before.items()),'COPY_UPDATE_INSTALLED_S13_HASH_DRIFT')
    core='scripts/archicad_project_accelerator.py';dynamic='scripts/archicad_dynamic_commands.py';registry='scripts/apa_ac29_dynamic_native_verifiers.py'
    new={core:before[core]+b"\n# Code-owned SDK group-root read for standalone copy qualification.\nREADS = READS | frozenset({'GetNativeGroupRootsV1'})\n",
         dynamic:replace_scope(before[dynamic],(source/dynamic).read_bytes()),
         registry:replace_function(before[registry],(source/registry).read_bytes(),'installed_verifiers')}
    for n in ADD:
        need(not (root/n).exists(),'COPY_UPDATE_ADDITION_ALREADY_EXISTS:'+n)
        new[n]=(source/n).read_bytes()
    for n,b in new.items():compile(b,n,'exec')
    return root,before,new


def stage(root,source,destination):
    import shutil
    root,before,new=preflight(root,source);dest=Path(destination).resolve()
    need(not dest.exists() and dest.parent.is_dir(),'COPY_UPDATE_FRESH_STAGE_REQUIRED')
    dest.mkdir()
    for n in ('scripts','schemas','archicad-addon'):
        shutil.copytree(root/n,dest/n,ignore=shutil.ignore_patterns('__pycache__','.apa-*','*.bak'))
    for n,b in new.items():atomic(dest/n,b)
    return {n:dict(beforeSHA256=sha(before[n]) if n in before else None,afterSHA256=sha(b)) for n,b in new.items()}


def install(root,source,smoke):
    root,before,new=preflight(root,source);need(callable(smoke),'COPY_UPDATE_SMOKE_REQUIRED')
    backup=root/'runtime-code-backups'/('copy-registry-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);backup.mkdir(parents=True,exist_ok=False)
    for n,b in before.items():p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    report=dict(schema='APA_INSTALLED_COPY_REGISTRY_UPDATE_V1',status='STAGED_BEFORE_REPLACEMENT',
        updaterDirectNativeCalls=0,modelWrites=0,files={n:dict(beforeSHA256=sha(before[n]) if n in before else None,afterSHA256=sha(b)) for n,b in new.items()},backup=str(backup))
    receipt=backup/'receipt.json';atomic(receipt,(json.dumps(report,indent=2)+'\n').encode())
    changed=[]
    try:
        for n,b in new.items():
            p=root/n;need((sha(p.read_bytes()) if p.exists() else None)==report['files'][n]['beforeSHA256'],'COPY_UPDATE_CONCURRENT_FILE_DRIFT:'+n)
            atomic(p,b);changed.append(n)
        smoke(root)
        need(all(sha((root/n).read_bytes())==sha(b) for n,b in new.items()),'COPY_UPDATE_POST_APPLY_HASH_DRIFT')
    except Exception:
        for n in reversed(changed):
            p=root/n;need(sha(p.read_bytes())==sha(new[n]),'COPY_UPDATE_NO_BLIND_ROLLBACK:'+n)
            if n in before:atomic(p,before[n])
            else:p.unlink()
        report['status']='ROLLED_BACK_AFTER_FAILED_SMOKE';atomic(receipt,(json.dumps(report,indent=2)+'\n').encode());raise
    report['status']='INSTALLED_COPY_REGISTRY_READBACK_VERIFIED';atomic(receipt,(json.dumps(report,indent=2)+'\n').encode())
    return report
