"""Additive V1 -> integrated discovery update, preserving the recovered core.

Only replaces the unmodified V1 discovery module and the exact V1 copy-family
method. Every other DynamicCommands byte and the ENTIRE installed APA core are
preserved. Unique backups/receipt precede replacement; rollback is hash-guarded.
No Archicad imports that connect, no native calls, no PLN enumeration or writes.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

V1_MODULE = '66b81202fcd10c2dda8a5f8c1596de8a57f6a6437ff9cf30e0f5e42654fccd5c'
V1_METHOD_SOURCE = 'e3966ac0de182bdd90ca39a2725ff21f03d6073a2a8bb37db0411bf46a760d60'


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def method(data):
    tree = ast.parse(data)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'DynamicCommands')
    matches = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'plan_reuse_existing']
    need(len(matches) == 1, 'UNIQUE_INSTALLED_COPY_METHOD_REQUIRED')
    node = matches[0]
    need(len(node.decorator_list) == 1 and isinstance(node.decorator_list[0], ast.Name)
         and node.decorator_list[0].id == 'staticmethod', 'COPY_METHOD_STATIC_BINDING_CHANGED')
    # Python 3.12 adds AST type_params; source hashes remain portable across
    # the development interpreter and the installed APA interpreter.
    source = b''.join(data.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
    return node, digest(source.replace(b'\r\n', b'\n'))


def atomic(path, data):
    fd, temp = tempfile.mkstemp(prefix='.apa-discovery-update-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def preflight(root, source):
    root, source = Path(root).resolve(), Path(source).resolve()
    core = root/'archicad_project_accelerator.py'
    current_core = core.read_bytes()
    names = [n.name for n in ast.parse(current_core).body if isinstance(n, ast.FunctionDef)]
    need(all(names.count(n) == 1 for n in ('prepare_auto_optimized_native_task',
         'run_auto_optimized_native_task', 'prepare_native_task', 'run_native_task')),
         'EXISTING_INSTALLED_APA_WRAPPERS_REQUIRED')
    paths = [root/'archicad_strategy_discovery.py', root/'archicad_dynamic_commands.py']
    old = [p.read_bytes() for p in paths]
    need(digest(old[0].replace(b'\r\n', b'\n')) == V1_MODULE,
         'INSTALLED_DISCOVERY_MODIFIED_OR_ALREADY_UPDATED_NO_OVERWRITE')
    node, signature = method(old[1])
    need(signature == V1_METHOD_SOURCE, 'INSTALLED_COPY_METHOD_MODIFIED_NO_OVERWRITE')
    new_module = (source/'archicad_strategy_discovery.py').read_bytes()
    need('def discover_catalog_task(' in new_module.decode('utf-8'), 'INTEGRATED_DISCOVERY_SOURCE_REQUIRED')
    source_dynamic = (source/'archicad_dynamic_commands.py').read_bytes()
    new_node, _ = method(source_dynamic)
    old_lines = old[1].splitlines(keepends=True)
    new_lines = source_dynamic.splitlines(keepends=True)
    replacement = b''.join(new_lines[new_node.lineno-1:new_node.end_lineno])
    if old[1].count(b'\r\n') == old[1].count(b'\n'):
        replacement = replacement.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    patched = b''.join(old_lines[:node.lineno-1])+replacement+b''.join(old_lines[node.end_lineno:])
    # The staticmethod decorator and all prefix/suffix bytes stay unchanged.
    for data, name in ((new_module, str(paths[0])), (patched, str(paths[1]))):
        compile(data, name, 'exec')
    return {'root': root, 'core': core, 'coreBytes': current_core, 'paths': paths,
            'old': old, 'new': [new_module, patched],
            'preservedPrefixBytes': len(b''.join(old_lines[:node.lineno-1])),
            'preservedSuffixBytes': len(b''.join(old_lines[node.end_lineno:]))}


def rollback(receipt_path):
    receipt_path = Path(receipt_path).resolve()
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    root = Path(receipt['scriptsDir']).resolve()
    need(receipt_path.parent.parent == root/'.apa-discovery-updates', 'RECEIPT_OUTSIDE_UPDATE_BACKUP_DIRECTORY')
    need(digest((root/'archicad_project_accelerator.py').read_bytes()) == receipt['coreSHA256'],
         'CORE_CHANGED_SINCE_UPDATE_RECONCILIATION_REQUIRED')
    for row in receipt['files']:
        path = root/row['name']; backup = receipt_path.parent/(row['name']+'.before')
        need(path.parent == root and backup.parent == receipt_path.parent, 'INVALID_RECEIPT_FILE_NAME')
        need(digest(backup.read_bytes()) == row['beforeSHA256'], 'BACKUP_HASH_MISMATCH')
        need(digest(path.read_bytes()) in {row['beforeSHA256'], row['afterSHA256']},
             'UPDATED_FILE_CHANGED_NO_BLIND_ROLLBACK')
    for row in reversed(receipt['files']):
        atomic(root/row['name'], (receipt_path.parent/(row['name']+'.before')).read_bytes())
    receipt['status'] = 'ROLLED_BACK_ORIGINAL_FILES_RESTORED'
    atomic(receipt_path, (json.dumps(receipt, indent=2)+'\n').encode())
    return receipt


def install(root, source, *, apply=False, smoke=None):
    s = preflight(root, source)
    report = {'schema': 'APA_DISCOVERY_ADDITIVE_UPDATE_V1',
        'status': 'ADDITIVE_UPDATE_PREFLIGHT_PASS', 'coreSHA256': digest(s['coreBytes']),
        'corePreservedByteForByte': True, 'scriptsDir': str(s['root']),
        'dynamicUnchangedPrefixBytes': s['preservedPrefixBytes'],
        'dynamicUnchangedSuffixBytes': s['preservedSuffixBytes'],
        'files': [{'name': p.name, 'beforeSHA256': digest(a), 'afterSHA256': digest(b)}
                  for p, a, b in zip(s['paths'], s['old'], s['new'])],
        'nativeCalls': 0, 'nativeWrites': 0, 'applied': False}
    if not apply:
        return report
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    folder = s['root']/'.apa-discovery-updates'/stamp
    folder.mkdir(parents=True, exist_ok=False)
    receipt = folder/'receipt.json'
    for path, data in zip(s['paths'], s['old']):
        (folder/(path.name+'.before')).write_bytes(data)
    (folder/'archicad_project_accelerator.py.unchanged').write_bytes(s['coreBytes'])
    report.update(status='UPDATE_STAGED_BEFORE_REPLACEMENT', receipt=str(receipt))
    atomic(receipt, (json.dumps(report, indent=2)+'\n').encode())
    try:
        need(s['core'].read_bytes() == s['coreBytes']
             and all(p.read_bytes() == b for p, b in zip(s['paths'], s['old'])),
             'INSTALLED_FILES_CHANGED_DURING_STAGING')
        for path, data in zip(s['paths'], s['new']):
            atomic(path, data)
        if smoke is not None:
            smoke(s['root'])
        else:
            code = ("import archicad_project_accelerator as a; import archicad_strategy_discovery as d; "
                    "assert callable(a.prepare_auto_optimized_native_task); "
                    "assert callable(a.run_auto_optimized_native_task); "
                    "assert callable(d.discover_catalog_task); assert callable(d.catalog_capabilities)")
            process = subprocess.run([sys.executable, '-c', code], cwd=s['root'],
                                     capture_output=True, timeout=45)
            need(process.returncode == 0, 'UPDATED_INSTALLED_IMPORT_SMOKE_FAILED:'+process.stderr.decode(errors='replace')[-500:])
        need(s['core'].read_bytes() == s['coreBytes']
             and all(p.read_bytes() == b for p, b in zip(s['paths'], s['new'])),
             'POST_UPDATE_HASH_OR_CORE_PRESERVATION_MISMATCH')
    except Exception:
        rollback(receipt)
        raise
    report.update(status='INTEGRATED_DISCOVERY_INSTALLED_ORIGINAL_CORE_PRESERVED', applied=True)
    atomic(receipt, (json.dumps(report, indent=2)+'\n').encode())
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scripts-dir')
    p.add_argument('--source-scripts', default=str(Path(__file__).resolve().parent))
    p.add_argument('--apply', action='store_true')
    p.add_argument('--rollback-receipt')
    args = p.parse_args()
    result = rollback(args.rollback_receipt) if args.rollback_receipt else install(
        args.scripts_dir, args.source_scripts, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
