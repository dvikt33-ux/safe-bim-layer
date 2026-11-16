# APA → Cassis → Grasshopper (Rhino 8), isolated pilot

**Status (2026-11-17):** implementation available on branch `integration/apa-cassis-gh-20261117`.
Local test: MCP HTTP protocol + stdio process + pinned graph guard. **NOT an accepted native Archicad 30 write path.**
The installed production APA release and its signed manifest were NOT modified.

## Architecture

```text
Local MCP client (e.g. Codex)
    -> launches APA MCP server (stdio, scripts/apa_cassis_entry.py)
    -> apa_grasshopper_read / apa_grasshopper_set_slider
    -> guarded scripts/apa_cassis_bridge.py
    -> Cassis 1.6.0 on 127.0.0.1:3003/mcp/
    -> Rhino 8 / Grasshopper active document
```

Desktop Commander can be used during installation but is **not in this runtime path**.
The adapter uses the *existing* `apa_control_mcp.server_for`; it does not implement an alternative MCP server.
Existing Tapir tools and gated SceneWriter write campaigns are unchanged.
This branch also allows opting in from the normal APA server using `--cassis-profile`;
no Cassis tool is exposed unless that flag is supplied.

## Isolation policy

- **Only** a SHA-256-pinned `.ghx` in an `experiments` directory.
- The open Grasshopper document path must match the profile before and after tool operations.
- Read operations: `status`, `document`, `components`, `connections`, `output`.
- Write operation: `set_slider` only, and only for two GUIDs explicitly pinned in profile.
- Write checks: pinned file hash unchanged, graph consists of one GH component, two GH parameters, two connections, integer value 100–10000.
- No arbitrary Cassis tool forwarding; no `loaddocument`, `savedocument`, `addcomponent`, `removecomponents`, scripting or PLN modification exposed to an MCP client.
- The underlying Cassis 3003 server has no authentication: never expose it on an untrusted network.
- Cassis can host several Rhino windows. If the active GH document changes, the adapter blocks operations; it does not automatically steal focus.

## Local start (stdio)

On the APA branch checkout with dependencies installed:

```powershell
python scripts/apa_cassis_entry.py --profile "D:\\path\\to\\cassis-profile.json"
```

Example Codex local MCP configuration:

```toml
[mcp_servers.apa_grasshopper]
command = "C:\\path\\to\\python.exe"
args = ["C:\\path\\to\\APA\\scripts\\apa_cassis_entry.py", "--profile", "D:\\path\\to\\cassis-profile.json"]
startup_timeout_sec = 30
tool_timeout_sec = 30
```

An isolated experimental launcher may set up module search paths while this change is pending release integration. It must not be substituted for a signed production release.

## Test results and limits

- Cassis v1.6.0 initialized and provided 63 MCP commands.
- Earlier isolated GHX rectangle: 4000 × 3000 mm, closed polyline, perimeter 14000 mm, 2 wires. Saved and re-opened with identical perimeter.
- Local APA HTTP MCP (`127.0.0.1:8761` test only): initialize/list tools PASS; status PASS; unauthorized write BLOCKED.
- APA stdio MCP client: initialize/list tools PASS; live Cassis status PASS; unauthorized write BLOCKED.
- `tests/test_apa_cassis_bridge.py`: 10 isolation tests.
- During pilot, another session changed active GHX to `APA_Cassis_Rectangle_5x4m_apa_mcp.ghx`; pinned-graph guard blocked access.
- Windows has Grasshopper-Archicad Live Connection 30 R1 INT 30.0.0.3000 installed; **no live-link handshake or native BIM element creation was validated**.
- There were multiple active Archicad 30 processes. An isolated PLN copy has been staged, not opened or written by this pilot.
- The account-specific cloud APA Windows tunnel is offline; local Codex stdio integration does NOT on its own make this MCP available to the ChatGPT cloud session.

## Native write acceptance gate (not yet passed)

1. Start one clearly identified Rhino + GH and one **isolated** Archicad 30 test PLN; match project path and runtime identity.
2. Confirm Live Connection handshake against precisely that Archicad instance.
3. Preflight exact PLN and separately saved byte-identical backup, allow one experimental native slab only.
4. Use a closed 4000×3000-mm GH planar polygon, explicit structure/stories/attributes and no automatic sync to an unrelated PLN.
5. Record GUID, read-back native geometry / BREP and dimensions, Save, close, reopen exact test PLN, check GUID and geometry again.
6. Reject whenever document ownership, project identity or add-on registration changes.

**No native PASS** until these observations are recorded. Do not change the active stair/project PLNs.
