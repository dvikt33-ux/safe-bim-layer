import sys,json,hashlib,importlib.metadata,tempfile
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
parser=argparse.ArgumentParser(description='Saved native/IFC data through the existing APA catalog; no native writes')
parser.add_argument('--native-dump',required=True,type=Path);parser.add_argument('--ifc',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands
root=ROOT;r=DynamicCommands(json.loads((root/'schemas/accelerator/mass-capabilities/commands.json').read_text(encoding='utf8')))
A.connect_functional_modules(r);before=r.fingerprint;A.connect_functional_modules(r);assert r.fingerprint==before
call=lambda name,p:r.read(None,r.prepare('AddOn.APAAnalysis.'+name,p),True)
dump=json.loads(args.native_dump.read_text(encoding='utf8'))
normalized=call('NormalizeNativeDump',dict(dump=dump));quantities=call('NativeBodyQuantities',dict(elements=normalized['elements']))
impact=call('DependencyImpact',dict(nodes=['story','wall','window','roof'],edges=[['story','wall'],['wall','window'],['story','roof']],changed=['story']));assert impact['affected']==['roof','story','wall','window']
cycle=call('DependencyImpact',dict(nodes=['a','b'],edges=[['a','b'],['b','a']],changed=['a']));assert cycle['status']=='CYCLIC'
polygons=[dict(id='slab',outline=[[0,0],[6,0],[6,6],[0,6]],holes=[[[2,2],[4,2],[4,4],[2,4]]]),dict(id='opening',outline=[[2.1,2.1],[3.9,2.1],[3.9,3.9],[2.1,3.9]]),dict(id='touching',outline=[[6,0],[7,0],[7,6],[6,6]])]
relations=call('PolygonRelations',dict(polygons=polygons));assert relations['polygons'][0]['area']==32 and len(relations['relations'])==1 and relations['relations'][0]['touches']
assignment=call('ConstrainedAssignment',dict(tasks=[dict(id='first',costs={'a':1,'b':8}),dict(id='second',costs={'a':2,'b':3})],capacities={'a':1,'b':1}));assert assignment['status']=='OPTIMAL' and assignment['objective']==4
ifc=args.ifc
selected=call('IFCSelect',dict(path=str(ifc),query='IfcWall'));assert selected['elements']
validated=call('IFCValidate',dict(path=str(ifc)))
geometry=call('IFCGeometry',dict(path=str(ifc),guids=[e['ifcId'] for e in selected['elements'][:3]]));assert all(e['status']=='IFC_GEOMETRY_COMPUTED' and e['volume']>0 for e in geometry['elements'])
exchange=call('IFCExchangeFacts',dict(path=str(ifc)))
graph=dict(operations=[dict(id='normalize',command='AddOn.APAAnalysis.NormalizeNativeDump',params=dict(dump=dump)),dict(id='quantities',command='AddOn.APAAnalysis.NativeBodyQuantities',params={'elements':{'$result':dict(step='normalize',pointer='/elements')}})])
plan=A.prepare_native_workflow(r,graph);result=r.run_workflow(None,plan);assert result['status']=='WORKFLOW_CALLABLE_VERIFIED'
# The existing KG indexes summaries only and resolves selected schemas lazily.
with tempfile.TemporaryDirectory(dir='.') as temp:
    indexPath=Path(temp)/'index.sqlite3';r.index(Path(temp)/'command-summary.md',indexPath)
    matches=A.native_task_tools(r,indexPath,'Dependency Impact descendants',3);assert any('DependencyImpact' in x.get('command','') for x in matches['matches']['results'])
proof=dict(schema='APA_FUNCTIONAL_MODULE_LOCAL_PROOF_V1',status='LOCAL_CALLABLE_VERIFIED',nativeWrites=0,nativeAPXInstalled=False,engineering='NOT_VERIFIED',catalog=dict(total=len(r.catalog['commands']),nativeOrOfficial=368,local=9,newNativeSDK=5,reusedDevKitBuildCommand=1,newAnalyticalCapabilities=6,reusedExistingAPAUtilities=3),versions={p:importlib.metadata.version(p) for p in ['ifcopenshell','networkx','shapely','ortools']},commands=list(r.callable),evidenceDomain='LOCAL_COMPUTATION_ON_SAVED_NATIVE_DUMP_AND_ARCHICAD_IFC_EXPORT_NOT_NEW_LIVE_READ',sources=dict(nativeDumpSHA256=hashlib.sha256(args.native_dump.read_bytes()).hexdigest(),ifcSHA256=hashlib.sha256(ifc.read_bytes()).hexdigest()),results=dict(normalizedElements=len(normalized['elements']),quantityStatuses={s:sum(e['quantities']['status']==s for e in quantities['elements']) for s in {e['quantities']['status'] for e in quantities['elements']}},impact=impact,cycle=cycle,polygonRelations=relations,assignment=assignment,ifcSelectionCount=len(selected['elements']),ifcValidationStatus=validated['status'],ifcValidationIssueCount=len(validated['issues']),ifcGeometry=[{k:v for k,v in e.items() if k!='ifcId'} for e in geometry['elements']],ifcExchangeCounts={k:len(exchange[k]) for k in ['voidRelations','materialAssignments','analyticalMembers']}),dataflow=dict(status=result['status'],steps=len(result['trace']),binding='NormalizeNativeDump.elements -> NativeBodyQuantities.elements',executor='Existing BIM Graph sequential dependency routing; no native mutation',KGselection=True,idempotentAttachment=True),events=[{k:v for k,v in e.items() if k!='inputHash'} for e in r.local_events])
path=args.output;path.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(status=proof['status'],commands=len(r.callable),ifcValidation=validated['status'],geometry=proof['results']['ifcGeometry'],catalog=len(r.catalog['commands']))))
