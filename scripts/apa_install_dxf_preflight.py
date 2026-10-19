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
    old=(root/FILES[0]).read_bytes()
    if sha(old)!=PIN or (root/FILES[1]).exists() or stage.exists() or root==source or not stage.parent.is_dir():
        raise ValueError('DXF_INSTALL_EXACT_CURRENT_FACTORY_AND_NEW_STAGE_REQUIRED')
    before=inspect_factory(root/'scripts',root)
    stage.mkdir();(stage/'scripts').mkdir()
    new={n:(source/n).read_bytes() for n in FILES}
    for n,data in new.items():compile(data,n,'exec');(stage/n).write_bytes(data)
    preview=inspect_factory(stage/'scripts',root)
    if before['contracts']!={k:preview['contracts'][k] for k in before['contracts']} or len(preview['contracts'])!=len(before['contracts'])+1:
        raise ValueError('DXF_INSTALL_PREVIOUS_CONTRACT_DRIFT')
    backup=root/'runtime-code-backups'/('dxf-preflight-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir();(backup/'apa_ac29_installed_factory.py').write_bytes(old)
    for n,data in new.items():atomic(root/n,data)
    try:
        after=inspect_factory(root/'scripts',root)
        if after!=preview or any((root/n).read_bytes()!=data for n,data in new.items()):raise ValueError('DXF_INSTALL_READBACK_DRIFT')
    except BaseException:
        atomic(root/FILES[0],old)
        raise
    result=dict(status='INSTALLED_READY_DXF_SOURCE_PREFLIGHT',files={n:dict(beforeSHA256=sha(old) if n==FILES[0] else None,afterSHA256=sha(data)) for n,data in new.items()},
        originalContractCount=len(before['contracts']),allPreviousContractsPreserved=True,inventory=after['inventory'],backupRetainedLocally=True,
        dependenciesReinstalled=False,nativeCalls=0,modelWrites=0,stageValidatedBeforeApply=True)
    (backup/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--stage',type=Path,required=True)
    a=p.parse_args();print(json.dumps(install(a.root,a.source,a.stage),ensure_ascii=False,indent=2))
