#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, pathlib, shutil, tarfile, tempfile

D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.5'; NEW='v2.6'; SRC='FAVORIT_SHEET_MATERIALS'
EXPECTED_BASE={'details':1215,'facts':1232,'variants':601,'queue':726}
KEEP_HIGH={9,12}

NOTES={
1:'System overview: source review found no additional buildable numeric dimension or fastener model beyond the existing legend/system semantics.',
2:'Bracket grid 600–1200 mm in both directions is already stored as source facts; the source also requires bracket type/spacing to be confirmed by strength calculation. Source transcription is complete; structural/project selection remains fail-closed.',
3:'KR1/KR2/KR3 wall attachment: numbered legend is complete; no additional numeric fastener size/model is printed on the reviewed sheet.',
4:'KR1/KR2/KR3 to metal structure, bolted basis: source gives generic fastening set; no additional size/model is printed.',
5:'Second KR1/KR2/KR3 bolted-to-metal variant: source gives generic fastening set; no additional size/model is printed.',
6:'KR4/KR5 wall attachment: numbered legend is complete; no additional numeric fastener size/model is printed.',
7:'KR4/KR5 to metal structure: generic bolted fastening set only; no additional size/model is printed.',
8:'Second KR4/KR5 bolted-to-metal variant: generic fastening set only; no additional size/model is printed.',
9:'Printed min 50 is present, but the exact Archicad constraint endpoints/parameter binding cannot be resolved safely from the raster sheet. Title also prints UKR1, UKR1, UKR3 while legend prints UKR1, UKR2, UKR3. Keep high priority.',
10:'UKR4-1/UKR5-1 extension connection uses blind rivets by title/legend; no additional numeric rivet designation is printed on this sheet.',
11:'UKR4/UKR5 extension connection uses blind rivets by title/legend; no additional numeric rivet designation is printed on this sheet.',
12:'Printed min 15 is present, but the exact Archicad constraint endpoints/parameter binding cannot be resolved safely from the raster sheet. Keep high priority.',
13:'Siding/linear-panel vertical layout dimensions are explicitly marked project-bound (по проекту); source transcription is complete.',
14:'Cladding fastener option is already stored from the source: galvanized self-tapping screw ВС 4.2×32 with source-literal washer РЕРДМ, or A2/A2 4×8 rivet. No normalization of РЕРДМ is made.',
15:'Profiled-sheet vertical layout/overlap is project-bound; the source fastener option is already stored. Source transcription is complete.',
16:'Profiled-sheet vertical section: generic blind-rivet/self-tapping-fastener legend only; no additional numeric designation is printed.',
17:'Profiled-sheet horizontal section: generic blind-rivet/self-tapping-fastener legend only; no additional numeric designation is printed.',
18:'Vertical thermal-joint min 10 mm is already stored and uniquely bound to the joint opening; source transcription is complete.',
19:'Horizontal thermal joint: source review found no additional buildable numeric dimension or fastener model beyond the legend.',
20:'Inner corner: literal source legend includes porcelain-stoneware slabs despite surrounding sheet-material context. Preserve anomaly/compile blocker; no untranscribed dimension or fastener remains on this sheet.',
21:'Outer corner: literal source legend includes porcelain-stoneware slabs despite surrounding sheet-material context. Preserve anomaly/compile blocker; no untranscribed dimension or fastener remains on this sheet.',
22:'Parapet junction: source review found no additional buildable numeric dimension or fastener model beyond the legend.',
23:'Plinth/vertical plane step: generic source components only; no additional numeric fastener designation is printed.',
24:'Window opening head: source review found no additional buildable numeric dimension/fastener designation beyond existing legend; earlier section-2 copy remains an alias to this canonical sheet.',
25:'Window opening jamb: source review found no additional buildable numeric dimension/fastener designation beyond existing legend; earlier section-2 copy remains an alias to this canonical sheet.',
26:'Window sill: source review found no additional buildable numeric dimension/fastener designation beyond existing legend.',
27:'Curtain-wall side junction: source review found no additional buildable numeric dimension/fastener designation beyond existing legend; earlier section-2 copy remains an alias to this canonical sheet.',
28:'Curtain-wall vertical junction: source review found no additional buildable numeric dimension/fastener designation beyond existing legend; earlier section-2 copy remains an alias to this canonical sheet.',
29:'Clearance 20–30 mm between lower facade edge and horizontal plane is already stored and uniquely bound; source transcription is complete.'
}

def js(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def wjs(path,rows): path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def extract(path,out):
    out.mkdir(parents=True,exist_ok=True)
    with tarfile.open(path,'r:gz') as t:
        root=out.resolve()
        for m in t.getmembers():
            q=(out/m.name).resolve()
            if q!=root and root not in q.parents: raise RuntimeError('unsafe tar path '+m.name)
        t.extractall(out)
def one(root,name):
    a=list(root.rglob(name))
    if len(a)!=1: raise RuntimeError(f'{name}: {len(a)} matches')
    return a[0]
def deep_commit_true(x):
    if isinstance(x,dict):
        if x.get('commit_allowed') is True: return True
        return any(deep_commit_true(v) for v in x.values())
    if isinstance(x,list): return any(deep_commit_true(v) for v in x)
    return False
def parse_json_field(v):
    if isinstance(v,dict): return dict(v)
    if isinstance(v,str) and v.strip():
        try:
            x=json.loads(v); return x if isinstance(x,dict) else {}
        except Exception: return {}
    return {}
def set_release(x):
    if isinstance(x,dict): return {k:(NEW if k in ('release','active_release') and isinstance(v,str) else set_release(v)) for k,v in x.items()}
    if isinstance(x,list): return [set_release(v) for v in x]
    return x

def main():
    with tempfile.TemporaryDirectory(prefix='details-v26-') as td0:
        td=pathlib.Path(td0); arc=td/'base.tgz'; bx=td/'base'
        b64=D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64'
        arc.write_bytes(base64.b64decode(b64.read_text(encoding='ascii'))); extract(arc,bx)
        root=one(bx,'details_active_v2.5.jsonl').parent
        m=td/'machine'; shutil.copytree(root,m)
        active=js(m/'details_active_v2.5.jsonl'); facts=js(m/'parameter_facts_v2.5.jsonl'); variants=js(m/'component_variants_v2.5.jsonl'); queue=js(m/'dimension_binding_queue_v2.5.jsonl')
        got=(len(active),len(facts),len(variants),len(queue)); exp=(1215,1232,601,726)
        if got!=exp: raise RuntimeError(f'base totals changed {got} != {exp}')
        by_id={r.get('detail',{}).get('detail_id'):r for r in active}
        target={f'{SRC}__S3_{n}' for n in range(1,30)}
        if target-set(by_id): raise RuntimeError('missing section3 active records')
        tq=[r for r in queue if r.get('record_id') in target and r.get('source_id')==SRC]
        if len(tq)!=29: raise RuntimeError(f'section3 queue rows {len(tq)} != 29')
        bad=[r for r in tq if r.get('priority')!='high' or r.get('queue_kind')!='node_printed_dimension_and_fastener_binding']
        if bad: raise RuntimeError('unexpected section3 queue state')
        reviews=[]; resolved=set(); kept=set()
        for n in range(1,30):
            did=f'{SRC}__S3_{n}'; row=by_id[did]; ir=row.get('ir') or {}; pre=parse_json_field(ir.get('preconditions_json')); ids=list(pre.get('source_fact_ids') or [])
            keep=n in KEEP_HIGH; state='open_high_endpoint_binding' if keep else 'resolved_source_review_complete'
            reviews.append({'review_id':f'{did}__DBR_v2_6','record_id':did,'source_id':SRC,'sheet':f'3.{n}','pdf_page':87+n,'review_release':'2.6','review_method':'manual_visual_review_of_rendered_supplied_source_page','raster_measurement_used':False,'existing_source_fact_ids':ids,'resolution_state':state,'queue_resolved':not keep,'remaining_blocker':('printed dimension exists but exact semantic endpoints/Archicad parameter binding remain unresolved' if keep else None),'note':NOTES[n],'commit_allowed':False})
            (kept if keep else resolved).add(did)
            d=row.get('detail') or {}; pbs=parse_json_field(d.get('parameter_binding_summary_json'))
            pbs.update({'source_page_review_release':'2.6','dimension_queue_state':state,'raster_measurement_used':False,'review_note':NOTES[n]})
            d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'))
            pre['dimension_binding_review_v2_6']={'state':state,'queue_resolved':not keep,'note':NOTES[n],'raster_measurement_used':False}
            ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':')); ir['commit_allowed']=0
        newq=[]
        for r in queue:
            rid=r.get('record_id')
            if rid in resolved: continue
            if rid in kept:
                r=dict(r); r.update({'queue_kind':'semantic_dimension_endpoint_resolution','priority':'high','reason':'Printed source dimension is known, but exact constraint endpoints / Archicad parameter binding are not uniquely resolved; raster measurement is forbidden.','status':'source_value_transcribed_endpoint_binding_open_v2.6'})
            newq.append(r)
        if len(newq)!=699: raise RuntimeError(f'queue {len(newq)} != 699')
        if {r.get('record_id') for r in newq if r.get('record_id') in target}!=kept: raise RuntimeError('wrong section3 survivors')
        if any(deep_commit_true(r) for r in active): raise RuntimeError('commit_allowed=true after review')
        wjs(m/'details_active_v2.6.jsonl',active); (m/'details_active_v2.5.jsonl').unlink()
        wjs(m/'parameter_facts_v2.6.jsonl',facts); (m/'parameter_facts_v2.5.jsonl').unlink()
        wjs(m/'component_variants_v2.6.jsonl',variants); (m/'component_variants_v2.5.jsonl').unlink()
        wjs(m/'dimension_binding_queue_v2.6.jsonl',newq); (m/'dimension_binding_queue_v2.5.jsonl').unlink()
        wjs(m/'favorit_section3_dimension_binding_v2.6.jsonl',reviews)
        for old,new in [('source_registry_v2.5.json','source_registry_v2.6.json'),('sources_v2.5.json','sources_v2.6.json'),('source_normative_claims_v2.5.json','source_normative_claims_v2.6.json')]:
            p=m/old
            if p.exists():
                (m/new).write_text(json.dumps(set_release(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); p.unlink()
        for n in ('SUMMARY_v2.5.json','AUDIT_v2.5.json','README_v2.5.md','manifest_v2.5.json','SOURCE_VERIFY_FULL_v2.5.json'):
            p=m/n
            if p.exists(): p.unlink()
        sv=set_release(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')))
        (m/'SOURCE_VERIFY_FULL_v2.6.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        checks=sv.get('representation_checks',[]) if isinstance(sv,dict) else []; ht=len(checks); hm=sum(bool(x.get('match')) for x in checks)
        if ht and hm!=ht: raise RuntimeError(f'source hash failures {hm}/{ht}')
        summary={'release':'2.6','base_release':'v2.5','focus_source':SRC,'focus_scope':'section 3, sheets 3.1-3.29 / PDF pages 88-116','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':1232,'component_variants_total':601,'dimension_queue_total':699,'section3_pages_reviewed':29,'section3_queue_tasks_resolved':27,'section3_high_remaining':2,'remaining_section3_records':sorted(kept),'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
        audit={'release':'2.6','checks':summary,'critical_findings':['27 of 29 FAVORIT sheet-material section-3 source-transcription tasks are closed after manual visual review of the supplied pages.','S3.9 remains high: min 50 is printed but exact constraint endpoints/Archicad parameter binding are not unique; title/legend UKR conflict remains preserved.','S3.12 remains high: min 15 is printed but exact constraint endpoints/Archicad parameter binding are not unique.','S3.18 min 10 and S3.29 clearance 20–30 are already source-bound facts; their transcription queue items are closed.','S3.20/S3.21 porcelain-stoneware context anomaly remains a compile blocker, but it is not an untranscribed dimension/fastener task.','Queue closure means source transcription is exhausted/bound; it does not grant automatic construction permission.','No raster-derived construction dimensions and no manufacturer normative claims promoted.'],'fail_closed':True,'commit_allowed_true_introduced':0}
        readme=f"# Archicad construction detail machine state v2.6\n\nFAVORIT sheet-material section-3 source-binding closure over active v2.5.\n\n- 1,215 detail units / active IR bindings\n- 1,232 typed parameter facts\n- 601 component variants\n- 699 unresolved dimension/source-binding tasks\n- section 3 reviewed: 29/29 sheets\n- section-3 source-binding tasks resolved: 27/29\n- remaining high: S3.9 (min 50 endpoint binding), S3.12 (min 15 endpoint binding)\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n"
        (m/'SUMMARY_v2.6.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); (m/'AUDIT_v2.6.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); (m/'README_v2.6.md').write_text(readme,encoding='utf-8')
        mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.6.json']
        man={'release':'2.6','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':1232,'component_variants':601,'dimension_queue':699,'files':mf}
        (m/'manifest_v2.6.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        rd=D/'releases'/NEW
        if rd.exists(): shutil.rmtree(rd)
        rd.mkdir(parents=True)
        out=td/'machine-state-v2.6.tar.gz'
        with tarfile.open(out,'w:gz') as t:
            for p in sorted(m.iterdir()):
                if p.is_file(): t.add(p,arcname=p.name)
        ah=sha(out)
        (rd/'machine-state-v2.6.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii')
        (rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.6.tar.gz\n',encoding='utf-8')
        shutil.copy2(m/'SUMMARY_v2.6.json',rd/'summary.json'); shutil.copy2(m/'AUDIT_v2.6.json',rd/'audit.json'); shutil.copy2(m/'manifest_v2.6.json',rd/'manifest.json'); (rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); (rd/'README.md').write_text(readme,encoding='utf-8')
        cp=D/'index'/'source_counts.json'; cnt=json.loads(cp.read_text(encoding='utf-8')); hit=False
        for r in cnt:
            if r.get('source_id')==SRC:
                r.update({'section3_dimension_binding_status':'reviewed_v2.6','section3_dimension_binding_tasks_resolved':27,'section3_dimension_binding_high_remaining':2}); hit=True
        if not hit: raise RuntimeError('FAVORIT source missing from source_counts')
        cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        sp=D/'index'/'systems.json'; sy=json.loads(sp.read_text(encoding='utf-8')); sy['release']=NEW; sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8')
        (D/'README.md').write_text("# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.6**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- 1232 typed parameter facts\n- 601 component variants\n- 699 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.6 preserves all v2.5 BRAAS work and closes 27/29 FAVORIT sheet-material section-3 source-binding tasks after manual source review. Only S3.9 and S3.12 remain high because their printed min 50 / min 15 values lack unique semantic endpoints. Safety remains fail-closed; manufacturer solutions are not mandatory norms and raster pixels never become construction dimensions.\n",encoding='utf-8')
        (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.6'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1]; r=d/'releases'/ACTIVE_RELEASE; data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii')); actual=hashlib.sha256(data).hexdigest(); assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256); target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked'; target.mkdir(parents=True,exist_ok=True); tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz'; tmp.write_bytes(data); tf=tarfile.open(tmp,'r:gz'); tf.extractall(target); tf.close(); tmp.unlink(); print(target)\nif __name__=='__main__': raise SystemExit(main())\n",encoding='utf-8')
        print('V2.6 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
    return 0
if __name__=='__main__': raise SystemExit(main())
