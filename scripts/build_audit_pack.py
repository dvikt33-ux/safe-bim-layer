"""Build a schema 1 Audit Pack from existing, pinned local JSON dumps only."""
import argparse
import json
from pathlib import Path
from audit_pack import AuditError, build_pack, historical_contract, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--contract', type=Path)
    source.add_argument('--historical-stage', type=int, choices=(1, 3))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deterministic', action='store_true', help='Always deterministic; timestamps are omitted')
    args = parser.parse_args()
    try:
        contract = read_json(args.contract) if args.contract else historical_contract(args.root, args.historical_stage)
        print(json.dumps(build_pack(args.root, contract, args.output)))
        return 0
    except (AuditError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': getattr(exc, 'status', 'FAIL'), 'error': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
