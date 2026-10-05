"""Source-pinned Stage 4 scenario packs, including failed/uncertain attempts."""
import argparse
import hashlib
from pathlib import Path
import tempfile

from scripts.audit_pack import (AuditError, canonical, changed_paths, delta, digest, file_info,
    model_summary, pinned_json, public_value, read_json, relative, scan_public_pack, semantic_delta)


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
    payloads, states = {}, {}
    for name, spec in sorted(records.items()):
        if name not in snapshots and spec['bytes'] > 1_000_000:
            if file_info(root, name) != spec:
                raise AuditError('Raw LFS source SHA/size mismatch: '+name)
            payloads['raw-refs/'+digest(name)+'.json'] = {'sourceRef': spec, 'storage': 'GIT_LFS'}
            continue
        data = pinned_json(root, spec)
        if name in snapshots:
            summary, index = model_summary(data, contract['modelIdentity'])
            key = summary['modelHash']
            states[name] = (summary, index)
            payloads[f'models/{key}/summary.json'] = summary
            lean_index = [
                {k: row[k] for k in ('guid', 'type', 'homeStory', 'fullElementHash') if k in row}
                for row in index]
            payloads[f'models/{key}/element-index.json'] = lean_index if contract.get('indexStyle') == 'GUID_FULL_HASH' else index
        else:
            # Ordinary-sized raw records remain independently inspectable in
            # the public pack, after recursive path sanitization.
            payloads['records/'+digest(name)+'.json'] = {'sourceRef': name, 'value': data}
    for number, pair in enumerate(contract['pairs'], 1):
        if pair['before'] not in states or pair['after'] not in states:
            raise AuditError('Delta requires two pinned factual snapshots')
        before = pinned_json(root, records[pair['before']])
        after = pinned_json(root, records[pair['after']])
        bm = {e['guid'].upper(): e for e in before['elements']}
        am = {e['guid'].upper(): e for e in after['elements']}
        change = delta(states[pair['before']][1], states[pair['after']][1])
        differences = [{'guid': guid, 'changedPaths': changed_paths(bm[guid], am[guid])} for guid in change['changed']]
        payloads[f'deltas/{number:03}.json'] = {'before': pair['before'], 'after': pair['after'],
            **semantic_delta(change, differences), 'changedFields': differences,
            'addedElements': [am[g] for g in change['added']], 'removedElements': [bm[g] for g in change['removed']]}
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
