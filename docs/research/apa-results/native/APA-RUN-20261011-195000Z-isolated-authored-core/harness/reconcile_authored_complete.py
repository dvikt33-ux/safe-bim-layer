import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import archicad_authored_extension as E
folder=Path('apa-live-evidence/extension-reconciliation-20261011');folder.mkdir(parents=True,exist_ok=False)
A.RUN.bind_isolated_writer_pln(19724);api=A.EvidenceAPI(A.native_transport,folder)
base=Path('apa-live-evidence/extension-execute-20261011-2001')
for name,h in json.loads((base/'SHA256.json').read_text(encoding='utf8')).items():
    assert Path(name).name==name and hashlib.sha256((base/name).read_bytes()).hexdigest()==h
ticket=json.loads((base/'preflight.json').read_text(encoding='utf8'));result=json.loads((base/'result.json').read_text(encoding='utf8'))
assert result['status']=='PARTIAL_OR_UNKNOWN_OUTCOME' and result['failedStep']=='FINAL_READBACK'
plan=ticket['preflight'];old=ticket['intent'];created=result['steps']
assert len(created)==17
assert A.RUN.guarded_project(api,plan['storyBindings'][0])==plan['binding']
verified=E.verify_model(api,plan,created);children=A.column_subelements(api,verified)
original_owned={v['guid'].lower() for v in old['oldCreated'].values()}
expected=sorted((set(old['inventory'])-original_owned)|{v['guid'].lower() for v in verified.values()}|{g for group in children.values() for g in group})
assert A.inventory_guids(api)==expected
receipt={'status':'AUTHORED_BUILDING17_NATIVE_READBACK_PASS','modelWriteAttempts':0,'baselineCount':20,
    'primaryCount':17,'columnSegmentCount':2,'inventoryCount':len(expected),'inventory':expected,
    'created':verified,'columnSegments':children,'preflight':plan,'historicalFailurePreserved':True,
    'guidLoss':0,'unexpectedGuidCount':0,'visualUI':'NOT_VERIFIED','structuralAcceptance':'NOT_VERIFIED'}
A.write_json(folder/'result.json',receipt)
A.write_json(folder/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()})
print(json.dumps({k:v for k,v in receipt.items() if k not in ('preflight','created','inventory')},ensure_ascii=True,indent=2))
