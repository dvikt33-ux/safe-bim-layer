"""Source-pinned Stage 4 scenario packs, including failed/uncertain attempts."""
import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import tempfile

from scripts.audit_pack import (AuditError, Conflict, canonical, changed_paths, delta, digest, element_index, file_info,
    public_value, read_json, relative, scan_public_pack, semantic_delta)

_NATIVE_SECONDS_KEY = b'"nativeSeconds":'
_NATIVE_SECONDS_NUMBER = re.compile(rb'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?')


def _semantic_source_key(root, spec):
    """Hash exact source bytes while normalizing only top-level dump timing.

    ModelDumpCommands adds nativeSeconds exactly once at the top level and
    model_hash deliberately excludes that timing field. If the key is absent
    or appears more than once, fall back to the full raw SHA so deduplication
    can never broaden the semantic contract.
    """
    path = relative(root, spec['path'])
    raw = path.read_bytes()
    raw_sha = hashlib.sha256(raw).hexdigest()
    actual = {'path': spec['path'], 'sha256': raw_sha, 'bytes': len(raw)}
    expected = {k: spec[k] for k in ('path', 'sha256', 'bytes')}
    if actual != expected:
        raise AuditError('Source SHA/size mismatch: '+spec['path'])
    if raw.count(_NATIVE_SECONDS_KEY) != 1:
        return 'raw:'+raw_sha
    key_at = raw.find(_NATIVE_SECONDS_KEY)
    value_at = key_at + len(_NATIVE_SECONDS_KEY)
    match = _NATIVE_SECONDS_NUMBER.match(raw, value_at)
    if match is None:
        return 'raw:'+raw_sha
    h = hashlib.sha256()
    h.update(raw[:value_at])
    h.update(b'0')
    h.update(raw[match.end():])
    return 'timing-normalized:'+h.hexdigest()


def _pinned_json_once(root, spec):
    """Parse the exact pinned bytes, then independently confirm the source still matches."""
    path = relative(root, spec['path'])
    raw = path.read_bytes()
    actual = {'path': spec['path'], 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    expected = {k: spec[k] for k in ('path', 'sha256', 'bytes')}
    if actual != expected:
        raise AuditError('Source SHA/size mismatch: '+spec['path'])

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError('Duplicate JSON key: ' + key)
            result[key] = value
        return result

    data = json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(AuditError('Nonfinite JSON: '+value)))
    # Preserve the old fail-closed concurrency check, but avoid the separate
    # pre-parse hash pass: the parsed bytes themselves were already hashed above.
    if file_info(root, spec['path']) != actual:
        raise AuditError('Source changed during read: '+spec['path'])
    return data


def _model_summary_once(data, identity):
    """Equivalent model summary without hashing every element twice."""
    rows = element_index(data)
    value = {k: v for k, v in data.items()
             if k not in ('elements', 'materials', 'unresolvedBodyOwners', 'nativeSeconds')}
    value['elements'] = sorted(row['fullElementHash'] for row in rows)
    for key in ('materials', 'unresolvedBodyOwners'):
        value[key] = sorted(digest(item) for item in data.get(key, []))
    result = {
        'modelIdentity': identity,
        'modelHash': digest(value),
        'elementCount': len(rows),
        'typeCounts': dict(sorted(Counter(str(e.get('type')) for e in data['elements']).items())),
    }
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


def source_contract(root, scenario, snapshots, pairs, records, identity, provenance):
    scenario = Path(scenario).resolve()
    root = Path(root).resolve()
    if not scenario.is_relative_to(root):
        raise AuditError('Scenario outside repository')
    names = sorted({Path(path).resolve().relative_to(root).as_posix() for path in records + snapshots})
    return {'schemaVersion': 1, 'scenarioId': scenario.name, 'provenance': provenance, 'indexStyle':'GUID_FULL_HASH',
        'modelIdentity': identity, 'records': [file_info(root, name) for name in names],
        'snapshots': [Path(path).resolve().relative_to(root).as_posix() for path in snapshots],
        'pairs': [{'before': Path(a).resolve().relative_to(root).as_posix(),
                   'after': Path(b).resolve().relative_to(root).as_posix()} for a, b in pairs]}


def extract(root, contract):
    if contract.get('schemaVersion') != 1 or contract['provenance'] not in ('LIVE', 'OFFLINE_FIXTURE'):
        raise AuditError('Explicit Stage 4 scenario provenance required')
    if contract.get('indexStyle','FULL') not in ('FULL','GUID_FULL_HASH'):
        raise AuditError('Unsupported index contract')
    records = {record['path']: record for record in contract['records']}
    if len(records) != len(contract['records']):
        raise AuditError('Duplicate source paths')
    snapshots = set(contract['snapshots'])
    if not snapshots.issubset(records):
        raise AuditError('Unpinned snapshot')

    # Verify every factual snapshot against its pinned raw SHA first. The
    # timing-normalized key is stricter than model_hash equality: two snapshots
    # share a key only when their source bytes are identical except for the
    # single top-level nativeSeconds scalar that model_hash already excludes.
    semantic_keys = {name: _semantic_source_key(root, records[name])
                     for name in sorted(snapshots)}

    payloads, states = {}, {}
    group_states, group_data = {}, {}

    def load_snapshot(name):
        if name not in snapshots or name not in records:
            raise AuditError('Delta requires two pinned factual snapshots')
        group = semantic_keys[name]
        if group not in group_states:
            data = _pinned_json_once(root, records[name])
            summary, index = _model_summary_once(data, contract['modelIdentity'])
            group_states[group] = (summary, index)
            group_data[group] = data
            key = summary['modelHash']
            payloads[f'models/{key}/summary.json'] = summary
            lean_index = [
                {k: row[k] for k in ('guid', 'type', 'homeStory', 'fullElementHash') if k in row}
                for row in index]
            payloads[f'models/{key}/element-index.json'] = (
                lean_index if contract.get('indexStyle') == 'GUID_FULL_HASH' else index)
        elif group not in group_data:
            # The semantic state was summarized earlier but its full object tree
            # was released after the last previous delta use. Reparse only if a
            # later delta unexpectedly needs that state again.
            group_data[group] = _pinned_json_once(root, records[name])
        states[name] = group_states[group]
        return group_data[group]

    # Non-snapshot records remain independently source-pinned. Large records
    # stay as LFS refs; ordinary records are embedded after sanitization.
    for name, spec in sorted(records.items()):
        if name in snapshots:
            continue
        if spec['bytes'] > 1_000_000:
            if file_info(root, name) != spec:
                raise AuditError('Raw LFS source SHA/size mismatch: '+name)
            payloads['raw-refs/'+digest(name)+'.json'] = {'sourceRef': spec, 'storage': 'GIT_LFS'}
            continue
        data = _pinned_json_once(root, spec)
        payloads['records/'+digest(name)+'.json'] = {'sourceRef': name, 'value': data}

    # Retain a semantic state only until its last delta occurrence. Multiple
    # 100-MiB snapshots of the same model state therefore share one JSON parse,
    # one element-index pass and one full in-memory object tree.
    pair_uses = Counter(semantic_keys[name] for pair in contract['pairs']
                        for name in (pair['before'], pair['after']))
    for number, pair in enumerate(contract['pairs'], 1):
        before_name, after_name = pair['before'], pair['after']
        before = load_snapshot(before_name)
        after = load_snapshot(after_name)
        bm = {e['guid'].upper(): e for e in before['elements']}
        am = {e['guid'].upper(): e for e in after['elements']}
        change = delta(states[before_name][1], states[after_name][1])
        differences = [{'guid': guid, 'changedPaths': changed_paths(bm[guid], am[guid])}
                       for guid in change['changed']]
        payloads[f'deltas/{number:03}.json'] = {'before': before_name, 'after': after_name,
            **semantic_delta(change, differences), 'changedFields': differences,
            'addedElements': [am[g] for g in change['added']],
            'removedElements': [bm[g] for g in change['removed']]}
        for name in (before_name, after_name):
            group = semantic_keys[name]
            pair_uses[group] -= 1
            if pair_uses[group] == 0:
                group_data.pop(group, None)

    # Snapshots not participating in a delta still require summary/index proof.
    # If an equivalent state was already processed, alias its verified state
    # without parsing the duplicate 100-MiB JSON again.
    for name in sorted(snapshots):
        group = semantic_keys[name]
        if name not in states:
            if group in group_states:
                states[name] = group_states[group]
            else:
                load_snapshot(name)
        group_data.pop(group, None)

    payloads['source.json'] = contract
    blobs = {}
    for name, value in payloads.items():
        value = public_value(value)
        if name.endswith('element-index.json'):
            blobs[name] = b'[\n'+b',\n'.join(canonical(row) for row in value)+b'\n]\n'
        else:
            blobs[name] = canonical(value)+b'\n'
    blobs['.gitattributes'] = b'.gitattributes -text\n*.json -text\n'
    manifest = {'schemaVersion': 1, 'extractor': 'scripts/stage4_audit_pack.py',
        'files': [{'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                  for name, raw in sorted(blobs.items())]}
    blobs['audit-pack-manifest.json'] = canonical(manifest)+b'\n'
    if sum(map(len, blobs.values())) > 9*1024*1024:
        raise AuditError('Stage 4 pack exceeds 9 MiB; full evidence must remain separate')
    return blobs


def build_pack(root, contract, output):
    output = Path(output)
    if output.exists():
        raise AuditError('Existing pack cannot be overwritten')
    blobs = extract(root, contract)
    output.mkdir(parents=True)
    for name, raw in blobs.items():
        path = relative(output, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    scan_public_pack(output)
    return {'status': 'PASS', 'files': len(blobs), 'bytes': sum(map(len, blobs.values())), 'sourceShaVerification': 'PASS'}


def verify_pack(root, output):
    output = Path(output)
    contract = read_json(output/'source.json')
    # Public contract hashes identity values. Extraction also sanitizes the
    # original private identity, yielding that same logical identity token.
    blobs = extract(root, contract)
    actual = {p.relative_to(output).as_posix(): p for p in output.rglob('*') if p.is_file()}
    if set(actual) != set(blobs):
        raise AuditError('Pack file set mismatch')
    for name, raw in blobs.items():
        if actual[name].read_bytes() != raw:
            raise AuditError('Re-extracted pack differs: '+name)
    scan_public_pack(output)
    return {'status': 'PASS', 'files': len(blobs), 'bytes': sum(map(len, blobs.values())),
            'absolutePathScan': 'PASS', 'sourceShaVerification': 'PASS', 'semanticDelta': 'PASS'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--contract', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    print(verify_pack(args.root, args.output) if args.verify else build_pack(args.root, read_json(args.contract), args.output))
