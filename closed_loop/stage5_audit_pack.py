"""Stage 5 source-pinned Audit Pack for the single Hosted Window live run."""
from pathlib import Path
import time

from .live_wall import ROOT, read
from .wall_attempts import durable_json
from scripts.stage4_audit_pack import source_contract, build_pack, verify_pack


def finish_pack(output, identity):
    output = Path(output).resolve()
    started = time.perf_counter()
    marks = {}

    def mark(name, phase):
        marks[name] = round(time.perf_counter()-phase, 3)
        print(f'[evidence] {name}: {marks[name]:.3f}s', flush=True)

    phase = time.perf_counter()
    snapshots, records, pairs = [], [], []
    for path in sorted(output.rglob('*.json')):
        if 'audit-pack' in path.parts or path.name in (
                'audit-pack-verification.json','full-evidence-manifest.json'):
            continue
        records.append(path)
        observation_sidecar = path.name.endswith(
            ('.request.json','.native-response.json','.metrics.json','.fingerprint.json'))
        if ((path.parent.name == 'observations' and not observation_sidecar)
                or (path.parent.name == 'executor' and path.name in ('before.json','after-create.json'))):
            snapshots.append(path)

    snapshot_set = {p.resolve() for p in snapshots}
    for before in snapshots:
        if before.name == 'before.json':
            after = before.with_name('after-create.json')
            if after.resolve() in snapshot_set:
                pairs.append((before, after))

    # The final independent read-back is a separate factual snapshot. Pair the
    # exact executor-before model to that read-back as the Stage-5 semantic delta.
    job_path = output/'job.json'
    if job_path.is_file():
        job = read(job_path)
        for step in job.get('iterations', []):
            readback = step.get('readback') or {}
            after_name = (readback.get('evidence', {}).get('live.snapshot', {}) or {}).get('path')
            before = output/'session'/f'iteration-{step["iteration"]}'/'executor'/'before.json'
            if after_name and before.resolve() in snapshot_set and Path(after_name).resolve() in snapshot_set:
                pair = (before, Path(after_name))
                if pair not in pairs:
                    pairs.append(pair)
    mark('collect', phase)

    print(f'[evidence] pinning {len(records)} records / {len(snapshots)} snapshots / {len(pairs)} deltas', flush=True)
    phase = time.perf_counter()
    contract = source_contract(ROOT, output, snapshots, pairs, records, identity, 'LIVE')
    mark('source-contract', phase)

    phase = time.perf_counter()
    build_pack(ROOT, contract, output/'audit-pack')
    mark('build-pack', phase)

    phase = time.perf_counter()
    result = verify_pack(ROOT, output/'audit-pack')
    mark('verify-pack', phase)

    phase = time.perf_counter()
    durable_json(output/'full-evidence-manifest.json', {
        'files':contract['records'],
        'largeFileStorage':'LOCAL_OR_GIT_LFS',
        'auditPackStorage':'ORDINARY_GIT',
    })
    mark('manifest', phase)
    marks['total'] = round(time.perf_counter()-started, 3)
    result = dict(result, timingsSeconds=marks)
    durable_json(output/'audit-pack-verification.json', result)
    print(f'[evidence] complete: {marks["total"]:.3f}s', flush=True)
    return result
