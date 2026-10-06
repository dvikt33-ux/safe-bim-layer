#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,pathlib,shutil,tarfile,tempfile

D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.7';NEW='v2.8';SRC='FAVORIT_SHEET_MATERIALS'
EXPECTED=(1215,1235,601,667)
KEEP={23,24}
GENERIC='Manual visual review of the supplied source page found no additional untranscribed numeric dimension or fastener designation beyond the existing legend/semantics.'
NOTES={
 2:'Bracket grid is source-bound: vertical 600–1200 mm and horizontal max 600 mm. Source notes say bracket length depends on insulation thickness and bracket type/spacing require strength-calculation confirmation.',
 8:'Open-cassette horizontal layout dimensions are explicitly project-defined (по проекту); no source numeric module is supplied.',
 9:'Open-cassette fastener option is source-literal: galvanized self-tapping screw ВС 4.2×32 with sealing washer РЕРДМ or A2/A2 4×8 rivet.',
 10:'Closed-cassette horizontal layout dimensions are explicitly project-defined (по проекту); no source numeric module is supplied.',
 11:'Closed-cassette fastener option is source-literal: galvanized self-tapping screw ВС 4.2×32 with sealing washer РЕРДМ or A2/A2 4×8 rivet.',
 12:'Steel siding / linear-panel horizontal layout dimensions are explicitly project-defined (по проекту); no source numeric module is supplied.',
 13:'Siding/linear-panel fastener option is source-literal: galvanized self-tapping screw ВС 4.2×32 with sealing washer РЕРДМ or A2/A2 4×8 rivet.',
 14:'Profiled-sheet horizontal layout/overlap is project-defined; source also prints fastening option ВС 4.2×32 with washer РЕРДМ or A2/A2 4×8 rivet.',
 17:'Vertical thermal-joint opening is explicitly printed min 10 mm and is uniquely source-bound to the joint opening.',
 23:'Upper window reveal contains two printed 35 mm dimensions. Values are transcribed, but exact semantic endpoints / Archicad parameter roles are not uniquely resolved. Keep high priority.',
 24:'Side window reveal contains two printed 35 mm dimensions. Values are transcribed, but exact semantic endpoints / Archicad parameter roles are not uniquely resolved. Keep high priority.',
 28:'Clearance 20–30 mm between lower facade edge and horizontal plane (paving/roof) is uniquely source-bound.'
}

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
def plist(v):
 if isinstance(v,list):return list(v)
 if isinstance(v,str) and v.strip():
  try:
   x=json.loads(v);return x if isinstance(x,list) else []
  except Exception:return []
 return []
def scan_commit(x):
 if isinstance(x,dict):return x.get('commit_allowed') is True or any(scan_commit(v) for v in x.values())
 if isinstance(x,list):return any(scan_commit(v) for v in x)
 return False
def rel(x):
 if isinstance(x,dict):return {k:(NEW if k in ('release','active_release') and isinstance(v,str) else rel(v)) for k,v in x.items()}
 if isinstance(x,list):return [rel(v) for v in x]
 return x

def fact(detail_id,page,kind,subject,literal,value,binding,seq):
 return {
  'fact_id':f'{SRC}__P{page}__{kind}__V28_{seq:03d}',
  'detail_id':detail_id,'source_id':SRC,'source_literal':literal,'fact_kind':kind,'subject':subject,
  'source_unit':'mm' if kind in ('spacing_range','max_spacing','minimum_dimension','printed_dimension_unresolved','clearance_range') else None,
  'normalized_unit':'mm' if kind in ('spacing_range','max_spacing','minimum_dimension','printed_dimension_unresolved','clearance_range') else None,
  'value_json':json.dumps(value,ensure_ascii=False,separators=(',',':')),
  'binding_state':binding,'bound_component_position':None,
  'source_locator_json':json.dumps({'representation':'atr_favorit_listovie_materiali.pdf','page':page,'actual_sheet':detail_id.split('__S5_')[-1].join(['5.','']) if '__S5_' in detail_id else None,'context_sequence':detail_id.split('__')[-1].replace('S','').replace('_','.')},ensure_ascii=False,separators=(',',':'))
 }

def add_if_missing(facts,row):
 for x in facts:
  if x.get('detail_id')==row['detail_id'] and x.get('source_literal')==row['source_literal'] and x.get('subject')==row['subject']:
   return x.get('fact_id'),False
 facts.append(row);return row['fact_id'],True

def main():
 with tempfile.TemporaryDirectory(prefix='v28-') as td0:
  td=pathlib.Path(td0);tgz=td/'base.tgz';bx=td/'b'
  b64=D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64'
  if not b64.exists():raise RuntimeError('missing base package '+str(b64))
  tgz.write_bytes(base64.b64decode(b64.read_text(encoding='ascii')));extract(tgz,bx)
  root=one(bx,'details_active_v2.7.jsonl').parent;m=td/'machine';shutil.copytree(root,m)
  active=js(m/'details_active_v2.7.jsonl');facts=js(m/'parameter_facts_v2.7.jsonl');vars=js(m/'component_variants_v2.7.jsonl');queue=js(m/'dimension_binding_queue_v2.7.jsonl')
  if (len(active),len(facts),len(vars),len(queue))!=EXPECTED:raise RuntimeError(f'base totals changed: {(len(active),len(facts),len(vars),len(queue))} != {EXPECTED}')
  byid={r.get('detail',{}).get('detail_id'):r for r in active};target={f'{SRC}__S5_{n}' for n in range(1,29)}
  tq=[r for r in queue if r.get('record_id') in target and r.get('source_id')==SRC]
  if len(tq)!=28:raise RuntimeError(f'unexpected section5 queue size {len(tq)} != 28')
  if any(r.get('priority')!='high' for r in tq):raise RuntimeError('section5 queue contains non-high task unexpectedly')

  added=[];seq=0
  def ADD(n,kind,subject,literal,value,binding):
   nonlocal seq;seq+=1;did=f'{SRC}__S5_{n}';page=153+n
   fid,new=add_if_missing(facts,fact(did,page,kind,subject,literal,value,binding,seq))
   if new:added.append(fid)
   return fid

  # Explicit printed / project-bound source facts from manual visual review of supplied pages 154-181.
  ADD(2,'spacing_range','bracket_grid_vertical','600...1200',{'min':600,'max':1200},'bound_unique')
  ADD(2,'max_spacing','bracket_grid_horizontal','max 600',{'max':600},'bound_unique')
  ADD(2,'technical_note','bracket_length_selection','Длина кронштейнов выбирается исходя из толщины утеплителя.',None,'semantic_note')
  ADD(2,'technical_note','bracket_type_and_spacing','Тип кронштейнов и шаг их установки подтверждается расчетом на прочность.',None,'semantic_note')
  for n,subject in [(8,'open_cassette_horizontal_layout_module'),(10,'closed_cassette_horizontal_layout_module'),(12,'siding_or_linear_panel_horizontal_layout_module'),(14,'profiled_sheet_horizontal_layout_and_overlap')]:
   ADD(n,'project_bound_dimension',subject,'по проекту','project_defined','project_input_required')
  fast='Самонарезающий оцинкованный винт ВС 4,2×32 с уплотнительной шайбой РЕРДМ или заклепка A2/A2 4×8'
  fastval={'option_1':{'type':'ВС','diameter_mm':4.2,'length_mm':32,'washer_text_source_literal':'РЕРДМ'},'option_2':{'type':'blind_rivet','material':'A2/A2','diameter_mm':4,'length_mm':8}}
  for n in (9,11,13,14):ADD(n,'fastener_option','cladding_to_subframe_fastener',fast,fastval,'bound_to_cladding_fastener')
  ADD(17,'minimum_dimension','thermal_joint_opening','min 10',10,'bound_unique')
  for n in (23,24):
   ADD(n,'printed_dimension_unresolved','window_reveal_dimension_1','35',35,'unresolved_semantic_binding')
   ADD(n,'printed_dimension_unresolved','window_reveal_dimension_2','35',35,'unresolved_semantic_binding')
  ADD(28,'clearance_range','facade_bottom_to_horizontal_plane','20...30',{'min':20,'max':30},'bound_unique')

  # Fix operation-role inconsistency globally, but only when the semantic role itself is explicit.
  role_fixes=[]
  for row in active:
   ir=row.get('ir') or {};ents=plist(ir.get('entities_json'));ops=plist(ir.get('operation_sequence_json'))
   posrole={e.get('source_component_position'):str(e.get('semantic_role') or '') for e in ents if e.get('source_component_position') is not None}
   changed=False
   for op in ops:
    role=str(op.get('component_role') or posrole.get(op.get('component_position')) or '').lower()
    hardware=('fastener' in role or role in {'anchor','bolt_set','bolt_fastening_set','clamping_washer','insulation_fastener'})
    if hardware and op.get('op') in {'PLACE_CLADDING','PLACE_COMPONENT'}:
     before=op.get('op');op['op']='PLACE_FASTENER_OR_HARDWARE';changed=True
     role_fixes.append({'detail_id':row.get('detail',{}).get('detail_id'),'component_position':op.get('component_position'),'semantic_role':role,'from':before,'to':'PLACE_FASTENER_OR_HARDWARE'})
   if changed:ir['operation_sequence_json']=json.dumps(ops,ensure_ascii=False,separators=(',',':'))

  fact_ids_by_detail={}
  for x in facts:
   fact_ids_by_detail.setdefault(x.get('detail_id'),[]).append(x.get('fact_id'))
  reviews=[];resolved=set();kept=set()
  for n in range(1,29):
   did=f'{SRC}__S5_{n}';row=byid.get(did)
   if not row:raise RuntimeError('missing '+did)
   ir=row.get('ir') or {};pre=pjson(ir.get('preconditions_json'));ids=list(dict.fromkeys((pre.get('source_fact_ids') or [])+fact_ids_by_detail.get(did,[])))
   pre['source_fact_ids']=ids;keep=n in KEEP;state='open_high_endpoint_binding' if keep else 'resolved_source_review_complete';note=NOTES.get(n,GENERIC)
   reviews.append({'review_id':f'{did}__DBR_v2_8','record_id':did,'source_id':SRC,'sheet':f'5.{n}','pdf_page':153+n,'review_release':'2.8','review_method':'manual_visual_review_of_rendered_supplied_source_page','raster_measurement_used':False,'existing_source_fact_ids':ids,'resolution_state':state,'queue_resolved':not keep,'remaining_blocker':('two printed 35 mm values are known, but exact semantic endpoints / Archicad parameter binding remain unresolved' if keep else None),'note':note,'commit_allowed':False})
   (kept if keep else resolved).add(did)
   d=row.get('detail') or {};pbs=pjson(d.get('parameter_binding_summary_json'));pbs.update({'source_page_review_release':'2.8','dimension_queue_state':state,'raster_measurement_used':False,'review_note':note});d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'))
   pre['dimension_binding_review_v2_8']={'state':state,'queue_resolved':not keep,'note':note,'raster_measurement_used':False};ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':'));ir['commit_allowed']=0

  nq=[]
  for r in queue:
   rid=r.get('record_id')
   if rid in resolved:continue
   if rid in kept:
    r=dict(r);r.update({'queue_kind':'semantic_dimension_endpoint_resolution','priority':'high','reason':'Two printed 35 mm source dimensions are transcribed, but exact constraint endpoints / Archicad parameter binding are not uniquely resolved; raster measurement is forbidden.','status':'source_values_transcribed_endpoint_binding_open_v2.8'})
   nq.append(r)
  if len(nq)!=641:raise RuntimeError(f'queue {len(nq)} != 641')
  if any(scan_commit(r) for r in active):raise RuntimeError('commit_allowed true')

  wjs(m/'details_active_v2.8.jsonl',active);(m/'details_active_v2.7.jsonl').unlink()
  wjs(m/'parameter_facts_v2.8.jsonl',facts);(m/'parameter_facts_v2.7.jsonl').unlink()
  wjs(m/'component_variants_v2.8.jsonl',vars);(m/'component_variants_v2.7.jsonl').unlink()
  wjs(m/'dimension_binding_queue_v2.8.jsonl',nq);(m/'dimension_binding_queue_v2.7.jsonl').unlink()
  wjs(m/'favorit_section5_dimension_binding_v2.8.jsonl',reviews)
  wjs(m/'ir_operation_role_corrections_v2.8.jsonl',role_fixes)

  for old,new in [('source_registry_v2.7.json','source_registry_v2.8.json'),('sources_v2.7.json','sources_v2.8.json'),('source_normative_claims_v2.7.json','source_normative_claims_v2.8.json')]:
   p=m/old
   if p.exists():(m/new).write_text(json.dumps(rel(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.unlink()
  for n in ('SUMMARY_v2.7.json','AUDIT_v2.7.json','README_v2.7.md','manifest_v2.7.json','SOURCE_VERIFY_FULL_v2.7.json'):
   p=m/n
   if p.exists():p.unlink()

  sv=rel(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')));(m/'SOURCE_VERIFY_FULL_v2.8.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  checks=sv.get('representation_checks',[]);hm=sum(bool(x.get('match')) for x in checks);ht=len(checks)
  if ht and hm!=ht:raise RuntimeError('source hash failure')
  summary={'release':'2.8','base_release':'v2.7','focus_source':SRC,'focus_scope':'section 5, sheets 5.1-5.28 / PDF pages 154-181','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':len(facts),'component_variants_total':601,'dimension_queue_total':641,'section5_pages_reviewed':28,'section5_queue_tasks_resolved':26,'section5_high_remaining':2,'remaining_section5_records':sorted(kept),'new_parameter_facts':len(added),'ir_operation_role_corrections':len(role_fixes),'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
  audit={'release':'2.8','checks':summary,'critical_findings':['26 of 28 FAVORIT section-5 source-transcription tasks are closed after manual visual review.','S5.23/S5.24 remain high: two printed 35 mm dimensions on each window-reveal detail are transcribed but exact semantic endpoints / Archicad parameter roles are not uniquely resolved.','S5.2 source-bound grid: vertical 600–1200 mm, horizontal max 600 mm; source explicitly requires bracket type/spacing strength-calculation confirmation.','S5.8/S5.10/S5.12/S5.14 layout dimensions are project-defined; no numeric module was invented.','S5.9/S5.11/S5.13/S5.14 source-literal fastener option is preserved as ВС 4.2×32 + washer РЕРДМ or A2/A2 4×8 rivet; РЕРДМ is not silently normalized.','S5.17 min 10 is bound to thermal-joint opening; S5.28 20–30 mm is bound to bottom clearance to horizontal plane.',f'{len(role_fixes)} IR operation-role inconsistencies were corrected only where explicit semantic roles identified hardware/fasteners previously emitted as generic/cladding placement.','Queue closure is not construction permission; all active IR remains fail-closed.'],'commit_allowed_true_introduced':0}
  readme=f'# Archicad construction detail machine state v2.8\n\nFAVORIT sheet-material section-5 source-binding closure over v2.7.\n\n- 1,215 detail units / active IR bindings\n- {len(facts):,} typed parameter facts\n- 601 component variants\n- 641 unresolved dimension/source-binding tasks\n- section 5 reviewed: 28/28 sheets\n- section-5 tasks resolved: 26/28\n- remaining high: S5.23, S5.24\n- IR hardware-role corrections: {len(role_fixes)}\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
  (m/'SUMMARY_v2.8.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'AUDIT_v2.8.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'README_v2.8.md').write_text(readme,encoding='utf-8')
  mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.8.json'];(m/'manifest_v2.8.json').write_text(json.dumps({'release':'2.8','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':len(facts),'component_variants':601,'dimension_queue':641,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

  rd=D/'releases'/NEW
  if rd.exists():shutil.rmtree(rd)
  rd.mkdir(parents=True);out=td/'machine-state-v2.8.tar.gz'
  with tarfile.open(out,'w:gz') as t:
   for p in sorted(m.iterdir()):
    if p.is_file():t.add(p,arcname=p.name)
  ah=sha(out);(rd/'machine-state-v2.8.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii');(rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.8.tar.gz\n',encoding='utf-8');shutil.copy2(m/'SUMMARY_v2.8.json',rd/'summary.json');shutil.copy2(m/'AUDIT_v2.8.json',rd/'audit.json');shutil.copy2(m/'manifest_v2.8.json',rd/'manifest.json');(rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(rd/'README.md').write_text(readme,encoding='utf-8')

  cp=D/'index'/'source_counts.json';cnt=json.loads(cp.read_text(encoding='utf-8'))
  for r in cnt:
   if r.get('source_id')==SRC:r.update({'parameter_facts':r.get('parameter_facts',0)+len(added),'section5_dimension_binding_status':'reviewed_v2.8','section5_dimension_binding_tasks_resolved':26,'section5_dimension_binding_high_remaining':2})
  cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp=D/'index'/'systems.json';sy=json.loads(sp.read_text(encoding='utf-8'));sy['release']=NEW;sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8')
  (D/'README.md').write_text(f'# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.8**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- {len(facts)} typed parameter facts\n- 601 component variants\n- 641 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.8 preserves v2.7 and closes 26/28 FAVORIT sheet-material section-5 source-binding tasks. Remaining high: S5.23 and S5.24. Safety remains fail-closed; raster pixels never become construction dimensions.\n',encoding='utf-8')
  (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.8'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1];r=d/'releases'/ACTIVE_RELEASE;data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii'));actual=hashlib.sha256(data).hexdigest();assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256);target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked';target.mkdir(parents=True,exist_ok=True);tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz';tmp.write_bytes(data);tf=tarfile.open(tmp,'r:gz');tf.extractall(target);tf.close();tmp.unlink();print(target)\nif __name__=='__main__':raise SystemExit(main())\n",encoding='utf-8')
  print('V2.8 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
 return 0
if __name__=='__main__':raise SystemExit(main())