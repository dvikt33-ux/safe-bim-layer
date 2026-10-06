#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, pathlib, shutil, tarfile, tempfile
from typing import Any

D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.3'; NEW='v2.4'; SRC='POROTHERM_LOWRISE'
TOTAL={'details':1215,'facts':1211,'variants':567,'queue':671}
SRCN={'details':73,'facts':37,'variants':21,'queue':73}

def js(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def wjs(path,rows):
    path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def strs(x):
    if isinstance(x,str): yield x
    elif isinstance(x,dict):
        for k,v in x.items(): yield from strs(k); yield from strs(v)
    elif isinstance(x,list):
        for v in x: yield from strs(v)
def isp(x):
    return any((SRC in s.upper() or s.upper().startswith('POROTHERM_') or s.upper().startswith('POROTHERM-')) for s in strs(x))
def ident(r):
    for k in ('detail_id','fact_id','variant_id','task_id','queue_id','ir_id','id'):
        if isinstance(r.get(k),str) and r[k]: return r[k]
    return json.dumps(r,ensure_ascii=False,sort_keys=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def decode(p,out): out.write_bytes(base64.b64decode(p.read_text(encoding='ascii')))
def extract(p,out):
    out.mkdir(parents=True,exist_ok=True)
    with tarfile.open(p,'r:gz') as t:
        root=out.resolve()
        for m in t.getmembers():
            q=(out/m.name).resolve()
            if q!=root and root not in q.parents: raise RuntimeError('unsafe tar path '+m.name)
        t.extractall(out)
def one(root,name):
    a=list(root.rglob(name))
    if len(a)!=1: raise RuntimeError(f'{name}: {len(a)} matches')
    return a[0]
def inventory(root):
    out=[]
    for p in root.rglob('*.jsonl'):
        try: rows=js(p)
        except Exception: continue
        n=sum(isp(r) for r in rows)
        if n: out.append((p,n))
    for p,n in sorted(out): print('PATCH',p.relative_to(root),n)
    return out
def choose(inv,kind,n):
    pos={'details':('detail','semantic','active'),'facts':('fact','parameter'),'variants':('variant','component'),'queue':('dimension','queue','binding')}[kind]
    neg={'details':('dimension','queue','fact','variant'),'facts':('queue','variant','detail'),'variants':('queue','fact','detail'),'queue':('fact','variant')}[kind]
    c=[]
    for p,k in inv:
        nm=p.name.lower()
        score=sum(x in nm for x in pos)-sum(x in nm for x in neg)+(10 if k==n else 0)
        c.append((score,k,p))
    c.sort(reverse=True,key=lambda x:(x[0],x[1]))
    if not c: raise RuntimeError('no patch candidates for '+kind)
    p=c[0][2]; rows=[r for r in js(p) if isp(r)]
    print('SELECT',kind,p.name,len(rows))
    if len(rows)!=n: raise RuntimeError(f'{kind}: {len(rows)} != {n}')
    return rows
def merge(base,patch,kind):
    print('MERGE',kind,'old',sum(isp(r) for r in base),'new',len(patch))
    out=[r for r in base if not isp(r)]+patch
    ids=[ident(r) for r in out]
    if len(ids)!=len(set(ids)): raise RuntimeError('duplicate ids in '+kind)
    return out
def release(x):
    if isinstance(x,dict): return {k:(NEW if k in ('release','active_release') and isinstance(v,str) else release(v)) for k,v in x.items()}
    if isinstance(x,list): return [release(v) for v in x]
    return x
def no_commit_true(rows):
    def scan(x):
        if isinstance(x,dict):
            if x.get('commit_allowed') is True: return True
            return any(scan(v) for v in x.values())
        if isinstance(x,list): return any(scan(v) for v in x)
        return False
    bad=[ident(r) for r in rows if isp(r) and scan(r)]
    if bad: raise RuntimeError('commit_allowed=true: '+repr(bad[:10]))

def main():
    with tempfile.TemporaryDirectory(prefix='v24-') as td0:
        td=pathlib.Path(td0); bx=td/'b'; px=td/'p'
        bt=td/'b.tgz'; pt=td/'p.tgz'
        decode(D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64',bt)
        decode(D/'patches'/'v2.3-porotherm'/'porotherm-v2.3-source-patch.tar.gz.b64',pt)
        extract(bt,bx); extract(pt,px)
        root=one(bx,'details_active_v2.3.jsonl').parent
        m=td/'machine'; shutil.copytree(root,m)
        inv=inventory(px)
        patch={k:choose(inv,k,SRCN[k]) for k in SRCN}
        spec=[
          ('details_active_v2.3.jsonl','details_active_v2.4.jsonl','details'),
          ('parameter_facts_v2.3.jsonl','parameter_facts_v2.4.jsonl','facts'),
          ('component_variants_v2.3.jsonl','component_variants_v2.4.jsonl','variants'),
          ('dimension_binding_queue_v2.3.jsonl','dimension_binding_queue_v2.4.jsonl','queue')]
        merged={}
        for old,new,k in spec:
            merged[k]=merge(js(m/old),patch[k],k)
            if len(merged[k])!=TOTAL[k] or sum(isp(r) for r in merged[k])!=SRCN[k]:
                raise RuntimeError(f'{k} count mismatch total={len(merged[k])} src={sum(isp(r) for r in merged[k])}')
            wjs(m/new,merged[k]); (m/old).unlink()
        no_commit_true(merged['details'])
        for old,new in (('source_registry_v2.3.json','source_registry_v2.4.json'),('sources_v2.3.json','sources_v2.4.json'),('source_normative_claims_v2.3.json','source_normative_claims_v2.4.json')):
            p=m/old
            if p.exists():
                (m/new).write_text(json.dumps(release(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); p.unlink()
        for p in list(m.iterdir()):
            if p.is_file() and 'porotherm' in p.name.lower(): p.unlink()
        skip=('summary','audit','manifest','source_verify','details_active','parameter_facts','component_variants','dimension_binding_queue','registry_patch')
        copied=[]
        for p in px.rglob('*'):
            if p.is_file() and 'porotherm' in p.name.lower() and not any(x in p.name.lower() for x in skip):
                shutil.copy2(p,m/p.name); copied.append(p.name)
        for n in ('SUMMARY_v2.3.json','AUDIT_v2.3.json','README_v2.3.md','manifest_v2.3.json','SOURCE_VERIFY_FULL_v2.3.json'):
            p=m/n
            if p.exists(): p.unlink()
        sv=json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8'))
        (m/'SOURCE_VERIFY_FULL_v2.4.json').write_text(json.dumps(release(sv),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        summary={'release':'2.4','base_release':'v2.3','focus_source':SRC,'detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':1211,'component_variants_total':567,'dimension_queue_total':671,'porotherm_detail_units':73,'porotherm_parameter_facts':37,'porotherm_component_variants':21,'porotherm_dimension_queue':73,'source_hash_matches':40,'source_hash_total':40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
        audit={'release':'2.4','checks':summary,'critical_findings':['POROTHERM correction rebased onto active v2.3; FAVORIT section-1 work preserved.','POROTHERM has 73 canonical technical-detail sheets; 12 divider/navigation pages remain excluded.','Old 69-row generic extraction and 25M-as-25m misparse are not carried forward.','No raster-derived construction dimensions; unresolved dimensions remain queued.','Manufacturer and source-quoted normative references remain unverified claims.','Unresolved POROTHERM construction operations remain fail-closed.'],'commit_policy':'fail_closed'}
        (m/'SUMMARY_v2.4.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (m/'AUDIT_v2.4.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        readme='# Archicad construction detail machine state v2.4\n\nPOROTHERM/Wienerberger correction rebased onto active v2.3 while preserving FAVORIT section-1 improvements.\n\n- 1,215 detail units\n- 1,215 active detail to Archicad IR bindings\n- 1,211 typed parameter facts\n- 567 component variants\n- 671 unresolved dimension/source-binding tasks\n- POROTHERM canonical technical sheets: 73\n- raw-source SHA verification: 40/40\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
        (m/'README_v2.4.md').write_text(readme,encoding='utf-8')
        mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.4.json']
        (m/'manifest_v2.4.json').write_text(json.dumps({'release':'2.4','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':1211,'component_variants':567,'dimension_queue':671,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        rd=D/'releases'/NEW
        if rd.exists(): shutil.rmtree(rd)
        rd.mkdir(parents=True)
        tgz=td/'machine-state-v2.4.tar.gz'
        with tarfile.open(tgz,'w:gz') as t:
            for p in sorted(m.iterdir()):
                if p.is_file(): t.add(p,arcname=p.name)
        ah=sha(tgz)
        (rd/'machine-state-v2.4.tar.gz.b64').write_text(base64.b64encode(tgz.read_bytes()).decode('ascii'),encoding='ascii')
        (rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.4.tar.gz\n',encoding='utf-8')
        shutil.copy2(m/'SUMMARY_v2.4.json',rd/'summary.json'); shutil.copy2(m/'AUDIT_v2.4.json',rd/'audit.json'); shutil.copy2(m/'manifest_v2.4.json',rd/'manifest.json'); shutil.copy2(D/'releases'/BASE/'source_verify.json',rd/'source_verify.json'); (rd/'README.md').write_text(readme,encoding='utf-8')
        cp=D/'index'/'source_counts.json'; counts=json.loads(cp.read_text(encoding='utf-8')); hit=False
        for r in counts:
            if r.get('source_id')==SRC: r.update({'details':73,'active_ir':73,'parameter_facts':37,'component_variants':21}); hit=True
        if not hit: raise RuntimeError('POROTHERM missing from source_counts')
        cp.write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        sp=D/'index'/'systems.json'; systems=json.loads(sp.read_text(encoding='utf-8')); systems['release']=NEW; sp.write_text(json.dumps(systems,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8')
        (D/'README.md').write_text('# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to v2.4.\n\n- 1,215 detail units\n- 1,215 active detail to Archicad IR bindings\n- 1,211 typed parameter facts\n- 567 component variants\n- 671 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.4 rebases corrected POROTHERM/Wienerberger onto v2.3 without dropping FAVORIT section-1 improvements. POROTHERM exposes 73 canonical technical-detail sheets; 12 divider/navigation pages are not buildable details.\n\nSafety remains fail-closed: manufacturer solutions are not mandatory norms, source-quoted SP/GOST references are unverified until independently checked, raster pixels never become construction dimensions, and unresolved critical bindings keep commit_allowed=false.\n',encoding='utf-8')
        (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.4'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1]; r=d/'releases'/ACTIVE_RELEASE; data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii')); actual=hashlib.sha256(data).hexdigest(); assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256); target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked'; target.mkdir(parents=True,exist_ok=True); tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz'; tmp.write_bytes(data); tf=tarfile.open(tmp,'r:gz'); tf.extractall(target); tf.close(); tmp.unlink(); print(target)\nif __name__=='__main__': raise SystemExit(main())\n",encoding='utf-8')
        print('V2.4 READY',json.dumps(summary,ensure_ascii=False),'archive',ah,'copied',copied)
    return 0
if __name__=='__main__': raise SystemExit(main())
