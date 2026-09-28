"""Canonical payload identity. Same message id is not enough."""
from __future__ import annotations

import hashlib
import json


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str)


def canonical_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()
