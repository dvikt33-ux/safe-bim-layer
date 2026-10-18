"""Opt-in controller-only AP2 read-only extension for the EXISTING APA receiver.

Never replaces APA core, never resets journals, never touches PLN, never
starts a second worker. Requires exact existing runtime-release SHA receipt,
a clean idle receiver and a single installed worker process.

This is an exceptional one-time upgrade, not a command executor.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(r"C:\LocalAI\APA_AC29_Stable")
CONTROLLERS=ROOT/"controllers"
WORKER=CONTROLLERS/"apa_ac29_autonomous_job_bridge.py"
RELEASE=CONTROLLERS/"runtime-release.json"
LAUNCHER=CONTROLLERS/"start-apa-bridge.cmd"
STATE=ROOT/"apa-job-bridge-state"
LOG=STATE/"bridge.log"
TARGET=Path(r"C:\Users\Admin\Documents\APA_AC29_Projects\AP2_Amur_Test\APA_AP2_Amur_Test_AC29.pln")
SOURCE=Path(__file__).resolve().parent/"apa_ac29_autonomous_job_bridge.py"
SPECIAL="AP2_READONLY_PROJECT_INVENTORY"
BRIDGE="dvikt33-ux/safe-bim-bridge"
INBOX="safe-bim-mailbox/apa-ac29/jobs"

def require(value,why):
    if not value:raise RuntimeError(why)

def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda:fd.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()

def import_installer():
    f=SOURCE.parent/"install_apa_ac29_autonomous_job_bridge.py"
    require(f.is_file(),"PINNED_INSTALLER_FILE_NOT_PRESENT")
    spec=importlib.util.spec_from_file_location("apa_guarded_prior_installer",f)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def compare_source_guards(old,new):
    # Require the new worker to preserve exact BDD and queue routing bytes.
    guards=(
        "WORKING = Path(", "ORIGINAL = Path(",
        'BRIDGE = "dvikt33-ux/safe-bim-bridge"',
        'INBOX = "safe-bim-mailbox/apa-ac29/jobs"',
        'RESULTS = "safe-bim-mailbox/apa-ac29/results"',
        "SOURCE_SHA = ", "BASE_SHA = "
    )
    for marker in guards:
        a=[r for r in old.splitlines() if r.startswith(marker)]
        b=[r for r in new.splitlines() if r.startswith(marker)]
        require(len(a)==len(b)==1 and a[0]==b[0],
                "ORIGINAL_WORKER_TARGET_OR_QUEUE_CHANGED:"+marker)
    require(SPECIAL not in old and new.count('def capture_ap2_inventory')==1
            and 'AP2_PORT = 19725' in new
            and 'readyForConstructionWrite": False' in new,
            "AP2_NEW_CONTROLLER_IS_NOT_BOUNDED")
    compile(new, str(SOURCE), "exec")

def pending_readonly_jobs_are_idle():
    # A just-started native operation must not be killed by this upgrade.
    now=time.time()
    if STATE.is_dir():
        for folder in STATE.iterdir():
            if not folder.is_dir():continue
            attempt=folder/"attempted.json"
            result=folder/"result.json"
            if attempt.exists() and not result.exists():
                raise RuntimeError("POSSIBLY_ACTIVE_EXISTING_APA_JOB:"+folder.name)

def python_from_launcher():
    require(LAUNCHER.is_file(),"STARTUP_LAUNCHER_MISSING")
    src=LAUNCHER.read_text(encoding="utf-8-sig",errors="strict")
    # The exact installed launcher created by the prior approved installer.
    line=next((x.strip() for x in src.splitlines()
               if "apa_ac29_autonomous_job_bridge.py" in x),None)
    require(line is not None,"INSTALLED_RECEIVER_LAUNCHER_MISSING")
    m=re.match(r'^"([^"]+\\python(?:\.exe)?)"\s+-u\s+',line,re.I)
    require(bool(m),"INSTALLED_PYTHON_CANNOT_BE_VERIFIED")
    py=Path(m.group(1))
    require(py.is_file() and py.name.lower()=="python.exe",
            "PYTHON_EXECUTABLE_INVALID")
    return py

def worker_processes(installer):
    """One receiver may have a parent and child Python process on Windows.

    The EXISTING APA updater already permits exactly one process tree.
    Reject independent roots, broken parent chains, or unrecognized commands.
    Return every member, never pick one PID arbitrarily.
    """
    rows=installer.processes(WORKER)
    if not rows:
        return []
    ids=[r["ProcessId"] for r in rows]
    require(len(ids)==len(set(ids)),"APA_RECEIVER_DUPLICATE_PROCESS_ID")
    by_pid={r["ProcessId"]:r for r in rows}
    for row in rows:
        line=row.get("CommandLine") or ""
        require(str(WORKER).casefold() in line.casefold()
                and "--loop" in line.split(),
                "APA_RECEIVER_UNEXPECTED_COMMAND_LINE")
    roots=[row for row in rows if row["ParentProcessId"] not in by_pid]
    require(len(roots)==1,"MULTIPLE_APA_RECEIVERS_FOUND_REFUSE_UPDATE")
    root_pid=roots[0]["ProcessId"]
    for row in rows:
        current=row["ProcessId"]
        traversed=set()
        while by_pid[current]["ParentProcessId"] in by_pid:
            require(current not in traversed,
                    "APA_RECEIVER_CYCLIC_PARENT_PROCESS_CHAIN")
            traversed.add(current)
            current=by_pid[current]["ParentProcessId"]
        require(current==root_pid,
                "MULTIPLE_APA_RECEIVERS_FOUND_REFUSE_UPDATE")
    return rows


def stop_receiver_tree(installer, before):
    """Stop only verified tree members, descendants before parent.

    No taskkill /T: unrelated children must never be terminated.
    """
    require(before and set(r["ProcessId"] for r in before) ==
            set(r["ProcessId"] for r in worker_processes(installer)),
            "RECEIVER_PROCESS_TREE_CHANGED_BEFORE_STOP")
    by_pid={r["ProcessId"]:r for r in before}
    def depth(row):
        n=0
        parent=row["ParentProcessId"]
        while parent in by_pid:
            n+=1
            parent=by_pid[parent]["ParentProcessId"]
        return n
    for row in sorted(before,key=depth,reverse=True):
        pid=row["ProcessId"]
        current={r["ProcessId"] for r in worker_processes(installer)}
        if pid not in current:
            continue
        stopped=subprocess.run(["taskkill","/PID",str(pid),"/F"],
                               capture_output=True,timeout=20)
        require(stopped.returncode==0 or
                pid not in {r["ProcessId"] for r in worker_processes(installer)},
                "OLD_RECEIVER_PROCESS_COULD_NOT_STOP:"+str(pid))
    for _ in range(30):
        if not worker_processes(installer):
            return
        time.sleep(.25)
    raise RuntimeError("OLD_RECEIVER_TREE_STILL_RUNNING")

def create_controller_backup(data,release):
    backup=CONTROLLERS/("backups-ap2-readonly-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    backup.mkdir(parents=False,exist_ok=False)
    (backup/WORKER.name).write_bytes(data)
    (backup/RELEASE.name).write_bytes(release)
    return backup

def run():
    require(sys.platform=="win32","WINDOWS_ONLY")
    require(WORKER.is_file() and RELEASE.is_file()
            and SOURCE.is_file() and TARGET.is_file()
            and STATE.is_dir(),"INSTALLED_RECEIVER_OR_AP2_MISSING")
    installed=WORKER.read_bytes()
    new=SOURCE.read_bytes()
    release_bytes=RELEASE.read_bytes()
    receipt=json.loads(release_bytes.decode("utf-8"))
    require(receipt.get("schema")=="APA_AC29_RUNTIME_RELEASE_V1"
            and receipt.get("workerSHA256")==sha(WORKER)
            and isinstance(receipt.get("moduleHashes"),dict),
            "INSTALLED_RECEIVER_RUNTIME_RELEASE_SHA_DRIFT")
    for filename,expected in receipt["moduleHashes"].items():
        require((ROOT/"scripts"/filename).is_file()
                and sha(ROOT/"scripts"/filename)==expected,
                "INSTALLED_CORE_MODULE_CHANGED:"+filename)
    compare_source_guards(installed.decode("utf-8"),new.decode("utf-8"))
    require(sha(WORKER)!=sha(SOURCE),"AP2_RECEIVER_UPDATE_ALREADY_INSTALLED")
    pending_readonly_jobs_are_idle()
    installer=import_installer()
    before=worker_processes(installer)
    py=python_from_launcher()
    saved_target_sha=sha(TARGET)
    check=subprocess.run([str(py),"-m","py_compile",str(SOURCE)],
                         capture_output=True,timeout=25)
    require(check.returncode==0,"NEW_RECEIVER_COMPILE_FAILED")
    # source file and local PLN are not modified by this preflight
    require(sha(TARGET)==saved_target_sha,"AP2_SOURCE_DISK_CHANGED_PREUPDATE")
    backup=create_controller_backup(installed,release_bytes)
    if before:
        stop_receiver_tree(installer,before)
    # Otherwise no running receiver was present; start exactly one after swap.
    replacement=WORKER.with_name(WORKER.name+".ap2-swap")
    payload=dict(receipt)
    payload["workerSHA256"]=sha(SOURCE)
    new_receipt=(json.dumps(payload,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    spawned=None
    try:
        replacement.write_bytes(new)
        os.replace(replacement,WORKER)
        release_swap=RELEASE.with_name(RELEASE.name+".ap2-swap")
        release_swap.write_bytes(new_receipt)
        os.replace(release_swap,RELEASE)
        require(sha(WORKER)==payload["workerSHA256"]
                and json.loads(RELEASE.read_text(encoding="utf-8"))["workerSHA256"]==sha(WORKER),
                "RECEIVER_NEW_BYTES_READBACK_FAILED")
        require(sha(TARGET)==saved_target_sha,"AP2_PLN_CHANGED_DURING_UPGRADE")
        with LOG.open("ab") as fd:
            spawned=subprocess.Popen([str(py),"-u",str(WORKER),"--loop"],
                  stdin=subprocess.DEVNULL,stdout=fd,stderr=fd,
                  cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        marker=STATE/"receiver-started.json"
        for _ in range(60):
            if spawned.poll() is not None:break
            if marker.is_file():
                evidence=json.loads(marker.read_text(encoding="utf-8"))
                if evidence.get("workerSHA256")==payload["workerSHA256"] and \
                    evidence.get("pid")==spawned.pid and \
                    any(x["ProcessId"]==spawned.pid for x in worker_processes(installer)):
                    break
            time.sleep(.25)
        else:raise RuntimeError("AP2_RECEIVER_START_NOT_CONFIRMED")
        require(spawned.poll() is None and marker.is_file()
                and json.loads(marker.read_text(encoding="utf-8")).get("pid")==spawned.pid,
                "AP2_RECEIVER_FAILED_TO_START")
        require(sha(TARGET)==saved_target_sha,"AP2_PLN_CHANGED_AFTER_UPGRADE")
    except Exception:
        if spawned is not None and spawned.poll() is None:
            subprocess.run(["taskkill","/PID",str(spawned.pid),"/F"],
                           capture_output=True,timeout=20)
            for _ in range(20):
                if not worker_processes(installer):break
                time.sleep(.2)
        shutil.copy2(backup/WORKER.name,WORKER)
        shutil.copy2(backup/RELEASE.name,RELEASE)
        # Start original worker only if it existed before.
        if before and not worker_processes(installer):
            with LOG.open("ab") as fd:
                subprocess.Popen([str(py),"-u",str(WORKER),"--loop"],
                        stdin=subprocess.DEVNULL,stdout=fd,stderr=fd,
                        cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        raise
    report={"status":"AP2_SAME_RECEIVER_UPDATED_LIVE",
            "sourceWorkerSHA256":payload["workerSHA256"],
            "previousWorkerSHA256":receipt["workerSHA256"],
            "localReceiverPID":spawned.pid,
            "targetPort":19725,
            "targetSavedPLNSHA256":saved_target_sha,
            "otherProjectsPreserved":True,
            "mainChanged":False,
            "existingMailboxesPreserved":True,
            "modelWrites":0,
            "backup":str(backup)}
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=="__main__":
    try:run()
    except Exception as exc:
        print("APA_AP2_SAME_RECEIVER_UPDATE_BLOCKED:"+type(exc).__name__+":"+str(exc),
              file=sys.stderr)
        sys.exit(2)
