#!/usr/bin/env python3
"""VIS-01 source-indexed scenario. Coordinates are arbitrary, never metres."""
import json,sys,argparse,csv,hashlib,math,subprocess
from pathlib import Path
from itertools import combinations
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/moag_topology'),str(ROOT/'scripts')]
import physical_connectivity_r22 as r22,integrated_spatial_r15 as r15,solver_r11 as r11
import archicad_bim_graph as apa_graph,archicad_scene_v1 as apa_scene
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import plotly.graph_objects as go
import trimesh

R22_HEAD='b6b333d62cd9a4de6afcd8262d5882bf668086f8'
HALL='M-L1-AH-OLD-001'; ALIAS='M-L1-CH-001'; GALLERY='M-L1-CH-GAL-001'
OVAL_IDS={HALL,'MOAG-G-0009','MOAG-G-0036'}
COLOR={1:'#2e8bbd',2:'#cfab28',3:'#71a472'}

def constraint(cid,rows,any_of=False):
 return {'id':cid,'rows':rows,'any_of':any_of,'sources':[], 'status':'SCENARIO_NOT_SOURCE_FACT','family':'vis01_scenario'}

def mzn_solve(m,exe,out,label,extra=(),fixed=None):
 # Reuse R15's model, data encoder and witness verifier with a longer limit.
 # UNKNOWN remains UNKNOWN; no solver result is inferred from timeout.
 data=r15.mzn_data(m,extra)
 if fixed:data+='constraint value = '+json.dumps(fixed['values'])+';\n'
 path=out/(label+'.mzn');path.write_text(data,encoding='utf-8')
 proc=subprocess.run([str(exe),'--solver','cp-sat','--time-limit','60000','--output-mode','item',
    str(r15.HERE/'integrated_spatial_r15.mzn'),str(path)],capture_output=True,text=True,encoding='utf-8',timeout=100)
 (out/(label+'.stdout.txt')).write_text(proc.stdout,encoding='utf-8')
 (out/(label+'.stderr.txt')).write_text(proc.stderr,encoding='utf-8')
 if proc.returncode:raise RuntimeError('VIS01_MINIZINC_ERROR: '+proc.stderr)
 witnesses=[json.loads(line) for line in proc.stdout.splitlines() if line.startswith('{')]
 for w in witnesses:r15.verify(m,w,extra)
 return {'status':'SAT' if witnesses else 'INFEASIBLE' if '=====UNSATISFIABLE=====' in proc.stdout else 'UNKNOWN'}

def model():
 m,a=r22.build(); vols={v['id']:v for v in m['r13']['volumes']}; bx=m['boxes']; h=bx[HALL];c=bx[ALIAS]
 # G0057 is the source-confirmed sleeping hall, distinct from the circular
 # hall. Its dimensions and location are explicitly a scenario.
 sleep='MOAG-G-0057'; sz=[12,10,8];bx[sleep]=[]
 for axis,hi in zip('XYZ',[68,70,28]):
  bx[sleep].append(len(m['variables']));m['variables'].append({'name':'VIS01::SLEEP-HALL::'+axis,'domain':[0,hi],'interval':True})
 vols[sleep]={'id':sleep,'global_block':1,'sample_size':sz,'parent':None,'source_refs':[r22.r21.source('P-216')]}
 for pt in m['points']:
  if pt['id'] not in ('RT015-G','REF::MOAG-G-0057'):continue
  for k in range(3):
   m['constraints'].append(constraint('VIS01-SLEEP-BIND::'+pt['id']+'::'+str(k),[
    r15.row([(pt['variables'][k],1),(bx[sleep][k],-1)]),
    r15.row([(bx[sleep][k],1),(pt['variables'][k],-1)],-sz[k])]))
 m['constraints'].append(constraint('VIS01-HALL-ONE-ORIGIN', [r15.row([(h[k],1),(c[k],-1)]) for k in range(3)]+[r15.row([(c[k],1),(h[k],-1)]) for k in range(3)]))
 # A conservative inscribed rectangle confines the elevated control room
 # inside the selected circular hall (radius 8 scenario units).
 ctrl=bx['M-L1-AH-OLD-CTRL-001']
 m['constraints'].append(constraint('VIS01-CONTROL-IN-ELLIPSE',[
   r15.row([(ctrl[0],1),(h[0],-1)],3),r15.row([(h[0],1),(ctrl[0],-1)],-7),
   r15.row([(ctrl[1],1),(h[1],-1)],3),r15.row([(h[1],1),(ctrl[1],-1)],-8)]))
 for point in m['points']:
  if point.get('host_volume') not in (HALL,ALIAS) or point['id']=='REF::'+GALLERY:continue
  q=point['variables']
  m['constraints'].append(constraint('VIS01-POINT-IN-ELLIPSE::'+point['id'],[
   r15.row([(q[0],1),(h[0],-1)],3),r15.row([(h[0],1),(q[0],-1)],-13),
   r15.row([(q[1],1),(h[1],-1)],3),r15.row([(h[1],1),(q[1],-1)],-13)]))
 # Source P-220 describes a partial raised bridge. The angular extent,
 # thickness, orientation and absolute position below are a scenario.
 bx[GALLERY]=[]
 for axis,hi in zip('XYZ',[66,72,35]):
  bx[GALLERY].append(len(m['variables']));m['variables'].append({'name':'VIS01::GALLERY::'+axis,'domain':[0,hi],'interval':True})
 gv=bx[GALLERY];point=next(p for p in m['points'] if p['id']=='REF::'+GALLERY);q=point['variables']
 vols[GALLERY]={'id':GALLERY,'global_block':1,'sample_size':[14,7,1],'parent':HALL,'source_refs':[r22.r21.source('P-220')]}
 m['constraints'].append(constraint('VIS01-GALLERY-PLACEMENT',[
   r15.row([(gv[0],1),(h[0],-1)],1),r15.row([(h[0],1),(gv[0],-1)],-1),
   r15.row([(gv[1],1),(h[1],-1)],8),r15.row([(h[1],1),(gv[1],-1)],-8),
   r15.row([(gv[2],1),(q[2],-1)]),r15.row([(q[2],1),(gv[2],-1)]),
   r15.row([(q[0],1),(h[0],-1)],15),r15.row([(h[0],1),(q[0],-1)],-15),
   r15.row([(q[1],1),(h[1],-1)],8),r15.row([(h[1],1),(q[1],-1)],-8),
   r15.row([(q[2],1),(h[2],-1)],1),r15.row([(h[2],1),(q[2],-1)],-15),
   r15.row([(q[2],1),(ctrl[2],-1)],4)]))
 # Other named oval/circular spaces use conservative inscribed regions.
 # Their points remain scenario references and do not establish wall boundaries.
 level_origins={b['id']:b['origin'] for b in m['r13']['blocks']}
 for point in m['points']:
  host=point.get('host_volume')
  if host not in ('MOAG-G-0009','MOAG-G-0036'):continue
  q=point['variables'];v=vols[host]; box=bx[host];origin=level_origins[v['global_block']]
  for k in (0,1):
   lo=math.ceil(v['sample_size'][k]/6);hi=math.floor(5*v['sample_size'][k]/6)
   m['constraints'].append(constraint('VIS01-ROUND-POINT::'+point['id']+'::'+str(k),[
     r15.row([(q[k],1),(box[k],-1)],origin[k]+lo),
     r15.row([(box[k],1),(q[k],-1)],-origin[k]-hi)]))
 top=[v for v in vols.values() if not v['parent'] and v['id']!=ALIAS]
 # Volumetric disjointness is a selected scenario, not a book assertion.
 for u,v in combinations(top,2):
  if u['global_block']!=v['global_block']:continue
  x,y=bx[u['id']],bx[v['id']];rs=[]
  for k in range(3):
   rs += [r15.row([(y[k],1),(x[k],-1)],u['sample_size'][k]),r15.row([(x[k],1),(y[k],-1)],v['sample_size'][k])]
  m['constraints'].append(constraint('VIS01-SEPARATE::'+u['id']+'::'+v['id'],rs,True))
 return m,a,vols

def generate(out,exe):
 out.mkdir(parents=True,exist_ok=True);m,a,vols=model();cp=r15.cp_solve(m)
 if cp['status']!='SAT':raise RuntimeError('SCENARIO_NOT_SAT '+cp['status'])
 mz=mzn_solve(m,exe,out,'vis01-sat');replay=mzn_solve(m,exe,out,'vis01-witness',fixed=cp['witness'])
 if mz['status']!='SAT' or replay['status']!='SAT':raise RuntimeError('MINIZINC_REPLAY_FAILED')
 x,y=m['boxes'][HALL],m['boxes'][ALIAS]
 wrong=constraint('VIS01-FALSE-DISJOINT-HALL',[r15.row([(x[0],1),(y[0],-1)],1),r15.row([(y[0],1),(x[0],-1)],1)],True)
 bad=r15.cp_solve(m,[wrong]);badmz=mzn_solve(m,exe,out,'vis01-hall-split',[wrong])
 if bad['status']!='INFEASIBLE' or badmz['status']!='INFEASIBLE':raise RuntimeError('HALL_SPLIT_ACCEPTED')
 boat=r22.query(a,'M-L1-FH-001','M-L1-FH-002','same','VIS01-FALSE-BOAT-MERGE')
 badboat=r15.cp_solve(m,[boat]);boatmz=mzn_solve(m,exe,out,'vis01-boat-merge',[boat])
 if badboat['status']!='INFEASIBLE' or boatmz['status']!='INFEASIBLE':raise RuntimeError('DISTINCT_BOAT_HANGARS_MERGED')
 val=cp['witness']['values'];blocks={b['id']:b for b in m['r13']['blocks']};raw,fr,bounds,_,graph=r11.inputs()
 assert r11.digest(graph)==a['R09_fingerprint'] and len(graph['edges'])==845
 physical={n['id']:n for n in graph['nodes'] if n['layer']=='PHYSICAL_INDEX'}
 original={n['id']:n for n in raw['indexed_source_entities']+raw['indexed_r03_entities']+fr['physical_entities']}
 profiles={p['id']:p for p in bounds['profiles']}; objects=[]
 for ident in sorted(physical):
  if ident==ALIAS:continue
  n=physical[ident]; o=original[ident]; kind=n['kind']
  category=('level' if kind in ('level','global_block') else 'stair_or_vertical' if kind in ('stair','vertical_route','vertical_access','vertical_transport_group','vertical_void','shaft','hatch','hatch_group','local_gallery','internal_gallery') else 'sector_or_composite' if kind in ('space_group','zone','complex','historical_zone','building_zone','vertical_industrial_volume') else 'corridor_or_route' if kind in ('corridor','cargo_corridor','major_corridor','circulation','tunnel','technical_route') else 'portal_or_door' if kind in ('portal','door','opening','gate','airlock') else 'space_candidate' if kind in ('space','room','hangar','industrial_hall','production_hall','public_hall','raised_control_room','control_room','medical_room','library','suite','airlock_chamber') else 'engineering_or_equipment' if kind in ('utility','technical','equipment','industrial_equipment','system') else 'concept_or_other')
  obj={'id':ident,'aliases':[ALIAS] if ident==HALL else [], 'name':o.get('name',ident),'kind':kind,'category':category,'source_index':o,'level_domain':n['possible_global_levels'],'R05_profile':profiles.get(ident),'placement':'UNPLACED_UNKNOWN','coordinates_known':False}
  if ident==HALL:obj['alias_source_index']=original[ALIAS];obj['alias_R05_profile']=profiles.get(ALIAS)
  if ident in vols:
   spec=vols[ident]; block=blocks[spec['global_block']]; origin=[val[i]+block['origin'][k] for k,i in enumerate(m['boxes'][ident])]
   obj.update({'placement':'SCENARIO','global_level':spec['global_block'],'origin':origin,'size':spec['sample_size'],'parent':spec['parent'],'sources':spec['source_refs'],'units':'ABSTRACT_NOT_METRES','sample_shape':'BOX_ENVELOPE'})
   if ident==HALL:obj['alias_sources']=vols[ALIAS]['source_refs'];obj['size']=vols[ALIAS]['sample_size']
   if ident in OVAL_IDS:obj['sample_shape']='ELLIPTICAL_CYLINDER_SCENARIO'
   if ident==GALLERY:obj['sample_shape']='HALF_ANNULAR_GALLERY_SCENARIO'
  objects.append(obj)
 placed=[o for o in objects if o['placement']=='SCENARIO'];ids=[o['id'] for o in placed];deps={o['id']:[o['parent']] if o.get('parent') else [] for o in placed}
 # Reuse APA's own dependency topological compiler for this scene's parent DAG.
 order=apa_graph._topo(ids,deps)
 if order is None or set(order)!=set(ids):raise RuntimeError('APA_DEPENDENCY_CYCLE')
 apa=apa_scene.prepare(0,0)
 if apa['status']!='SCENE_PREVIEW_OFFLINE':raise RuntimeError('APA_SELF_CHECK_FAILED')
 # Rebuild volume order using APA dependency order.
 lookup={o['id']:o for o in placed};placed=[lookup[i] for i in order]
 def overlaps(u,v):return all(max(u['origin'][k],v['origin'][k])<min(u['origin'][k]+u['size'][k],v['origin'][k]+v['size'][k]) for k in range(3))
 issues=[]
 for u,v in combinations(placed,2):
  if u['global_level']!=v['global_level']:continue
  if u.get('parent')==v['id'] or v.get('parent')==u['id']:continue
  if overlaps(u,v):issues.append([u['id'],v['id']])
 # The conservative rectangle also guarantees every corner of the control
 # room and every R15-bound point assigned to either hall is inside its ellipse.
 hall=lookup[HALL];hx,hy,hz=hall['origin'];hw,hd,hh=hall['size']
 control=lookup['M-L1-AH-OLD-CTRL-001'];cx,cy,cz=control['origin'];cw,cd,ch=control['size']
 for px in (cx,cx+cw):
  for py in (cy,cy+cd):
   if ((px-hx-hw/2)/(hw/2))**2+((py-hy-hd/2)/(hd/2))**2>1:raise RuntimeError('CONTROL_OUTSIDE_ELLIPSE')
 for point in m['points']:
  if point.get('host_volume') not in (HALL,ALIAS):continue
  px,py=[val[i] for i in point['variables'][:2]]
  if ((px-hx-hw/2)/(hw/2))**2+((py-hy-hd/2)/(hd/2))**2>1:raise RuntimeError('BOUND_POINT_OUTSIDE_ELLIPSE')
 gallery=lookup[GALLERY];gx,gy,gz=gallery['origin'];gw,gd,gh=gallery['size']
 if not (hw==hd==16 and [gx,gy,gw,gd,gh]==[hx+1,hy+8,14,7,1] and hz<=gz and gz+gh<=hz+hh and 7<hw/2):
  raise RuntimeError('GALLERY_OUTSIDE_CIRCULAR_HALL')
 for point in m['points']:
  host=point.get('host_volume')
  if host not in ('MOAG-G-0009','MOAG-G-0036'):continue
  obj=lookup[host];hx,hy,_=obj['origin'];hw,hd,_=obj['size'];px,py=[val[i] for i in point['variables'][:2]]
  if ((px-hx-hw/2)/(hw/2))**2+((py-hy-hd/2)/(hd/2))**2>1:raise RuntimeError('ROUND_AREA_POINT_OUTSIDE_ELLIPSE')
 if issues:raise RuntimeError('SCENARIO_NONPARENT_OVERLAP '+str(issues))
 for o in placed:
  if not o.get('parent'):continue
  p=lookup[o['parent']]
  if not all(p['origin'][k]<=o['origin'][k] and o['origin'][k]+o['size'][k]<=p['origin'][k]+p['size'][k] for k in range(3)):raise RuntimeError('CHILD_OUTSIDE_PARENT')
 # Check whether one *hypothetical* conversion factor could satisfy each
 # existing R05 per-object area/height interval. No factor is selected and no
 # model dimension becomes a real measurement. The ellipsoid area uses the
 # same 32-sided polygon as the actual mesh.
 area_checks=[];lower=0.0;upper=float('inf');anchor=bounds['scale_anchor_m'];module2=bounds['module_area_m2']
 for o in placed:
  dx,dy,dz=o['size'];area=8*math.sin(2*math.pi/32)*(49-36) if o['id']==GALLERY else dx*dy*(4*math.sin(2*math.pi/32) if o['id'] in OVAL_IDS else 1)
  for profile in (o.get('R05_profile'),o.get('alias_R05_profile')):
   if profile is None:continue
   limits=profile['bounds'];lo=0.0;hi=float('inf')
   for key,den,root,ismin in (('min_module2',area,True,True),('max_module2',area,True,False),
      ('min_height_in_human_modules',dz,False,True),('max_height_in_human_modules',dz,False,False),
      ('editable_area_min_m2',area*module2,True,True),('editable_area_max_m2',area*module2,True,False),
      ('editable_height_min_m',dz*anchor,False,True),('editable_height_max_m',dz*anchor,False,False)):
    if o['id']==GALLERY and 'height' in key:continue
    value=limits.get(key)
    if value is None:continue
    threshold=(value/den)**(.5 if root else 1)
    if ismin:lo=max(lo,threshold)
    else:hi=min(hi,threshold)
   if lo>hi:raise RuntimeError('R05_SCENARIO_PROFILE_INFEASIBLE:'+profile['id'])
   lower=max(lower,lo);upper=min(upper,hi)
   area_checks.append({'object_id':o['id'],'profile_id':profile['id'],'area_scenario_units2':area,
       'height_scenario_units':dz,'height_comparison':'NOT_COMPARABLE_VISUAL_SLAB_IS_NOT_CLEARANCE' if o['id']==GALLERY else 'SCENARIO_HEIGHT', 'compatible_scale_interval_modules_per_unit':[lo,hi]})
 if lower>upper:raise RuntimeError('R05_NO_SHARED_SCENARIO_SCALE')
 area_evidence={'status':'SYMBOLIC_COMMON_SCALE_EXISTS_NOT_SELECTED','scale_interval_modules_per_scenario_unit':[lower,upper],
   'human_module_reference_m':anchor,'human_module_reference_source':bounds['scale_anchor_source'],
   'checks':area_checks,'limits':'Per-object area and comparable height intervals only; gallery visual thickness is not clearance. No global area/volume accounting or real dimensions proven.'}
 # Diagram and exterior show circular tier silhouettes; these are envelopes,
 # not new rooms. Circumscribed scenario circles contain each R13 domain.
 hull=[]
 for b in blocks.values():
  ox,oy,oz=b['origin'];w,d,h=b['bounds'];rw=w*np.sqrt(2)/2;rd=d*np.sqrt(2)/2
  hull.append({'id':'LEVEL-'+str(b['id']),'global_level':b['id'],
   'origin':[ox+w/2-rw,oy+d/2-rd,oz],'size':[2*rw,2*rd,h],
   'sample_shape':'CIRCULAR_TIER_ENVELOPE_SCENARIO','is_shell':True,
   'basis':['synthesis/r11/assets/station-plan.jpg','synthesis/r11/assets/station-exterior.webp'],
   'accuracy':'AUTHOR_IMAGES_QUALITATIVE_RADIUS_AND_HEIGHT_NOT_EVIDENCE'})
 scene={'schema':'MOAG-VIS01-SCENARIO/1','base_R22':R22_HEAD,'R09_fingerprint':a['R09_fingerprint'],'units':'ABSTRACT_SCENARIO_NOT_METRES','R05_symbolic_scale_check':area_evidence,'physical_indices':197,'identity_classes_in_R22_quotient':196,'confirmed_placements':0,'scenario_placements':len(placed),'unplaced_index_classes':len(physical)-1-len(placed),'blocks':list(blocks.values()),'shells':hull,'objects':objects,'placed_volumes':placed,'route_occurrences':[n for n in graph['nodes'] if n['layer']=='ROUTE_OCCURRENCE'],'gap_nodes':[n for n in graph['nodes'] if n['layer'] not in ('ROUTE_OCCURRENCE','PHYSICAL_INDEX')],'original_typed_edges':graph['edges'],'R22_edge_dispositions':a['edge_dispositions'],'route_relations_preserved_in_R22':845,'new_doors':0,'hull':'CIRCULAR_SCENARIO_SILHOUETTE_BASED_ON_AUTHOR_IMAGES_NOT_EXACT_AUTHOR_MESH','limits':'R13-based volumes, a scenario sleeping hall and a partial gallery are placed; remaining indices are unplaced. AABB geometry is not a solid wall model.'}
 r11.write(out/'scene.json',scene)
 with (out/'objects.csv').open('w',encoding='utf-8-sig',newline='') as f:
  fields=['id','name','kind','category','placement','global_level','origin','size','parent','aliases']; w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(objects)
 # One source of geometry for views, mesh export and interactive scene.
 def box_vertices(o):
  x,y,z=o['origin']; dx,dy,dz=o['size'];return np.array([[x,y,z],[x+dx,y,z],[x+dx,y+dy,z],[x,y+dy,z],[x,y,z+dz],[x+dx,y,z+dz],[x+dx,y+dy,z+dz],[x,y+dy,z+dz]])
 def shape(o):
  if o['id']==GALLERY:
   x,y,z=o['origin'];n=16;angles=np.linspace(0,np.pi,n+1)
   outer=np.column_stack((x+7+7*np.cos(angles),y+7*np.sin(angles),np.full(n+1,z)))
   inner=np.column_stack((x+7+6*np.cos(angles),y+6*np.sin(angles),np.full(n+1,z)))
   base=np.vstack((outer,inner));vertices=np.vstack((base,base+[0,0,o['size'][2]]));shift=2*(n+1);faces=[]
   for i in range(n):
    a,b=i,i+1;c,d=n+1+i,n+2+i
    faces.extend([[a,c,d,b],[a+shift,b+shift,d+shift,c+shift],
                  [a,b,b+shift,a+shift],[d,c,c+shift,d+shift]])
   faces.extend([[0,shift,n+1+shift,n+1],[n,2*n+1,2*n+1+shift,n+shift]])
   return vertices,faces
  if o['id'] not in OVAL_IDS and not o.get('is_shell'):return box_vertices(o),[[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
  x,y,z=o['origin'];dx,dy,dz=o['size'];n=32;angles=np.arange(n)*2*np.pi/n
  ring=np.column_stack((x+dx/2+dx/2*np.cos(angles),y+dy/2+dy/2*np.sin(angles),np.full(n,z)))
  vertices=np.vstack((ring,ring+[0,0,dz]));faces=[list(range(n)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
  return vertices,faces
 faces=[[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
 fig=go.Figure()
 for o in hull+placed:
  verts,polygons=shape(o); tri=[(0,1,2),(0,2,3),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
  if o['id'] in OVAL_IDS or o.get('is_shell') or o['id']==GALLERY:tri=[(f[0],f[j],f[j+1]) for f in polygons for j in range(1,len(f)-1)]
  shell=o['id'].startswith('LEVEL-'); t=np.array(tri);shade='#e67e22' if o['id']==GALLERY else COLOR[o['global_level']]
  fig.add_trace(go.Mesh3d(x=verts[:,0],y=verts[:,1],z=verts[:,2],i=t[:,0],j=t[:,1],k=t[:,2],color=shade,opacity=0.035 if shell else (0.65 if o['id']==GALLERY else 0.32),name=o['id'],legendgroup='level'+str(o['global_level']),hovertext=o['id']+' • scenario; not metres',hoverinfo='text',showlegend=True))
 fig.update_layout(title='МОАГ VIS-01 — сценарные оболочка и габариты, не стены; условные единицы',scene=dict(aspectmode='data',xaxis_title='X условно',yaxis_title='Y условно',zaxis_title='Z условно'),legend=dict(groupclick='togglegroup'),margin=dict(l=0,r=0,t=60,b=0))
 controls='''
 const plot=document.getElementById('{plot_id}');
 const panel=document.createElement('div');panel.style='position:fixed;top:70px;left:12px;background:white;padding:10px;z-index:1000;font:14px sans-serif';
 panel.innerHTML='<b>Показать</b><br><small>Только сценарий; не метры.<br>Объекты без размещения — в реестре.</small><br><label><input type=checkbox id=v1 checked> Уровень 1</label><br><label><input type=checkbox id=v2 checked> Уровень 2</label><br><label><input type=checkbox id=v3 checked> Уровень 3</label><br><label><input type=checkbox id=vs checked> Оболочка-сценарий</label><br><label><input type=checkbox id=vo checked> Сценарные объёмы</label>';
 document.body.appendChild(panel);function refresh(){let visible=plot.data.map(t=>{let lev=Number(t.legendgroup.slice(-1));let shell=t.name.startsWith('LEVEL-');return document.getElementById('v'+lev).checked && document.getElementById(shell?'vs':'vo').checked;});Plotly.restyle(plot,{visible:visible});} panel.querySelectorAll('input').forEach(e=>e.onchange=refresh);
 '''
 fig.write_html(str(out/'station.html'),include_plotlyjs=True,full_html=True,post_script=controls)
 mesh=trimesh.Scene()
 for o in hull+placed:
  if o['id']==GALLERY:
   verts,polygons=shape(o);triangles=[(f[0],f[j],f[j+1]) for f in polygons for j in range(1,len(f)-1)]
   obj=trimesh.Trimesh(vertices=verts,faces=triangles,process=False)
  else:
   obj=trimesh.creation.cylinder(radius=1,height=o['size'][2],sections=32) if o['id'] in OVAL_IDS or o.get('is_shell') else trimesh.creation.box(extents=o['size'])
   if o['id'] in OVAL_IDS or o.get('is_shell'):obj.apply_scale([o['size'][0]/2,o['size'][1]/2,1])
   obj.apply_translation(np.array(o['origin'])+np.array(o['size'])/2)
  hexcol=('#e67e22' if o['id']==GALLERY else COLOR[o['global_level']]).lstrip('#');color=[int(hexcol[i:i+2],16) for i in (0,2,4)]+[15 if o['id'].startswith('LEVEL-') else (170 if o['id']==GALLERY else 90)]
  material=trimesh.visual.material.PBRMaterial(baseColorFactor=color,alphaMode='BLEND',doubleSided=True,metallicFactor=0,roughnessFactor=1)
  obj.visual=trimesh.visual.texture.TextureVisuals(material=material)
  mesh.add_geometry(obj,node_name=o['id'],geom_name=o['id'])
 (out/'station.glb').write_bytes(mesh.export(file_type='glb'))
 def axon(name,selected):
  fig=plt.figure(figsize=(12,9));ax=fig.add_subplot(111,projection='3d');ax.set_autoscale_on(False)
  for o in hull+placed:
   if o['global_level'] not in selected:continue
   v,shape_faces=shape(o);shell=o['id'].startswith('LEVEL-');shade='#e67e22' if o['id']==GALLERY else COLOR[o['global_level']];poly=Poly3DCollection([v[f] for f in shape_faces],facecolors=shade,edgecolors=shade,linewidths=.5,alpha=.035 if shell else (.65 if o['id']==GALLERY else .25));ax.add_collection3d(poly)
   if not shell:ax.text(*(np.array(o['origin'])+np.array(o['size'])/2),o['id'].replace('M-L1-',''),fontsize=6)
  zmax=36 if selected=={1} else 84
  ax.set(xlim=(-18,98),ylim=(-18,98),zlim=(0,zmax),xlabel='X — условно',ylabel='Y — условно',zlabel='Z — условно');ax.set_box_aspect((116,116,zmax));ax.view_init(24,-57);ax.set_title('МОАГ: круглая оболочка по рисункам — сценарий; цветные тела — условные габариты, не стены');fig.savefig(out/name,dpi=140,bbox_inches='tight');plt.close(fig)
 axon('station-axon.png',{1,2,3});axon('level-1-axon.png',{1})
 for level in (1,2,3):
  fig,ax=plt.subplots(figsize=(9,9));shell=next(o for o in hull if o['global_level']==level);sx,sy,_=shell['origin'];sw,sd,_=shell['size'];ax.add_patch(matplotlib.patches.Ellipse((sx+sw/2,sy+sd/2),sw,sd,fill=False,ls='--',color=COLOR[level]))
  for o in placed:
   if o['global_level']!=level:continue
   x,y,z=o['origin'];dx,dy,dz=o['size'];patch=matplotlib.patches.Wedge((x+7,y),7,0,180,width=1,facecolor='#e67e22',edgecolor='black',alpha=.55) if o['id']==GALLERY else (matplotlib.patches.Ellipse((x+dx/2,y+dy/2),dx,dy,facecolor=COLOR[level],edgecolor='black',alpha=.27) if o['id'] in OVAL_IDS else plt.Rectangle((x,y),dx,dy,facecolor=COLOR[level],edgecolor='black',alpha=.27));ax.add_patch(patch);ax.text(x+dx/2,y+dy/2,o['id'],ha='center',va='center',fontsize=6)
  ax.set(xlim=(-18,98),ylim=(-18,98),aspect='equal',title=f'Уровень {level}: сценарные проекции (не план стен)',xlabel='X условно',ylabel='Y условно');fig.savefig(out/f'level-{level}.png',dpi=140,bbox_inches='tight');plt.close(fig)
 section_y=lookup[HALL]['origin'][1]+lookup[HALL]['size'][1]/2
 fig,ax=plt.subplots(figsize=(12,7))
 for o in hull+placed:
  x,y,z=o['origin'];dx,dy,dz=o['size'];shell=o['id'].startswith('LEVEL-')
  if not y<=section_y<=y+dy:continue
  if o['id']==GALLERY:
   for section_x in (x,x+dx-1):ax.add_patch(plt.Rectangle((section_x,z),1,dz,facecolor='#e67e22',edgecolor='black',alpha=.6))
   continue
  if o['id'] in OVAL_IDS or shell:
   ratio=(section_y-y-dy/2)/(dy/2); half=(dx/2)*np.sqrt(max(0,1-ratio*ratio));x=x+dx/2-half;dx=2*half
  ax.add_patch(plt.Rectangle((x,z),dx,dz,facecolor=COLOR[o['global_level']],edgecolor=COLOR[o['global_level']],alpha=.05 if shell else .26))
  if not shell:ax.text(x+dx/2,z+dz/2,o['id'],fontsize=6,ha='center')
 ax.set(xlim=(-18,98),ylim=(0,84),aspect='equal',title=f'Вертикальный разрез Y={section_y:g}, условные единицы',xlabel='X условно',ylabel='Z условно');fig.savefig(out/'vertical-section.png',dpi=140,bbox_inches='tight');plt.close(fig)
 r11.write(out/'validation.json',{'python_cp_sat':cp['status'],'minizinc':mz['status'],'minizinc_python_witness_replay':replay['status'],'false_hall_split_python':bad['status'],'false_hall_split_minizinc':badmz['status'],'false_boat_merge_python':badboat['status'],'false_boat_merge_minizinc':boatmz['status'],'actual_nonparent_aabb_intersections':issues,'parent_aabb_containment':'PASS','hall_ellipse_control_and_bound_points':'PASS','partial_gallery_containment':'PASS','R05_symbolic_scale_check':area_evidence,'APA_scene_graph_topological_order':order,'APA_independent_sample':{'status':apa['status'],'operations':len(apa['executionOrder']),'applies_to_moag':'NO'},'R22_fingerprint':a['R09_fingerprint'],'warning':'No physical coordinates proven. Disjointness assumptions apply only to this particular scenario; unsupported indexed rooms remain unplaced.'})
 artifacts=[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
            for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json']
 r11.write(out/'manifest.json',{'schema':'MOAG-VIS01-FILE-MANIFEST/1','base_R22':R22_HEAD,
    'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'files':artifacts})
 print(json.dumps({'placed':len(placed),'unplaced_indices':len(physical)-1-len(placed),'solver':cp['status'],'apa':apa['status'],'intersections':len(issues)}))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--minizinc',type=Path,default=next((ROOT/'.runtime/minizinc').glob('*/bin/minizinc.exe'),None) or next((ROOT/'.runtime/minizinc').glob('*/bin/minizinc'),None));z=ap.parse_args()
 if not z.minizinc:ap.error('MiniZinc executable required')
 generate(z.out,z.minizinc)
