"""Install the reviewed APA AC29 job bridge ONCE beside the stable APA core.

Installs a user-level Startup entry, launches a single background receiver,
never changes Dispatcher/GPT/Arena or the stable APA scripts. Safe, pinned
GitHub blobs and digest-checked local core; fails closed on mismatched versions.
"""
from __future__ import annotations

import base64
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import time
from datetime import datetime, timezone

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
CONTROLLERS = ROOT / "controllers"
REPO = "dvikt33-ux/safe-bim-layer"
WORKER_COMMIT = "dce42af8eac09b50a29c9a9a7970c01973ae12db"
WORKER_BLOB = "ef52f5fc184c6ac59c1197c14e1bbbc06237fdd2"
REVIEW_COMMIT = "b32e60f998f7c9337130ad58c723a947998753a8"
REVIEW_BLOB = "35a7bd794317ba91056334aff6801cd0ec71f220"
KNOWN = {
    "archicad_project_accelerator.py": "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b",
    "archicad_dynamic_commands.py": "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8",
    "archicad_strategy_discovery.py": "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce",
}
NAME = "APA-AC29-GPT-Bridge"
LOG = ROOT / "apa-job-bridge-state" / "bridge.log"


def processes(worker):
    """Exact installed receiver only; wrapper and child are one process tree."""
    data=subprocess.check_output(['powershell','-NoProfile','-Command',
        "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } | "
        "Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"],
        timeout=30)
    rows=json.loads(data.decode('utf-8-sig'))
    rows=rows if isinstance(rows,list) else [rows]
    return [r for r in rows if str(worker).casefold() in (r.get('CommandLine') or '').casefold()]


def update_from_checkout(checkout, manifest_path, apply=False):
    """One checked update of existing code; preserve queues, settings and ledger.

    The manifest is local and pins old bytes, new Git revision and saved
    project fingerprint. This installer makes NO Archicad calls or grants.
    """
    require(sys.platform=='win32','WINDOWS_REQUIRED')
    checkout=Path(checkout).resolve();m=json.loads(Path(manifest_path).read_text(encoding='utf8'))
    modules=set(KNOWN)|{'apa_ac29_dynamic_write_scopes.py','apa_ac29_dynamic_native_verifiers.py'}
    worker=ROOT/'controllers'/'apa_ac29_autonomous_job_bridge.py'
    targets={name:ROOT/'scripts'/name for name in modules}
    targets[worker.name]=worker
    require(set(m)=={'schema','revision','oldHashes','workingPath','workingSha256',
                     'protectedPath','protectedSha256','expectedGuidCount'} and
        m['schema']=='APA_AC29_LOCAL_RUNTIME_UPDATE_V1' and
        set(m['oldHashes'])==set(targets),'LOCAL_UPDATE_EXACT_MANIFEST_REQUIRED')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout).decode().strip()
    require(revision==m['revision'] and len(revision)==40,'UPDATE_SOURCE_REVISION_DRIFT')
    working,original=Path(m['workingPath']),Path(m['protectedPath'])
    # The installed worker owns the exact approved paths; manifests cannot
    # turn this updater into an arbitrary project/receiver installer.
    import importlib.util
    spec=importlib.util.spec_from_file_location('apa_installed_update_target',worker)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    require(working==old.WORKING and original==old.ORIGINAL and
        type(m['expectedGuidCount']) is int and m['expectedGuidCount']>0,
        'UPDATE_MUST_PRESERVE_INSTALLED_PROJECT_SCOPE')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def unchanged():
        require(sha(working)==m['workingSha256'] and sha(original)==m['protectedSha256'],
                'UPDATE_PROJECT_BYTES_CHANGED')
    unchanged()
    payload={}
    for name,target in targets.items():
        current=sha(target) if target.exists() else None
        require(current==m['oldHashes'][name],'UPDATE_INSTALLED_FILE_DRIFT:'+name)
        data=subprocess.check_output(['git','show',revision+':scripts/'+name],cwd=checkout)
        compile(data.decode('utf-8-sig'),name,'exec');payload[name]=data
    # Immutable Git data, not potentially dirty checkout source files.
    updated_hashes={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}
    state=ROOT/'apa-job-bridge-state'
    require(all((p/'result.json').exists() for p in state.iterdir()
                if p.is_dir() and (p/'attempted.json').exists()),
            'UPDATE_BLOCKED_BY_IN_FLIGHT_OR_UNKNOWN_RECEIVER_JOB')
    protected_state={p:sha(p) for p in state.rglob('*') if p.is_file()
        and p.name not in {'bridge.log','.single-instance.lock','receiver-started.json'}}
    ledger=Path(os.environ['LOCALAPPDATA'])/'APA_BDD_Window1p8'/'apa_scene_writer.sqlite'
    require(ledger.is_file(),'ORIGINAL_SCENEWRITER_LEDGER_MISSING')
    protected_state[ledger]=sha(ledger)
    def state_unchanged():
        require(all(p.is_file() and sha(p)==digest for p,digest in protected_state.items()),
                'UPDATE_EXISTING_QUEUE_OR_SQLITE_BYTES_CHANGED')
    before=processes(worker)
    ids={r['ProcessId'] for r in before}
    require(before and len([r for r in before if r['ParentProcessId'] not in ids])==1,
            'UPDATE_REQUIRES_ONE_EXISTING_RECEIVER_PROCESS_TREE')
    report={'status':'UPDATE_PREFLIGHT_PASS_NO_CHANGES','revision':revision,
            'releaseHashes':updated_hashes,'modelWrites':0,'grantsInstalled':0}
    if not apply:return report
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=ROOT/'runtime-code-backups'/stamp;backup.mkdir(parents=True,exist_ok=False)
    release_path=worker.parent/'runtime-release.json'
    for name,target in targets.items():
        if target.exists():shutil.copy2(target,backup/name)
    if release_path.exists():shutil.copy2(release_path,backup/'runtime-release.json')
    (backup/'update-manifest.json').write_text(json.dumps(m,indent=2),encoding='utf8')
    # No new worker until the exact old tree is stopped and the same singleton
    # byte lock can be acquired. Existing Startup entry is preserved.
    require({r['ProcessId'] for r in processes(worker)}==ids,'UPDATE_RECEIVER_IDENTITY_CHANGED')
    subprocess.check_call(['powershell','-NoProfile','-Command',
        'Stop-Process -Id '+','.join(str(i) for i in sorted(ids))+' -Force -ErrorAction Stop'],timeout=30)
    for _ in range(30):
        if not processes(worker):break
        time.sleep(.2)
    require(not processes(worker),'OLD_RECEIVER_DID_NOT_STOP_NO_SECOND_WORKER')
    import msvcrt
    lock=(state/'.single-instance.lock').open('r+b');lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        unchanged()
        for name,target in targets.items():
            require((sha(target) if target.exists() else None)==m['oldHashes'][name],
                    'UPDATE_INSTALLED_FILE_CHANGED_DURING_STOP:'+name)
        for name,target in targets.items():
            staged=target.with_name(target.name+'.update-'+stamp)
            staged.write_bytes(payload[name]);staged.replace(target)
            require(sha(target)==updated_hashes[name],'UPDATE_FILE_READBACK_FAILED:'+name)
        release={'schema':'APA_AC29_RUNTIME_RELEASE_V1','revision':revision,
            'workerSHA256':updated_hashes[worker.name],
            'moduleHashes':{name:updated_hashes[name] for name in modules},
            'workingPlnSha256':m['workingSha256'],'expectedGuidCount':m['expectedGuidCount']}
        staged=release_path.with_suffix('.writing')
        staged.write_text(json.dumps(release,indent=2),encoding='utf8');staged.replace(release_path)
        check=subprocess.run([sys.executable,str(worker),'--healthcheck'],
            cwd=ROOT,capture_output=True,timeout=30)
        require(check.returncode==0 and b'APA_BRIDGE_HEALTHCHECK_PASS_NO_NATIVE_CALLS' in check.stdout,
                'UPDATED_RECEIVER_HEALTHCHECK_FAILED:'+check.stderr.decode(errors='replace')[-1000:])
        unchanged()
    except Exception:
        # Restore CODE ONLY. Never touch PLN, queues, job journals or SQLite.
        for name,target in targets.items():
            saved=backup/name
            if saved.exists():shutil.copy2(saved,target)
            elif target.exists() and sha(target)==updated_hashes[name]:target.unlink()
        prior=backup/'runtime-release.json'
        if prior.exists():shutil.copy2(prior,release_path)
        elif release_path.exists():release_path.unlink()
        raise
    finally:lock.close()
    with LOG.open('ab') as stream:
        spawned=subprocess.Popen([sys.executable,'-u',str(worker),'--loop'],cwd=ROOT,
            stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,
            creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    marker=state/'receiver-started.json'
    for _ in range(40):
        if marker.exists():
            started=json.loads(marker.read_text(encoding='utf8'))
            live=processes(worker)
            if (started.get('workerSHA256')==updated_hashes[worker.name] and
                started.get('pid') in {r['ProcessId'] for r in live}):break
        require(spawned.poll() is None,'UPDATED_RECEIVER_EXITED')
        time.sleep(.25)
    else:raise ValueError('UPDATED_RECEIVER_START_NOT_CONFIRMED')
    # A launch PID alone is insufficient: the child must hold the singleton.
    with (state/'.single-instance.lock').open('r+b') as probe:
        probe.seek(0)
        try:msvcrt.locking(probe.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:pass
        else:
            msvcrt.locking(probe.fileno(),msvcrt.LK_UNLCK,1)
            raise ValueError('UPDATED_RECEIVER_NOT_HOLDING_SINGLETON')
    unchanged()
    state_unchanged()
    report.update(status='UPDATED_RECEIVER_INTEGRITY_IMPORT_PROCESS_AND_SINGLETON_PASS',
        backup=str(backup),receiverPID=started['pid'],queuePreserved=True,
        sqlitePreserved=True,projectBytesPreserved=True)
    (backup/'update-result.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def source(repo, commit, path, sha):
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={commit}"],
        timeout=45, capture_output=True
    )
    require(result.returncode == 0, "GH_PINNED_SOURCE_ACCESS_FAILED:" +
            path)
    obj = json.loads(result.stdout.decode("utf-8"))
    data = base64.b64decode(obj["content"])
    calculated = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    require(calculated == sha == obj["sha"], "RELEASE_GIT_BLOB_MISMATCH")
    compile(data.decode("utf-8-sig"), path, "exec")
    return data


def install():
    require(sys.platform == "win32", "WINDOWS_REQUIRED")
    for name, expected in KNOWN.items():
        local = ROOT / "scripts" / name
        require(local.is_file() and
                hashlib.sha256(local.read_bytes()).hexdigest() == expected,
                "EXISTING_APA_CHANGED_REFUSE_UNSAFE_UPDATE:" + name)
    receipt = ROOT / "apa-selector-install-receipt.json"
    require(receipt.is_file() and
            json.loads(receipt.read_text(encoding="utf-8"))["applied"] is True,
            "STABLE_APA_UNVERIFIED")
    worker = source(REPO, WORKER_COMMIT,
                    "scripts/apa_ac29_autonomous_job_bridge.py", WORKER_BLOB)
    review = source(REPO, REVIEW_COMMIT,
                    "scripts/apa_bdd114_native_roof_face_review.py", REVIEW_BLOB)
    require(not CONTROLLERS.exists(),
            "BRIDGE_CONTROLLERS_ALREADY_EXIST_NO_OVERWRITE")
    startup = (Path(os.environ["APPDATA"]) /
               "Microsoft/Windows/Start Menu/Programs/Startup")
    require(startup.is_dir(), "WINDOWS_USER_STARTUP_FOLDER_NOT_FOUND")
    entry = startup / (NAME + ".vbs")
    require(not entry.exists(), "AUTOSTART_ENTRY_ALREADY_EXISTS_NO_OVERWRITE")

    path = CONTROLLERS / "apa_ac29_autonomous_job_bridge.py"
    launcher = CONTROLLERS / "start-apa-bridge.cmd"
    try:
        CONTROLLERS.mkdir(parents=True, exist_ok=False)
        path.write_bytes(worker)
        (CONTROLLERS / "apa_bdd114_native_roof_face_review.py").write_bytes(review)
        logdir = LOG.parent
        logdir.mkdir(parents=True, exist_ok=True)
        py = Path(sys.executable).resolve()
        require(py.is_file(), "SELECTED_PYTHON_EXECUTABLE_MISSING")
        launcher.write_text(
            "@echo off\r\n"
            "cd /d \"" + str(ROOT) + "\"\r\n"
            "\"" + str(py) + "\" -u \"" + str(path) +
            "\" --loop >>\"" + str(LOG) + "\" 2>&1\r\n",
            encoding="utf-8"
        )
        vbs = (
            "Set shell = CreateObject(\"WScript.Shell\")\r\n"
            "shell.Run Chr(34) & \"" + str(launcher).replace("\\", "\\\\") +
            "\" & Chr(34), 0, False\r\n"
        )
        # VBS string literals use raw backslash, not Python/JSON escaping.
        vbs = vbs.replace("\\\\", "\\")
        entry.write_text(vbs, encoding="utf-8")
        checked = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True, timeout=30
        )
        require(checked.returncode == 0,
                "INSTALLED_BRIDGE_CANNOT_IMPORT_OR_PARSE")
        # Create new detached process. Startup entry preserves it across reboot.
        with LOG.open("ab") as stream:
            spawned = subprocess.Popen(
                [str(py), "-u", str(path), "--loop"],
                cwd=ROOT, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=stream,
                creationflags=subprocess.CREATE_NO_WINDOW,
                close_fds=True
            )
        report = {
            "schema": "APA_AC29_BRIDGE_INSTALL_V1",
            "status": "BRIDGE_AUTOSTART_INSTALLED_PROCESS_LAUNCHED",
            "root": str(ROOT),
            "workerSourceBlob": WORKER_BLOB,
            "reviewSourceBlob": REVIEW_BLOB,
            "workerPid": spawned.pid,
            "startupEntry": str(entry),
            "log": str(LOG),
            "apaCorePreserved": True,
            "apaDynamicPreserved": True,
            "apaSelectorPreserved": True,
            "existingDispatcherUnchanged": True,
            "existingMailboxWatcherUnchanged": True,
            "archicadModelWrites": 0,
            "nativeBuildAuthorization": False,
        }
        (CONTROLLERS / "installation.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        print("APA_STATUS:", report["status"])
        print("PID:", report["workerPid"])
        print("AUTOSTART:", entry)
        print("LOG:", LOG)
        print("MODEL_WRITES: 0")
    except Exception:
        # Never remove unknown/existing artifacts; rollback only known newly
        # created files. Do not alter the stable APA scripts or user PLN.
        if entry.exists():
            entry.unlink()
        raise


if __name__ == "__main__":
    try:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--update-from-checkout',type=Path)
        parser.add_argument('--manifest',type=Path)
        parser.add_argument('--apply',action='store_true')
        args=parser.parse_args()
        if args.update_from_checkout:
            require(args.manifest is not None,'LOCAL_UPDATE_MANIFEST_REQUIRED')
            print(json.dumps(update_from_checkout(args.update_from_checkout,args.manifest,args.apply),indent=2))
        else:
            install()
    except Exception as e:
        print("APA_STATUS: BRIDGE_INSTALL_BLOCKED")
        print("ERROR:", type(e).__name__ + ": " + str(e))
        sys.exit(2)
