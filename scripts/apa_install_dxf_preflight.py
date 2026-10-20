"""Incremental ready-DXF installation on the accepted current APA, no packages.

Stages two files, imports the real existing factory in a child process, checks
every previous command contract, backs up the old factory, then applies.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys
from apa_install_mass_selector import atomic
PIN='32fffd5d6da4bd99a16c3be9c697c57e5d878d2b90cd64c618317f48540c8c0e'
FILES=('scripts/apa_ac29_installed_factory.py','scripts/apa_dxf_source_preflight.py')

def sha(data):return hashlib.sha256(data).hexdigest()

def inspect_factory(scripts,root):
    code="""import sys,json,pathlib;sys.path[:0]=sys.argv[1:3];import apa_ac29_installed_factory as F;F.ROOT=pathlib.Path(sys.argv[3]);r=F.native_command_router();print(json.dumps(dict(inventory=F.inventory(r),contracts={k:r.contract_hash(k) for k in r.catalog['commands']})))"""
    return json.loads(subprocess.check_output([sys.executable,'-c',code,str(scripts),str(root/'scripts'),str(root)],text=True,encoding='utf8'))

def install(root,source,stage):
    root,source,stage=[Path(p).resolve() for p in (root,source,stage)]
    old=(root/FILES[0]).read_bytes();old_files={FILES[0]:old}
    upgrade=(sha(old)=='dda2b87d7dbab7a6d53f3e40bd2296812e08b0998084c2b4dc53bc1404a878bf' and
             (root/FILES[1]).is_file() and sha((root/FILES[1]).read_bytes())=='4e9b866860755f5fee63ecc2a1682a84f646158c5a9a0260a3f9c6fa0d9ea064')
    initial=sha(old)==PIN and not (root/FILES[1]).exists()
    if not (initial or upgrade) or stage.exists() or root==source or not stage.parent.is_dir():
        raise ValueError('DXF_INSTALL_EXACT_CURRENT_FACTORY_AND_NEW_STAGE_REQUIRED')
    if upgrade:old_files[FILES[1]]=(root/FILES[1]).read_bytes()
    before=inspect_factory(root/'scripts',root)
    stage.mkdir();(stage/'scripts').mkdir()
    new={n:(source/n).read_bytes() for n in FILES}
    for n,data in new.items():compile(data,n,'exec');(stage/n).write_bytes(data)
    preview=inspect_factory(stage/'scripts',root)
    updated={'AddOn.APADXFPreflight.DXFSourcePreflight'} if upgrade else set()
    checked={k:v for k,v in before['contracts'].items() if k not in updated}
    if checked!={k:preview['contracts'][k] for k in checked} or len(preview['contracts'])!=len(before['contracts'])+int(initial):
        raise ValueError('DXF_INSTALL_PREVIOUS_CONTRACT_DRIFT')
    backup=root/'runtime-code-backups'/('dxf-preflight-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir()
    for n,data in old_files.items():(backup/Path(n).name).write_bytes(data)
    for n,data in new.items():atomic(root/n,data)
    try:
        after=inspect_factory(root/'scripts',root)
        if after!=preview or any((root/n).read_bytes()!=data for n,data in new.items()):raise ValueError('DXF_INSTALL_READBACK_DRIFT')
    except BaseException:
        for n,data in old_files.items():atomic(root/n,data)
        raise
    result=dict(status='INSTALLED_READY_DXF_SOURCE_PREFLIGHT',files={n:dict(beforeSHA256=sha(old_files[n]) if n in old_files else None,afterSHA256=sha(data)) for n,data in new.items()},
        originalContractCount=len(before['contracts']),allPreviouslyAcceptedContractsPreserved=True,updatedPendingContractIds=sorted(updated),
        allPreviousContractsPreserved=not updated,inventory=after['inventory'],backupRetainedLocally=True,
        dependenciesReinstalled=False,nativeCalls=0,modelWrites=0,stageValidatedBeforeApply=True)
    (backup/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--stage',type=Path,required=True)
    a=p.parse_args();print(json.dumps(install(a.root,a.source,a.stage),ensure_ascii=False,indent=2))
