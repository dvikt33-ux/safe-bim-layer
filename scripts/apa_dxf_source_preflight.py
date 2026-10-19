"""Ready ezdxf diagnostics on the existing APA Router and existing vendor venv.

Never saves a DXF, follows an outside/remote XREF, expands MINSERT geometry,
installs packages, calls Archicad or infers BIM coordinates.
"""
from pathlib import Path,PureWindowsPath
import argparse,hashlib,importlib.util,importlib.metadata,json,os,re,subprocess,sys

ROOT=Path(r'C:\LocalAI\APA_AC29_Stable')
CMD='AddOn.APADXFPreflight.DXFSourcePreflight'
SCHEMA='APA_DXF_SOURCE_PREFLIGHT_V1'
MAX_BYTES=256*1024*1024

def need(ok,why):
    if not ok:raise ValueError(why)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def runtime():
    p=ROOT/'external-tools/apa-dxf-geometry-c1/apa_high_density_readonly_v2.py'
    need(digest(p)=='c94cc5f9c3024ca5c20a312aa3591d79970a2370915493ed018b47b711b47ec0','DXF_PREFLIGHT_EXISTING_HELPER_DRIFT')
    spec=importlib.util.spec_from_file_location('apa_existing_v2_for_dxf_preflight',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,mod.verified_python()

def xref_record(block,source_root,budget):
    raw=block.dxf.xref_path
    result=dict(block=block.dxf.name,path=raw,flags=int(block.dxf.flags))
    if not raw:return dict(result,status='MISSING_PATH')
    if raw.startswith(('\\\\','//')) or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://',raw):
        return dict(result,status='REMOTE_PATH_NOT_READ')
    ref=Path(raw)
    if PureWindowsPath(raw).drive and not ref.is_absolute():return dict(result,status='FOREIGN_ABSOLUTE_PATH_NOT_READ')
    ref=(ref if ref.is_absolute() else source_root/ref).resolve()
    if ref==source_root or source_root not in ref.parents:return dict(result,status='OUTSIDE_SOURCE_ROOT_NOT_READ')
    if not ref.is_file():return dict(result,status='MISSING_LOCAL_FILE')
    size=ref.stat().st_size
    if size>budget[0]:return dict(result,status='HASH_BUDGET_EXCEEDED',bytes=size)
    budget[0]-=size;before=digest(ref);after=digest(ref)
    need(before==after,'DXF_PREFLIGHT_XREF_CHANGED_DURING_HASH')
    return dict(result,status='PRESENT_HASHED',bytes=size,sha256=before)

def analyze(doc,auditor,source_root,parse_mode='STRICT'):
    from ezdxf.lldxf.const import BLK_XREF,BLK_XREF_OVERLAY
    xrefs=[];budget=[MAX_BYTES]
    for block in doc.blocks:
        if int(block.block.dxf.flags)&(BLK_XREF|BLK_XREF_OVERLAY):
            need(len(xrefs)<200,'DXF_PREFLIGHT_XREF_COUNT_LIMIT')
            xrefs.append(xref_record(block.block,source_root,budget))
    rows=[];total=nominal=effective=matrices=0
    for entity in doc.modelspace().query('INSERT'):
        total+=1;need(total<=100000,'DXF_PREFLIGHT_INSERT_LIMIT')
        columns,rr=int(entity.dxf.column_count),int(entity.dxf.row_count)
        need(1<=columns<=1000000 and 1<=rr<=1000000,'DXF_PREFLIGHT_INVALID_MATRIX_COUNTS')
        slots=columns*rr;count=entity.mcount
        need(1<=count<=slots<=1000000,'DXF_PREFLIGHT_MATRIX_CAPACITY_EXCEEDED')
        nominal+=slots;effective+=count;matrices+=int(slots>1)
        if len(rows)<100:rows.append(dict(handle=entity.dxf.handle,block=entity.dxf.name,rowCount=rr,columnCount=columns,
            nominalMatrixSlots=slots,ezdxfEffectiveInsertCount=count))
    code=doc.header.get('$INSUNITS',0);known=type(code) is int and 1<=code<=24
    errors,fixes=len(auditor.errors),len(auditor.fixes)
    return dict(parseMode=parse_mode,dxfVersion=doc.dxfversion,auditErrors=errors,auditInMemoryFixes=fixes,
        repairedDrawingSaved=False,insunitsCode=code,unitsDeclared=known,scaleCalibration='NOT_VERIFIED',unitConversionApplied=False,
        xrefs=xrefs,xrefsComplete=all(x['status']=='PRESENT_HASHED' for x in xrefs),
        inserts=dict(countScope='MODELSPACE_TOP_LEVEL_ONLY',insertRecords=total,minsertRecords=matrices,
            nominalMatrixSlots=nominal,ezdxfEffectiveInsertCount=effective,examples=rows,examplesTruncated=total>len(rows),
            nestedBlockExpansionApplied=False,virtualGeometryCreated=False),
        readyForFurtherSourceAnalysis=parse_mode=='STRICT' and errors==fixes==0 and known and all(x['status']=='PRESENT_HASHED' for x in xrefs),
        automaticBIMWriteAllowed=False)

def analyze_file(source):
    import ezdxf
    need(importlib.metadata.version('ezdxf')=='1.4.5','DXF_PREFLIGHT_PINNED_VENDOR_VERSION_REQUIRED')
    source=Path(source).resolve(strict=True)
    need(source.is_file() and source.suffix.lower()=='.dxf' and source.stat().st_size<=MAX_BYTES,'DXF_PREFLIGHT_BOUNDED_DXF_REQUIRED')
    before=digest(source);mode='STRICT'
    try:doc=ezdxf.readfile(source);auditor=doc.audit()
    except ezdxf.DXFStructureError:
        from ezdxf import recover
        doc,auditor=recover.readfile(source);mode='RECOVERED_IN_MEMORY_REVIEW_REQUIRED'
    result=analyze(doc,auditor,source.parent,mode)
    need(digest(source)==before,'DXF_PREFLIGHT_SOURCE_CHANGED')
    return dict(schema=SCHEMA,source=dict(path=str(source),sha256=before,bytes=source.stat().st_size),
        result=result,sourceUnchanged=True,nativeCalls=0,nativeWrites=0,modelWrites=0,dependencyVersion='ezdxf1.4.5')

def call(a,output):
    helper,python=runtime();source=helper.input_file(a,'.dxf');out=helper.output_file(output,source)
    need(source.stat().st_size<=MAX_BYTES,'DXF_PREFLIGHT_SOURCE_TOO_LARGE')
    script=Path(__file__).resolve();before=digest(source);code=digest(script)
    done=subprocess.run([str(python),str(script),'--worker','--a',str(source),'--output',str(out)],capture_output=True,text=True,encoding='utf8',timeout=180)
    need(done.returncode==0 and out.is_file(),'DXF_PREFLIGHT_WORKER_FAILED:'+done.stderr[-1000:])
    need(digest(script)==code and digest(source)==before and out.stat().st_size<4*1024*1024,'DXF_PREFLIGHT_CODE_SOURCE_OR_REPORT_DRIFT')
    report=json.loads(out.read_text(encoding='utf8'))
    need(report['schema']==SCHEMA and report['source']['sha256']==before and report['sourceUnchanged'] is True and
         report['nativeCalls']==report['modelWrites']==0,'DXF_PREFLIGHT_REPORT_CONTRACT_DRIFT')
    return dict(report,artifact=dict(path=str(out),sha256=digest(out)))

def register(router):
    need(CMD not in router.catalog['commands'],'DXF_PREFLIGHT_ALREADY_REGISTERED')
    contract=dict(version='1',description='Source DXF recover/audit, local XREF hashes, bounded MINSERT counts and declared units; no model writes',
        parameters=dict(type='object',properties={k:dict(type='string',minLength=1) for k in ('a','output')},required=['a','output'],additionalProperties=False),
        returns=dict(type='object',required=['schema','source','result','sourceUnchanged','nativeCalls','modelWrites','artifact']))
    router.add_local_provider('APADXFPreflight',{'DXFSourcePreflight':contract},{'DXFSourcePreflight':call},SCHEMA,{'DXFSourcePreflight':[]})
    router.review_policy(CMD,'READ_ONLY','READ_ONLY',dict(source=SCHEMA,sha256=router.contract_hash(CMD)))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',action='store_true');parser.add_argument('--a',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    if args.worker:
        helper,_=runtime();source=helper.input_file(args.a,'.dxf');out=helper.output_file(args.output,source)
        report=analyze_file(source)
        with out.open('x',encoding='utf8') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    else:
        import apa_ac29_installed_factory as F
        router=F.native_command_router();ticket=router.prepare(CMD,dict(a=args.a,output=args.output))
        print(json.dumps(router.read(None,ticket,reviewed_read_only=True),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
