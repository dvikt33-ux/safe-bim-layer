from contextlib import closing
import argparse,hashlib,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import archicad_authored_extension as E
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source',required=True);p.add_argument('--operation-id',required=True);args=p.parse_args()
folder=Path(args.output);folder.mkdir(parents=True,exist_ok=False)
source=json.loads(Path(args.source).read_text(encoding='utf8'))
plan=source['preflight'];created=source['created'];expected=source['inventory'];children=source['columnSegments']
A.RUN.bind_isolated_writer_pln(19724)
api=A.EvidenceAPI(A.native_transport,folder);api.allowed=api.allowed|{'SaveProject','OpenProject'}
target=Path(A.RUN.APPROVED_ISOLATED_WRITER_PATH)
def verify():
    assert A.RUN.guarded_project(api,plan['storyBindings'][0])==plan['binding']
    E.verify_model(api,plan,created)
    assert A.inventory_guids(api)==expected
    assert A.column_subelements(api,created)==children
def filehash():return hashlib.sha256(target.read_bytes()).hexdigest()
receipt={'status':'BLOCKED','modelWriteAttempts':0,'nativeCreates':0,'preflight':plan,'created':created,'inventory':expected,'columnSegments':children,'automaticRetry':False}
try:
    verify();receipt['fileHashBefore']=filehash()
    with closing(sqlite3.connect('apa-live-state-isolated-writer/scene-v1-attempts.sqlite3')) as db:
        db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO isolated_persistence VALUES(?,?,?)',(args.operation_id,'ATTEMPTED',A.RUN.canonical({'path':str(target),'guids':expected,'commands':['SaveProject','OpenProject']})));db.commit()
    assert A.RUN.guarded_project(api,plan['storyBindings'][0])==plan['binding']
    receipt['saveResponse']=api('SaveProject',{});assert receipt['saveResponse'].get('success') is True
    receipt['fileHashAfterSave']=filehash();verify()
    receipt['openResponse']=api('OpenProject',{'projectFilePath':str(target)});assert receipt['openResponse'].get('success') is True
    verify();receipt['fileHashAfterReopen']=filehash()
    receipt.update(status='SAVED_REOPENED_BUILDING17_READBACK_PASS',primaryCount=17,inventoryCount=len(expected),visualUI='NOT_VERIFIED',structuralAcceptance='NOT_VERIFIED')
except Exception as exc:receipt.update(status='PARTIAL_OR_UNKNOWN_OUTCOME',reason=type(exc).__name__+': '+str(exc))
A.write_json(folder/'result.json',receipt)
A.write_json(folder/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()})
print(json.dumps({k:v for k,v in receipt.items() if k not in ('preflight','created','inventory')},ensure_ascii=True,indent=2))
sys.exit(0 if receipt['status']=='SAVED_REOPENED_BUILDING17_READBACK_PASS' else 2)
