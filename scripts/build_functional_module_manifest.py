"""Rebuild typed adapter schemas from code-owned declarations.

Uses the existing provider schema format. No runtime discovery, native call,
third-party import, provider search or new documentation service.
"""
import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S={'type':'string'};N={'type':'number'};I={'type':'integer'};B={'type':'boolean'}
def obj(properties,required=None,extra=False):
    return dict(type='object',properties=properties,required=list(properties) if required is None else required,additionalProperties=extra)
def arr(items,**bounds):return dict(type='array',items=items,**bounds)
def nullable(schema):return dict(anyOf=[schema,{'type':'null'}])
def sha(path):return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def build():
    cpp=ROOT/'archicad-addon/Sources/NativeModuleCommands.cpp';text=cpp.read_text(encoding='utf8')
    error=obj({'error':obj({'code':I,'message':S})})
    either=lambda row:dict(anyOf=[row,error])
    eid=obj({'guid':S});xyz=arr(N,minItems=3,maxItems=3)
    defaults=obj(dict(type=S,nativeTypeId=I,variationId=I,homeStory=I,layerIndex=I,height=N,thickness=N,buildingMaterialIndex=I,roofClass=I,shellClass=I,complexParameters=S),['type','nativeTypeId','variationId','homeStory','layerIndex'])
    polygon=obj(dict(elementId=eid,nativeTypeId=I,variationId=I,homeStory=I,coordinates=arr(obj({'index':I,'x':N,'y':N})),contourEnds=arr(I),arcs=arr(obj({'beginIndex':I,'endIndex':I,'angle':N}))))
    output={
      'GetNativeElementDefaultsV1':obj({'nativeModelWrites':{'const':0},'geometryAuthority':S,'defaults':arr(either(defaults))}),
      'GetNativePolygonMemoV1':obj({'nativeModelWrites':{'const':0},'geometryAuthority':S,'elements':arr(either(polygon))}),
      'GetNativeWorkingUnitsV1':either(obj({k:I for k in ['nativeModelWrites','lengthUnit','areaUnit','volumeUnit','angleUnit','lengthDecimals','areaDecimals','volumeDecimals','angleDecimals']})),
      'GetNativeGroupRootsV1':obj({'nativeModelWrites':{'const':0},'groups':arr(either(obj({'elementId':eid,'groupId':eid,'rootGroupId':eid})))}),
      'GetNativeLibraryPartOriginV1':either(obj({'nativeModelWrites':{'const':0},'parts':arr(either(obj({'index':I,'name':S,'libraryName':S,'originStatus':S},['index'])))}))}
    # The raw response schemas also feed the existing GenerateDocumentation.
    text=re.sub(r'^#define DEF\(name\).*$', '#define DEF(name) name##Command::name##Command():CommandBase(CommonSchema::NotUsed){} GS::String name##Command::GetName() const {return #name;}',text,count=1,flags=re.M)
    for name,schema in output.items():
        pattern=rf'GS::Optional<GS::UniString> {name}Command::GetRawResponseSchema\(\) const \{{return R"APA\(.*?\)APA";\}}\n'
        text=re.sub(pattern,'',text)
    anchor='#undef DEF\n';schemas=''.join(f'GS::Optional<GS::UniString> {name}Command::GetRawResponseSchema() const {{return R"APA({json.dumps(schema,separators=(",",":"))})APA";}}\n' for name,schema in output.items())
    text=text.replace(anchor,anchor+schemas,1);cpp.write_text(text,encoding='utf8')
    inputs={name:json.loads(re.search(rf'{name}Command::GetInputParametersSchema\(\) const \{{return R"\((.*?)\)";',text).group(1)) for name in output if name!='GetNativeGroupRootsV1'}
    inputs['GetNativeGroupRootsV1']=inputs['GetNativePolygonMemoV1']
    native={name:dict(version='29',category='Native SDK grouped read adapter',description=description,parameters=inputs[name],returns=output[name],availability='BUILD_CANDIDATE_NOT_RUNTIME_REGISTERED') for name,description in {
      'GetNativeElementDefaultsV1':'Native tool defaults for twelve types; complex tool header only, no solver.',
      'GetNativePolygonMemoV1':'Native polygon memo coordinates/holes/arcs, not resultant BREP.',
      'GetNativeWorkingUnitsV1':'Read project working unit enums and decimal preferences without mutation.',
      'GetNativeGroupRootsV1':'Immediate and nested root group membership for element GUIDs.',
      'GetNativeLibraryPartOriginV1':'Modern SDK GDL part name and containing library origin.'}.items()}
    protection=dict(version='29',category='SDK DevKit licensing query',description='Existing DevKit ProtectionInfoCommand reused unchanged namespace; license flags only.',parameters=obj({}),returns=obj({k:B for k in ['isSTART','isEDU','isSOLO','isDEMO','isTRIAL','isBTC','isNFR','isNetworkLicense']}),availability='BUILD_CANDIDATE_NOT_RUNTIME_REGISTERED')
    point=arr(N,minItems=2,maxItems=2);outline=arr(point,minItems=3);nativeElement=obj({'guid':S,'type':S,'homeStory':I,'bodies':arr({'type':'object'})},['guid'],True)
    local={};deps={}
    def add(name,parameters,returns,packages,description):
        local[name]=dict(version='1',category='Local analytical module',description=description,parameters=parameters,returns=returns,scope='LOCAL_READ_OR_ANALYSIS_NO_NATIVE_WRITE');deps[name]=packages
    add('NormalizeNativeDump',obj({'dump':{'type':'object'}}),obj({'elements':arr(nativeElement)},['elements'],True),[],'Reuse existing Native Model Dump normalizer; no second geometry model.')
    add('NativeBodyQuantities',obj({'elements':arr(nativeElement)}),obj({'elements':arr(obj({'guid':S,'quantities':obj({'status':S},['status'],True)})),'authority':S,'engineering':S}),['shapely'],'Existing APA closed planar BREP quantity adapter, now selectable in common catalog.')
    add('DependencyImpact',obj({'nodes':arr(S,uniqueItems=True),'edges':arr(arr(S,minItems=2,maxItems=2)),'changed':arr(S,uniqueItems=True)}),obj({'status':S,'affected':arr(S),'updateOrder':arr(S),'cycleWitness':arr(arr(S)),'executionAllowed':{'const':False}},['status','executionAllowed']),['networkx'],'NetworkX affected descendants and dependency order; cycle witness fails execution closed.')
    add('PolygonRelations',obj({'polygons':arr(obj({'id':S,'outline':outline,'holes':arr(outline)},['id','outline'])),'tolerance':dict(N,minimum=0)},['polygons']),obj({'units':S,'polygons':arr(obj({'id':S,'area':N,'perimeter':N})),'relations':arr(obj({'first':S,'second':S,'intersects':B,'touches':B,'intersectionArea':N,'distance':N})),'scope':S,'engineering':S}),['shapely'],'Shapely STRtree source polygon/holes spatial relations; 2D only, no native collision claim.')
    add('ConstrainedAssignment',obj({'tasks':arr(obj({'id':S,'costs':dict(type='object',additionalProperties=I,minProperties=1)})),'capacities':dict(type='object',additionalProperties=dict(I,minimum=0),minProperties=1),'time_limit':dict(N,exclusiveMinimum=0,maximum=60)},['tasks','capacities']),obj({'status':S,'assignment':dict(type='object',additionalProperties=S),'objective':N,'scope':S,'engineering':S},['status','assignment','scope','engineering']),['ortools'],'Existing CP-SAT backend for explicit integer assignment costs/capacities; no design inference.')
    path=dict(S,minLength=1)
    add('IFCSelect',obj({'path':path,'query':dict(S,minLength=1)}),obj({'schema':S,'elements':arr(obj({'ifcId':nullable(S),'stepId':I,'type':S,'name':nullable(S),'properties':{'type':'object'}})),'semanticCompatibility':S}),['ifcopenshell'],'IfcOpenShell public selector and actual property sets from an explicit existing file.')
    add('IFCValidate',obj({'path':path,'express_rules':B},['path']),obj({'schema':S,'status':S,'issues':arr(dict(type='object',additionalProperties=S)),'scope':S}),['ifcopenshell'],'IfcOpenShell schema/attribute and optional EXPRESS validation; not engineering acceptance.')
    add('IFCGeometry',obj({'path':path,'guids':arr(S,uniqueItems=True)}),obj({'elements':arr(obj({'ifcId':S,'status':S,'bounds':arr(arr(N,minItems=2,maxItems=2),minItems=3,maxItems=3),'area':N,'volume':N,'source':S,'reason':S},['ifcId','status'])),'scope':S,'engineering':S}),['ifcopenshell'],'IfcOpenShell native geometry kernel world-coordinate bounds, surface area and volume; not Archicad readback.')
    add('IFCExchangeFacts',obj({'path':path}),obj({'schema':S,'voidRelations':arr({'type':'object'}),'nativePortRelationsExported':arr({'type':'object'}),'materialAssignments':arr({'type':'object'}),'analyticalMembers':arr({'type':'object'}),'analysisModels':arr({'type':'object'}),'loadGroupCount':I,'analyticalExchangeStatus':S,'safStatus':S,'semanticCompatibility':S,'calculationResults':S}),['ifcopenshell'],'Reuse existing APA IFC exchange facts adapter; no new analytical engine.')
    manifest=dict(schema='APA_FUNCTIONAL_MODULES_V1',sdkImplementationSHA256=sha(cpp),sdkProviders={'TapirCommand':native,'AddOnCommandTest':{'ProtectionInfoCommand':protection}},local=dict(implementationSHA256=sha(ROOT/'scripts/archicad_local_modules.py'),commands=local,dependencies=deps),newNativeContracts=5,newLocalCatalogEntries=9,newAnalyticalCapabilities=6,reusedExistingAPALocalUtilities=3,reusedDevKitCommands=1)
    dest=ROOT/'schemas/accelerator/functional-modules.json';dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return manifest
if __name__=='__main__':build()
