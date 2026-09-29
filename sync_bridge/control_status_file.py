"""Atomic read-only status transport for the Safe BIM control surface.

The publisher accepts raw BridgeHost.status() data but persists only the
UI-safe projection returned by build_control_status(). It owns no BIM command
path and performs no Archicad I/O.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from copy import deepcopy
from pathlib import Path

from sync_bridge.control_status import (
    CONTROL_STATUS_VERSION,
    build_control_status,
)

CONTROL_STATUS_TRANSPORT_VERSION = 1
CONTROL_STATUS_FILENAME = "control-status.json"
DEFAULT_MAX_AGE_MS = 10_000


class ControlStatusFilePublisher:
    def __init__(self, path, *, publisher_id=None, clock_ms=None):
        self.path = Path(path)
        self.publisher_id = publisher_id or uuid.uuid4().hex
        if not isinstance(self.publisher_id, str) or not self.publisher_id:
            raise ValueError("publisher_id must be a non-empty string")
        self._clock_ms = clock_ms or _unix_ms
        self._sequence = 0

    @property
    def sequence(self):
        return self._sequence

    def publish(self, host_status: dict) -> dict:
        status = build_control_status(host_status)

        published_at = self._clock_ms()
        if type(published_at) is not int or published_at < 0:
            raise ValueError("clock_ms must return a non-negative integer")

        next_sequence = self._sequence + 1
        envelope = {
            "transportVersion": CONTROL_STATUS_TRANSPORT_VERSION,
            "publisherId": self.publisher_id,
            "sequence": next_sequence,
            "publishedAtUnixMs": published_at,
            "status": status,
        }

        payload = (
            json.dumps(
                envelope,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        )

        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary = self.path.with_name(
            f".{self.path.name}.{self.publisher_id}.{next_sequence}.tmp"
        )

        try:
            with temporary.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temporary, self.path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

        self._sequence = next_sequence
        return deepcopy(envelope)


def read_control_status_file(path) -> dict:
    path = Path(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid control status file") from exc

    return _validated_envelope(data)


def status_snapshot_is_fresh(
    envelope: dict,
    *,
    max_age_ms: int = DEFAULT_MAX_AGE_MS,
    now_ms=None,
) -> bool:
    data = _validated_envelope(envelope)

    if type(max_age_ms) is not int or max_age_ms < 0:
        raise ValueError("max_age_ms must be a non-negative integer")

    current = _unix_ms() if now_ms is None else now_ms
    if type(current) is not int or current < 0:
        raise ValueError("now_ms must be a non-negative integer")

    age = current - data["publishedAtUnixMs"]
    return 0 <= age <= max_age_ms


def default_control_status_path(data_dir) -> Path:
    return Path(data_dir) / CONTROL_STATUS_FILENAME


def _validated_envelope(data) -> dict:
    if not isinstance(data, dict):
        raise ValueError("control status envelope must be an object")

    required = {
        "transportVersion",
        "publisherId",
        "sequence",
        "publishedAtUnixMs",
        "status",
    }
    if set(data) != required:
        raise ValueError("invalid control status envelope fields")

    if data["transportVersion"] != CONTROL_STATUS_TRANSPORT_VERSION:
        raise ValueError("unsupported control status transport version")

    if not isinstance(data["publisherId"], str) or not data["publisherId"]:
        raise ValueError("invalid publisherId")

    if type(data["sequence"]) is not int or data["sequence"] <= 0:
        raise ValueError("invalid sequence")

    if (
        type(data["publishedAtUnixMs"]) is not int
        or data["publishedAtUnixMs"] < 0
    ):
        raise ValueError("invalid publishedAtUnixMs")

    status = data["status"]
    if not isinstance(status, dict):
        raise ValueError("invalid status payload")

    if status.get("schemaVersion") != CONTROL_STATUS_VERSION:
        raise ValueError("unsupported control status schema")

    return deepcopy(data)


def _unix_ms() -> int:
    return time.time_ns() // 1_000_000