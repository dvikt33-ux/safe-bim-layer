import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import archicad_authored_extension as E
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--execute',action='store_true');p.add_argument('--confirm-plan-hash');args=p.parse_args()
folder=Path(args.output);folder.mkdir(parents=True,exist_ok=False)
A.RUN.bind_isolated_writer_pln(19724)
api=A.EvidenceAPI(A.native_transport,folder,execute=args.execute)
if args.execute:api.allowed=api.allowed|{'ModifyWalls'}
oldfolder=Path('apa-live-evidence/reconcile-execute-20261011-1937')
for base in [oldfolder,Path('apa-live-evidence/persistence-20261011-shell10')]:
    hashes=json.loads((base/'SHA256.json').read_text(encoding='utf8'))
    for name,h in hashes.items():
        assert Path(name).name==name and hashlib.sha256((base/name).read_bytes()).hexdigest()==h
oldplan=json.loads((oldfolder/'preflight.json').read_text(encoding='utf8'))['preflight']
oldresult=json.loads((oldfolder/'result.json').read_text(encoding='utf8'))
assert oldresult['status']=='COMPLETE_UNSAVED'
intent=json.loads(Path('apa-core/examples/accelerator/isolated-authored-building.json').read_text(encoding='utf8'))
journal=Path('apa-live-state-isolated-writer/scene-v1-attempts.sqlite3')
try:
    ticket=E.prepare(api,intent,oldplan,oldresult['steps'],journal,'isolated-authored-building17-20261011')
    A.write_json(folder/'preflight.json',ticket)
    result=E.execute(api,ticket,journal,args.confirm_plan_hash) if args.execute else ticket
except Exception as exc:result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME' if api.write_attempts or api.calls['ModifyWalls'] else 'BLOCKED','reason':str(exc),'automaticRetry':False}
result['modelWriteAttempts']=api.write_attempts+api.calls['ModifyWalls'];result['commandCounts']=dict(api.calls)
A.write_json(folder/'result.json',result)
A.write_json(folder/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()})
print(json.dumps({k:v for k,v in result.items() if k not in ('intent','preflight')},ensure_ascii=True,indent=2))
sys.exit(0 if result['status'] in ('READY_FOR_AUTHORED_EXTENSION','COMPLETE_UNSAVED') else 2)
