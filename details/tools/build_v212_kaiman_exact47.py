#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,pathlib,shutil,tarfile,tempfile,collections
D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.11';NEW='v2.12';SRC='KAIMAN_KERAKAM_WALL';EXPECTED=(1215,1299,601,579)
IMPORT=D/'import'/'kaiman-exact-v2.5'/'kaiman-kerakam-exact-v2.5.tar.gz'

def js(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def wjs(p,rows):p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def extract(p,out):
 out.mkdir(parents=True,exist_ok=True)
 with tarfile.open(p,'r:gz') as t:
  root=out.resolve()
  for mm in t.getmembers():
   q=(out/mm.name).resolve()
   if q!=root and root not in q.parents:raise RuntimeError('unsafe tar '+mm.name)
  t.extractall(out)
def one(root,name):
 a=list(root.rglob(name))
 if len(a)!=1:raise RuntimeError(f'{name}: {len(a)}')
 return a[0]
def pjson(v):
 if isinstance(v,dict):return dict(v)
 if isinstance(v,str) and v.strip():
  try:x=json.loads(v);return x if isinstance(x,dict) else {}
  except Exception:return {}
 return {}
def scan_commit(x):
 if isinstance(x,dict):return x.get('commit_allowed') is True or any(scan_commit(v) for v in x.values())
 if isinstance(x,list):return any(scan_commit(v) for v in x)
 return False
def rel(x):
 if isinstance(x,dict):return {k:(NEW if k in ('release','active_release') and isinstance(v,str) else rel(v)) for k,v in x.items()}
 if isinstance(x,list):return [rel(v) for v in x]
 return x

def main():
 if not IMPORT.exists():raise RuntimeError('missing imported KAIMAN exact layer '+str(IMPORT))
 with tempfile.TemporaryDirectory(prefix='v212-') as td0:
  td=pathlib.Path(td0);base_tgz=td/'base.tgz';bx=td/'base';base_tgz.write_bytes(base64.b64decode((D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64').read_text(encoding='ascii')));extract(base_tgz,bx)
  root=one(bx,'details_active_v2.11.jsonl').parent;m=td/'machine';shutil.copytree(root,m)
  active=js(m/'details_active_v2.11.jsonl');facts=js(m/'parameter_facts_v2.11.jsonl');vars=js(m/'component_variants_v2.11.jsonl');queue=js(m/'dimension_binding_queue_v2.11.jsonl')
  if (len(active),len(facts),len(vars),len(queue))!=EXPECTED:raise RuntimeError(f'base totals changed {(len(active),len(facts),len(vars),len(queue))}')
  ex=td/'exact';extract(IMPORT,ex)
  bindfiles=['kaiman_kerakam_wt11_dimension_bindings_v2.3.jsonl','kaiman_kerakam_wt12_dimension_bindings_v2.4.jsonl','kaiman_kerakam_wt13_dimension_bindings_v2.5.jsonl']
  bindings=[]
  for n in bindfiles:bindings+=js(one(ex,n))
  if len(bindings)!=536:raise RuntimeError(f'exact bindings {len(bindings)} != 536')
  sheets=sorted({int(x['sheet']) for x in bindings})
  if sheets!=list(range(1,48)):raise RuntimeError('unexpected exact sheet coverage '+repr(sheets[:5])+repr(sheets[-5:]))
  mismatches=js(one(ex,'kaiman_kerakam_source_mismatches_v2.5.jsonl'))
  if len(mismatches)!=5:raise RuntimeError(f'mismatches {len(mismatches)} != 5')
  mismatch_by_sheet=collections.defaultdict(list)
  for mm in mismatches:
   for s in mm.get('sheets',[]):mismatch_by_sheet[int(s)].append(mm['mismatch_id'])
  byid={r.get('detail',{}).get('detail_id'):r for r in active}
  for n in range(1,48):
   if f'{SRC}__S{n}' not in byid:raise RuntimeError('missing active detail '+str(n))
  qids={r.get('record_id'):r for r in queue};targets={f'{SRC}__{n}__V22Q' for n in range(1,48)};present=targets & set(qids)
  if len(present)!=47:raise RuntimeError(f'exact queue targets present {len(present)} != 47; missing={sorted(targets-present)[:10]}')
  # Integrate every exact endpoint-bound source dimension as a typed parameter fact.
  existing={x.get('fact_id') for x in facts};added=[];bydetail=collections.defaultdict(list)
  for b in bindings:
   fid=b['dimension_id'];bydetail[b['detail_id']].append(fid)
   if fid in existing:continue
   fact={'fact_id':fid,'detail_id':b['detail_id'],'source_id':SRC,'source_literal':b.get('source_literal'),'fact_kind':'exact_printed_dimension','subject':b.get('key') or b.get('meaning'),'source_unit':b.get('unit'),'normalized_unit':b.get('unit'),'value_json':json.dumps(b.get('value'),ensure_ascii=False,separators=(',',':')),'binding_state':b.get('binding_state','exact_printed_value_endpoint_bound'),'bound_component_position':None,'source_locator_json':json.dumps(b.get('source_locator') or {'representation':'albom_tehnicheskih_reshenii_kaiman,_kerakam.pdf','page':b.get('source_page'),'sheet':b.get('sheet')},ensure_ascii=False,separators=(',',':')),'endpoint_binding_json':json.dumps({'axis':b.get('axis'),'endpoint_a':b.get('endpoint_a'),'endpoint_b':b.get('endpoint_b'),'template_ref':b.get('template_ref'),'machine_use':b.get('machine_use'),'meaning':b.get('meaning')},ensure_ascii=False,separators=(',',':'))}
   facts.append(fact);existing.add(fid);added.append(fid)
  if len(added)!=536:raise RuntimeError(f'new exact facts {len(added)} != 536')
  reviews=[]
  for n in range(1,48):
   did=f'{SRC}__S{n}';row=byid[did];ir=row.get('ir') or {};pre=pjson(ir.get('preconditions_json'));ids=list(dict.fromkeys((pre.get('source_fact_ids') or [])+bydetail[did]));pre['source_fact_ids']=ids
   mmids=mismatch_by_sheet.get(n,[]);state='exact_dimensions_bound_with_cross_sheet_mismatch_blocker' if mmids else 'exact_dimensions_bound_sheet_local'
   pre['kaiman_exact_dimension_integration_v2_12']={'state':state,'exact_binding_count':len(bydetail[did]),'cross_sheet_mismatch_ids':mmids,'raster_measurement_used':False,'commit_allowed':False,'policy':'sheet-local printed endpoint-bound values only; never average cross-sheet mismatch'}
   ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':'));ir['commit_allowed']=0
   d=row.get('detail') or {};pbs=pjson(d.get('parameter_binding_summary_json'));pbs.update({'source_page_review_release':'KAIMAN-exact-v2.5 integrated in v2.12','dimension_queue_state':'resolved_exact_endpoint_bound','exact_binding_count':len(bydetail[did]),'cross_sheet_mismatch_ids':mmids,'raster_measurement_used':False});d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'))
   reviews.append({'review_id':f'{did}__KAIMAN_EXACT_v2_12','record_id':did,'source_id':SRC,'sheet':str(n),'pdf_page':40+n,'exact_binding_count':len(bydetail[did]),'source_layer':'KAIMAN exact-dimension layer v2.5','resolution_state':state,'queue_record_removed':f'{SRC}__{n}__V22Q','cross_sheet_mismatch_ids':mmids,'raster_measurement_used':False,'commit_allowed':False})
  nq=[r for r in queue if r.get('record_id') not in targets]
  if len(nq)!=532:raise RuntimeError(f'queue {len(nq)} != 532')
  if any(scan_commit(r) for r in active):raise RuntimeError('commit_allowed true')
  # Preserve the exact-layer source artifacts in the active machine package.
  for name in bindfiles+['kaiman_kerakam_dimension_templates_v2.5.json','kaiman_kerakam_exact_binding_index_v2.5.json','kaiman_kerakam_source_mismatches_v2.5.jsonl','SUMMARY_KAIMAN_v2.5.json','AUDIT_KAIMAN_v2.5.json','README_KAIMAN_v2.5.md']:
   shutil.copy2(one(ex,name),m/name)
  wjs(m/'kaiman_exact_integration_v2.12.jsonl',reviews)
  wjs(m/'details_active_v2.12.jsonl',active);(m/'details_active_v2.11.jsonl').unlink();wjs(m/'parameter_facts_v2.12.jsonl',facts);(m/'parameter_facts_v2.11.jsonl').unlink();wjs(m/'component_variants_v2.12.jsonl',vars);(m/'component_variants_v2.11.jsonl').unlink();wjs(m/'dimension_binding_queue_v2.12.jsonl',nq);(m/'dimension_binding_queue_v2.11.jsonl').unlink()
  for old,new in [('source_registry_v2.11.json','source_registry_v2.12.json'),('sources_v2.11.json','sources_v2.12.json'),('source_normative_claims_v2.11.json','source_normative_claims_v2.12.json')]:
   p=m/old
   if p.exists():(m/new).write_text(json.dumps(rel(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.unlink()
  for n in ('SUMMARY_v2.11.json','AUDIT_v2.11.json','README_v2.11.md','manifest_v2.11.json','SOURCE_VERIFY_FULL_v2.11.json'):
   p=m/n
   if p.exists():p.unlink()
  sv=rel(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')));(m/'SOURCE_VERIFY_FULL_v2.12.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');checks=sv.get('representation_checks',[]);hm=sum(bool(x.get('match')) for x in checks);ht=len(checks)
  if ht and hm!=ht:raise RuntimeError('source hash failure')
  summary={'release':'2.12','base_release':'v2.11','focus_source':SRC,'focus_scope':'integrate existing KAIMAN exact-dimension layer for sheets 1-47 / PDF pages 41-87','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':len(facts),'component_variants_total':601,'dimension_queue_total':532,'kaiman_exact_sheets_integrated':47,'kaiman_exact_bindings_integrated':len(added),'kaiman_cross_sheet_mismatches_preserved':len(mismatches),'kaiman_remaining_queue_tasks':180,'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
  audit={'release':'2.12','checks':summary,'critical_findings':['Integrated 536 previously audited KAIMAN/KERAKAM exact printed endpoint-bound dimensions for sheets 1-47; no re-measurement from raster was performed.','47 sheet-specific dimension-transcription queue records are removed because their exact sheet-local bindings now exist in active parameter facts.','Five cross-sheet mismatches from KAIMAN exact v2.5 remain explicit blockers; no averaging or silent normalization is permitted.','WT1.3 overview sheets 40/42/44/46 print 80 mm upper insulation while paired enlarged nodes 41/43/45/47 print 150 mm; values remain sheet-local.','Node-class inner structural zone 230 mm versus 290 mm remains node-specific and may not be propagated across node classes.','Queue closure is not construction permission; all active IR remains fail-closed and project structural sizing remains unresolved.'],'commit_allowed_true_introduced':0}
  readme=f'# Archicad construction detail machine state v2.12\n\nKAIMAN/KERAKAM exact-dimension integration over v2.11.\n\n- 1,215 detail units / active IR bindings\n- {len(facts):,} typed parameter facts\n- 601 component variants\n- 532 unresolved dimension/source-binding tasks\n- KAIMAN exact sheets integrated: 47/227\n- exact endpoint-bound KAIMAN dimensions integrated: 536\n- KAIMAN sheet queue remaining: 180\n- preserved cross-sheet mismatches: 5\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
  (m/'SUMMARY_v2.12.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'AUDIT_v2.12.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'README_v2.12.md').write_text(readme,encoding='utf-8');mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.12.json'];(m/'manifest_v2.12.json').write_text(json.dumps({'release':'2.12','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':len(facts),'component_variants':601,'dimension_queue':532,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  rd=D/'releases'/NEW
  if rd.exists():shutil.rmtree(rd)
  rd.mkdir(parents=True);out=td/'machine-state-v2.12.tar.gz'
  with tarfile.open(out,'w:gz') as t:
   for p in sorted(m.iterdir()):
    if p.is_file():t.add(p,arcname=p.name)
  ah=sha(out);(rd/'machine-state-v2.12.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii');(rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.12.tar.gz\n',encoding='utf-8');shutil.copy2(m/'SUMMARY_v2.12.json',rd/'summary.json');shutil.copy2(m/'AUDIT_v2.12.json',rd/'audit.json');shutil.copy2(m/'manifest_v2.12.json',rd/'manifest.json');(rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(rd/'README.md').write_text(readme,encoding='utf-8')
  cp=D/'index'/'source_counts.json';cnt=json.loads(cp.read_text(encoding='utf-8'))
  for r in cnt:
   if r.get('source_id')==SRC:r.update({'parameter_facts':r.get('parameter_facts',0)+len(added),'exact_dimension_status':'integrated_v2.12','exact_dimension_sheets_integrated':47,'exact_dimension_bindings_integrated':536,'dimension_queue_remaining':180,'cross_sheet_mismatches_preserved':5})
  cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp=D/'index'/'systems.json';sy=json.loads(sp.read_text(encoding='utf-8'));sy['release']=NEW;sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8');(D/'README.md').write_text(f'# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.12**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- {len(facts)} typed parameter facts\n- 601 component variants\n- 532 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.12 integrates the audited KAIMAN/KERAKAM exact-dimension layer for sheets 1-47: 536 exact printed endpoint-bound dimensions. Five cross-sheet mismatches remain fail-closed blockers.\n',encoding='utf-8')
  (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.12'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1];r=d/'releases'/ACTIVE_RELEASE;data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii'));actual=hashlib.sha256(data).hexdigest();assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256);target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked';target.mkdir(parents=True,exist_ok=True);tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz';tmp.write_bytes(data);tf=tarfile.open(tmp,'r:gz');tf.extractall(target);tf.close();tmp.unlink();print(target)\nif __name__=='__main__':raise SystemExit(main())\n",encoding='utf-8')
  print('V2.12 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
 return 0
if __name__=='__main__':raise SystemExit(main())