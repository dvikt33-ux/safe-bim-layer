"""Source-pinned Stage 4 scenario packs, including failed/uncertain attempts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tempfile

from scripts.audit_pack import (AuditError, canonical, changed_paths, delta, digest, file_info,
    model_summary, public_value, read_json, relative, scan_public_pack, semantic_delta)


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

    data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(AuditError('Nonfinite JSON: '+value)))
    # Preserve the old fail-closed concurrency check, but avoid the separate
    # pre-parse hash pass: the parsed bytes themselves were already hashed above.
    if file_info(root, spec['path']) != actual:
        raise AuditError('Source changed during read: '+spec['path'])
    return data


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

    payloads, states, snapshot_cache = {}, {}, {}

    def load_snapshot(name):
        if name not in snapshots or name not in records:
            raise AuditError('Delta requires two pinned factual snapshots')
        if name not in snapshot_cache:
            data = _pinned_json_once(root, records[name])
            if name not in states:
                summary, index = model_summary(data, contract['modelIdentity'])
                key = summary['modelHash']
                states[name] = (summary, index)
                payloads[f'models/{key}/summary.json'] = summary
                lean_index = [
                    {k: row[k] for k in ('guid', 'type', 'homeStory', 'fullElementHash') if k in row}
                    for row in index]
                payloads[f'models/{key}/element-index.json'] = (
                    lean_index if contract.get('indexStyle') == 'GUID_FULL_HASH' else index)
            snapshot_cache[name] = data
        return snapshot_cache[name]

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

    # Keep only snapshots still needed by later deltas. A chain therefore holds
    # roughly the current pair in memory instead of reparsing every pair source.
    pair_uses = Counter(name for pair in contract['pairs'] for name in (pair['before'], pair['after']))
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
            pair_uses[name] -= 1
            if pair_uses[name] == 0:
                snapshot_cache.pop(name, None)

    # Snapshots not participating in a delta still require summary/index proof.
    for name in sorted(snapshots):
        if name not in states:
            load_snapshot(name)
        snapshot_cache.pop(name, None)

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
