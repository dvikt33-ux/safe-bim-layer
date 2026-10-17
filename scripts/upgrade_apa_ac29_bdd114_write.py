"""Upgrade ONLY the existing APA AC29 receiver to one approved BDD 1.14 write action.

One-time, interactive current-user installation. Fail closed on process ambiguity,
pending prior jobs, model drift, startup mismatch or unexpected GitHub blobs.
Preserves original APA scripts, Dispatcher/Arena, job state and SQLite journals.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(r"C:\LocalAI\APA_AC29_Stable")
CTRL=ROOT/"controllers"
WORKER=CTRL/"apa_ac29_autonomous_job_bridge.py"
ADAPTER=CTRL/"apa_bdd114_native_copy_save_once.py"
STATE=ROOT/"apa-job-bridge-state"
WORKING=Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
PROTECTED=Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
REPO="dvikt33-ux/safe-bim-layer"
COMMIT="037b0ca1a8dec8f7971800dbe3471ba8a50a76fa"
PREVIOUS_WORKER_BLOB="ef52f5fc184c6ac59c1197c14e1bbbc06237fdd2"
NEW_WORKER_BLOB="4bf5f463517b3fa95b5c103a9377c3155acb9b2d"
NEW_ADAPTER_BLOB="eb94a3a3d4feb69bb0f65fa3400599f9f85ece1d"
PREVIOUS_ROOF_BLOB="35a7bd794317ba91056334aff6801cd0ec71f220"
WORKING_BASE="e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
SOURCE_BASE="33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"


def require(test, reason):
    if not test:raise ValueError(reason)


def blobhash(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+bytes([0])+raw).hexdigest()


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(path,expected):
    cmd=["gh","api",f"repos/{REPO}/contents/{path}?ref={COMMIT}"]
    p=subprocess.run(cmd,capture_output=True,timeout=45)
    require(p.returncode==0,"PINNED_GITHUB_UPGRADE_SOURCE_MISSING")
    obj=json.loads(p.stdout.decode("utf-8"))
    raw=base64.b64decode(obj["content"])
    require(blobhash(raw)==obj["sha"]==expected,"UPGRADE_SOURCE_BLOB_MISMATCH")
    compile(raw.decode("utf-8-sig"),path,"exec")
    return raw


def exact_processes():
    # Filter source executable by actual WMI command line, not mere python.exe.
    script=(
        "$ErrorActionPreference='Stop';"
        "Get-CimInstance Win32_Process | "
        "Where-Object {$_.Name -in @('python.exe','pythonw.exe') -and "
        "$_.CommandLine -match 'apa_ac29_autonomous_job_bridge[.]py'} | "
        "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    )
    p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",script],
                     capture_output=True,timeout=25)
    require(p.returncode==0,"WINDOWS_PROCESS_INSPECTION_FAILED")
    value=p.stdout.decode("utf-8-sig",errors="replace").strip()
    if not value:return []
    rows=json.loads(value)
    if isinstance(rows,dict):rows=[rows]
    require(isinstance(rows,list),"WMI_PROCESS_INSPECTION_INVALID")
    verified=[]
    for row in rows:
        cmd=row.get("CommandLine","").lower()
        require(str(WORKER).lower() in cmd and "--loop" in cmd,
                "FOREIGN_OR_UNVERIFIED_RECEIVER_PROCESS_FOUND")
        pid=row.get("ProcessId")
        require(type(pid)==int and pid>0,"RECEIVER_PROCESS_ID_INVALID")
        verified.append(pid)
    require(len(verified)<=1,"TWO_ACTIVE_RECEIVERS_REFUSING_UPGRADE")
    return verified


def previous_jobs_complete():
    require(STATE.is_dir(),"EXISTING_BRIDGE_STATE_MISSING")
    for path in STATE.iterdir():
        if not path.is_dir():continue
        if (path/"attempted.json").exists():
            require((path/"result.json").is_file(),
                    "IN_FLIGHT_OR_UNRECONCILED_NATIVE_JOB:"+path.name)


def install():
    require(sys.platform=="win32","WINDOWS_ONLY")
    require(WORKER.is_file() and STATE.is_dir(),"ORIGINAL_INSTALLED_RECEIVER_NOT_FOUND")
    current=blobhash(WORKER.read_bytes())
    if current==NEW_WORKER_BLOB and ADAPTER.is_file() and blobhash(ADAPTER.read_bytes())==NEW_ADAPTER_BLOB:
        print("APA_STATUS: VERIFIED_WRITE_ADAPTER_ALREADY_DEPLOYED")
        return
    require(current==PREVIOUS_WORKER_BLOB,
            "EXISTING_RECEIVER_MODIFIED_NO_OVERWRITE")
    require(not ADAPTER.exists(),"UNREVIEWED_ADAPTER_ALREADY_PRESENT")
    require(blobhash((CTRL/"apa_bdd114_native_roof_face_review.py").read_bytes())==PREVIOUS_ROOF_BLOB,
            "EXISTING_ROOF_REVIEW_DRIFT")
    require(filehash(WORKING)==WORKING_BASE and filehash(PROTECTED)==SOURCE_BASE,
            "SOURCE_OR_WORKING_PLN_CHANGED")
    require((ROOT/"apa-selector-install-receipt.json").is_file(),
            "STABLE_APA_INSTALL_RECEIPT_MISSING")
    startup=Path(os.environ["APPDATA"])/"Microsoft/Windows/Start Menu/Programs/Startup/APA-AC29-GPT-Bridge.vbs"
    launcher=CTRL/"start-apa-bridge.cmd"
    require(startup.is_file() and launcher.is_file() and
            str(WORKER).lower() in launcher.read_text(encoding="utf-8").lower(),
            "EXISTING_AUTOSTART_ENTRY_NOT_VERIFIED")
    previous_jobs_complete()
    receiver_bytes=source("scripts/apa_ac29_autonomous_job_bridge.py",NEW_WORKER_BLOB)
    adapter_bytes=source("scripts/apa_bdd114_native_copy_save_once.py",NEW_ADAPTER_BLOB)
    staged_worker=CTRL/"apa_ac29_autonomous_job_bridge.py.new"
    staged_adapter=CTRL/"apa_bdd114_native_copy_save_once.py.new"
    backup=CTRL/"apa_ac29_autonomous_job_bridge.py.v1.bak"
    require(not any(p.exists() for p in (staged_worker,staged_adapter,backup)),
            "UPGRADE_ARTIFACTS_ALREADY_EXIST_REFUSE_OVERWRITE")
    staged_worker.write_bytes(receiver_bytes)
    staged_adapter.write_bytes(adapter_bytes)
    # Validate the new worker CLI BEFORE stopping original receiver.
    ready=subprocess.run([sys.executable,str(staged_worker),"--help"],
                         capture_output=True,timeout=25)
    require(ready.returncode==0,"UPDATED_WORKER_CLI_NOT_IMPORTABLE")
    running=exact_processes()
    if running:
        previous_jobs_complete()
        os.kill(running[0],signal.SIGTERM)
        for _ in range(30):
            time.sleep(.2)
            if not exact_processes():break
        require(not exact_processes(),"OLD_RECEIVER_DID_NOT_STOP")
    # Backup allows manual recovery, without changing source PLN or SQL ledger.
    backup.write_bytes(WORKER.read_bytes())
    os.replace(staged_adapter,ADAPTER)
    os.replace(staged_worker,WORKER)
    log=STATE/"bridge.log"
    with log.open("ab") as stream:
        new=subprocess.Popen([sys.executable,"-u",str(WORKER),"--loop"],
                             cwd=ROOT,stdin=subprocess.DEVNULL,
                             stdout=stream,stderr=stream,
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             close_fds=True)
    time.sleep(2)
    require(new.poll() is None,"UPDATED_RECEIVER_EXITED_IMMEDIATELY")
    receipt={"status":"APA_BDD114_WRITE_ADAPTER_DEPLOYED_RECEIVER_RESTARTED",
             "previousPid":running[0] if running else None,
             "newPid":new.pid,"previousWorkerBlob":PREVIOUS_WORKER_BLOB,
             "newWorkerBlob":NEW_WORKER_BLOB,"writeAdapterBlob":NEW_ADAPTER_BLOB,
             "inboxStatePreserved":True,"originalPLNUnchanged":True,
             "workingPLNUnchanged":True,"sqliteLedgerUnchanged":True,
             "onlyApprovedAction":"BDD114_COPY_SAVE",
             "modelWrites":0}
    (CTRL/"bdd114-write-upgrade-receipt.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("APA_STATUS:",receipt["status"])
    print("NEW_PID:",new.pid)
    print("MODEL_WRITES: 0")
    print("UPGRADE_RECEIPT:",CTRL/"bdd114-write-upgrade-receipt.json")


if __name__=="__main__":
    try:install()
    except Exception as e:
        print("APA_STATUS: UPGRADE_BLOCKED_NO_AUTOMATIC_WRITE")
        print("ERROR:",type(e).__name__+": "+str(e))
        sys.exit(2)
