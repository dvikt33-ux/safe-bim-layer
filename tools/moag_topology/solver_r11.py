#!/usr/bin/env python3
"""Read R09 unchanged; solve a source-qualified ordinal sidecar with ready solvers."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess

import reconcile_uncertainty_r09 as r09

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/research/apa-results/moag'
SYNTH = BASE / 'synthesis'
HERE = Path(__file__).parent
INPUT = SYNTH / 'r11/source_review.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                   allow_nan=False) + '\n', encoding='utf-8')


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def inputs():
    g = read(SYNTH / 'full_indexed_parametric_graph_r04.json')
    f = read(SYNTH / 'progressive_fragments_r05.json')
    b = read(SYNTH / 'area_volume_bounds_r05.json')
    routes = read(BASE / 'v2/character_routes.json')
    return g, f, b, routes, r09.build(g, f, b, routes)


def build(scope=1):
    g, f, bounds, routes, graph = inputs()
    review = read(INPUT)
    observations = {x['id']: x for x in read(BASE / 'v2/page_observations.json')['observations']}
    sources = {x['id']: x for x in read(BASE / 'v1/evidence_graph.json')['sources']}
    inventory = {x['id']: x for x in g['indexed_source_entities'] + g['indexed_r03_entities'] + f['physical_entities']}
    profiles = {x['id']: x for x in bounds['profiles']}
    graph_edges = {x['id']: x for x in graph['edges']}
    source_records = {x['id'] for x in g['source_relationships'] + g['derived_r03_relationships']}
    physical = [x for x in graph['nodes'] if x['layer'] == 'PHYSICAL_INDEX'
                and x['moag_station_identity_verified']
                and x['possible_global_levels'] == [scope]]
    # Sub-lower well stays globally unresolved; its local relation is still usable.
    if scope == 1:
        physical += [x for x in graph['nodes'] if x['id'] == g['legacy_id_to_stable_id']['SUB-LOWER-WELL']]
    node_ids = {x['id'] for x in physical}
    constraints = []
    deferred = []

    def provenance(ids):
        out = []
        for sid in ids:
            if sid in observations:
                o = observations[sid]
                out.append({'id': sid, 'page_id': o['page_id'], 'url': o['citation_url'],
                            'paraphrase': o['spatial_assertion']})
            elif sid in sources:
                s = sources[sid]
                out.append({'id': sid, 'section': s['section'], 'url': s['url']})
            else:
                raise ValueError('UNRESOLVED_SOURCE: ' + sid)
        if not out:
            raise ValueError('UNSOURCED_CONSTRAINT')
        return out

    def add(eid, high, low, ids, kind=1, status='fact', note=None):
        if high not in node_ids or low not in node_ids:
            return
        if eid not in graph_edges and eid not in source_records and not eid.startswith(('MOAG-Z-', 'PLAN-')):
            raise ValueError('NOT_IN_R09: ' + eid)
        constraints.append({'id': eid, 'a': high, 'b': low, 'kind': kind,
                            'status': status, 'sources': provenance(ids) if kind == 1 else ids,
                            'interpretation': note, 'hard_in_this_projection': True,
                            'present_as_edge_in_R09': eid in graph_edges,
                            'source_register': 'R04 source-qualified relation / vertical_connections / supplied plan'})

    for e in g['source_relationships']:
        if e['evidence_state'] != 'TEXT_DIRECT' or e['binding_status'] in {'RECHECK_REQUIRED', 'QUARANTINED_DO_NOT_USE_AS_DIRECT_GEOMETRY'}:
            continue
        if e['relation'] in {'above', 'above_floor'}:
            add(e['id'], e['from'], e['to'], e['source_ids'], note=e['claim'])
        # A level label is not an elevation reference plane. E57 is retained in
        # the evidence graph; Z01 gives a narrower usable side-exit reference.
    vertical = read(SYNTH / 'vertical_connections.json')
    for e in vertical['relative_height_constraints']:
        a, b = (g['legacy_id_to_stable_id'][e[k]] for k in ('higher', 'lower'))
        if e['state'] == 'TEXT_DIRECT' and e['relation'] in {'above', 'above_floor'}:
            add('MOAG-Z-' + e['id'], a, b, e['source_ids'], note=e['proof'])
        elif a in node_ids or b in node_ids:
            deferred.append({'source_record': e, 'reason': 'NOT_A_STRICT_SOURCE_PROVEN_FLOOR_ORDER'})
    for e in g['derived_r03_relationships']:
        if e['evidence_state'] != 'DIRECT_TEXT':
            continue
        if e['relation'] in {'HAS_INTERNAL_UPPER_ROOM', 'HAS_UPPER_GALLERY'}:
            add(e['id'], e['to'], e['from'], e['source_observation_ids'], note=e['relation'])
        elif e['relation'] == 'ELEVATED_WITHIN':
            add(e['id'], e['from'], e['to'], e['source_observation_ids'], note=e['relation'])
    for e in read(SYNTH / 'qualitative_placement_constraints_r06.json')['constraints']:
        if e['kind'] == 'RELATIVE_LOCAL_VERTICAL_ORDER':
            # This existing R06 register is an additional source-qualified input.
            if e['subject'] in node_ids and e['reference'] in node_ids:
                constraints.append({'id': e['id'], 'a': e['subject'], 'b': e['reference'],
                    'kind': 1, 'status': 'fact', 'sources': provenance(e['source_ids']),
                    'interpretation': e['interpretation'], 'hard_in_this_projection': True})
    if scope == 1:
        for p in review['plan_constraints']:
            asset = review['assets'][0]
            add(p['id'], p['a'], p['b'], [{'id': asset['id'], 'file': asset['file'],
                'sha256': asset['sha256'], 'reading': p['reading']}], p['kind'])
    for asset in review['assets']:
        if hashlib.sha256((ROOT / asset['file']).read_bytes()).hexdigest() != asset['sha256']:
            raise ValueError('VISUAL_SOURCE_BYTES_CHANGED')
    entities = []
    for n in sorted(physical, key=lambda x: x['id']):
        orig = inventory[n['id']]
        entities.append({'id': n['id'], 'name': orig['name'], 'kind': n['kind'],
            'source_refs': provenance(n['source_ids']),
            'global_level_domain': n['possible_global_levels'],
            'global_level_status': 'unknown' if len(n['possible_global_levels']) > 1 else 'fact_or_inherited_R09',
            'local_height_domain': [0, len(physical)], 'height_units': 'ORDINAL_WITNESS_ONLY',
            'height_reference': 'KNOWN_SIDE_EXIT_NOT_ALL_BASE_FLOORS' if n['id'] == 'MOAG-G-0006' else 'LOCAL_FLOOR_OR_ACCESS_REFERENCE',
            'metric_z_m': None, 'metric_xy_m': None,
            'area_volume_profile_R05': profiles[n['id']],
            'metric_intervals_status': 'hypothesis' if profiles[n['id']]['bounds'] else 'unknown',
            'volume_interval_m3': None, 'status': 'fact_exists_not_placed'})
    relationships = [deepcopy(e) for e in graph['edges']
                     if e['from'] in node_ids or e['to'] in node_ids]
    return {'schema': 'MOAG-SOLVER-SIDECAR-R11/1', 'global_blocks': [1, 2, 3],
        'scope_global_block': scope, 'entities': entities, 'constraints': constraints,
        'retained_typed_relations_not_turned_into_geometry': relationships,
        'deferred_vertical_records': deferred, 'source_review': review,
        'R09_fingerprint': digest(graph), 'R09_quantities': graph['quantities'],
        'R09_mutated': False, 'hypothesis_edges_used_as_hard_constraints': 0,
        'all_local_ranks_are_nonmetric': True, 'full_floor_decks_inferred': False,
        'metric_area_constraints_enabled': False,
        'area_profile_reason': 'R05 bounds are project hypotheses; no silent promotion to book facts',
        'archicad_write': False, 'geometry_approved': False}


def verify(model, witness, constraints=None):
    ids = [x['id'] for x in model['entities']]
    if set(witness) != {'block', 'z', 'plan_x', 'plan_y'} or any(len(v) != len(ids) for v in witness.values()):
        raise ValueError('MALFORMED_WITNESS')
    for i, e in enumerate(model['entities']):
        if witness['block'][i] not in e['global_level_domain']:
            raise ValueError('GLOBAL_LEVEL_VIOLATION')
        for key in ('z', 'plan_x', 'plan_y'):
            if type(witness[key][i]) is not int or not 0 <= witness[key][i] <= len(ids):
                raise ValueError('RANK_DOMAIN_VIOLATION')
    ix = {s: i for i, s in enumerate(ids)}
    for c in constraints if constraints is not None else model['constraints']:
        key = {1: 'z', 2: 'plan_x', 3: 'plan_y'}[c['kind']]
        if witness[key][ix[c['a']]] <= witness[key][ix[c['b']]]:
            raise ValueError('RELATION_VIOLATION: ' + c['id'])
    return True


def cp_solve(model, constraints=None, count=3):
    from ortools.sat.python import cp_model
    cs = constraints if constraints is not None else model['constraints']
    m = cp_model.CpModel()
    es = model['entities']; n = len(es)
    ids = {e['id']: i for i, e in enumerate(es)}
    vs = {k: [m.new_int_var(0, n, f'{k}_{i}') for i in range(n)]
          for k in ('z', 'plan_x', 'plan_y')}
    vs['block'] = [m.new_int_var_from_domain(cp_model.Domain.from_values(e['global_level_domain']), f'block_{i}') for i, e in enumerate(es)]
    guards = {}
    for c in cs:
        g = m.new_bool_var(c['id'])
        key = {1: 'z', 2: 'plan_x', 3: 'plan_y'}[c['kind']]
        m.add(vs[key][ids[c['a']]] > vs[key][ids[c['b']]]).only_enforce_if(g)
        m.add_assumption(g); guards[g.index] = c
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    solver.parameters.max_time_in_seconds = 15
    witnesses = []
    status = None
    for _ in range(count):
        status = solver.solve(m)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            break
        w = {k: [solver.value(v) for v in values] for k, values in vs.items()}
        verify(model, w, cs); witnesses.append(w)
        # Exclude the local elevation assignment, so alternatives cannot differ
        # merely in unconstrained plan ranks or in translation of the plan.
        m.add_forbidden_assignments(vs['z'], [w['z']])
    core = []
    if status == cp_model.INFEASIBLE and not witnesses:
        core = [guards[i] for i in solver.sufficient_assumptions_for_infeasibility()]
    return {'status': 'SAT' if witnesses else solver.status_name(status),
            'solver_status_last': solver.status_name(status), 'witnesses': witnesses,
            'unsat_core': core, 'core_minimality_claimed': False,
            'all_solutions_enumerated': False}


def dzn(model, constraints):
    ids = {e['id']: i+1 for i, e in enumerate(model['entities'])}
    arr = lambda seq: '[' + ','.join(map(str, seq)) + ']'
    return '\n'.join([f'n={len(ids)};', f'c={len(constraints)};',
        'level_domain=[' + ','.join('{' + ','.join(map(str,e['global_level_domain'])) + '}' for e in model['entities']) + '];',
        'kind=' + arr(c['kind'] for c in constraints) + ';',
        'a=' + arr(ids[c['a']] for c in constraints) + ';',
        'b=' + arr(ids[c['b']] for c in constraints) + ';',
        'active=' + arr('true' for _ in constraints) + ';']) + '\n'


def mzn_solve(model, executable, outdir, label, constraints=None):
    cs = constraints if constraints is not None else model['constraints']
    data = outdir / (label + '.dzn'); data.write_text(dzn(model, cs), encoding='utf-8')
    command = [str(executable), '--solver', 'cp-sat', '--time-limit', '15000',
               '--output-mode', 'item', str(HERE / 'solver_r11.mzn'), str(data)]
    r = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
    (outdir / (label + '.stdout.txt')).write_text(r.stdout, encoding='utf-8')
    (outdir / (label + '.stderr.txt')).write_text(r.stderr, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(f'MINIZINC_EXIT_{r.returncode}: {r.stderr}')
    rows = [json.loads(line) for line in r.stdout.splitlines() if line.startswith('{')]
    for row in rows:
        verify(model, row, cs)
    status = 'SAT' if rows else 'INFEASIBLE' if '=====UNSATISFIABLE=====' in r.stdout else 'UNKNOWN'
    return {'status': status, 'witnesses': rows, 'solver_id': 'cp-sat',
            'stdout_file': label + '.stdout.txt', 'stderr_file': label + '.stderr.txt'}


def experiment(outdir, executable, scope=1):
    import ortools
    outdir.mkdir(parents=True, exist_ok=True)
    model = build(scope)
    before = model['R09_fingerprint']
    write(outdir / 'model.json', model)
    cp = cp_solve(model)
    mz = mzn_solve(model, executable, outdir, 'sat')
    base = next(c for c in model['constraints'] if c['kind'] == 1)
    inverse = {**deepcopy(base), 'id': 'TEST-REVERSED-' + base['id'],
               'a': base['b'], 'b': base['a'], 'status': 'synthetic_test_only',
               'interpretation': 'Deliberate reversal; never an additional book claim'}
    conflict_constraints = model['constraints'] + [inverse]
    conflict = cp_solve(model, conflict_constraints)
    mz_conflict = mzn_solve(model, executable, outdir, 'unsat', conflict_constraints)
    core = conflict['unsat_core']
    core_replay = cp_solve(model, core, count=1)
    mzn_core = mzn_solve(model, executable, outdir, 'unsat-core', core)
    # Independently validate each CP alternative through the actual MiniZinc
    # backend, fixing all variables in a separate .mzn data file.
    crosschecks = []
    for i, witness in enumerate(cp['witnesses']):
        data = dzn(model, model['constraints'])
        for k, values in witness.items():
            data += f'constraint {k} = {values};\n'
        path = outdir / f'alternative-{i+1}.mzn'; path.write_text(data, encoding='utf-8')
        r = subprocess.run([str(executable), '--solver', 'cp-sat', '--time-limit', '15000',
            str(HERE / 'solver_r11.mzn'), str(path)], capture_output=True, text=True, encoding='utf-8', timeout=30)
        valid = r.returncode == 0 and any(l.startswith('{') for l in r.stdout.splitlines())
        crosschecks.append(valid)
        (outdir / f'alternative-{i+1}.stdout.txt').write_text(r.stdout, encoding='utf-8')
        if not valid:
            raise RuntimeError('CROSS_BACKEND_WITNESS_REJECTED: ' + r.stderr)
    # Query the tempting but unsupported all-bases-above-all-hangars claim.
    nonentailment = None
    reversed_countermodel = None
    if scope == 1:
        probe = {'id': 'TEST-BASE-BELOW-HANGAR', 'a': 'M-L1-FH-001', 'b': 'MOAG-G-0008',
                 'kind': 1, 'status': 'countermodel_query_not_fact', 'sources': []}
        nonentailment = cp_solve(model, model['constraints'] + [probe], count=1)
        nonentailment['minizinc_replay'] = mzn_solve(model, executable, outdir,
            'base-below-hangar-countermodel', model['constraints'] + [probe])
        reverse_probe = {**probe, 'id': 'TEST-BASE-ABOVE-HANGAR', 'a': probe['b'], 'b': probe['a']}
        reversed_countermodel = cp_solve(model, model['constraints'] + [reverse_probe], count=1)
        reversed_countermodel['minizinc_replay'] = mzn_solve(model, executable, outdir,
            'base-above-hangar-countermodel', model['constraints'] + [reverse_probe])
        if not all(x['status'] == x['minizinc_replay']['status'] == 'SAT'
                   for x in (nonentailment, reversed_countermodel)):
            raise RuntimeError('UNSUPPORTED_BASE_HANGAR_ORDER_BECAME_MANDATORY')
    assert digest(inputs()[-1]) == before
    ready = (cp['status'] == mz['status'] == 'SAT' and len(cp['witnesses']) >= 3
             and conflict['status'] == mz_conflict['status'] == core_replay['status'] == mzn_core['status'] == 'INFEASIBLE'
             and bool(core) and all(crosschecks))
    if not ready:
        raise RuntimeError('EXPERIMENT_ACCEPTANCE_FAILED')
    report = {'schema': 'MOAG-REAL-SOLVER-EXPERIMENT-R11/1',
        'status': 'COMPUTATIONAL_PROTOTYPE_PASS_SOURCE_GAPS_REMAIN',
        'scope_global_block': scope, 'python': platform.python_version(), 'platform': platform.platform(),
        'ortools_python_version': ortools.__version__,
        'minizinc_version': subprocess.check_output([str(executable), '--version'], text=True).strip(),
        'minizinc_backend': [{k: x.get(k) for k in ('id','name','version')} for x in
            json.loads(subprocess.check_output([str(executable), '--solvers-json'], text=True)) if x['id'] == 'cp-sat'],
        'entities': len(model['entities']), 'strict_constraints': len(model['constraints']),
        'cp_sat': cp, 'minizinc_cp_sat': mz, 'cp_sat_injected_unsat': conflict,
        'minizinc_injected_unsat': mz_conflict, 'cp_sat_core_replay': core_replay,
        'minizinc_core_replay': mzn_core, 'alternatives_crosschecked': crosschecks,
        'all_bases_above_all_hangars_not_entailed': nonentailment,
        'opposite_base_hangar_order_also_possible': reversed_countermodel,
        'canonical_R09_unchanged': True, 'source_review_complete': False,
        'unknowns': model['source_review']['unresolved'],
        'geometry_approved': False, 'archicad_write': False}
    write(outdir / 'results.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'entities', 'strict_constraints', 'minizinc_backend')}, ensure_ascii=False))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    portable = next((ROOT / '.runtime/minizinc').glob('*/bin/minizinc.exe'), None)
    portable = portable or next((ROOT / '.runtime/minizinc').glob('*/bin/minizinc'), None)
    p.add_argument('--minizinc', type=Path, default=shutil.which('minizinc') or portable)
    p.add_argument('--scope', type=int, choices=(1,2,3), default=1)
    args = p.parse_args()
    if not args.minizinc:
        p.error('MiniZinc CLI required; install official bundle or pass --minizinc')
    experiment(args.out, args.minizinc, args.scope)


if __name__ == '__main__':
    main()
