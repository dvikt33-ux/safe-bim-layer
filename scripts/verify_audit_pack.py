"""Verify source hashes, manifest and recomputed Audit Pack content offline."""
import argparse
import json
from pathlib import Path
from audit_pack import AuditError, verify_pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('pack', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_pack(args.root, args.pack)))
        return 0
    except (AuditError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': getattr(exc, 'status', 'FAIL'), 'error': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
