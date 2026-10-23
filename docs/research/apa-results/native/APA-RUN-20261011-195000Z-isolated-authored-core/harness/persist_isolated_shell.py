from contextlib import closing
import hashlib,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import reconcile_apa_isolated_authored as R
folder=Path('apa-live-evidence/persistence-20261011-shell10');folder.mkdir(parents=True,exist_ok=False)
A.RUN.bind_isolated_writer_pln(19724)
api=A.EvidenceAPI(A.native_transport,folder)
api.allowed=api.allowed|{'SaveProject','OpenProject'}
plan=json.loads(Path('apa-live-evidence/reconcile-execute-20261011-1937/preflight.json').read_text(encoding='utf8'))['preflight']
result=json.loads(Path('apa-live-evidence/reconcile-execute-20261011-1937/result.json').read_text(encoding='utf8'))
ops={s['id']:s for s in plan['graph']['operations']}
target=Path(A.RUN.APPROVED_ISOLATED_WRITER_PATH)
def filehash():return hashlib.sha256(target.read_bytes()).hexdigest()
def verify():
    assert A.RUN.guarded_project(api,plan['storyBindings'][0])==plan['binding'],'TARGET_DRIFT'
    for sid,row in result['steps'].items():R.verify_step(api,ops[sid],row['guid'],plan)
    return A.inventory_guids(api)
receipt={'status':'BLOCKED','automaticRetry':False,'nativeCreates':0}
try:
    before=verify();receipt['fileHashBefore']=filehash()
    assert len(before)==30 and result['status']=='COMPLETE_UNSAVED'
    journal=Path('apa-live-state-isolated-writer/scene-v1-attempts.sqlite3')
    with closing(sqlite3.connect(journal)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS isolated_persistence(operation_id TEXT PRIMARY KEY,state TEXT,intent TEXT)')
        db.commit();db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO isolated_persistence VALUES(?,?,?)',('shell10-save-reopen-20261011','ATTEMPTED',A.RUN.canonical({'path':str(target),'guids':before,'commands':['SaveProject','OpenProject']})));db.commit()
    assert A.RUN.guarded_project(api,plan['storyBindings'][0])==plan['binding']
    saved=api('SaveProject',{});receipt['saveResponse']=saved
    assert saved.get('success') is True,'SAVE_NOT_CONFIRMED'
    receipt['fileHashAfterSave']=filehash()
    assert verify()==before,'POST_SAVE_NATIVE_DRIFT'
    opened=api('OpenProject',{'projectFilePath':str(target)});receipt['openResponse']=opened
    assert opened.get('success') is True,'REOPEN_NOT_CONFIRMED'
    after=verify();assert after==before,'POST_REOPEN_NATIVE_DRIFT'
    receipt.update(status='SAVED_REOPENED_NATIVE_READBACK_PASS',guidCount=len(after),verifiedCreatedGuids=10,binding=plan['binding'],fileHashAfterReopen=filehash())
except Exception as exc:receipt.update(status='PARTIAL_OR_UNKNOWN_OUTCOME',reason=type(exc).__name__+': '+str(exc))
A.write_json(folder/'result.json',receipt);A.write_json(folder/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()})
print(json.dumps(receipt,ensure_ascii=True,indent=2))
sys.exit(0 if receipt['status']=='SAVED_REOPENED_NATIVE_READBACK_PASS' else 2)
