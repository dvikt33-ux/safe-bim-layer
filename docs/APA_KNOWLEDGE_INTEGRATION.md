# Existing knowledge graph in APA

PR69 merge `64cec581b257b209a097556ae19d498e53631ba1` is the component source. The entire `tools/apa_knowledge_graph` subtree is brought into the exact PR70 base unchanged, with runtime file hashes in `schemas/accelerator/apa_knowledge_component_lock.json`. This is one component shared by core and MCP, not a second search engine, task controller, publisher or normative executor.

## Working core entry points

`archicad_project_accelerator.retrieve_project_knowledge(config, query, mode, remote=None)` calls the existing SnapshotService/gateway. `inspect_project_knowledge` exposes original scheduling dependency/possible artifact impact/delta contracts, a source-bound TDK trace and explicit small source fragments. Query text is data, never executable instructions. The optional imports do not execute when the feature is disabled.

Start from `examples/apa_knowledge_access.config.json`: `enabled` is false. Operator-owned paths, source class allowlist, response ceiling and optional exact code commit cannot be supplied through the MCP tool. `LOCAL_CHECKOUT` explicitly has local authority only. `GITHUB_CURRENT` requires independent current canonical commit + plan byte verification on each request; returned excerpts are checked against that commit. Private repository read credentials come from `APA_GITHUB_READ_TOKEN`, never a query argument or published config.

The existing bootstrap builds disposable indexes outside the source checkout. Current plan fingerprints and an independently reconstructed original graph reject stale or forged index contents. Remote failures never downgrade to local/cached authority. A changed remote plan yields `STALE_INDEX_REMOTE_PLAN`; fetch the canonical branch in the operator-owned checkout and rebuild through the existing bootstrap. No automatic task claim or status update follows from a suggestion.

Registered ART/PR/report/receipt pointers preserve their original verification labels; a registry label is not new live/native/normative acceptance. Scheduling edges, shared document references and semantic/engineering dependencies remain distinct. TDK uses the existing ExistingMachineSource protocol-first byte checks and original machine_adapter route/release/whitelist checks; quarantined design_only remains non-authoritative. No source rules or normative evaluator are changed.

Explicit source fragments require an operator allowlist, at most20 lines, and optionally a separately pinned code checkout. GitHub bytes supply the excerpt/hash. A Windows CRLF checkout matching GitHub LF is labeled as a line-ending difference, never a byte-exact local match. The existing search library still indexes Markdown only; no code indexer is added.

## Local installation and real MCP test

Use Python3.11 in a standard virtual environment, which loads the SDK's Windows `.pth`/pywin32 dependencies correctly. Install `scripts/requirements-connected.txt` and optional `scripts/requirements-knowledge.txt`. Keep a separate canonical research checkout with PROJECT_PLAN and artifacts. Configure its absolute root and an outside cache folder in a local operator config; turn on the flag.

```text
python scripts/archicad_knowledge_access.py rebuild --config OPERATOR_CONFIG.json
python scripts/archicad_knowledge_access.py query --config OPERATOR_CONFIG.json --query APA-P70.A11.S03 --mode research
python scripts/archicad_knowledge_access.py mcp --config OPERATOR_CONFIG.json
python scripts/apa_knowledge_integration_smoke.py --corpus CANONICAL_CHECKOUT --output NEW_EVIDENCE_DIRECTORY
```

For a stdio-capable client, set its command to the virtual environment's Python executable, with arguments `scripts/archicad_knowledge_access.py mcp --config OPERATOR_CONFIG.json` using operator-owned absolute paths. Only `apa_retrieve` is exposed. The smoke launches a separate server process, negotiates with the official MCP2.3 client and calls task/artifact queries plus a denied source class over pipes. It is a real transport test; no BIM/task write tools exist.

## ChatGPT connection boundary

Local stdio acceptance is separate from an actual call inside this ChatGPT environment. This package does not register a server, open a port or start a tunnel. Current official [connection instructions](https://developers.openai.com/plugins/deploy/connect-chatgpt) support a reachable HTTPS MCP endpoint or Secure MCP Tunnel. The existing stdio command can be forwarded using [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), subject to the user's account/workspace association and operator credentials.

Operator steps when that facility is available: create an endpoint in Platform tunnel settings; configure the tunnel client with this exact stdio command; start the client; in ChatGPT Plugins choose Add custom MCP server → Tunnel and select the associated endpoint; install/select the resulting plugin and call `apa_retrieve` for a known S-ID. Accept only after that target environment returns the expected current plan provenance. Account/workspace association and tunnel availability have not been verified here. No paid API/model calls or external deployment are performed.

## Quality and context measurements

Preserve PR69 benchmarks. This package adds measurements for the actual core calls and stdio payloads: correctness against original plan records, response time, GitHub call count and transmitted bytes/characters; `tiktoken:o200k_base` is a tokenizer proxy, not actual GPT billing. Freshness checks can increase network calls/latency even when payloads shrink. No universal saving or independent semantic recall claim follows from exact-ID tests. The80-question independent semantic benchmark remains a separate proposal, not a prerequisite for the working narrow integration.

No Archicad calls are made. PR70's documentation, BIM Graph, SceneWriter and existing normative functions are protected by the full APA suite. A11.S03 can publish this completed package while retaining unrelated native blockers and remaining PARTIAL.
