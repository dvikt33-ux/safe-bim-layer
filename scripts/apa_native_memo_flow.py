"""Captured native parameter memo -> BIM Graph -> existing Shapely adapter.

No native calls or writes. Supply an explicit captured GetNativePolygonMemoV1
or GetNativeEnvelopeMemoV1 result; curves are retained as unsupported records.
"""
import argparse,hashlib,json
from pathlib import Path
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands

def run(memo):
    root=Path(__file__).resolve().parents[1]
    r=DynamicCommands(json.loads((root/'schemas/accelerator/mass-capabilities/commands.json').read_text(encoding='utf8')))
    A.connect_functional_modules(r)
    graph=dict(operations=[
        dict(id='memo',command='AddOn.APAAnalysis.MemoPolygonInputs',params=dict(memo=memo)),
        dict(id='relations',command='AddOn.APAAnalysis.PolygonRelations',params={'polygons':{'$result':dict(step='memo',pointer='/polygons')}})])
    plan=A.prepare_native_workflow(r,graph);answer=r.run_workflow(None,plan)
    converted=answer['results']['memo'];relations=answer['results']['relations']
    # Public proof carries counts/scalars and content hashes, not a native dump.
    proof=dict(schema='APA_NATIVE_MEMO_FLOW_V1',status=answer['status'],
        sourceMemoSHA256=hashlib.sha256(json.dumps(memo,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        preparedCommands=len(r.catalog['commands']),nativePrepared=372,localPrepared=10,
        sourceElements=len(memo['elements']),convertedElements=len(converted['polygons']),
        preservedHoles=sum(len(p['holes']) for p in converted['polygons']),
        omittedReasons=[x['reason'] for x in converted['omitted']],
        polygonMeasures=[{k:v for k,v in p.items() if k!='id'} for p in relations['polygons']],
        spatialRelationCount=len(relations['relations']),sourcePlanHash=answer['sourcePlanHash'],
        steps=answer['trace'],sourceDomain='CAPTURED_NATIVE_PARAMETER_MEMO',
        executor='Existing BIM Graph and local provider dispatch',
        nativeModelWrites=0,geometryAuthority='2D_PARAMETER_FOOTPRINTS_NOT_RESULTANT_BREP_OR_3D_COLLISION',
        engineering='NOT_VERIFIED')
    return proof

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memo',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();proof=run(json.loads(args.memo.read_text(encoding='utf8')))
    args.output.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(status=proof['status'],converted=proof['convertedElements'],holes=proof['preservedHoles'],nativeWrites=0)))
