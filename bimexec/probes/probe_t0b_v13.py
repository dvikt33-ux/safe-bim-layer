#!/usr/bin/env python3
"""BIMEXEC T0B v1.3 runner.

Uses the AC29/Tapir 1.5.9 compatibility backend from backends_v13.py while
preserving all v1.2 T0B safety rules: dry-run by default, two-key write gate,
receipt-before-mutation, single-attempt steps, restore verification, and no
geometry writes.
"""
from __future__ import annotations

import probe_t0b as probe
from backends_v13 import PROBE_VERSION, build_backends_v13, discover_ports_v13

probe.PROBE_VERSION = PROBE_VERSION
probe.build_backends = build_backends_v13
probe.discover_ports = discover_ports_v13

if __name__ == "__main__":
    raise SystemExit(probe.main())
