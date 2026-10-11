import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import archicad_authored_extension as E
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source',required=True);p.add_argument('--width',type=float,required=True);p.add_argument('--operation-id',required=True);p.add_argument('--execute',action='store_true');p.add_argument('--confirm-plan-hash');args=p.parse_args()
folder=Path(args.output);folder.mkdir(parents=True,exist_ok=False)
sourcepath=Path(args.source);source=json.loads(sourcepath.read_text(encoding='utf8'))
assert hashlib.sha256(sourcepath.read_bytes()).hexdigest()==json.loads((sourcepath.parent/'SHA256.json').read_text(encoding='utf8'))[sourcepath.name]
assert source['status'] in ('SAVED_REOPENED_BUILDING17_READBACK_PASS','EXISTING_OPENING_EDIT_READBACK_PASS')
A.RUN.bind_isolated_writer_pln(19724);api=A.EvidenceAPI(A.native_transport,folder)
if args.execute:api.allowed=api.allowed|{'ModifyWindows'}
try:
    ticket=E.prepare_opening_width(api,source['preflight'],source['created'],'authored-window-east-1',args.width,Path('apa-live-state-isolated-writer/scene-v1-attempts.sqlite3'),args.operation_id)
    A.write_json(folder/'ticket.json',ticket)
    result=E.execute_opening_width(api,ticket,Path('apa-live-state-isolated-writer/scene-v1-attempts.sqlite3'),args.confirm_plan_hash) if args.execute else ticket
    if args.execute and result['status']=='EXISTING_OPENING_EDIT_READBACK_PASS':
        result.update(preflight=ticket['intent']['newPlan'],created=ticket['intent']['created'],inventory=ticket['intent']['inventory'],columnSegments=ticket['intent']['columnSegments'])
except Exception as exc:result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME' if api.calls['ModifyWindows'] else 'BLOCKED','reason':str(exc),'automaticRetry':False}
result.update(modelWriteAttempts=api.calls['ModifyWindows'],commandCounts=dict(api.calls))
A.write_json(folder/'result.json',result)
A.write_json(folder/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()})
print(json.dumps({k:v for k,v in result.items() if k not in ('intent','preflight','created','inventory')},ensure_ascii=True,indent=2))
sys.exit(0 if result['status'] in ('READY_FOR_EXISTING_OPENING_EDIT','EXISTING_OPENING_EDIT_READBACK_PASS') else 2)
