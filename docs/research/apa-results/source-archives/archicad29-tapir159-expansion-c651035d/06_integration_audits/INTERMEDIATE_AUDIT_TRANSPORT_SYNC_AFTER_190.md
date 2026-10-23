# INTERMEDIATE AUDIT — transport/sync after pass 190

Date: 2026-09-28

## Audit question
What is the fastest architecture that still lets ordinary ChatGPT understand current Archicad state and send work back, while keeping setup nearly invisible to the user?

## Confirmed conclusions

### 1. Pure local is fastest, but incomplete for ordinary ChatGPT
Local named-pipe IPC is the correct transport between the Archicad palette, Safe BIM bridge and local cache. It should be effectively independent of Internet availability for local QA, history, recipes, selection and execution.

However, ordinary ChatGPT cannot simply open an arbitrary local Git clone on the workstation. Desktop Work can be granted local-file access, but that is not the desired routine workflow. Current custom MCP documentation also states that local MCP is not directly connected; a secure tunnel/remote path is needed.

Therefore a purely local Git repository cannot by itself close the ChatGPT ↔ Archicad loop.

### 2. GitHub Desktop is not the runtime bridge
The local clone can be useful, but GitHub Desktop is not a queue API and must not be required to stay open. The bridge should use its own local service and standard Git/API mechanisms.

### 3. Webhooks are not the v0.1 default
GitHub recommends webhooks over polling where practical, but receiving a webhook on a workstation requires reachable HTTPS infrastructure. Development relays are not production mechanisms; public tunnels add setup and attack surface.

For the user's explicit `open Archicad → open Safe BIM → work` requirement, webhook infrastructure loses to conditional polling for v0.1.

### 4. Preferred v0.1 remote wake mechanism
Authenticated ETag/If-None-Match polling of one tiny queue-head resource, with adaptive cadence and immediate request on explicit AI operations.

Fallback: narrow Git fetch if standard Git authentication is already operational and API authentication is not available.

### 5. GitHub must carry minimal task context, not the whole live model
The earlier continuous-cloud-snapshot idea is unnecessarily expensive. A local authoritative mirror should stay current. GitHub should receive coherent task snapshots only when an AI request needs them, plus compact queue/result envelopes.

## Risks discovered

- Auth cannot be magically absent for a private remote repository on a completely fresh machine. Embedding a permanent token is unacceptable.
- GitHub Desktop authentication cannot be assumed to be a stable public API for another process.
- Polling too aggressively without conditional requests can hit secondary limits.
- Webhook relay creates a public-ingress dependency and a secret-management problem.
- A cloud snapshot can become stale while ChatGPT is generating a plan.

## Required next passes

1. design an out-of-box auth bootstrap without user-created PATs;
2. design a request-driven fresh-context handshake;
3. design a model-change lease / stale-context protocol;
4. distinguish mechanical auto-actions from AI-generated writes;
5. define offline behavior;
6. define install/startup lifecycle so no PowerShell/manual services are required.

**Intermediate verdict:** local-first hybrid remains the strongest architecture, but auth/bootstrap and fresh-context handshake need to be solved before implementation.