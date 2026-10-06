#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,pathlib,shutil,tarfile,tempfile
D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.8';NEW='v2.9';SRC='FAVORIT_SHEET_MATERIALS'
EXPECTED=(1215,1253,601,641);KEEP={12,29,30}
GENERIC='Manual visual review of the supplied source page found no additional untranscribed numeric dimension or fastener designation beyond the existing legend/semantics.'
NOTES={
 2:'Bracket grid is source-bound: both vertical and horizontal spacing are printed 600–1200 mm. Source notes say bracket length depends on insulation thickness and bracket type/spacing require strength-calculation confirmation.',
 12:'Open-cassette layout is project-bound and also contains a printed 29 mm dimension. The 29 mm value is transcribed, but exact semantic endpoints / Archicad parameter role are not uniquely resolved. Keep high priority.',
 13:'Open-cassette detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',
 14:'Closed-cassette horizontal layout dimensions are project-defined (по проекту); no numeric module is supplied.',
 15:'Closed-cassette detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',
 16:'Siding/linear-panel horizontal layout dimensions are project-defined (по проекту); no numeric module is supplied.',
 17:'Siding/linear-panel detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',
 18:'Profiled-sheet vertical layout is project-defined and the source prints fastening option ВС 4.2×32 with washer РЕРДМ or A2/A2 4×8 rivet.',
 19:'Profiled-sheet/siding detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',
 20:'Profiled-sheet horizontal layout/overlap is project-defined and the source prints fastening option ВС 4.2×32 with washer РЕРДМ or A2/A2 4×8 rivet.',
 23:'Vertical thermal-joint opening is explicitly printed 10 mm and is uniquely bound to the joint opening.',
 24:'Horizontal thermal-joint opening is explicitly printed 10 mm and is uniquely bound to the joint opening.',
 29:'Upper window reveal contains two printed 35 mm dimensions. Values are transcribed, but exact semantic endpoints / Archicad parameter roles are not uniquely resolved. Keep high priority.',
 30:'Side window reveal contains two printed 35 mm dimensions. Values are transcribed, but exact semantic endpoints / Archicad parameter roles are not uniquely resolved. Keep high priority.',
 34:'Clearance 20–30 mm between lower facade edge and horizontal plane (paving/roof) is uniquely source-bound.'}

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

def mkfact(n,seq,kind,subject,literal,value,binding):
 page=182+n;did=f'{SRC}__S6_{n}';sheet=f'6.{n}'
 return {'fact_id':f'{SRC}__P{page}__{kind}__V29_{seq:03d}','detail_id':did,'source_id':SRC,'source_literal':literal,'fact_kind':kind,'subject':subject,'source_unit':'mm' if kind in ('spacing_range','minimum_dimension','printed_dimension_unresolved','clearance_range') else None,'normalized_unit':'mm' if kind in ('spacing_range','minimum_dimension','printed_dimension_unresolved','clearance_range') else None,'value_json':json.dumps(value,ensure_ascii=False,separators=(',',':')),'binding_state':binding,'bound_component_position':None,'source_locator_json':json.dumps({'representation':'atr_favorit_listovie_materiali.pdf','page':page,'actual_sheet':sheet,'context_sequence':sheet},ensure_ascii=False,separators=(',',':'))}
def add_if_missing(facts,row):
 for x in facts:
  if x.get('detail_id')==row['detail_id'] and x.get('source_literal')==row['source_literal'] and x.get('subject')==row['subject']:return x.get('fact_id'),False
 facts.append(row);return row['fact_id'],True

def main():
 with tempfile.TemporaryDirectory(prefix='v29-') as td0:
  td=pathlib.Path(td0);tgz=td/'base.tgz';bx=td/'b'
  tgz.write_bytes(base64.b64decode((D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64').read_text(encoding='ascii')));extract(tgz,bx)
  root=one(bx,'details_active_v2.8.jsonl').parent;m=td/'machine';shutil.copytree(root,m)
  active=js(m/'details_active_v2.8.jsonl');facts=js(m/'parameter_facts_v2.8.jsonl');vars=js(m/'component_variants_v2.8.jsonl');queue=js(m/'dimension_binding_queue_v2.8.jsonl')
  if (len(active),len(facts),len(vars),len(queue))!=EXPECTED:raise RuntimeError(f'base totals changed {(len(active),len(facts),len(vars),len(queue))} != {EXPECTED}')
  byid={r.get('detail',{}).get('detail_id'):r for r in active};target={f'{SRC}__S6_{n}' for n in range(1,35)}
  tq=[r for r in queue if r.get('record_id') in target and r.get('source_id')==SRC]
  if len(tq)!=34:raise RuntimeError(f'unexpected section6 queue {len(tq)} != 34')
  if any(r.get('priority')!='high' for r in tq):raise RuntimeError('section6 queue contains non-high task unexpectedly')
  added=[];seq=0
  def ADD(n,kind,subject,literal,value,binding):
   nonlocal seq;seq+=1;fid,new=add_if_missing(facts,mkfact(n,seq,kind,subject,literal,value,binding));
   if new:added.append(fid)
   return fid
  ADD(2,'spacing_range','bracket_grid_vertical','600...1200',{'min':600,'max':1200},'bound_unique');ADD(2,'spacing_range','bracket_grid_horizontal','600...1200',{'min':600,'max':1200},'bound_unique')
  ADD(2,'technical_note','bracket_length_selection','Длина кронштейнов выбирается исходя из толщины утеплителя.',None,'semantic_note');ADD(2,'technical_note','bracket_type_and_spacing','Тип кронштейнов и шаг их установки подтверждается расчетом на прочность.',None,'semantic_note')
  for n,subject in [(12,'open_cassette_horizontal_layout_module'),(14,'closed_cassette_horizontal_layout_module'),(16,'siding_or_linear_panel_horizontal_layout_module'),(18,'profiled_sheet_vertical_layout'),(20,'profiled_sheet_horizontal_layout_and_overlap')]:ADD(n,'project_bound_dimension',subject,'по проекту','project_defined','project_input_required')
  ADD(12,'printed_dimension_unresolved','open_cassette_layout_dimension_29','29',29,'unresolved_semantic_binding')
  fast='Самонарезающий оцинкованный винт ВС 4,2×32 с уплотнительной шайбой РЕРДМ или заклепка A2/A2 4×8';fastval={'option_1':{'type':'ВС','diameter_mm':4.2,'length_mm':32,'washer_text_source_literal':'РЕРДМ'},'option_2':{'type':'blind_rivet','material':'A2/A2','diameter_mm':4,'length_mm':8}}
  for n in (13,15,17,18,19,20):ADD(n,'fastener_option','cladding_to_subframe_fastener',fast,fastval,'bound_to_cladding_fastener')
  ADD(23,'minimum_dimension','thermal_joint_opening_vertical','10',10,'bound_unique');ADD(24,'minimum_dimension','thermal_joint_opening_horizontal','10',10,'bound_unique')
  for n in (29,30):
   ADD(n,'printed_dimension_unresolved','window_reveal_dimension_1','35',35,'unresolved_semantic_binding');ADD(n,'printed_dimension_unresolved','window_reveal_dimension_2','35',35,'unresolved_semantic_binding')
  ADD(34,'clearance_range','facade_bottom_to_horizontal_plane','20...30',{'min':20,'max':30},'bound_unique')
  fact_ids_by_detail={}
  for x in facts:fact_ids_by_detail.setdefault(x.get('detail_id'),[]).append(x.get('fact_id'))
  reviews=[];resolved=set();kept=set()
  for n in range(1,35):
   did=f'{SRC}__S6_{n}';row=byid.get(did)
   if not row:raise RuntimeError('missing '+did)
   ir=row.get('ir') or {};pre=pjson(ir.get('preconditions_json'));ids=list(dict.fromkeys((pre.get('source_fact_ids') or [])+fact_ids_by_detail.get(did,[])));pre['source_fact_ids']=ids
   keep=n in KEEP;state='open_high_endpoint_binding' if keep else 'resolved_source_review_complete';note=NOTES.get(n,GENERIC)
   rem=('printed source value(s) are known, but exact semantic endpoints / Archicad parameter binding remain unresolved' if keep else None)
   reviews.append({'review_id':f'{did}__DBR_v2_9','record_id':did,'source_id':SRC,'sheet':f'6.{n}','pdf_page':182+n,'review_release':'2.9','review_method':'manual_visual_review_of_rendered_supplied_source_page','raster_measurement_used':False,'existing_source_fact_ids':ids,'resolution_state':state,'queue_resolved':not keep,'remaining_blocker':rem,'note':note,'commit_allowed':False})
   (kept if keep else resolved).add(did)
   d=row.get('detail') or {};pbs=pjson(d.get('parameter_binding_summary_json'));pbs.update({'source_page_review_release':'2.9','dimension_queue_state':state,'raster_measurement_used':False,'review_note':note});d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'))
   pre['dimension_binding_review_v2_9']={'state':state,'queue_resolved':not keep,'note':note,'raster_measurement_used':False};ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':'));ir['commit_allowed']=0
  nq=[]
  for r in queue:
   rid=r.get('record_id')
   if rid in resolved:continue
   if rid in kept:
    r=dict(r);r.update({'queue_kind':'semantic_dimension_endpoint_resolution','priority':'high','reason':'Printed source dimension value(s) are transcribed, but exact constraint endpoints / Archicad parameter binding are not uniquely resolved; raster measurement is forbidden.','status':'source_values_transcribed_endpoint_binding_open_v2.9'})
   nq.append(r)
  if len(nq)!=610:raise RuntimeError(f'queue {len(nq)} != 610')
  if any(scan_commit(r) for r in active):raise RuntimeError('commit_allowed true')
  wjs(m/'details_active_v2.9.jsonl',active);(m/'details_active_v2.8.jsonl').unlink();wjs(m/'parameter_facts_v2.9.jsonl',facts);(m/'parameter_facts_v2.8.jsonl').unlink();wjs(m/'component_variants_v2.9.jsonl',vars);(m/'component_variants_v2.8.jsonl').unlink();wjs(m/'dimension_binding_queue_v2.9.jsonl',nq);(m/'dimension_binding_queue_v2.8.jsonl').unlink();wjs(m/'favorit_section6_dimension_binding_v2.9.jsonl',reviews)
  for old,new in [('source_registry_v2.8.json','source_registry_v2.9.json'),('sources_v2.8.json','sources_v2.9.json'),('source_normative_claims_v2.8.json','source_normative_claims_v2.9.json')]:
   p=m/old
   if p.exists():(m/new).write_text(json.dumps(rel(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.unlink()
  for n in ('SUMMARY_v2.8.json','AUDIT_v2.8.json','README_v2.8.md','manifest_v2.8.json','SOURCE_VERIFY_FULL_v2.8.json'):
   p=m/n
   if p.exists():p.unlink()
  sv=rel(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')));(m/'SOURCE_VERIFY_FULL_v2.9.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');checks=sv.get('representation_checks',[]);hm=sum(bool(x.get('match')) for x in checks);ht=len(checks)
  if ht and hm!=ht:raise RuntimeError('source hash failure')
  summary={'release':'2.9','base_release':'v2.8','focus_source':SRC,'focus_scope':'section 6, sheets 6.1-6.34 / PDF pages 183-216','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':len(facts),'component_variants_total':601,'dimension_queue_total':610,'section6_pages_reviewed':34,'section6_queue_tasks_resolved':31,'section6_high_remaining':3,'remaining_section6_records':sorted(kept),'new_parameter_facts':len(added),'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
  audit={'release':'2.9','checks':summary,'critical_findings':['31 of 34 FAVORIT section-6 source-transcription tasks are closed after manual visual review.','S6.12 remains high: printed 29 mm is transcribed but exact semantic endpoints / Archicad parameter role are not uniquely resolved.','S6.29/S6.30 remain high: two printed 35 mm dimensions on each window-reveal detail are transcribed but exact semantic endpoints / Archicad parameter roles are not uniquely resolved.','S6.2 source-bound bracket grid is 600–1200 mm in both directions; source explicitly requires bracket type/spacing strength-calculation confirmation.','S6.12/S6.14/S6.16/S6.18/S6.20 layout dimensions are project-defined; no module/overlap value was invented.','S6.13/S6.15/S6.17/S6.18/S6.19/S6.20 source-literal fastener option is preserved as ВС 4.2×32 + washer РЕРДМ or A2/A2 4×8 rivet; РЕРДМ is not silently normalized.','S6.23 and S6.24 thermal-joint openings are printed 10 mm and uniquely bound. S6.34 clearance 20–30 mm is uniquely bound to lower facade edge versus horizontal plane.','Queue closure is not construction permission; all active IR remains fail-closed.'],'commit_allowed_true_introduced':0}
  readme=f'# Archicad construction detail machine state v2.9\n\nFAVORIT sheet-material section-6 source-binding closure over v2.8.\n\n- 1,215 detail units / active IR bindings\n- {len(facts):,} typed parameter facts\n- 601 component variants\n- 610 unresolved dimension/source-binding tasks\n- section 6 reviewed: 34/34 sheets\n- section-6 tasks resolved: 31/34\n- remaining high: S6.12, S6.29, S6.30\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
  (m/'SUMMARY_v2.9.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'AUDIT_v2.9.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'README_v2.9.md').write_text(readme,encoding='utf-8')
  mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.9.json'];(m/'manifest_v2.9.json').write_text(json.dumps({'release':'2.9','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':len(facts),'component_variants':601,'dimension_queue':610,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  rd=D/'releases'/NEW
  if rd.exists():shutil.rmtree(rd)
  rd.mkdir(parents=True);out=td/'machine-state-v2.9.tar.gz'
  with tarfile.open(out,'w:gz') as t:
   for p in sorted(m.iterdir()):
    if p.is_file():t.add(p,arcname=p.name)
  ah=sha(out);(rd/'machine-state-v2.9.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii');(rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.9.tar.gz\n',encoding='utf-8');shutil.copy2(m/'SUMMARY_v2.9.json',rd/'summary.json');shutil.copy2(m/'AUDIT_v2.9.json',rd/'audit.json');shutil.copy2(m/'manifest_v2.9.json',rd/'manifest.json');(rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(rd/'README.md').write_text(readme,encoding='utf-8')
  cp=D/'index'/'source_counts.json';cnt=json.loads(cp.read_text(encoding='utf-8'))
  for r in cnt:
   if r.get('source_id')==SRC:r.update({'parameter_facts':r.get('parameter_facts',0)+len(added),'section6_dimension_binding_status':'reviewed_v2.9','section6_dimension_binding_tasks_resolved':31,'section6_dimension_binding_high_remaining':3})
  cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp=D/'index'/'systems.json';sy=json.loads(sp.read_text(encoding='utf-8'));sy['release']=NEW;sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8')
  (D/'README.md').write_text(f'# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.9**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- {len(facts)} typed parameter facts\n- 601 component variants\n- 610 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.9 preserves v2.8 and closes 31/34 FAVORIT sheet-material section-6 source-binding tasks. Remaining high: S6.12, S6.29 and S6.30. Safety remains fail-closed; raster pixels never become construction dimensions.\n',encoding='utf-8')
  (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.9'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1];r=d/'releases'/ACTIVE_RELEASE;data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii'));actual=hashlib.sha256(data).hexdigest();assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256);target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked';target.mkdir(parents=True,exist_ok=True);tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz';tmp.write_bytes(data);tf=tarfile.open(tmp,'r:gz');tf.extractall(target);tf.close();tmp.unlink();print(target)\nif __name__=='__main__':raise SystemExit(main())\n",encoding='utf-8')
  print('V2.9 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
 return 0
if __name__=='__main__':raise SystemExit(main())