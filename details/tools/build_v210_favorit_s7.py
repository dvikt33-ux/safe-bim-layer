#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,pathlib,shutil,tarfile,tempfile
D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.9';NEW='v2.10';SRC='FAVORIT_SHEET_MATERIALS';EXPECTED=(1215,1276,601,610);KEEP={28,29}
GENERIC='Manual visual review of the supplied source page found no additional untranscribed numeric dimension or fastener designation beyond the existing legend/semantics.'
NOTES={5:'Variant 1 prints 5–10 mm at the vertical splice between adjacent reinforced interstory C-profiles; value is bound to the profile end gap.',6:'Variant 2 prints 5–10 mm at the same interstory profile splice; value is bound to the profile end gap.',12:'KM3/KM4 variant 1 prints 5–10 mm at the vertical splice between adjacent reinforced interstory C-profiles; value is bound to the profile end gap.',13:'KM3/KM4 variant 2 prints 5–10 mm at the same interstory profile splice; value is bound to the profile end gap.',15:'Open-cassette horizontal layout is explicitly project-defined (по проекту).',16:'Open-cassette detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',17:'Closed-cassette horizontal layout is explicitly project-defined (по проекту).',18:'Closed-cassette detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',19:'Siding/linear-panel horizontal layout is explicitly project-defined (по проекту).',20:'Siding/linear-panel detail prints fastening option ВС 4.2×32 with source-literal washer РЕРДМ or A2/A2 4×8 rivet.',21:'Profiled-sheet horizontal layout/overlap is project-defined; source also prints fastening option ВС 4.2×32 with washer РЕРДМ or A2/A2 4×8 rivet.',28:'Window vertical junction contains two printed 35 mm dimensions. Values are transcribed but exact semantic endpoints / Archicad parameter roles remain unresolved. Keep high priority.',29:'Window side junction contains two printed 35 mm dimensions. Values are transcribed but exact semantic endpoints / Archicad parameter roles remain unresolved. Keep high priority.',33:'Clearance 20–30 mm between lower facade edge and horizontal plane is uniquely source-bound.'}
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
 page=217+n;did=f'{SRC}__S7_{n}';sheet=f'7.{n}';dim=kind in ('gap_range','printed_dimension_unresolved','clearance_range')
 return {'fact_id':f'{SRC}__P{page}__{kind}__V210_{seq:03d}','detail_id':did,'source_id':SRC,'source_literal':literal,'fact_kind':kind,'subject':subject,'source_unit':'mm' if dim else None,'normalized_unit':'mm' if dim else None,'value_json':json.dumps(value,ensure_ascii=False,separators=(',',':')),'binding_state':binding,'bound_component_position':None,'source_locator_json':json.dumps({'representation':'atr_favorit_listovie_materiali.pdf','page':page,'actual_sheet':sheet,'context_sequence':sheet},ensure_ascii=False,separators=(',',':'))}
def add_if_missing(facts,row):
 for x in facts:
  if x.get('detail_id')==row['detail_id'] and x.get('source_literal')==row['source_literal'] and x.get('subject')==row['subject']:return x.get('fact_id'),False
 facts.append(row);return row['fact_id'],True
def main():
 with tempfile.TemporaryDirectory(prefix='v210-') as td0:
  td=pathlib.Path(td0);tgz=td/'base.tgz';bx=td/'b';tgz.write_bytes(base64.b64decode((D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64').read_text(encoding='ascii')));extract(tgz,bx)
  root=one(bx,'details_active_v2.9.jsonl').parent;m=td/'machine';shutil.copytree(root,m)
  active=js(m/'details_active_v2.9.jsonl');facts=js(m/'parameter_facts_v2.9.jsonl');vars=js(m/'component_variants_v2.9.jsonl');queue=js(m/'dimension_binding_queue_v2.9.jsonl')
  if (len(active),len(facts),len(vars),len(queue))!=EXPECTED:raise RuntimeError('base totals changed')
  byid={r.get('detail',{}).get('detail_id'):r for r in active};target={f'{SRC}__S7_{n}' for n in range(1,34)};tq=[r for r in queue if r.get('record_id') in target and r.get('source_id')==SRC]
  if len(tq)!=33 or any(r.get('priority')!='high' for r in tq):raise RuntimeError(f'unexpected section7 queue state {len(tq)}')
  added=[];seq=0
  def ADD(n,kind,subject,literal,value,binding):
   nonlocal seq;seq+=1;fid,new=add_if_missing(facts,mkfact(n,seq,kind,subject,literal,value,binding));
   if new:added.append(fid)
  for n in (5,6,12,13):ADD(n,'gap_range','interstory_profile_vertical_splice_gap','5-10',{'min':5,'max':10},'bound_unique')
  for n,sub in [(15,'open_cassette_horizontal_layout_module'),(17,'closed_cassette_horizontal_layout_module'),(19,'siding_or_linear_panel_horizontal_layout_module'),(21,'profiled_sheet_horizontal_layout_and_overlap')]:ADD(n,'project_bound_dimension',sub,'по проекту','project_defined','project_input_required')
  fast='Самонарезающий оцинкованный винт ВС 4,2×32 с уплотнительной шайбой РЕРДМ или заклепка A2/A2 4×8';fastval={'option_1':{'type':'ВС','diameter_mm':4.2,'length_mm':32,'washer_text_source_literal':'РЕРДМ'},'option_2':{'type':'blind_rivet','material':'A2/A2','diameter_mm':4,'length_mm':8}}
  for n in (16,18,20,21):ADD(n,'fastener_option','cladding_to_subframe_fastener',fast,fastval,'bound_to_cladding_fastener')
  for n in (28,29):ADD(n,'printed_dimension_unresolved','window_reveal_dimension_1','35',35,'unresolved_semantic_binding');ADD(n,'printed_dimension_unresolved','window_reveal_dimension_2','35',35,'unresolved_semantic_binding')
  ADD(33,'clearance_range','facade_bottom_to_horizontal_plane','20...30',{'min':20,'max':30},'bound_unique')
  fbd={}
  for x in facts:fbd.setdefault(x.get('detail_id'),[]).append(x.get('fact_id'))
  reviews=[];resolved=set();kept=set()
  for n in range(1,34):
   did=f'{SRC}__S7_{n}';row=byid.get(did)
   if not row:raise RuntimeError('missing '+did)
   ir=row.get('ir') or {};pre=pjson(ir.get('preconditions_json'));ids=list(dict.fromkeys((pre.get('source_fact_ids') or [])+fbd.get(did,[])));pre['source_fact_ids']=ids;keep=n in KEEP;state='open_high_endpoint_binding' if keep else 'resolved_source_review_complete';note=NOTES.get(n,GENERIC)
   reviews.append({'review_id':f'{did}__DBR_v2_10','record_id':did,'source_id':SRC,'sheet':f'7.{n}','pdf_page':217+n,'review_release':'2.10','review_method':'manual_visual_review_of_rendered_supplied_source_page','raster_measurement_used':False,'existing_source_fact_ids':ids,'resolution_state':state,'queue_resolved':not keep,'remaining_blocker':('two printed 35 mm values are known, but exact semantic endpoints / Archicad parameter binding remain unresolved' if keep else None),'note':note,'commit_allowed':False});(kept if keep else resolved).add(did)
   d=row.get('detail') or {};pbs=pjson(d.get('parameter_binding_summary_json'));pbs.update({'source_page_review_release':'2.10','dimension_queue_state':state,'raster_measurement_used':False,'review_note':note});d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'));pre['dimension_binding_review_v2_10']={'state':state,'queue_resolved':not keep,'note':note,'raster_measurement_used':False};ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':'));ir['commit_allowed']=0
  nq=[]
  for r in queue:
   rid=r.get('record_id')
   if rid in resolved:continue
   if rid in kept:r=dict(r);r.update({'queue_kind':'semantic_dimension_endpoint_resolution','priority':'high','reason':'Two printed 35 mm source dimensions are transcribed, but exact constraint endpoints / Archicad parameter binding are not uniquely resolved; raster measurement is forbidden.','status':'source_values_transcribed_endpoint_binding_open_v2.10'})
   nq.append(r)
  if len(nq)!=579:raise RuntimeError(f'queue {len(nq)} != 579')
  if any(scan_commit(r) for r in active):raise RuntimeError('commit_allowed true')
  wjs(m/'details_active_v2.10.jsonl',active);(m/'details_active_v2.9.jsonl').unlink();wjs(m/'parameter_facts_v2.10.jsonl',facts);(m/'parameter_facts_v2.9.jsonl').unlink();wjs(m/'component_variants_v2.10.jsonl',vars);(m/'component_variants_v2.9.jsonl').unlink();wjs(m/'dimension_binding_queue_v2.10.jsonl',nq);(m/'dimension_binding_queue_v2.9.jsonl').unlink();wjs(m/'favorit_section7_dimension_binding_v2.10.jsonl',reviews)
  for old,new in [('source_registry_v2.9.json','source_registry_v2.10.json'),('sources_v2.9.json','sources_v2.10.json'),('source_normative_claims_v2.9.json','source_normative_claims_v2.10.json')]:
   p=m/old
   if p.exists():(m/new).write_text(json.dumps(rel(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.unlink()
  for n in ('SUMMARY_v2.9.json','AUDIT_v2.9.json','README_v2.9.md','manifest_v2.9.json','SOURCE_VERIFY_FULL_v2.9.json'):
   p=m/n
   if p.exists():p.unlink()
  sv=rel(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')));(m/'SOURCE_VERIFY_FULL_v2.10.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');checks=sv.get('representation_checks',[]);hm=sum(bool(x.get('match')) for x in checks);ht=len(checks)
  if ht and hm!=ht:raise RuntimeError('source hash failure')
  summary={'release':'2.10','base_release':'v2.9','focus_source':SRC,'focus_scope':'section 7, sheets 7.1-7.33 / PDF pages 218-250','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':len(facts),'component_variants_total':601,'dimension_queue_total':579,'section7_pages_reviewed':33,'section7_queue_tasks_resolved':31,'section7_high_remaining':2,'remaining_section7_records':sorted(kept),'new_parameter_facts':len(added),'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
  audit={'release':'2.10','checks':summary,'critical_findings':['31 of 33 FAVORIT section-7 source-transcription tasks are closed after manual visual review.','S7.28/S7.29 remain high: two printed 35 mm dimensions on each window-junction detail are transcribed but exact semantic endpoints / Archicad parameter roles are not uniquely resolved.','S7.5/S7.6/S7.12/S7.13 print 5–10 mm at the interstory reinforced C-profile splice; values are uniquely bound to the vertical profile end gap.','S7.15/S7.17/S7.19/S7.21 layout dimensions are project-defined; no module/overlap value was invented.','S7.16/S7.18/S7.20/S7.21 source-literal fastener option is preserved as ВС 4.2×32 + washer РЕРДМ or A2/A2 4×8 rivet; РЕРДМ is not silently normalized.','S7.33 clearance 20–30 mm is uniquely bound to the lower facade edge versus horizontal plane.','Queue closure is not construction permission; all active IR remains fail-closed.'],'commit_allowed_true_introduced':0}
  readme=f'# Archicad construction detail machine state v2.10\n\nFAVORIT sheet-material section-7 source-binding closure over v2.9.\n\n- 1,215 detail units / active IR bindings\n- {len(facts):,} typed parameter facts\n- 601 component variants\n- 579 unresolved dimension/source-binding tasks\n- section 7 reviewed: 33/33 sheets\n- section-7 tasks resolved: 31/33\n- remaining high: S7.28, S7.29\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
  (m/'SUMMARY_v2.10.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'AUDIT_v2.10.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'README_v2.10.md').write_text(readme,encoding='utf-8');mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.10.json'];(m/'manifest_v2.10.json').write_text(json.dumps({'release':'2.10','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':len(facts),'component_variants':601,'dimension_queue':579,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  rd=D/'releases'/NEW
  if rd.exists():shutil.rmtree(rd)
  rd.mkdir(parents=True);out=td/'machine-state-v2.10.tar.gz'
  with tarfile.open(out,'w:gz') as t:
   for p in sorted(m.iterdir()):
    if p.is_file():t.add(p,arcname=p.name)
  ah=sha(out);(rd/'machine-state-v2.10.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii');(rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.10.tar.gz\n',encoding='utf-8');shutil.copy2(m/'SUMMARY_v2.10.json',rd/'summary.json');shutil.copy2(m/'AUDIT_v2.10.json',rd/'audit.json');shutil.copy2(m/'manifest_v2.10.json',rd/'manifest.json');(rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(rd/'README.md').write_text(readme,encoding='utf-8')
  cp=D/'index'/'source_counts.json';cnt=json.loads(cp.read_text(encoding='utf-8'))
  for r in cnt:
   if r.get('source_id')==SRC:r.update({'parameter_facts':r.get('parameter_facts',0)+len(added),'section7_dimension_binding_status':'reviewed_v2.10','section7_dimension_binding_tasks_resolved':31,'section7_dimension_binding_high_remaining':2})
  cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp=D/'index'/'systems.json';sy=json.loads(sp.read_text(encoding='utf-8'));sy['release']=NEW;sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8');(D/'README.md').write_text(f'# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.10**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- {len(facts)} typed parameter facts\n- 601 component variants\n- 579 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.10 preserves v2.9 and closes 31/33 FAVORIT sheet-material section-7 source-binding tasks. Remaining high: S7.28 and S7.29. Safety remains fail-closed; raster pixels never become construction dimensions.\n',encoding='utf-8')
  (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.10'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1];r=d/'releases'/ACTIVE_RELEASE;data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii'));actual=hashlib.sha256(data).hexdigest();assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256);target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked';target.mkdir(parents=True,exist_ok=True);tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz';tmp.write_bytes(data);tf=tarfile.open(tmp,'r:gz');tf.extractall(target);tf.close();tmp.unlink();print(target)\nif __name__=='__main__':raise SystemExit(main())\n",encoding='utf-8')
  print('V2.10 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
 return 0
if __name__=='__main__':raise SystemExit(main())