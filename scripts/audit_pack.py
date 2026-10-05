"""Deterministic, offline derivatives of pinned model dumps. No runtime imports."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
import tempfile

SCHEMA_VERSION = 1
EXTRACTOR_VERSION = '2'
TOLERANCE = 1e-7


class AuditError(ValueError):
    status = 'FAIL'


class Conflict(AuditError):
    status = 'CONFLICT'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


# Scan parsed JSON strings, so escaped separators cannot conceal local paths.
LOCAL_PATH = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|\\\\|(?:^|[\s\"'=:(])/(?!/)[^\s]*|"
    r"(?:^|[\s\"'=(])//[^\s]+|(?:^|[\s/\\])(?:Users|home)[/\\][^/\\\s]+|"
    r"(?:^|[\s\"'=:(])\\[^\s]+|~[/\\]|%(?:USERPROFILE|HOMEPATH)%|\$HOME(?:[/\\]|$)", re.IGNORECASE)


def unsafe_path(value):
    return isinstance(value, str) and LOCAL_PATH.search(value) is not None


def public_value(value):
    """Opaque logical ID; original source bytes/hashes remain the provenance anchor."""
    if isinstance(value, str) and unsafe_path(value):
        return 'local-path-sha256:' + hashlib.sha256(value.encode('utf-8')).hexdigest()
    if isinstance(value, dict):
        return {k: public_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [public_value(v) for v in value]
    return value


def assert_public(value):
    if isinstance(value, str) and unsafe_path(value):
        raise AuditError('Absolute/local user path in published pack')
    if isinstance(value, dict):
        for k, v in value.items():
            assert_public(k)
            assert_public(v)
    elif isinstance(value, list):
        for v in value:
            assert_public(v)


def scan_public_pack(output):
    if not Path(output).is_dir():
        raise AuditError('Published pack directory missing')
    files = 0
    for p in Path(output).rglob('*'):
        if p.is_file():
            assert_public(p.relative_to(output).as_posix())
            assert_public(read_json(p) if p.suffix == '.json' else p.read_text(encoding='utf-8'))
            files += 1
    if not files:
        raise AuditError('Published pack is empty')
    return {'status': 'PASS', 'files': files}


def semantic_delta(change, differences):
    """Only the direct per-body index field is technical noise; all else is semantic."""
    noise = sorted(e['guid'] for e in differences if e['changedPaths'] and all(
        re.fullmatch(r'bodies\[\d+\]\.nativeBodyIndex', p) for p in e['changedPaths']))
    change['rawChanged'] = list(change['changed'])
    change['semanticChanged'] = sorted(set(change['rawChanged']) - set(noise))
    change['technicalNoiseChanged'] = noise
    change['semanticUnchangedCount'] = change['unchangedCount'] + len(noise)
    return change


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(AuditError('Nonfinite JSON: '+value)))


def relative(root, name):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts or not name or '\\' in name:
        raise AuditError('Expected repository-relative POSIX path: '+str(name))
    resolved = (Path(root)/p).resolve()
    if not resolved.is_relative_to(Path(root).resolve()):
        raise AuditError('Path outside root: '+name)
    return resolved


def file_info(root, name):
    p = relative(root, name)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b''):
            h.update(chunk)
    return {'path': name, 'sha256': h.hexdigest(), 'bytes': p.stat().st_size}


def pinned_json(root, spec):
    actual = file_info(root, spec['path'])
    if actual != {k: spec[k] for k in ('path', 'sha256', 'bytes')}:
        raise AuditError('Source SHA/size mismatch: '+spec['path'])
    data = read_json(relative(root, spec['path']))
    # Ensure the parsed source still matches the pinned bytes, including concurrent edits.
    if file_info(root, spec['path']) != actual:
        raise AuditError('Source changed during read: '+spec['path'])
    return data


def guid_map(elements):
    result = {}
    for e in elements:
        g = e.get('guid')
        if not isinstance(g, str) or not g.strip() or g.upper() in result:
            raise AuditError('Missing or duplicate element GUID')
        result[g.upper()] = e
    return result


def element_index(data):
    rows = []
    for g, e in sorted(guid_map(data['elements']).items()):
        row = {'guid': g, 'fullElementHash': digest(e)}
        for key in ('type', 'homeStory', 'bbox'):
            if key in e:
                row[key] = e[key]
        for key, output in [('placement', 'placementHash'), ('bodies', 'geometryHash'),
                            ('properties', 'propertiesHash')]:
            if key in e:
                row[output] = digest(e[key])
        rows.append(row)
    return rows


def model_hash(data):
    # Same canonical fingerprint contract as Stage 3; nativeSeconds is timing only.
    value = {k: v for k, v in data.items()
             if k not in ('elements', 'materials', 'unresolvedBodyOwners', 'nativeSeconds')}
    for key in ('elements', 'materials', 'unresolvedBodyOwners'):
        value[key] = sorted(digest(item) for item in data.get(key, []))
    return digest(value)


def model_summary(data, identity):
    rows = element_index(data)
    result = {'modelIdentity': identity, 'modelHash': model_hash(data),
              'elementCount': len(rows),
              'typeCounts': dict(sorted(Counter(str(e.get('type')) for e in data['elements']).items()))}
    if 'materials' in data:
        result['materialsCount'] = len(data['materials'])
    if 'stories' in data:
        result['stories'] = data['stories']
    if 'unresolvedBodyOwners' in data:
        result['unresolvedBodyOwners'] = len(data['unresolvedBodyOwners'])
    if 'counts' in data:
        result['reportedCounts'] = data['counts']
        if data['counts'].get('elements', len(rows)) != len(rows):
            raise Conflict('Dump reported element count differs from element array')
    return result, rows


def delta(before, after):
    bm = {e['guid']: e['fullElementHash'] for e in before}
    am = {e['guid']: e['fullElementHash'] for e in after}
    changed = sorted(g for g in bm.keys() & am.keys() if bm[g] != am[g])
    return {'beforeCount': len(bm), 'afterCount': len(am),
            'added': sorted(am.keys()-bm.keys()), 'removed': sorted(bm.keys()-am.keys()),
            'changed': changed, 'unchangedCount': len(bm.keys() & am.keys())-len(changed)}


def changed_paths(before, after, path=''):
    """Describe raw field differences without weakening canonical changed detection."""
    if type(before) is not type(after):
        return [path]
    if isinstance(before, dict):
        paths = []
        for key in sorted(before.keys() | after.keys()):
            child = path+'.'+key if path else key
            if key not in before or key not in after:
                paths.append(child)
            else:
                paths.extend(changed_paths(before[key], after[key], child))
        return paths
    if isinstance(before, list):
        if len(before) != len(after):
            return [path]
        return [p for n, (a, b) in enumerate(zip(before, after))
                for p in changed_paths(a, b, f'{path}[{n}]')]
    return [] if before == after else [path]


def wall_geometry(source, created):
    if source.get('type') != 'Wall' or created.get('type') != 'Wall':
        raise AuditError('Wall geometry requires factual Wall elements')
    sr = source['placement']['referenceGeometry']
    cr = created['placement']['referenceGeometry']
    if sr.get('arcAngle', 0) != 0 or cr.get('arcAngle', 0) != 0:
        raise AuditError('Schema 1 Wall check supports straight reference lines only')
    def point(p):
        v = [p[a] for a in ('x', 'y')]
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in v):
            raise AuditError('Invalid Wall coordinate')
        return v
    sb, se, cb, ce = map(point, (sr['begin'], sr['end'], cr['begin'], cr['end']))
    sv, cv = [b-a for a, b in zip(sb, se)], [b-a for a, b in zip(cb, ce)]
    sl, cl = math.hypot(*sv), math.hypot(*cv)
    if not sl or not cl:
        raise AuditError('Degenerate Wall reference line')
    cosine = sum(a*b for a, b in zip(sv, cv))/(sl*cl)
    return {'computedFromDump': True, 'geometryBasis': 'placement.referenceGeometry (2D straight Wall)',
            'sourceGuid': source['guid'], 'createdGuid': created['guid'],
            'sourceBegin': sr['begin'], 'sourceEnd': sr['end'],
            'createdBegin': cr['begin'], 'createdEnd': cr['end'], 'length': cl,
            'jointDistance': math.dist(se, cb), 'directionCosine': cosine,
            'sameDirection': cosine >= 1-1e-6,
            'sourceHomeStory': source.get('homeStory'), 'homeStory': created.get('homeStory'),
            'sourceFields': {k: sr[k] for k in ('height', 'thickness', 'bottomOffsetFromHomeStory') if k in sr},
            'createdFields': {k: cr[k] for k in ('height', 'thickness', 'bottomOffsetFromHomeStory') if k in cr},
            'sourceMaterialBindings': source.get('materialBindings'),
            'createdMaterialBindings': created.get('materialBindings')}


def compare_compact(summary, geometry, change, source, created):
    facts = {'sourceGuid': source['guid'], 'createdGuid': created['guid'],
             'length': geometry['length'], 'jointDistance': geometry['jointDistance'],
             'homeStory': geometry['homeStory'], 'begin': geometry['createdBegin'],
             'end': geometry['createdEnd'], 'sourceBegin': geometry['sourceBegin'],
             'sourceEnd': geometry['sourceEnd'], 'elementCountBefore': change['beforeCount'],
             'elementCountAfter': change['afterCount']}
    checked = []
    for key, actual in facts.items():
        if key not in summary:
            continue
        expected = summary[key]
        if isinstance(actual, float):
            equal = isinstance(expected, (int, float)) and abs(actual-expected) <= TOLERANCE
        else:
            equal = actual == expected
        if not equal:
            raise Conflict('Compact/full mismatch: '+key)
        checked.append(key)
    for key, e in [('sourceBefore', source), ('sourceAfter', source), ('created', created)]:
        if key in summary and summary[key] != e:
            raise Conflict('Compact/full extracted object mismatch: '+key)
    return checked


def historical_contract(root, stage):
    """Pin existing historical manifests/records; never infer GUIDs from filenames."""
    base = 'outputs/closed-loop-stage3/run-002' if stage == 3 else 'outputs/closed-loop-stage1'
    mp = base+'/manifest.json' if stage == 3 else base+'/evidence-manifest.json'
    manifest = read_json(relative(root, mp))
    entries = {e['path']: {'path': e['path'], 'sha256': e['sha256'], 'bytes': e['bytes']}
               for e in manifest['files']}
    def record(path):
        if path not in entries:
            raise AuditError('Not in historical manifest: '+path)
        return entries[path]
    identity_path = base+'/live-job/identity/001-GetProjectInfo.response.json' if stage == 3 else base+'/GetProjectInfo.response.json'
    identity = pinned_json(root, record(identity_path))['result']['addOnCommandResponse']['projectPath']
    prefix = base+'/live-job' if stage == 3 else base
    initial = prefix+'/observations/001-observe.json' if stage == 3 else prefix+'/initial-model-dump.json'
    snapshots = [{'id': 'initial', **record(initial)}]
    iterations = []
    for n in (1, 2):
        ip = prefix+f'/iteration-{n}'
        s = pinned_json(root, record(ip+'/summary.json'))
        snapshots.extend([{'id': f'iteration-{n}-before', **record(ip+'/executor/before.json')},
                          {'id': f'iteration-{n}-after', **record(ip+'/executor/after-create.json')}])
        refs = [record(ip+'/summary.json')]
        if stage == 3:
            request = pinned_json(root, record(ip+'/executor-request.json'))
            result = pinned_json(root, record(ip+'/executor-result.json'))
            if request['request']['sourceGuid'] != s['sourceGuid'] or result['createdGuid'] != s['createdGuid']:
                raise Conflict('Action/result GUID differs from summary')
            refs.extend(record(ip+'/'+f) for f in ('executor-request.json', 'executor-result.json', 'readback-witness.json'))
            observation_numbers = (2, 3) if n == 1 else (4, 5, 6)
            for num in observation_numbers:
                role = {2:'stale-check',3:'read-back',4:'observe',5:'stale-check',6:'read-back'}[num]
                p = prefix+f'/observations/{num:03d}-{role}.json'
                snapshots.append({'id': f'observation-{num:03d}', **record(p),
                                  'fingerprint': record(p.replace('.json', '.fingerprint.json'))})
            expected = request['request']['length']
        else:
            refs = [record(ip+'/summary.json')]
            expected = s['typedRequest']['length']
        iterations.append({'iteration': n, 'before': f'iteration-{n}-before',
                           'after': f'iteration-{n}-after', 'sourceGuid': s['sourceGuid'],
                           'createdGuid': s['createdGuid'], 'expectedLength': expected,
                           'expectedAddedCount': 1, 'compactEvidence': refs})
    if stage == 3:
        snapshots[0]['fingerprint'] = record(initial.replace('.json', '.fingerprint.json'))
    return {'schemaVersion': 1, 'goalId': s.get('goalId', 'stage1-v0-regression'),
            'modelIdentity': identity, 'identityEvidence': record(identity_path),
            'historicalManifest': file_info(root, mp), 'initial': 'initial',
            'snapshots': snapshots, 'iterations': iterations, 'requireDependency': True,
            'historicalStage': stage}


def build_pack(root, contract, output):
    if contract.get('schemaVersion') != 1 or not contract.get('goalId') or not contract.get('iterations'):
        raise AuditError('Invalid schema 1 contract')
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise AuditError('Output must be new or empty')
    specs = contract['snapshots']
    if len({s['id'] for s in specs}) != len(specs):
        raise AuditError('Duplicate snapshot id')
    for s in specs:
        relative(output, s['id'])
        if output.resolve() == relative(root, s['path']) or output.resolve() in relative(root, s['path']).parents:
            raise AuditError('Output overlaps source')
    records = []
    if 'historicalManifest' in contract:
        historic = pinned_json(root, contract['historicalManifest'])
        trusted = {e['path']: e for e in historic['files']}
        for spec in specs:
            if any(spec[k] != trusted[spec['path']][k] for k in ('sha256', 'bytes')):
                raise AuditError('Contract differs from historical manifest')
        records.append(contract['historicalManifest'])
    if 'identityEvidence' in contract:
        identity = pinned_json(root, contract['identityEvidence'])['result']['addOnCommandResponse']['projectPath']
        if public_value(identity) != public_value(contract['modelIdentity']):
            raise Conflict('Identity record mismatch')
        records.append(contract['identityEvidence'])
    wanted = {i[k].upper() for i in contract['iterations'] for k in ('sourceGuid', 'createdGuid')}
    states = {}
    payloads = {}
    origins = {}
    def put(name, value, refs):
        payloads[name] = value
        origins[name] = sorted(set(refs))
    indexes = {}
    for spec in specs:
        data = pinned_json(root, spec)
        summary, index = model_summary(data, contract.get('modelIdentity'))
        key = digest(index)
        folder = 'initial' if spec['id'] == contract['initial'] else spec['id']
        if key not in indexes:
            indexes[key] = folder+'/element-index.json'
            put(indexes[key], index, [spec['path']])
        else:
            origins[indexes[key]] = sorted(set(origins[indexes[key]]+[spec['path']]))
        summary['elementIndex'] = indexes[key]
        put(folder+'/model-summary.json', summary, [spec['path']])
        selected = {g: e for g, e in guid_map(data['elements']).items() if g in wanted}
        states[spec['id']] = {'summary': summary, 'index': index, 'selected': selected, 'spec': spec}
        if spec.get('fingerprint'):
            fp = pinned_json(root, spec['fingerprint'])
            if any((public_value(fp[k]) != public_value(summary[k]) if k == 'modelIdentity'
                    else fp[k] != summary[k]) for k in ('modelIdentity', 'modelHash', 'elementCount')):
                raise Conflict('Full dump/fingerprint mismatch: '+spec['path'])
            records.append(spec['fingerprint'])
        del data
    chain = [states[contract['initial']]]
    compact_checks = []
    previous_created = None
    dependencies = []
    for number, step in enumerate(contract['iterations'], 1):
        if step['iteration'] != number:
            raise AuditError('Iterations must be consecutive starting at 1')
        expected_length = step['expectedLength']
        if isinstance(expected_length, bool) or not isinstance(expected_length, (int, float)) or not math.isfinite(expected_length) or expected_length <= 0:
            raise AuditError('Expected length must be a finite positive number')
        before, after = states[step['before']], states[step['after']]
        sg, cg = step['sourceGuid'].upper(), step['createdGuid'].upper()
        if sg not in before['selected'] or sg not in after['selected'] or cg not in after['selected']:
            raise AuditError('Source/created GUID absent from required dump')
        source, created = after['selected'][sg], after['selected'][cg]
        change = delta(before['index'], after['index'])
        if type(step.get('expectedAddedCount')) is not int or step['expectedAddedCount'] != 1:
            raise AuditError('Schema 1 requires explicit expectedAddedCount=1')
        if change['added'] != [cg] or change['removed']:
            raise Conflict('Mutation delta is not exactly one expected addition')
        if before['selected'][sg] != source:
            raise Conflict('Source element changed during mutation')
        geometry = wall_geometry(source, created)
        if (abs(geometry['length']-step['expectedLength']) > TOLERANCE or
            geometry['jointDistance'] > TOLERANCE or not geometry['sameDirection'] or
            geometry['sourceHomeStory'] != geometry['homeStory'] or
            geometry['sourceFields'] != geometry['createdFields']):
            raise Conflict('Wall geometry contract failed')
        prefix = f'iteration-{number}/'
        refs = [before['spec']['path'], after['spec']['path']]
        put(prefix+'before-summary.json', before['summary'], [refs[0]])
        put(prefix+'after-summary.json', after['summary'], [refs[1]])
        put(prefix+'before-after-delta.json', change, refs)
        put(prefix+'source-wall.json', source, [refs[1]])
        put(prefix+'source-wall-before.json', before['selected'][sg], [refs[0]])
        put(prefix+'created-wall.json', created, [refs[1]])
        put(prefix+'geometry-check.json', geometry, refs)
        neighbours = []
        if change['changed']:
            bd = pinned_json(root, before['spec']); ad = pinned_json(root, after['spec'])
            bm, am = guid_map(bd['elements']), guid_map(ad['elements'])
            neighbours = [{'guid': g, 'before': bm[g], 'after': am[g]} for g in change['changed']]
            del bd, ad, bm, am
        put(prefix+'changed-elements.json', neighbours, refs)
        differences = [{'guid': e['guid'], 'changedPaths': changed_paths(e['before'], e['after'])}
                       for e in neighbours]
        semantic_delta(change, differences)
        put(prefix+'changed-fields.json', {'computedFromDump': True, 'elements': differences,
            'onlyNativeBodyIndexChanges': bool(differences) and all(
                re.fullmatch(r'bodies\[\d+\]\.nativeBodyIndex', path)
                for e in differences for path in e['changedPaths'])}, refs)
        checked = []
        for record in step.get('compactEvidence', []):
            value = pinned_json(root, record)
            checked.extend(compare_compact(value, geometry, change, source, created))
            if 'request' in value:
                if value.get('goalId') != contract['goalId'] or value['request'].get('sourceGuid') != source['guid'] or abs(value['request']['length']-geometry['length']) > TOLERANCE:
                    raise Conflict('Action record differs from full dump')
                checked.append('action')
            if 'typedRequest' in value:
                request = value['typedRequest']
                if request.get('sourceGuid') != source['guid'] or abs(request['length']-geometry['length']) > TOLERANCE:
                    raise Conflict('Typed request differs from full dump')
                checked.append('typedRequest')
            if 'sourceGuids' in value and value['sourceGuids'] != [source['guid']]:
                raise Conflict('Executor source GUID differs from full dump')
            for field, expected in [('plannedHash', before['summary']['modelHash']),
                                    ('preExecutionHash', before['summary']['modelHash']),
                                    ('executorBeforeHash', before['summary']['modelHash']),
                                    ('readbackHash', after['summary']['modelHash'])]:
                if field in value:
                    if value[field] != expected:
                        raise Conflict('Compact/full model hash mismatch: '+field)
                    checked.append(field)
            records.append(record)
        compact_checks.append({'iteration': number, 'status': 'PASS', 'checkedFields': sorted(set(checked))})
        if previous_created is not None:
            equal = previous_created.upper() == source['guid'].upper()
            dependencies.append({'previousIteration': number-1, 'nextIteration': number,
                                 'iteration1CreatedGuid': previous_created, 'iteration2SourceGuid': source['guid'], 'equal': equal})
            if contract.get('requireDependency') and not equal:
                raise Conflict('Iteration dependency does not match factual created GUID')
            previous = chain[-1]
            if previous['summary']['modelHash'] != before['summary']['modelHash']:
                raise Conflict('Model changed between dependent iterations')
        previous_created = created['guid']
        chain.extend([before, after])
        if contract.get('historicalStage') == 3:
            readback = states[f'observation-{3 if number == 1 else 6:03d}']
            if readback['summary']['modelHash'] != after['summary']['modelHash']:
                raise Conflict('Read-back differs from executor after dump')
            for observation_id in ([contract['initial'], 'observation-002'] if number == 1
                                   else ['observation-004', 'observation-005']):
                if states[observation_id]['summary']['modelHash'] != before['summary']['modelHash']:
                    raise Conflict('Fresh/stale observation differs from executor before dump')
    if chain[0]['summary']['modelHash'] != chain[1]['summary']['modelHash']:
        raise Conflict('Initial differs from first before snapshot')
    put('dependency-check.json', {'computedFromDump': True, 'dependencies': dependencies,
                                 'equal': all(x['equal'] for x in dependencies)}, [s['spec']['path'] for s in chain])
    put('hash-chain.json', [{**{k:s['spec'][k] for k in ('path','sha256','bytes')},
                             **{k:s['summary'][k] for k in ('modelHash','elementCount')}} for s in chain],
        [s['spec']['path'] for s in chain])
    put('compact-evidence-check.json', {'status': 'PASS', 'iterations': compact_checks}, [s['path'] for s in specs])
    records = list({r['path']: r for r in records}.values())
    if 'historicalManifest' in contract:
        for record in records:
            if record['path'] == contract['historicalManifest']['path']:
                continue
            historical = trusted.get(record['path'])
            if historical is None or any(record[k] != historical[k] for k in ('sha256', 'bytes')):
                raise AuditError('Evidence record differs from historical manifest: '+record['path'])
    put('source.json', {'schemaVersion': 1, 'extractor': 'scripts/build_audit_pack.py',
                       'extractorVersion': EXTRACTOR_VERSION, 'deterministic': True,
                       'canonicalization': 'UTF-8 JSON; sorted object keys; array order preserved; finite numbers',
                       'contract': contract, 'sourceFullDumps': [{k:s[k] for k in ('id','path','sha256','bytes')} for s in specs],
                       'evidenceRecords': sorted(records, key=lambda r:r['path'])}, [s['path'] for s in specs])
    # One index/changed-element record per line supports Connector line-range reads.
    blobs = {}
    for name, value in payloads.items():
        value = public_value(value)
        assert_public(value)
        if isinstance(value, list) and name.endswith(('element-index.json', 'changed-elements.json')):
            blobs[name] = b'[\n'+b',\n'.join(canonical(row) for row in value)+b'\n]\n'
        else:
            blobs[name] = canonical(value)+b'\n'
    # Directory-local rules preserve exact evidence bytes on Windows checkouts.
    blobs['.gitattributes'] = b'.gitattributes -text\n*.json -text\n'
    origins['.gitattributes'] = sorted(s['path'] for s in specs)
    manifest = {'schemaVersion': 1, 'extractorVersion': EXTRACTOR_VERSION,
                'sourceFullDumps': [{k:s[k] for k in ('id','path','sha256','bytes')} for s in specs],
                'files': [{'path': name, 'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob),
                           'sourceDumpRefs': origins[name]} for name, blob in sorted(blobs.items())]}
    assert_public(manifest)
    blobs['audit-pack-manifest.json'] = canonical(manifest)+b'\n'
    if sum(map(len, blobs.values())) > 9*1024*1024:
        raise AuditError('Audit pack exceeds 9 MiB bound; no full model duplication allowed')
    for name, blob in blobs.items():
        target = relative(output, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    return {'status': 'PASS', 'files': len(blobs), 'bytes': sum(map(len, blobs.values()))}


def verify_pack(root, output):
    output = Path(output)
    scan_public_pack(output)
    source = read_json(output/'source.json')
    manifest = read_json(output/'audit-pack-manifest.json')
    if manifest.get('schemaVersion') != 1 or source.get('extractorVersion') != EXTRACTOR_VERSION:
        raise AuditError('Unsupported pack schema/extractor')
    listed = manifest['files']
    names = [e['path'] for e in listed]
    actual = {str(p.relative_to(output)).replace('\\','/') for p in output.rglob('*') if p.is_file()}
    if len(set(names)) != len(names) or actual != set(names)|{'audit-pack-manifest.json'}:
        raise AuditError('Manifest file set mismatch')
    for entry in listed:
        if file_info(output, entry['path']) != {k:entry[k] for k in ('path','sha256','bytes')}:
            raise AuditError('Audit manifest SHA/size mismatch: '+entry['path'])
    # Re-extraction checks sources, full objects, all indices, deltas, geometry, fingerprints,
    # compact evidence and provenance. A self-consistent forged derived file still fails.
    with tempfile.TemporaryDirectory(prefix='audit-pack-verify-') as temp:
        result = build_pack(root, source['contract'], temp)
        for name in sorted(actual):
            if relative(output, name).read_bytes() != relative(temp, name).read_bytes():
                raise Conflict('Derived data differs from deterministic extraction: '+name)
    return result
