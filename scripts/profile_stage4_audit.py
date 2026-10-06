"""Read-only profiler for Stage 4 Audit Pack verification.

This module never writes Archicad, source evidence, or the audit pack. It wraps
existing verification primitives only to report where CPU/I/O time is spent.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import time

import scripts.stage4_audit_pack as pack
from scripts.audit_pack import read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='Existing Stage 4 audit-pack directory')
    args = parser.parse_args()

    output = args.output.resolve()
    source = read_json(output / 'source.json')
    root = Path(__file__).resolve().parents[1]

    snapshots = set(source.get('snapshots', []))
    specs = {row['path']: row for row in source.get('records', [])}
    snapshot_bytes = sum(specs[name]['bytes'] for name in snapshots if name in specs)
    record_bytes = sum(row['bytes'] for row in source.get('records', []))

    totals = defaultdict(float)
    counts = defaultdict(int)
    per_source = []

    original_pinned = pack._pinned_json_once
    original_summary = pack._model_summary_once
    original_changed = pack.changed_paths
    original_scan = pack.scan_public_pack
    original_extract = pack.extract

    def timed_pinned(root_arg, spec):
        started = time.perf_counter()
        result = original_pinned(root_arg, spec)
        elapsed = time.perf_counter() - started
        totals['pinned-json'] += elapsed
        counts['pinned-json'] += 1
        per_source.append((elapsed, spec['bytes'], spec['path']))
        return result

    def timed_summary(data, identity):
        started = time.perf_counter()
        result = original_summary(data, identity)
        totals['model-summary'] += time.perf_counter() - started
        counts['model-summary'] += 1
        return result

    def timed_changed(before, after, path=''):
        started = time.perf_counter()
        result = original_changed(before, after, path)
        totals['changed-paths'] += time.perf_counter() - started
        counts['changed-paths'] += 1
        return result

    def timed_scan(path):
        started = time.perf_counter()
        result = original_scan(path)
        totals['public-scan'] += time.perf_counter() - started
        counts['public-scan'] += 1
        return result

    def timed_extract(root_arg, contract):
        started = time.perf_counter()
        result = original_extract(root_arg, contract)
        totals['extract-total'] += time.perf_counter() - started
        counts['extract-total'] += 1
        return result

    pack._pinned_json_once = timed_pinned
    pack._model_summary_once = timed_summary
    pack.changed_paths = timed_changed
    pack.scan_public_pack = timed_scan
    pack.extract = timed_extract

    print('===== STAGE 4 AUDIT PROFILE =====', flush=True)
    print(f'records: {len(specs)}', flush=True)
    print(f'snapshots: {len(snapshots)}', flush=True)
    print(f'record bytes: {record_bytes / (1024**2):.1f} MiB', flush=True)
    print(f'snapshot bytes: {snapshot_bytes / (1024**2):.1f} MiB', flush=True)

    started = time.perf_counter()
    result = pack.verify_pack(root, output)
    total = time.perf_counter() - started

    print('\n===== RESULT =====', flush=True)
    print(result, flush=True)
    print('\n===== TIMINGS =====', flush=True)
    for key in ('extract-total', 'pinned-json', 'model-summary', 'changed-paths', 'public-scan'):
        print(f'{key}: {totals[key]:.3f}s ({counts[key]} calls)', flush=True)
    residual = max(0.0, total - totals['extract-total'] - totals['public-scan'])
    print(f'pack-compare/other-after-extract: {residual:.3f}s', flush=True)
    print(f'TOTAL: {total:.3f}s', flush=True)

    print('\n===== SLOWEST PINNED SOURCES =====', flush=True)
    for elapsed, size, name in sorted(per_source, reverse=True)[:15]:
        print(f'{elapsed:8.3f}s  {size/(1024**2):8.1f} MiB  {name}', flush=True)

    return 0 if result.get('status') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
