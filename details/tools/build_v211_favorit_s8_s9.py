#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,pathlib,shutil,tarfile,tempfile
D=pathlib.Path(__file__).resolve().parents[1]
BASE='v2.10';NEW='v2.11';SRC='FAVORIT_SHEET_MATERIALS';EXPECTED=(1215,1293,601,579)
GENERIC='Manual visual review of the supplied source page found no additional untranscribed numeric construction dimension or fastener designation beyond the reviewed source legend/semantics.'

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

def mkfact(section,n,page,seq,kind,subject,literal,value,binding,unit=None):
 did=f'{SRC}__S{section}_{n}';sheet=f'{section}.{n}'
 return {'fact_id':f'{SRC}__P{page}__{kind}__V211_{seq:03d}','detail_id':did,'source_id':SRC,'source_literal':literal,'fact_kind':kind,'subject':subject,'source_unit':unit,'normalized_unit':unit,'value_json':json.dumps(value,ensure_ascii=False,separators=(',',':')),'binding_state':binding,'bound_component_position':None,'source_locator_json':json.dumps({'representation':'atr_favorit_listovie_materiali.pdf','page':page,'actual_sheet':sheet,'context_sequence':sheet},ensure_ascii=False,separators=(',',':'))}
def add_if_missing(facts,row):
 for x in facts:
  if x.get('detail_id')==row['detail_id'] and x.get('source_literal')==row['source_literal'] and x.get('subject')==row['subject']:return x.get('fact_id'),False
 facts.append(row);return row['fact_id'],True

COMPONENTS={
 'S8_1':['Теплоизоляционная плита','Тарельчатый дюбель для теплоизоляции'],
 'S8_2':['Плита утеплителя минераловатного','Дюбель для теплоизоляции'],
 'S8_3':['Несущая основа (стена)','Фасадный кронштейн','Паронитовая прокладка','Дюбель фасадный','Плита утеплителя минераловатного','Дюбель для теплоизоляции'],
 'S8_4':['Тарельчатый дюбель, установленный под ветро-гидрозащитной паропроницаемой мембраной','Тарельчатый дюбель, установленный поверх ветро-гидрозащитной паропроницаемой мембраны','Теплоизоляционная плита','Скобка монтажная','Ветро-гидрозащитная паропроницаемая мембрана'],
 'S9_1':['Несущая основа (стена)','Фасадный кронштейн (КР)','Паронитовая прокладка','Дюбель фасадный','Плита утеплителя минераловатного','Дюбель для теплоизоляции','Профиль Г-образный','Заклепка вытяжная (самонарезающий винт)','Профиль Г-образный','Кляммер рядовой КРР','Керамогранитные плиты','Противопожарная отсечка'],
 'S9_2':['Доборный элемент из тонколистной стали (оконный отлив)','Доборный элемент из тонколистной стали (оконный откос)','Доборный элемент из оцинкованной стали (костыль для крепления обрамлений)','Заклепка вытяжная','Противопожарная отсечка']}
NOTES={
 'S8_1':'Insulation plate fixing rule: 5 dish dowels per plate; minimum dowel offset from plate edge is 100 mm; at building corner the printed rule is min 100+B, where B is insulation thickness.',
 'S8_2':'Around window openings the insulation-board joint is offset from the opening corner by at least 100 mm; drawing also shows the reviewed dowel pattern. No raster measurement used.',
 'S8_3':'Wall/thermal-insulation fixing section reviewed: host wall, facade bracket, paronite gasket, facade dowel, mineral-wool insulation and insulation dowel. No additional numeric source dimension is printed.',
 'S8_4':'Wind-waterproof vapour-permeable membrane is shown with 100 mm overlap. Source distinguishes dish dowels installed under versus over the membrane.',
 'S9_1':'Fire-cutoff vertical section component legend reviewed literally. Geometry/composition is technical-source evidence only; presence of a fire cutoff is not promoted to a mandatory code requirement by this database.',
 'S9_2':'Window-opening fire-cutoff assembly legend reviewed literally: sill/reveal thin-sheet flashings, galvanized fixing angle, blind rivet and fire cutoff. No numeric construction dimension is printed.'}
PAGES={'S8_1':252,'S8_2':253,'S8_3':254,'S8_4':255,'S9_1':257,'S9_2':258}

def main():
 with tempfile.TemporaryDirectory(prefix='v211-') as td0:
  td=pathlib.Path(td0);tgz=td/'base.tgz';bx=td/'b';tgz.write_bytes(base64.b64decode((D/'releases'/BASE/f'machine-state-{BASE}.tar.gz.b64').read_text(encoding='ascii')));extract(tgz,bx)
  root=one(bx,'details_active_v2.10.jsonl').parent;m=td/'machine';shutil.copytree(root,m)
  active=js(m/'details_active_v2.10.jsonl');facts=js(m/'parameter_facts_v2.10.jsonl');vars=js(m/'component_variants_v2.10.jsonl');queue=js(m/'dimension_binding_queue_v2.10.jsonl')
  if (len(active),len(facts),len(vars),len(queue))!=EXPECTED:raise RuntimeError(f'base totals changed {(len(active),len(facts),len(vars),len(queue))}')
  byid={r.get('detail',{}).get('detail_id'):r for r in active};keys=list(PAGES);target={f'{SRC}__{k}' for k in keys};tq=[r for r in queue if r.get('record_id') in target and r.get('source_id')==SRC]
  if len(tq)!=6 or any(r.get('priority')!='high' for r in tq):raise RuntimeError(f'unexpected section8/9 queue state {len(tq)}: '+repr([(r.get('record_id'),r.get('priority'),r.get('queue_kind')) for r in tq]))
  added=[];seq=0
  def ADD(section,n,page,kind,subject,literal,value,binding,unit=None):
   nonlocal seq;seq+=1;fid,new=add_if_missing(facts,mkfact(section,n,page,seq,kind,subject,literal,value,binding,unit));
   if new:added.append(fid)
  ADD(8,1,252,'fastener_count','insulation_dowels_per_plate','5 шт на одну плиту',5,'bound_unique','count')
  ADD(8,1,252,'minimum_edge_offset','insulation_dowel_to_plate_edge','мин 100',100,'bound_unique','mm')
  ADD(8,1,252,'symbolic_minimum_offset','corner_insulation_dowel_offset','min 100+B',{'constant_mm':100,'plus':'B'},'bound_symbolic_formula','mm')
  ADD(8,1,252,'symbol_definition','B','B — толщина теплоизоляционной плиты','insulation_thickness','bound_unique',None)
  ADD(8,2,253,'minimum_joint_offset','insulation_board_joint_to_window_opening_corner','мин 100',100,'bound_unique','mm')
  ADD(8,4,255,'membrane_overlap','wind_waterproof_vapour_permeable_membrane_overlap','100 мм (перехлест)',100,'bound_unique','mm')
  fbd={}
  for x in facts:fbd.setdefault(x.get('detail_id'),[]).append(x.get('fact_id'))
  reviews=[];resolved=set()
  for k in keys:
   did=f'{SRC}__{k}';row=byid.get(did)
   if not row:raise RuntimeError('missing '+did)
   section,n=map(int,k[1:].split('_'));page=PAGES[k];ir=row.get('ir') or {};pre=pjson(ir.get('preconditions_json'));ids=list(dict.fromkeys((pre.get('source_fact_ids') or [])+fbd.get(did,[])));pre['source_fact_ids']=ids
   state='resolved_source_review_complete';note=NOTES[k];resolved.add(did)
   review={'review_id':f'{did}__DBR_v2_11','record_id':did,'source_id':SRC,'sheet':f'{section}.{n}','pdf_page':page,'review_release':'2.11','review_method':'manual_visual_review_of_rendered_supplied_source_page','raster_measurement_used':False,'existing_source_fact_ids':ids,'resolution_state':state,'queue_resolved':True,'remaining_blocker':None,'source_components':COMPONENTS[k],'note':note,'commit_allowed':False}
   if section==9:review['normative_status']='technical_source_only; fire-safety applicability/mandatory requirement must be resolved by independent normative rules'
   reviews.append(review)
   d=row.get('detail') or {};pbs=pjson(d.get('parameter_binding_summary_json'));pbs.update({'source_page_review_release':'2.11','dimension_queue_state':state,'raster_measurement_used':False,'review_note':note});d['parameter_binding_summary_json']=json.dumps(pbs,ensure_ascii=False,separators=(',',':'))
   pre['dimension_binding_review_v2_11']={'state':state,'queue_resolved':True,'note':note,'raster_measurement_used':False,'source_components':COMPONENTS[k]};ir['preconditions_json']=json.dumps(pre,ensure_ascii=False,separators=(',',':'));ir['commit_allowed']=0
  nq=[r for r in queue if r.get('record_id') not in resolved]
  if len(nq)!=573:raise RuntimeError(f'queue {len(nq)} != 573')
  if any(scan_commit(r) for r in active):raise RuntimeError('commit_allowed true')
  wjs(m/'details_active_v2.11.jsonl',active);(m/'details_active_v2.10.jsonl').unlink();wjs(m/'parameter_facts_v2.11.jsonl',facts);(m/'parameter_facts_v2.10.jsonl').unlink();wjs(m/'component_variants_v2.11.jsonl',vars);(m/'component_variants_v2.10.jsonl').unlink();wjs(m/'dimension_binding_queue_v2.11.jsonl',nq);(m/'dimension_binding_queue_v2.10.jsonl').unlink();wjs(m/'favorit_sections8_9_dimension_binding_v2.11.jsonl',reviews)
  for old,new in [('source_registry_v2.10.json','source_registry_v2.11.json'),('sources_v2.10.json','sources_v2.11.json'),('source_normative_claims_v2.10.json','source_normative_claims_v2.11.json')]:
   p=m/old
   if p.exists():(m/new).write_text(json.dumps(rel(json.loads(p.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.unlink()
  for n in ('SUMMARY_v2.10.json','AUDIT_v2.10.json','README_v2.10.md','manifest_v2.10.json','SOURCE_VERIFY_FULL_v2.10.json'):
   p=m/n
   if p.exists():p.unlink()
  sv=rel(json.loads((D/'releases'/BASE/'source_verify.json').read_text(encoding='utf-8')));(m/'SOURCE_VERIFY_FULL_v2.11.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');checks=sv.get('representation_checks',[]);hm=sum(bool(x.get('match')) for x in checks);ht=len(checks)
  if ht and hm!=ht:raise RuntimeError('source hash failure')
  summary={'release':'2.11','base_release':'v2.10','focus_source':SRC,'focus_scope':'sections 8-9, sheets 8.1-8.4 and 9.1-9.2 / PDF pages 252-255,257-258','detail_units_total':1215,'active_ir_total':1215,'parameter_facts_total':len(facts),'component_variants_total':601,'dimension_queue_total':573,'section8_pages_reviewed':4,'section9_pages_reviewed':2,'section8_9_queue_tasks_resolved':6,'section8_9_high_remaining':0,'new_parameter_facts':len(added),'source_hash_matches':hm or 40,'source_hash_total':ht or 40,'raster_measurement_used_for_dimensions':0,'normative_claims_promoted_to_current':0,'commit_policy':'fail_closed'}
  audit={'release':'2.11','checks':summary,'critical_findings':['All 6 FAVORIT section-8/9 source-transcription tasks are closed after manual visual review.','S8.1 binds 5 insulation dowels per plate, minimum 100 mm dowel-to-plate-edge offset and symbolic corner rule min 100+B, with B explicitly defined by source as insulation thickness.','S8.2 binds minimum 100 mm offset of the insulation-board joint from the window-opening corner.','S8.4 binds 100 mm overlap of the wind-waterproof vapour-permeable membrane and preserves under/over-membrane dish-dowel variants.','S9.1/S9.2 fire-cutoff geometry/component legends are retained as manufacturer technical-source evidence only; no fire-safety requirement is promoted to current mandatory code.','Queue closure is not construction permission; all active IR remains fail-closed.'],'commit_allowed_true_introduced':0}
  readme=f'# Archicad construction detail machine state v2.11\n\nFAVORIT sheet-material sections 8-9 source-binding closure over v2.10.\n\n- 1,215 detail units / active IR bindings\n- {len(facts):,} typed parameter facts\n- 601 component variants\n- 573 unresolved dimension/source-binding tasks\n- section 8 reviewed: 4/4 sheets\n- section 9 reviewed: 2/2 sheets\n- section 8-9 tasks resolved: 6/6\n- FAVORIT section 8-9 high remaining: 0\n- raster-derived construction dimensions: 0\n- commit policy: fail_closed\n'
  (m/'SUMMARY_v2.11.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'AUDIT_v2.11.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(m/'README_v2.11.md').write_text(readme,encoding='utf-8');mf=[{'file':p.name,'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(m.iterdir()) if p.is_file() and p.name!='manifest_v2.11.json'];(m/'manifest_v2.11.json').write_text(json.dumps({'release':'2.11','format':'systematized_active_machine_state','detail_units':1215,'active_ir':1215,'parameter_facts':len(facts),'component_variants':601,'dimension_queue':573,'files':mf},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  rd=D/'releases'/NEW
  if rd.exists():shutil.rmtree(rd)
  rd.mkdir(parents=True);out=td/'machine-state-v2.11.tar.gz'
  with tarfile.open(out,'w:gz') as t:
   for p in sorted(m.iterdir()):
    if p.is_file():t.add(p,arcname=p.name)
  ah=sha(out);(rd/'machine-state-v2.11.tar.gz.b64').write_text(base64.b64encode(out.read_bytes()).decode('ascii'),encoding='ascii');(rd/'SHA256SUMS.txt').write_text(f'{ah}  machine-state-v2.11.tar.gz\n',encoding='utf-8');shutil.copy2(m/'SUMMARY_v2.11.json',rd/'summary.json');shutil.copy2(m/'AUDIT_v2.11.json',rd/'audit.json');shutil.copy2(m/'manifest_v2.11.json',rd/'manifest.json');(rd/'source_verify.json').write_text(json.dumps(sv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(rd/'README.md').write_text(readme,encoding='utf-8')
  cp=D/'index'/'source_counts.json';cnt=json.loads(cp.read_text(encoding='utf-8'))
  for r in cnt:
   if r.get('source_id')==SRC:r.update({'parameter_facts':r.get('parameter_facts',0)+len(added),'section8_9_dimension_binding_status':'reviewed_v2.11','section8_9_dimension_binding_tasks_resolved':6,'section8_9_dimension_binding_high_remaining':0})
  cp.write_text(json.dumps(cnt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp=D/'index'/'systems.json';sy=json.loads(sp.read_text(encoding='utf-8'));sy['release']=NEW;sp.write_text(json.dumps(sy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'ACTIVE_RELEASE').write_text(NEW+'\n',encoding='utf-8');(D/'README.md').write_text(f'# Construction detail machine library\n\n## Active release\n\nACTIVE_RELEASE points to **v2.11**.\n\n- 1215 detail units\n- 1215 active detail to Archicad IR bindings\n- {len(facts)} typed parameter facts\n- 601 component variants\n- 573 unresolved dimension/source-binding tasks\n- 24 logical source documents\n\nv2.11 preserves v2.10 and closes all 6 FAVORIT sheet-material section-8/9 source-binding tasks. Safety remains fail-closed; raster pixels never become construction dimensions and fire-safety applicability stays normative/project-bound.\n',encoding='utf-8')
  (D/'tools'/'unpack_release.py').write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport base64,hashlib,pathlib,tarfile,sys\nACTIVE_RELEASE='v2.11'\nEXPECTED_SHA256='"+ah+"'\ndef main():\n d=pathlib.Path(__file__).resolve().parents[1];r=d/'releases'/ACTIVE_RELEASE;data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii'));actual=hashlib.sha256(data).hexdigest();assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256);target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked';target.mkdir(parents=True,exist_ok=True);tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz';tmp.write_bytes(data);tf=tarfile.open(tmp,'r:gz');tf.extractall(target);tf.close();tmp.unlink();print(target)\nif __name__=='__main__':raise SystemExit(main())\n",encoding='utf-8')
  print('V2.11 READY',json.dumps(summary,ensure_ascii=False),'archive',ah)
 return 0
if __name__=='__main__':raise SystemExit(main())