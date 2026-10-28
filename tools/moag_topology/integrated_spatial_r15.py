#!/usr/bin/env python3
"""R15: one CP-SAT feasibility problem for R13 boxes, R12 strata and R14 visits.

This is an adapter, not a path planner. Unknown intermediate path geometry is
represented by visit domains; no physical corridor, distance or door is created.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from collections import Counter

import solver_r11 as r11
import spatial_constraints_r12 as r12
import scenario_volumes_r13 as r13
import route_constraints_r14 as r14

HERE = Path(__file__).parent
AXES = ('x', 'y', 'z')


class Adapter:
    def __init__(self):
        self.variables = []
        self.constraints = []

    def var(self, name, lo=0, hi=84, domain=None):
        i = len(self.variables)
        self.variables.append({'name': name, 'domain': list(domain) if domain is not None else [lo, hi],
                               'interval': domain is None})
        return i

    def add(self, cid, rows, sources=(), status='fact_relation_in_scenario', any_of=False,
            family='source'):
        self.constraints.append({'id': cid, 'rows': rows, 'sources': list(sources),
            'status': status, 'any_of': any_of, 'family': family})


def row(terms, rhs=0, when=None):
    return {'terms': [[v,c] for v,c in terms], 'rhs': rhs, 'when': when}


def source(step):
    return {'id': step['id'], 'page_id': step['page_id'],
            'url': step['citation_url'], 'citation_status': step['citation_status'],
            'summary': step['observed_constraint']}


def build():
    volumes = r13.build()
    routes = r14.build()
    strata = {k:r12.build(k) for k in (1,2,3)}
    raw, fragments, bounds, _, master = r11.inputs()
    nodes = {x['id']:x for x in master['nodes'] if x['layer']=='PHYSICAL_INDEX'}
    original = {x['id']:x for x in raw['indexed_source_entities'] + raw['indexed_r03_entities'] + fragments['physical_entities']}
    profiles = {x['id']:x for x in bounds['profiles']}
    blocks = {b['id']:b for b in volumes['blocks']}
    a = Adapter(); boxes = {}; points = {}; times = {}

    for v in volumes['volumes']:
        boxes[v['id']] = [a.var('BOX::'+v['id']+'::'+axis, 0,
            blocks[v['global_block']]['bounds'][k]-v['sample_size'][k]) for k,axis in enumerate(AXES)]
    vi = {v['id']:v for v in volumes['volumes']}
    for v in volumes['volumes']:
        if not v['parent']: continue
        c,p = boxes[v['id']],boxes[v['parent']]
        rows = [row([(c[k],1),(p[k],-1)],1 if k==2 else 0) for k in range(3)]
        rows += [row([(p[k],1),(c[k],-1)],v['sample_size'][k]-vi[v['parent']]['sample_size'][k]) for k in range(3)]
        a.add('R13-ENCLOSE-'+v['id'],rows,v['parent_enclosure_source']['sources'])
    for pair in volumes['disjoint_3d_pairs']:
        i,j=pair['a'],pair['b']; rows=[]
        for k in range(3):
            rows.extend([row([(boxes[j][k],1),(boxes[i][k],-1)],vi[i]['sample_size'][k]),
                         row([(boxes[i][k],1),(boxes[j][k],-1)],vi[j]['sample_size'][k])])
        a.add('R13-DISJOINT-'+i+'-'+j,rows,vi[i]['source_refs']+vi[j]['source_refs'],any_of=True)
    for i,h in enumerate(volumes['schematic_plan_label_order']):
        k=AXES.index(h['axis']); u,v=h['a'],h['b']
        a.add('R13-PLAN-'+str(i),[row([(boxes[u][k],2),(boxes[v][k],-2)],
            1-vi[u]['sample_size'][k]+vi[v]['sample_size'][k])],
            [{'id':'USER-PLAN-20261028','file':'synthesis/r11/assets/station-plan.jpg'}],family='image')

    # Only explicit source containment; no aliases, historical relations,
    # trajectory order, contextual matches or hypotheses enter this map.
    parents={}
    for e in raw['source_relationships']:
        if (e['relation'] in {'contains','includes'} and e['evidence_state']=='TEXT_DIRECT'
                and e['semantic_class']=='FUNCTIONAL_CONTAINMENT_NOT_WALL_GEOMETRY'
                and e['binding_status']!='QUARANTINED_DO_NOT_USE_AS_DIRECT_GEOMETRY'):
            parents.setdefault(e['to'],[]).append(e)

    def host(eid, seen=frozenset()):
        if eid in boxes: return eid,[]
        if eid in seen: return None,[]
        matches=[]
        for e in parents.get(eid,[]):
            p,chain=host(e['from'],seen|{eid})
            if p: matches.append((p,[e['id']]+chain))
        if len({x[0] for x in matches})==1: return matches[0]
        return None,[]

    def point(pid, domain, src, graph_id, status='unknown'):
        xyz=[a.var('POINT::'+pid+'::'+q,0,84 if q=='z' else 80) for q in AXES]
        block=a.var('BLOCK::'+pid,domain=domain)
        records=[]
        for b in domain:
            box=blocks[b]; condition=[block,b]
            for k in range(3):
                records += [row([(xyz[k],1)],box['origin'][k],condition),
                            row([(xyz[k],-1)],-(box['origin'][k]+box['bounds'][k]-1),condition)]
        a.add('DOMAIN::'+pid,records,src,status='scenario_search_domain_not_book_dimensions',family='scenario')
        points[pid]={'id':pid,'graph_id':graph_id,'variables':xyz,'block_variable':block,
            'possible_blocks':domain,'sources':src,'status':status,
            'actual_metric_xyz':None,'physical_room_created':False}
        return xyz

    def bind(pid, target, src, chain=()):
        p=points[pid]['variables']; v=vi[target]; b=blocks[v['global_block']]; c=boxes[target]
        rows=[]
        for k in range(3):
            rows += [row([(p[k],1),(c[k],-1)],b['origin'][k]),
                     row([(c[k],1),(p[k],-1)],1-b['origin'][k]-v['sample_size'][k])]
        a.add('BIND::'+pid,rows,src,status='logical_inference_from_index_and_source_containment',family='binding')
        points[pid].update({'host_volume':target,'containment_source_chain':list(chain),
                           'binding_means':'VISIT_WITHIN_SCENARIO_REGION_NOT_DOOR_OR_EQUAL_FLOOR'})

    refs={}
    for eid,n in sorted(nodes.items()):
        obj=original[eid]
        refs[eid]=point('REF::'+eid,n['possible_global_levels'],
                       [{'id':s} for s in n['source_ids']],eid)
        target,chain=host(eid)
        if target and n['moag_station_identity_verified']:
            bind('REF::'+eid,target,[{'id':s} for s in n['source_ids']],chain)
        if eid in boxes:
            # Chosen reference is the floor of this scenario box, not all
            # visits/floors of an aggregate object sharing its source label.
            q=refs[eid][2];v=vi[eid];b=blocks[v['global_block']]
            a.add('BOX-FLOOR::'+eid,[row([(q,1),(boxes[eid][2],-1)],b['origin'][2]),
                                   row([(q,-1),(boxes[eid][2],1)],-b['origin'][2])],
                  v['source_refs'],status='scenario_floor_reference',family='scenario')

    access_envelopes={}
    for scope,p in strata.items():
        for c in p['r11']['constraints']:
            if c['kind']==1:
                a.add('R11::'+c['id'],[row([(refs[c['a']][2],1),(refs[c['b']][2],-1)],1)],c['sources'])
        for e in p['envelopes']:
            low,high=refs[e['container']][2],refs[e['upper']][2]
            rows=[row([(high,1),(low,-1)],1)]
            if e['container'] in boxes:
                v=vi[e['container']];b=blocks[v['global_block']]
                ceiling=([(boxes[e['container']][2],1)],1-b['origin'][2]-v['sample_size'][2])
                rows.append(row([(boxes[e['container']][2],1),(high,-1)],
                    1-b['origin'][2]-v['sample_size'][2]))
                # A partial gallery is a reference-point domain inside the
                # volume, never a rectangular room or continuous full deck.
                if 'host_volume' not in points['REF::'+e['upper']]:
                    bind('REF::'+e['upper'],e['container'],e['sources'])
            else:
                top=a.var('LOCAL-TOP::'+e['container'],blocks[scope]['origin'][2]+1,
                          blocks[scope]['origin'][2]+blocks[scope]['bounds'][2]-1)
                ceiling=([(top,1)],1)
                rows.append(row([(top,1),(high,-1)],1))
            a.add('R12::'+e['id'],rows,e['sources'])
            access_envelopes[e['upper']]={'lower':low,'ceiling':ceiling,'source':e}

    for s in routes['steps']:
        pid=s['id']; domain=[s['global_block']] if s['global_block'] else [1,2,3]
        point(pid,domain,[source(s)],'ROUTE::'+s['route']+'::'+pid)
        times[pid]=a.var('ORDER::'+pid,0,len(routes['steps']))
        target,chain=host(s['stable_graph_anchor'])
        if target: bind(pid,target,[source(s)],chain)
        if s['stable_graph_anchor'] in access_envelopes:
            envelope=access_envelopes[s['stable_graph_anchor']]
            sz=points[pid]['variables'][2];terms,rhs=envelope['ceiling']
            a.add('VISIT-UPPER::'+pid,[row([(sz,1),(envelope['lower'],-1)],1),
                row(terms+[(sz,-1)],rhs)],envelope['source']['sources']+[source(s)],family='binding')
            points[pid]['upper_envelope_source']=envelope['source']['id']
        points[pid]['stable_index_anchor']=s['stable_graph_anchor']
        points[pid]['block_from_route_record_not_multilevel_alias']=True
    for c in routes['strict_local_or_global_relative_z']:
        a.add(c['id'],[row([(points[c['higher']]['variables'][2],1),
                           (points[c['lower']]['variables'][2],-1)],1)],
              [{'id':c['id'],'page_id':c['source_page_id'],'url':c['citation_url'],'summary':c['source_claim']}])
    bystep={s['id']:s for s in routes['steps']}
    for c in routes['observed_order_not_direct_access']:
        a.add(c['id'],[row([(times[c['b']],1),(times[c['a']],-1)],1)],
              [source(bystep[c['a']]),source(bystep[c['b']])])

    descriptions=[]
    for path in routes['author_attached_base_route_overlays']:
        ids=[]
        for suffix,target in [('FROM',path['from']),('UNLOCATED-INTERVAL',None),('TO',path['to'])]:
            pid=path['id']+'::'+suffix;ids.append(pid)
            point(pid,[1] if target else [1,2,3],[path['source']],None)
            if target: bind(pid,target,[path['source']])
            points[pid]['descriptor_not_additional_route_stage_or_physical_corridor']=True
        descriptions.append({**deepcopy(path),'domain_element_ids':ids,
            'interval_is_entire_unlocated_description_not_one_physical_room':True,
            'door_geometry':None,'path_polyline':None,
            'direction_relation':'OPPOSITE_BRANCH_DIRECTIONS_IN_OBSERVER_FRAME' if path['source']['id']=='P-024' else 'SHORTER_DESCRIPTION_NO_METRIC_RATIO'})

    assets=strata[1]['r11']['source_review']['assets']
    for image in assets:
        if hashlib.sha256((r11.ROOT/image['file']).read_bytes()).hexdigest()!=image['sha256']:
            raise ValueError('AUTHOR_IMAGE_BYTES_CHANGED')
    visual=[{'id':x['id'],'file':x['file'],'sha256':x['sha256']} for x in assets]
    # Coarse sheet sectors only. No angle, true north or physical radius.
    dark,wild,oval=(boxes[x] for x in ('MOAG-G-0008','MOAG-G-0010','MOAG-G-0009'))
    for cid,terms,rhs in [('DARK-LEFT',[(dark[0],-2)],-79+10),
                          ('WILD-TOP',[(wild[1],-2)],-79+8),
                          ('OVAL-BOTTOM',[(oval[1],2)],81-9)]:
        a.add('IMAGE::'+cid,[row(terms,rhs)],visual[:1],family='image')
    # A sector's schematic representative stays outside the base-side belt.
    # Individual R03 hangars are NOT automatically equated with this label.
    a.add('IMAGE::HANGAR-SECTOR-OUTER-LEFT',
          [row([(dark[0],1),(refs['MOAG-G-0007'][0],-1)],1)],visual[:1],family='image')
    ring_inner=a.var('VISUAL::INNER-RING',0,2)
    ring_outer=a.var('VISUAL::OUTER-RING',0,2)
    a.add('IMAGE::RING-RADIAL-ORDER',[row([(ring_outer,1),(ring_inner,-1)],1)],visual[:1],family='image')

    entities=[{'id':eid,'name':original[eid]['name'],'sources':n['source_ids'],
        'global_block_domain':n['possible_global_levels'],'domain_element':'REF::'+eid,
        'reference_is_not_all_floors_of_aggregate':True,'R05_profile':profiles[eid],
        'metric_bounds_status':'hypothesis' if profiles[eid]['bounds'] else 'unknown',
        'actual_geometry':None,'station_identity_verified':n['moag_station_identity_verified']}
        for eid,n in sorted(nodes.items())]
    missing=[{'id':p['id'],'graph_id':p['graph_id'],'anchor':p.get('stable_index_anchor'),
        'reason':'NO_PROVEN_R13_VOLUME_OR_UNAMBIGUOUS_CONTAINMENT_CHAIN',
        'domain_blocks':p['possible_blocks'],'source':p['sources']}
        for p in points.values() if p['id'] in bystep and 'host_volume' not in p]
    corpus=[]
    for book in ('B1','B2','B3','B4'):
        ledger=r11.read(r11.BASE/'v2/pages'/f'{book}.json')
        corpus.append({'book':book,'title':ledger['title'],'total_pages':ledger['page_count'],
            'recorded_review_statuses':dict(Counter(p['status'] for p in ledger['pages'])),
            'source_ledger':'v2/pages/'+book+'.json',
            'route_steps_in_R14':sum(s['page_id'].startswith(book+'-') for s in routes['steps']),
            'full_book_reaudit_performed_in_R15':False})
    model={'schema':'MOAG-R15-JOINT-SOURCE-CONSTRAINED-SCENARIO/1',
        'r13':volumes,'r14':routes,'r12_envelopes':[e for p in strata.values() for e in p['envelopes']],
        'entities':entities,'points':list(points.values()),'boxes':boxes,'order_variables':times,
        'variables':a.variables,'constraints':a.constraints,'base_path_descriptions':descriptions,
        'four_book_source_ledgers':corpus,
        'unbound_route_steps':missing,'historical_bases':{'original_id':'MOAG-G-0073','numbers':[3,4],
            'individual_correspondence_to_named_bases':'unknown','new_physical_indices_created':False},
        'author_image_checks':{'assets':visual,'base_sheet_sectors':'HARD_COARSE_ORDINAL',
            'hangar_sector':'OUTER_LABEL_DOMAIN_NOT_INDIVIDUAL_HANGAR_IDENTITY',
            'ring_radial_organisation':'TYPED_INNER_OUTER_ORDER_NOT_POLYGON_OR_DOORS',
            'radial_connectors':'SCHEMATIC_CONNECTION_OF_DISTINCT_RINGS_NOT_NEW_GRAPH_EDGES',
            'stepped_silhouette':'NESTED_XY_THREE_SEPARATE_BLOCK_DOMAINS_ONLY',
            'exact_hull_mesh_verified':False},
        'R09_fingerprint':r11.digest(master),'R13_fingerprint':r11.digest(volumes),
        'R14_fingerprint':r11.digest(routes),'source_R09_unchanged':True,
        'metric_units':'ARTIFICIAL_R13_SCENARIO_NOT_METRES',
        'unknown_path_geometry_created':False,'geometry_approved':False,'archicad_write':False}
    validate(model)
    return model


def validate(m):
    r13.validate(m['r13']);r14.validate(m['r14'])
    if len(m['entities'])!=197 or len(m['r12_envelopes'])!=9:
        raise ValueError('SOURCE_INVENTORY_LOST')
    if r11.digest(m['r13'])!=m['R13_fingerprint'] or r11.digest(m['r14'])!=m['R14_fingerprint']:
        raise ValueError('SOURCE_PROJECTION_MUTATED')
    points={p['id']:p for p in m['points']}
    if len(points)!=len(m['points']) or len({c['id'] for c in m['constraints']})!=len(m['constraints']):
        raise ValueError('DUPLICATE_IDENTIFIER')
    if {p['id'] for p in m['points'] if p['id'] in m['order_variables']}!={s['id'] for s in m['r14']['steps']}:
        raise ValueError('INTERMEDIATE_ROUTE_STAGE_LOST')
    record_ids={c['id'] for c in m['constraints']}
    required={c['id'] for c in m['r14']['observed_order_not_direct_access']+m['r14']['strict_local_or_global_relative_z']}
    required|={'R12::'+e['id'] for e in m['r12_envelopes']}
    if not required<=record_ids:raise ValueError('SOURCE_CONSTRAINT_NOT_COMPILED')
    if {p['graph_id'] for p in m['points'] if p['id'].startswith('REF::')}!={e['id'] for e in m['entities']}:
        raise ValueError('INDEX_REFERENCE_DOMAIN_LOST')
    for p in m['points']:
        if 'host_volume' in p and 'BIND::'+p['id'] not in record_ids:
            raise ValueError('REPORTED_BINDING_NOT_IN_SOLVER')
        if 'upper_envelope_source' in p and 'VISIT-UPPER::'+p['id'] not in record_ids:
            raise ValueError('UPPER_GALLERY_VISIT_CONSTRAINT_LOST')
    if any(p['physical_room_created'] or p['actual_metric_xyz'] is not None for p in points.values()):
        raise ValueError('UNKNOWN_STAGE_PROMOTED_TO_GEOMETRY')
    for path in m['base_path_descriptions']:
        for pid,target in zip((path['domain_element_ids'][0],path['domain_element_ids'][-1]),(path['from'],path['to'])):
            if points[pid].get('host_volume')!=target:
                raise ValueError('BASE_PATH_DETACHED_FROM_CONFIRMED_ENDPOINT')
    if points['RT007-H'].get('host_volume') or any(c['becomes_hard_geometry_anchor'] for c in m['r14']['candidate_only_step_index_matches']):
        raise ValueError('CARGO_CANDIDATE_BECAME_APPROVED_IDENTITY')
    b=m['r13']['blocks']
    for lower,upper in zip(b,b[1:]):
        if (upper['origin'][2]<lower['origin'][2]+lower['bounds'][2] or
            any(not lower['origin'][k]<=upper['origin'][k] or
                upper['origin'][k]+upper['bounds'][k]>lower['origin'][k]+lower['bounds'][k] for k in (0,1))):
            raise ValueError('STEPPED_SILHOUETTE_DOMAIN_VIOLATED')
    expected={'DARK-LEFT','WILD-TOP','OVAL-BOTTOM','HANGAR-SECTOR-OUTER-LEFT','RING-RADIAL-ORDER'}
    if {c['id'].removeprefix('IMAGE::') for c in m['constraints'] if c['id'].startswith('IMAGE::')}!=expected:
        raise ValueError('AUTHOR_IMAGE_CONSTRAINT_DROPPED')
    if m['geometry_approved'] or m['archicad_write'] or m['unknown_path_geometry_created']:
        raise ValueError('UNSUPPORTED_GEOMETRY_OR_WRITE')
    if [x['book'] for x in m['four_book_source_ledgers']]!=['B1','B2','B3','B4']:
        raise ValueError('BOOK_SOURCE_LEDGER_DROPPED')
    return True


def domain(v):
    return range(v['domain'][0],v['domain'][1]+1) if v['interval'] else v['domain']


def enabled(c, active=None, exclude_families=()):
    return c['family'] not in exclude_families and (active is None or c['id'] in active)


def verify(m,w,extra=(),active=None,exclude_families=()):
    values=w['values']
    if len(values)!=len(m['variables']) or any(type(x)!=int or x not in domain(v) for x,v in zip(values,m['variables'])):
        raise ValueError('INVALID_SCENARIO_VARIABLE_DOMAIN')
    for c in m['constraints']+list(extra):
        if not enabled(c,active,exclude_families):continue
        ok=[]
        for r in c['rows']:
            satisfied=(r['when'] is not None and values[r['when'][0]]!=r['when'][1]) or sum(values[i]*co for i,co in r['terms'])>=r['rhs']
            ok.append(satisfied)
        if not (any(ok) if c['any_of'] else all(ok)):
            raise ValueError('JOINT_CONSTRAINT_VIOLATED: '+c['id'])
    if active is None and not exclude_families:
        index={v['id']:i for i,v in enumerate(m['r13']['volumes'])}
        vw={q:[values[m['boxes'][eid][k]] for eid in index] for k,q in enumerate(AXES)}
        r13.verify(m['r13'],vw)
    return True


def cp_solve(m,extra=(),active=None,exclude_families=(),objective=None):
    from ortools.sat.python import cp_model
    validate(m)
    solver_model=cp_model.CpModel()
    variables=[solver_model.new_int_var_from_domain(cp_model.Domain.from_values(list(domain(v))),v['name']) for v in m['variables']]
    guards={}
    for c in m['constraints']+list(extra):
        if not enabled(c,active,exclude_families):continue
        guard=solver_model.new_bool_var(c['id']); guards[guard.index]=c
        solver_model.add_assumption(guard)
        options=[]
        for n,r in enumerate(c['rows']):
            conditions=[guard]
            if c['any_of']:
                opt=solver_model.new_bool_var(c['id']+'-'+str(n));options.append(opt);conditions.append(opt)
            if r['when'] is not None:
                vi,val=r['when'];cond=solver_model.new_bool_var(c['id']+'-when-'+str(n))
                solver_model.add(variables[vi]==val).only_enforce_if(cond)
                solver_model.add(variables[vi]!=val).only_enforce_if(cond.Not());conditions.append(cond)
            expr=sum(variables[i]*co for i,co in r['terms'])
            solver_model.add(expr>=r['rhs']).only_enforce_if(conditions)
        if c['any_of']:solver_model.add_bool_or(options).only_enforce_if(guard)
    if objective:
        vi,mode=objective
        (solver_model.minimize if mode=='min' else solver_model.maximize)(variables[vi])
    s=cp_model.CpSolver();s.parameters.num_search_workers=1;s.parameters.random_seed=0;s.parameters.max_time_in_seconds=20
    state=s.solve(solver_model);sat=state in (cp_model.OPTIMAL,cp_model.FEASIBLE)
    w={'values':[s.value(x) for x in variables]} if sat else None
    if sat:verify(m,w,extra,active,exclude_families)
    return {'status':'SAT' if sat else s.status_name(state),'solver_status':s.status_name(state),
        'witness':w,'objective':s.value(variables[objective[0]]) if sat and objective else None,
        'unsat_core':[guards[i] for i in s.sufficient_assumptions_for_infeasibility()] if state==cp_model.INFEASIBLE else [],
        'core_minimality_claimed':False}


def mzn_data(m,extra=(),active=None,exclude_families=()):
    cs=m['constraints']+list(extra); rows=[];terms=[]
    for gi,c in enumerate(cs,1):
        for r in c['rows']:
            rows.append((gi,r))
            terms.extend((len(rows),i+1,co) for i,co in r['terms'])
    arr=lambda v:'['+','.join(map(str,v))+']'
    sets='['+','.join(('{'+','.join(map(str,domain(v)))+'}') if not v['interval'] else str(v['domain'][0])+'..'+str(v['domain'][1]) for v in m['variables'])+']'
    return '\n'.join([f'nv={len(m["variables"])};',f'ng={len(cs)};',f'nr={len(rows)};',f'nt={len(terms)};',
        'domains='+sets+';',
        'active='+arr(str(enabled(c,active,exclude_families)).lower() for c in cs)+';',
        'disjunction='+arr(str(c['any_of']).lower() for c in cs)+';',
        'group='+arr(g for g,r in rows)+';', 'rhs='+arr(r['rhs'] for g,r in rows)+';',
        'condition_var='+arr(r['when'][0]+1 if r['when'] is not None else 0 for g,r in rows)+';',
        'condition_value='+arr(r['when'][1] if r['when'] is not None else 0 for g,r in rows)+';',
        'term_var='+arr(v for r,v,c in terms)+';', 'term_coefficient='+arr(c for r,v,c in terms)+';',
        'term_row='+arr(r for r,v,c in terms)+';'])+'\n'


def mzn_solve(m,executable,outdir,label,extra=(),fixed=None,active=None):
    validate(m)
    data=mzn_data(m,extra,active)
    if fixed:data+='constraint value = '+json.dumps(fixed['values'])+';\n'
    path=outdir/(label+'.mzn');path.write_text(data,encoding='utf-8')
    run=subprocess.run([str(executable),'--solver','cp-sat','--time-limit','20000','--output-mode','item',
                        str(HERE/'integrated_spatial_r15.mzn'),str(path)],capture_output=True,text=True,encoding='utf-8',timeout=50)
    (outdir/(label+'.stdout.txt')).write_text(run.stdout,encoding='utf-8')
    (outdir/(label+'.stderr.txt')).write_text(run.stderr,encoding='utf-8')
    if run.returncode:raise RuntimeError('R15_MINIZINC_ERROR: '+run.stderr)
    witnesses=[json.loads(line) for line in run.stdout.splitlines() if line.startswith('{')]
    for w in witnesses:verify(m,w,extra,active)
    return {'status':'SAT' if witnesses else 'INFEASIBLE' if '=====UNSATISFIABLE=====' in run.stdout else 'UNKNOWN',
            'witnesses':witnesses,'input_file':path.name}


def probe(cid,rows):
    return {'id':cid,'rows':rows,'sources':[],'status':'synthetic_not_book_fact','any_of':False,'family':'test'}


def experiment(outdir,executable):
    outdir.mkdir(parents=True,exist_ok=True);m=build();r11.write(outdir/'joint-model.json',m)
    cp=cp_solve(m);mz=mzn_solve(m,executable,outdir,'joint-sat')
    if cp['status']!=mz['status'] or cp['status']!='SAT':raise RuntimeError('R15_JOINT_SAT_NOT_PROVEN')
    replay=mzn_solve(m,executable,outdir,'python-witness',fixed=cp['witness'])
    if replay['status']!='SAT':raise RuntimeError('R15_WITNESS_REPLAY_FAILED')
    ps={p['id']:p for p in m['points']}; order=m['order_variables']
    c=next(c for c in m['constraints'] if c['id']=='R14-Z-RT-007-1')
    inverse=probe('R15-TEST-REVERSE-SECOND-STAIR',[row([(i,-co) for i,co in c['rows'][0]['terms']],1)])
    shortcut=probe('R15-TEST-DROP-RT006-STAGES',[row([(order['RT006-A'],1),(order['RT006-G'],-1)],-1)])
    px=ps['RT006-A']['variables'][0]; bx=m['boxes']['MOAG-G-0008'][0]
    detach=probe('R15-TEST-DETACH-DARK-VISIT',[row([(px,1),(bx,-1)],10)])
    conflicts=[]
    for test,label in ((inverse,'stair-unsat'),(shortcut,'lost-stages-unsat'),(detach,'detached-endpoint-unsat')):
        bad=cp_solve(m,[test]);mb=mzn_solve(m,executable,outdir,label,[test])
        core_ids={c['id'] for c in bad['unsat_core']}
        if bad['status']!=mb['status'] or bad['status']!='INFEASIBLE' or test['id'] not in core_ids:
            raise RuntimeError('R15_INJECTED_CONFLICT_NOT_EXPLAINED: '+test['id'])
        corecp=cp_solve(m,[test],active=core_ids)
        coremz=mzn_solve(m,executable,outdir,label+'-core',[test],active=core_ids)
        if corecp['status']!=coremz['status'] or corecp['status']!='INFEASIBLE':raise RuntimeError('R15_CORE_REPLAY_FAILED')
        conflicts.append({'test':test,'cp_sat':bad['status'],'minizinc':mb['status'],
            'unsat_core':bad['unsat_core'],'core_replay_cp_sat':corecp['status'],'core_replay_minizinc':coremz['status']})
    # Optimize the same variable before/after adding evidence families.
    # Bounds are exact only after an OPTIMAL response, never from one witness.
    reductions=[]
    for pid,axis,families in [('RT006-A',0,('binding',)),('RT006-A',0,('image',)),('RT007-A',2,('binding',))]:
        vi=ps[pid]['variables'][axis];record={'point':pid,'axis':AXES[axis],'ablated_families':list(families)}
        for key,excluded in [('before',families),('after',())]:
            runs=[cp_solve(m,exclude_families=excluded,objective=(vi,mode)) for mode in ('min','max')]
            if any(r['solver_status']!='OPTIMAL' for r in runs):raise RuntimeError('UNCERTAINTY_BOUNDS_NOT_PROVEN')
            record[key]=[r['objective'] for r in runs]
        record['strictly_reduced']=record['after']!=record['before'];reductions.append(record)
    # Alternative placement of a genuinely unlocated intermediate observation.
    var=ps['RT006-C']['variables'][0]
    alternatives=[]
    for label,bound in [('left',row([(var,-1)],-20)),('right',row([(var,1)],60))]:
        test=probe('R15-ALTERNATIVE-'+label,[bound]);r=cp_solve(m,[test])
        if r['status']!='SAT':raise RuntimeError('ALTERNATIVE_DOMAIN_LOST')
        mm=mzn_solve(m,executable,outdir,'alternative-'+label,[test],fixed=r['witness'])
        if mm['status']!='SAT':raise RuntimeError('ALTERNATIVE_REPLAY_FAILED')
        alternatives.append({'id':label,'status':'hypothesis_witness_not_selected','cp_sat':r,'minizinc':mm})
    if r11.digest(r11.inputs()[-1])!=m['R09_fingerprint']:raise RuntimeError('R09_MUTATED')
    summary={'schema':'MOAG-R15-ACTUAL-JOINT-EXPERIMENT/1','status':'LIMITED_JOINT_INTEGRATION_SAT_UNSAT_PASS',
        'scenario_volumes':len(m['r13']['volumes']),'indexed_entities_preserved':len(m['entities']),
        'registered_routes':52,'registered_stages':378,'registered_height_relations':32,
        'r12_envelopes_preserved':9,'geometrically_bound_route_occurrences':sum('host_volume' in ps[s['id']] for s in m['r14']['steps']),
        'unbound_route_occurrences':len(m['unbound_route_steps']),
        'joint_python':cp,'joint_minizinc':mz,'cross_backend_replay':replay['status'],
        'synthetic_conflicts':conflicts,'uncertainty_reductions':reductions,'alternative_witnesses':alternatives,
        'global_blocks':3,'R09_unchanged':True,'geometry_approved':False,'archicad_write':False,
        'scope_limit':'BOUNDED_SCENARIO_AND_DOMAIN_INTEGRATION_NOT_COMPLETE_STATION_GEOMETRY'}
    r11.write(outdir/'results.json',summary)
    r11.write(outdir/'missing_evidence.json',{'unbound_steps':m['unbound_route_steps'],
        'unverified_route_pages':m['r14']['unverified_page_cross_references'],
        'candidate_matches_not_promoted':m['r14']['candidate_only_step_index_matches'],
        'historical_base_numbers':m['historical_bases'],
        'not_solved':['metric hull geometry','individual hangar location within author sector','full radial corridor geometry',
                      'actual path lengths and door openings','new observed routes for books B3/B4']})
    print(json.dumps({k:summary[k] for k in ('status','scenario_volumes','registered_routes','registered_stages',
        'geometrically_bound_route_occurrences','unbound_route_occurrences')},ensure_ascii=False))
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    portable=next((r11.ROOT/'.runtime/minizinc').glob('*/bin/minizinc.exe'),None)
    portable=portable or next((r11.ROOT/'.runtime/minizinc').glob('*/bin/minizinc'),None)
    p.add_argument('--minizinc',type=Path,default=shutil.which('minizinc') or portable)
    args=p.parse_args()
    if not args.minizinc:p.error('Official MiniZinc CP-SAT required')
    experiment(args.out,args.minizinc)


if __name__=='__main__': main()
