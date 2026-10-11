import hashlib,json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import archicad_authored_extension as E
folder=Path('apa-live-evidence/core-final-readonly-20261011');folder.mkdir(parents=True,exist_ok=False)
source=json.loads(Path('apa-live-evidence/persistence-20261011-after-edit-restore/result.json').read_text(encoding='utf8'))
original=json.loads(Path('apa-live-evidence/persistence-20261011-building17/result.json').read_text(encoding='utf8'))
assert source['status']=='SAVED_REOPENED_BUILDING17_READBACK_PASS'
assert source['created']==original['created'] and source['preflight']['graph']==original['preflight']['graph']
A.RUN.bind_isolated_writer_pln(19724);api=A.EvidenceAPI(A.native_transport,folder)
assert A.RUN.guarded_project(api,source['preflight']['storyBindings'][0])==source['preflight']['binding']
product=A.archicad29(api)
intent=json.loads(Path('apa-core/examples/accelerator/isolated-authored-building.json').read_text(encoding='utf8'))
compiled=A.compile_authored_intent(intent,A.RUN.DEFAULT_SCENE_SCHEMA,api)
assert compiled['graph']==source['preflight']['graph']
owned={v['guid'].lower() for v in source['created'].values()}|{g for group in source['columnSegments'].values() for g in group}
def scan(cmd,params):
    result=api(cmd,params)
    if cmd=='GetAllElements':
        assert sorted(r['elementId']['guid'].lower() for r in result['elements'])==source['inventory']
        return {'elements':[r for r in result['elements'] if r['elementId']['guid'].lower() not in owned]}
    return result
writer=A.RUN.SceneWriter(scan,Path('apa-live-state-isolated-writer/scene-v1-attempts.sqlite3'),preview_factory=A.AUTHORED_NATIVE.make_read_only_scene_writer_preview_factory(compiled['authoredCandidate']))
plan=writer.preflight(40,40)
assert plan['sourcePlanHash']==original['preflight']['sourcePlanHash']
E.verify_model(api,plan,source['created'])
assert A.column_subelements(api,source['created'])==source['columnSegments']
assert A.inventory_guids(api)==source['inventory']
receipt={'status':'AUTHORED_CORE_FINAL_READONLY_PASS','modelWriteAttempts':0,'archicadProduct':product,
    'intentHash':compiled['intentHash'],'preflight':plan,'created':source['created'],'inventory':source['inventory'],
    'columnSegments':source['columnSegments'],'counts':dict(Counter(v['kind'] for v in source['created'].values())),
    'originalGeometryRestored':True,'originalBoundPlanHashRestored':True,'baselineGuidsPreserved':True,
    'savedReopenedEvidence':'persistence-20261011-after-edit-restore/result.json',
    'visualUI':'NOT_VERIFIED','structuralAcceptance':'NOT_VERIFIED','normativeAcceptance':'NOT_VERIFIED',
    'requiredUnsupportedComponents':[],'expansionLimitations':['roof','stair','MEP','automatic space planning','junction quality','Archicad30']}
A.write_json(folder/'result.json',receipt)
A.write_json(folder/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()})
print(json.dumps({k:v for k,v in receipt.items() if k not in ('preflight','created','inventory','columnSegments')},ensure_ascii=True,indent=2))
