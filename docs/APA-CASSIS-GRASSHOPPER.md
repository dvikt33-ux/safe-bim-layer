# APA → Cassis → Grasshopper (Rhino 8), isolated pilot

**Status (2026-11-17):** implementation available on branch `integration/apa-cassis-gh-20261117`.
Local test: MCP HTTP protocol + stdio process + pinned graph guard. **NOT an accepted native Archicad 30 write path.**
The installed production APA release and its signed manifest were NOT modified.

## Architecture

```text
ChatGPT conversation
    -> existing APA Windows ChatGPT plugin / authorized remote tunnel
    -> APA server (apa_control_mcp.server_for)
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

## Target: ChatGPT -> APA Windows (not Codex)

The requested user-facing entry point is the **existing ChatGPT APA Windows plugin**.
The plugin currently exposes a fixed set of APA Windows tools; new Grasshopper tools are **not yet available through it**. The remote APA tunnel is offline (tunnel-client has not been seen for 300 seconds).
To complete the requested route: deploy the guarded tools in the server behind the existing plugin, restore the tunnel, refresh connector discovery/schema if required, then invoke and verify `apa_grasshopper_read` from the ChatGPT conversation. None of these steps may be reported as passed before executing them.

The `scripts/apa_cassis_entry.py` local stdio entry point remains a development-only test fixture for the MCP protocol. It is **not** the intended production client. The temporary Codex MCP registration was removed on 2026-11-17 and its removal verified.

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
- The account-specific cloud APA Windows tunnel is offline; working local MCP tests do NOT make these tools available in the ChatGPT conversation.

## Native write acceptance gate (not yet passed)

1. Start one clearly identified Rhino + GH and one **isolated** Archicad 30 test PLN; match project path and runtime identity.
2. Confirm Live Connection handshake against precisely that Archicad instance.
3. Preflight exact PLN and separately saved byte-identical backup, allow one experimental native slab only.
4. Use a closed 4000×3000-mm GH planar polygon, explicit structure/stories/attributes and no automatic sync to an unrelated PLN.
5. Record GUID, read-back native geometry / BREP and dimensions, Save, close, reopen exact test PLN, check GUID and geometry again.
6. Reject whenever document ownership, project identity or add-on registration changes.

**No native PASS** until these observations are recorded. Do not change the active stair/project PLNs.

## ChatGPT R04.1 secure tunnel pilot — 2026-11-17

The original signed APA R04.1 release is **not edited**. An isolated Windows overlay combines `Control` from the signed `APA-Windows` release with the branch `server_for(..., cassis=CassisControl(...))` at the existing tunnel backend URL `http://127.0.0.1:18787/mcp`.

Executed live local MCP tests: initialize HTTP 200, four tools (`apa_read`, `apa_execute`, `apa_grasshopper_read`, `apa_grasshopper_set_slider`), `apa_read(kind=status) => MCP_APA_READY`, `apa_grasshopper_read(operation=status) => CASSIS_CONNECTED`, foreign active GH document => BLOCKED. The original release revision and manifest hash were read back.

Verified existing `tunnel-client.exe` version 0.0.20 profiles `apa-r04` (backend `127.0.0.1:18787/mcp`) and `apa-powershell` (backend `127.0.0.1:18790/mcp`). The `doctor` command on both profiles failed solely on absent environment variable `CONTROL_PLANE_API_KEY`. Verified no key in Process/User/Machine environment for the tested account. Do not print, commit, or pass a raw key as a CLI argument.

Local one-click launcher (kept in an isolated test directory, not in this repo) validates the four tools, starts the isolated APA overlay only if needed, asks for a restricted runtime key using Windows PowerShell `Read-Host -AsSecureString`, calls `tunnel-client doctor --config ...`, then `tunnel-client run --config ...`, and clears the key environment variable on exit. The `.ps1` file was encoded UTF-8 with BOM for PowerShell 5.1; AST parse errors: 0. The tunnel itself **has not been run with a credential yet**.

**Final acceptance pending:** operator supplies a restricted key with Tunnels Read + Use locally, starts the tunnel, verifies `/readyz` and actual tool invocation from the existing ChatGPT plugin; if the existing app has stale tools, refresh its MCP discovery/connection. Only then may `ChatGPT → APA → Cassis` be called end-to-end PASS. Native AC30 Live Connection and PLN Save/Reopen are separate blocked acceptance gates.
