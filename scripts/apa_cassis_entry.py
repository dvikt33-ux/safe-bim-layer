"""Launch the existing APA MCP server with an opt-in guarded Cassis test bridge.

Example: python scripts/apa_cassis_entry.py --profile C:\\path\\cassis-profile.json
The server speaks MCP stdio; the client launches it automatically.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from apa_cassis_bridge import CassisControl
from apa_control_mcp import run_server, server_for


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    cassis = CassisControl(args.profile)
    run_server(server_for(cassis=cassis), None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
