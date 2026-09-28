"""Canonical payload identity. Same message id is not enough."""
from __future__ import annotations

import hashlib
import json
import math


def _require_json_value(value, path: str = '$') -> None:
    value_type = type(value)
    if value is None or value_type in (bool, int, str):
        return
    if value_type is float:
        if not math.isfinite(value):
            raise ValueError(f'{path} contains a non-finite number')
        return
    if value_type is list:
        for index, item in enumerate(value):
            _require_json_value(item, f'{path}[{index}]')
        return
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f'{path} contains a non-string object key')
            _require_json_value(item, f'{path}.{key}')
        return
    raise TypeError(f'{path} contains a non-JSON value')


def canonical_json(value) -> str:
    _require_json_value(value)
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':'),
        allow_nan=False,
    )


def canonical_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()
