# APA Windows → Grasshopper through the existing ChatGPT tools

**Implementation state (2026-11-22):** source and offline CI on a draft branch.
**NOT DEPLOYED** to the user's Windows machine. No claim of a successful end-to-end ChatGPT → Grasshopper model change or Archicad PLN write.

## Why this route

The existing ChatGPT application exposes only \`apa_read\` and \`apa_execute\`,
while Cassis 1.6.0 is separately listening on \`127.0.0.1:3003/mcp/\`.
Refreshing plugin tool discovery is not necessary when the two familiar tool
names remain unchanged. The compatibility gateway therefore implements:

- \`apa_execute(operation="gh-read",job_id="...",target=null,intent={"tool":"getdocumentinfo","arguments":{}})\`
- \`apa_execute(operation="gh-write",job_id="...",target=null,intent={"tool":"addcomponent","arguments":{...}})\`
- \`apa_read(kind="job",job_id="...")\`: reads saved operation receipt.

Existing APA operation names are passed unchanged to the signed APA Control.
The signed release itself is never patched. All GH write requests must match
a **separately created, absolute, SHA-pinned, experimental Grasshopper file**
under the operator-selected working directory.

### Actual Windows observations

On 2026-11-22, the authorized local MCP diagnostic returned HTTP 200 from both
servers. The APA tool list contained \`apa_read\` and \`apa_execute\` only.
Cassis reported an active \`D:\GHWallNative_20261121\GH_NATIVE_WALL_SINGLE_COMPOSITE_STAGE.gh\`
document with 18 components, 10 parameters and 31 connections. Its
\`mod=true\` flag means the current graph has unsaved changes.
**Do not close, replace, resave or steal focus from that document.**

## Operator-controlled deployment procedure

These are criteria for a separate, locally authorized deployment, **not steps
claimed as already performed**:

1. Confirm the signed APA release root and exactly its existing profile,
   the currently listening process for \`127.0.0.1:18787\`, and its startup
   command. Check active APA jobs and preserve rollback/backup records.
   Never assume a path from prior notes; do not print tunnel credentials.
2. Copy \`scripts/apa_cassis_compat_gateway.py\` into a separate experimental
   directory, preserving its SHA. Do **not** edit anything from the signed
   release manifest.
3. Create a separate, isolated \`experiments\` directory under the user's
   chosen working folder. For read-only testing, do not supply
   \`--gh-profile\`: this permanently disables \`gh-write\` for that process.
4. The original APA Control owns an exclusive job transport lock. **A sidecar
   using the same APA profile cannot run alongside the existing APA backend.**
   Do not kill the live process as a casual test. A controlled maintenance
   switch must first confirm the exact PID, startup command, zero unfinished
   writes, preserved configuration, and rollback. Only then can the new
   process replace the existing backend at the **same \`18787\` endpoint**,
   leaving tunnel authentication/configuration unchanged.
5. Example launcher shape once the actual paths have been verified:

   \`\`\`powershell
   py -3.11 -I -B -X utf8 ".\apa_cassis_compat_gateway.py" --release-root "EXACT_SIGNED_RELEASE_ROOT" --apa-profile "EXACT_EXISTING_APA_PROFILE" --gh-workdir "EXACT_EXPERIMENT_DIRECTORY" --port 18787
   \`\`\`

   Placeholder paths are deliberate: none was established by a permitted
   local file/path inspection. Do not copy this line verbatim.

6. Read \`apa_read(kind="status")\` and execute a fresh \`gh-read\` job
   from **this ChatGPT plugin**; inspect the actual Grasshopper document
   returned, verify same process/port, and read the receipt with
   \`apa_read(kind="job",job_id="...")\`.
7. For write testing, first **save a separate experimental GHX** in the chosen
   \`experiments\` directory without changing the unsaved live user graph.
   Pin its SHA-256 in a local JSON profile:

   \`\`\`json
   {
     "schema": "APA_GH_COMPAT_V1",
     "testDocument": "D:\\experiments\\apa-gh\\isolated.ghx",
     "documentSha256": "<64-character-current-sha256>",
     "allowWrites": true
   }
   \`\`\`

   The profile path must exist and its \`testDocument\` must reside inside
   \`--gh-workdir\` and contain an \`experiments\` directory segment.
   Restart gateway with \`--gh-profile\` only in another approved maintenance
   switch. With a different active document, all writes are blocked.
8. Author one \`gh-write\` request using a tool/argument schema returned by
   the real Cassis service, check the receipt and verify actual Grasshopper
   component count / connections. Save and reopen the isolated GHX; verify
   the model survived. Only after these observations can native **GH**
   acceptance be considered. Native **Archicad** acceptance is separate:
   Live Connection → test PLN → save → reopen → read-back.

## Safety, failure and rollback

- GH read allowlist and write allowlist are distinct. There is no generic
  Cassis forwarding; no C#/Python source editing, no arbitrary filesystem
  or shell tools, no natural-language command execution.
- The active GH document must be the pinned experiment for every write.
- Each request uses an immutable job ID, written before dispatch. An uncertain
  write is **never replayed** and blocks subsequent writes until manual
  reconciliation.
- The existing signed APA/PLN stays unchanged. The original backend can be
  restored with its *recorded exact original command* after stopping the
  experimental proxy. Do not fabricate or guess restart arguments.
- A local test passing on GitHub Actions is **not** evidence that the installed
  tunnel or active Rhino/Grasshopper document was changed.

## Automated tests

\`\`\`text
python -m py_compile scripts/apa_cassis_compat_gateway.py
python -m unittest discover -s tests -p test_apa_cassis_compat_gateway.py -v
\`\`\`

The GitHub-hosted workflow \`apa-cassis-compat-gateway.yml\` verifies syntax and
15 isolated guard/idempotency tests. It does not start Rhino or Archicad.
