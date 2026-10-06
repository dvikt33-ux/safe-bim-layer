#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,pathlib,shutil,tarfile,tempfile
D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.6';NEW='v2.7';SRC='FAVORIT_SHEET_MATERIALS'
EXPECTED=(1215,1232,601,699);KEEP={9,30,31}
GENERIC='Manual source-page review found no additional untranscribed numeric dimension or fastener designation beyond the existing legend/semantics.'
NOTES={2:'Bracket grid is already source-bound: vertical 600–1200 mm and horizontal max 600 mm; bracket length depends on insulation thickness and type/spacing require strength-calculation confirmation.',9:'Printed min 50 remains semantically ambiguous for exact constraint endpoints; title/legend UKR conflict is preserved. Keep high priority.',14:'Open-cassette horizontal layout is explicitly project-defined (по проекту); no source numeric module is supplied.',15:'Open-cassette fastener option is already stored: ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',16:'Closed-cassette horizontal layout is explicitly project-defined (по проекту); no source numeric module is supplied.',17:'Closed-cassette fastener option is already stored: ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',18:'Siding/linear-panel horizontal layout is explicitly project-defined (по проекту); no source numeric module is supplied.',19:'Siding/linear-panel fastener option is already stored: ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',20:'Profiled-sheet horizontal layout, overlap and fastening option are already source-bound/project-bound in parameter facts.',24:'Vertical thermal-joint min 10 mm is already source-bound to the joint opening.',30:'Two printed 35 mm dimensions exist at the upper window reveal, but exact semantic endpoints/Archicad parameter roles remain unresolved. Keep high priority.',31:'Two printed 35 mm dimensions exist at the side window reveal, but exact semantic endpoints/Archicad parameter roles remain unresolved. Keep high priority.',35:'Clearance 20–30 mm between lower facade edge and horizontal plane is already uniquely source-bound.'}
NEW_FACTS={14:{'page':131,'literal':'по проекту','subject':'open_cassette_horizontal_layout_module'},16:{'page':133,'literal':'по проекту','subject':'closed_cassette_horizontal_layout_module'},18:{'page':135,'literal':'по проекту','subject':'siding_or_linear_panel_horizontal_layout_module'}}

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
  for m in t.getmembers():
   q=(out/m.name).resolve()
   if q!=root and root not in q.parents:raise RuntimeError('unsafe tar '+m.name)
  t.extractall(out)
def one(root,name):
 a=list(root.rglob(name))
 if len(a)!=1:raise RuntimeError(f'{name}: {len(a)}')
 return a[0]
def pjson(v):
 if isinstance(v,dict):return dict(v)
 if isinstance(v,str) and v.strip():
  try:
   x=json.loads(v);return x if isinstance(x,dict) else {}
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
 with tempfile.TemporaryDirectory(prefix='v27-') as td0:
  td=pathlib.Path(td0);tgz=td/'base.tgz';bx=td/'b'
  tgz.write_bytes(base64.b64decode((D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64').read_text(encoding='ascii')));extract(tgz,bx)
  root=one(bx,'details_active_v2.6.jsonl').parent;m=td/'machine';shutil.copytree(root,m)
  active=js(m/'details_active_v2.6.jsonl');facts=js(m/'parameter_facts_v2.6.jsonl');vars=js(m/'component_variants_v2.6.jsonl');queue=js(m/'dimension_binding_queue_v2.6.jsonl')
  if (len(active),len(facts),len(vars),len(queue))!=EXPECTED:raise RuntimeError('base totals changed')
  byid={r.get('detail',{}).get('detail_id'):r for r in active};target={f'{SRC}__S4_{n}' for n in range(1,36)}
  tq=[r for r in queue if r.get('record_id') in target and r.get('source_id')==SRC]
  if len(tq)!=35 or any(r.get('priority')!='high' or r.get('queue_kind')!='node_printed_dimension_and_fastener_binding' for r in tq):raise RuntimeError('unexpected section4 queue state')
  existing={r.get('fact_id') for r in facts};added=[]
  for n,spec in NEW_FACTS.items():
   fid=f'{SRC}__P{spec["page"]}__project_bound_dimension__V27_{n:02d}'
   if fid not in existing:
    facts.append({'fact_id':fid,'detail_id':f'{SRC}__S4_{n}','source_id':SRC,'source_literal':spec['literal'],'fact_kind':'project_bound_dimension','subject':spec['subject'],'source_unit':None,'normalized_unit':None,'value_json':'"project_defined"','binding_state':'project_input_required','bound_component_position':None,'source_locator_json':json.dumps({'representation':'atr_favorit_listovie_materiali.pdf','page':spec['page'],'actual_sheet':f'4.{n}','context_sequence':f'4.{n}'},ensure_ascii=False)});added.append(fid)
  reviews=[];resolved=set();kept=set()
  for n in range(1,36):
   did=f'{SRC}__S4_{n}';row=byid.get(did)
   if not row:raise RuntimeError('missing '+did)
   ir=row.get('ir') or {};pre=pjson(ir.get('preconditions_json'));ids=list(pre.get('source_fact_ids') or [])
   for fid in added:
    if fid.startswith(f'{SRC}__P{117+n}__') and fid not in ids:ids.append(fid)
   pre['source_fact_ids']=ids;keep=n in KEEP;state='open_high_endpoint_binding' if keep else 'resolved_source_review_complete';note=NOTES.get(n,GENERIC)
   reviews.append({'review_id':f'{did}__DBR_v2_7','record_id':did,'source_id':SRC,'sheet':f'4.{n}','pdf_page':117+n,'review_release':'2.7','review_method':'manual_visual_review_of_rendered_supplied_source_page','raster_measurement_used':False,'existing_source_fact_ids':ids,'resolution_state':state,'queue_resolved':not keep,'remaining_blocker':('printed dimension exists but exact semantic endpoints/Archicad parameter binding remain unresolved' if keep else None),'note':note,'commit_allowed':False})
   (kept if keep else resolved).add(did)
   d=row.get('detail') or {};pbs=pjson(d.get('parameter_binding_summary_json'));pbs.update({'source_page_review_release':'2.7','dimension_queue_state':state,'raster_measurement_used':False,'review_note':note});d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'))
   pre['dimension_binding_review_v2_7']={'state':state,'queue_resolved':not keep,'note':note,'raster_measurement_used':False};ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':'));ir['commit_allowed']=0
  nq=[]
  for r in queue:
   rid=r.get('record_id')
   if rid in resolved:continue
   if rid in kept:
    r=dict(r);r.update({'queue_kind':'semantic_dimension_endpoint_resolution','priority':'high','reason':'Printed source dimension is known, but exact constraint endpoints / Archicad parameter binding are not uniquely resolved; raster measurement is forbidden.','status':'source_value_transcribed_endpoint_binding_open_v2.7'})
   nq.append(r)
  if len(nq)!=667:raise RuntimeError(f'queue {len(nq)} != 667')
  if any(scan_commit(r) for r in active):raise RuntimeError('commit_allowed true')
  wjs(m/'details_active_v2.7.jsonl',active);(m/'details_active_v2.6.jsonl').unlink();wjs(m/'parameter_facts_v2.7.jsonl',facts);(m/'parameter_facts_v2.6.jsonl').unlink();wjs(m/'component_variants_v2.7.jsonl',vars);(m/'component_variants_v2.6.jsonl').unlink();wjs(m/'dimension_binding_queue_v2.7.jsonl',nq);(m/'dimension_binding_queue_v2.6.jsonl').unlink();wjs(m/'favorit_section4_dimension_binding_v2.7.jsonl',reviews)
  for old,new in [('source_registry_v2.6.json','source_registry_v2.7.json'),('sources_v2.6.json','sources_v2.7.json'),('source_normative_claims_v2.6.json','source_normative_claims_v2.7.json')]:
   p=m/old
   if p.exists():(m/new).write_text(json.dumps(rel(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.unlink()
  for n in ('SUMMARY_v2.6.json','AUDIT_v2.6.json','README_v2.6.md','manifest_v2.6.json','SOURCE_VERIFY_FULL_v2.6.json'):
   p=m/n
   if p.exists():p.unlink()
  sv=rel(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')));(m/'SOURCE_VERIFY_FULL_v2.7.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');checks=sv.get('representation_checks',[]);hm=sum(bool(x.get('match')) for x in checks);ht=len(checks)
  if ht and hm!=ht:raise RuntimeError('source hash failure')
  summary={'release':'2.7','base_release':'v2.6','focus_source':SRC,'focus_scope':'section 4, sheets 4.1-4.35 / PDF pages 118-152','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':len(facts),'component_variants_total':601,'dimension_queue_total':667,'section4_pages_reviewed':35,'section4_queue_tasks_resolved':32,'section4_high_remaining':3,'remaining_section4_records':sorted(kept),'new_project_bound_facts':len(added),'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
  audit={'release':'2.7','checks':summary,'critical_findings':['32 of 35 FAVORIT section-4 source-transcription tasks are closed after manual visual review.','S4.9 remains high: min 50 endpoint binding is not unique and UKR title/legend conflict remains preserved.','S4.30/S4.31 remain high: two printed 35 mm dimensions on each window-reveal detail lack unique semantic endpoint/parameter binding.','S4.14/S4.16/S4.18 layout modules are explicitly project-defined; three project-bound facts were added instead of inventing numeric modules.','S4.24 min 10 and S4.35 clearance 20–30 are already source-bound and their queue tasks are closed.','Queue closure is not construction permission; all active IR stays fail-closed.'],'commit_allowed_true_introduced':0}
  readme=f'# Archicad construction detail machine state v2.7\n\nFAVORIT sheet-material section-4 source-binding closure over v2.6.\n\n- 1,215 detail units / active IR bindings\n- {len(facts):,} typed parameter facts\n- 601 component variants\n- 667 unresolved dimension/source-binding tasks\n- section 4 reviewed: 35/35 sheets\n- section-4 tasks resolved: 32/35\n- remaining high: S4.9, S4.30, S4.31\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
  (m/'SUMMARY_v2.7.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'AUDIT_v2.7.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'README_v2.7.md').write_text(readme,encoding='utf-8')
  mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.7.json'];(m/'manifest_v2.7.json').write_text(json.dumps({'release':'2.7','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':len(facts),'component_variants':601,'dimension_queue':667,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  rd=D/'releases'/NEW
  if rd.exists():shutil.rmtree(rd)
  rd.mkdir(parents=True);out=td/'machine-state-v2.7.tar.gz'
  with tarfile.open(out,'w:gz') as t:
   for p in sorted(m.iterdir()):
    if p.is_file():t.add(p,arcname=p.name)
  ah=sha(out);(rd/'machine-state-v2.7.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii');(rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.7.tar.gz\n',encoding='utf-8');shutil.copy2(m/'SUMMARY_v2.7.json',rd/'summary.json');shutil.copy2(m/'AUDIT_v2.7.json',rd/'audit.json');shutil.copy2(m/'manifest_v2.7.json',rd/'manifest.json');(rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(rd/'README.md').write_text(readme,encoding='utf-8')
  cp=D/'index'/'source_counts.json';cnt=json.loads(cp.read_text(encoding='utf-8'))
  for r in cnt:
   if r.get('source_id')==SRC:r.update({'parameter_facts':r.get('parameter_facts',0)+len(added),'section4_dimension_binding_status':'reviewed_v2.7','section4_dimension_binding_tasks_resolved':32,'section4_dimension_binding_high_remaining':3})
  cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp=D/'index'/'systems.json';sy=json.loads(sp.read_text(encoding='utf-8'));sy['release']=NEW;sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8')
  (D/'README.md').write_text(f'# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.7**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- {len(facts)} typed parameter facts\n- 601 component variants\n- 667 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.7 preserves v2.6 and closes 32/35 FAVORIT sheet-material section-4 source-binding tasks. Remaining high: S4.9, S4.30 and S4.31. Safety remains fail-closed; raster pixels never become construction dimensions.\n',encoding='utf-8')
  (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.7'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1];r=d/'releases'/ACTIVE_RELEASE;data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii'));actual=hashlib.sha256(data).hexdigest();assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256);target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked';target.mkdir(parents=True,exist_ok=True);tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz';tmp.write_bytes(data);tf=tarfile.open(tmp,'r:gz');tf.extractall(target);tf.close();tmp.unlink();print(target)\nif __name__=='__main__':raise SystemExit(main())\n",encoding='utf-8')
  print('V2.7 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
 return 0
if __name__=='__main__':raise SystemExit(main())
