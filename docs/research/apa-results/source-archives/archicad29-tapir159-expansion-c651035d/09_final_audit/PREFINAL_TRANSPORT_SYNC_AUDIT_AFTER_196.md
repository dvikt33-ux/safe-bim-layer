# PREFINAL AUDIT — transport/sync after pass 196

Date: 2026-09-28

## Objective
Choose the remote/local communication model that is fastest in daily work, preserves safety, and meets the UX requirement: start Archicad, open Safe BIM, work — no PowerShell, no manual keys, no helper windows.

## Candidate matrix

### A. Pure local Git / local files
**Speed:** excellent.
**Setup:** excellent locally.
**Ordinary ChatGPT visibility:** insufficient.
**Verdict:** use internally only; cannot be the complete ChatGPT bridge.

### B. GitHub Desktop as runtime bridge
**Speed:** acceptable when synchronized.
**Determinism:** weak; desktop client is not a queue API.
**Out-of-box:** tempting because already installed, but coupling to its UI/background behavior is brittle.
**Verdict:** do not depend on GitHub Desktop. Reuse existing auth if available, but own the bridge lifecycle.

### C. Private GitHub + full git fetch/push polling
**Speed:** adequate.
**Auth:** can reuse standard Git/GCM.
**Overhead:** heavier than REST conditional polling.
**Verdict:** strong fallback transport.

### D. Private GitHub + authenticated ETag polling
**Speed:** adequate for 1–5 s active-wait cadence.
**Network overhead:** minimal when unchanged.
**Rate-limit posture:** good when conditional and serialized.
**Auth:** must be solved once.
**Verdict:** preferred v0.1 remote wake channel.

### E. Direct webhook
**Speed:** strongest cloud-to-local notification model.
**Out-of-box:** poor without a stable inbound endpoint.
**Security/setup:** requires HTTPS endpoint and webhook secret.
**Verdict:** not v0.1 default.

### F. Smee / ngrok / Cloudflare Tunnel / Tailscale Funnel
**Speed:** webhook-class.
**Out-of-box:** adds agent/account/service and public ingress.
**Reliability:** another dependency.
**Verdict:** optional experimentation only; not required runtime.

### G. GitHub Actions self-hosted runner
**Speed:** push-like job assignment.
**Security:** grants a generic remote workflow execution surface on the BIM workstation.
**Complexity:** high.
**Verdict:** reject.

### H. custom ChatGPT local MCP
Current product constraints do not make a direct local MCP connection in ordinary Chat the simple path. Supported local/private MCP requires a tunnel, and full MCP write capabilities are plan/product dependent.
**Verdict:** not core architecture for this user workflow today.

## Prefinal architecture decision

**LOCAL-FIRST HYBRID**

```text
Archicad Add-On
  ↕ Named Pipe
Safe BIM Bridge
  ↕
SQLite / local hot cache / job journal
  ↕
Private GitHub bridge repo (minimal task envelopes)
  ↕
ordinary ChatGPT GitHub connector
```

### Critical refinement: request-driven context, not continuous cloud export
ChatGPT should issue a `CONTEXT_REQUEST` before generating project-dependent code/recipe. The extension publishes a task-bound coherent snapshot from its already-hot local cache. This eliminates thousands of background commits while guaranteeing much fresher state.

### Safety contract
No remote job may write until:
- project identity matches;
- context lease/snapshot matches;
- target state hashes match;
- operation capability is certified;
- duplicate job ID is rejected;
- requested automation level allows that class of action.

Mechanical trusted recipes remain local and automatic. Novel AI-generated writes default to preview/confirmation/sandbox.

## Remaining uncertainties before final audit

1. exact measured latency of ETag poll + context publish on the user's network;
2. whether current Windows Git/GCM credentials can be reused silently on this specific workstation;
3. whether task-context GitHub connector round-trip can complete within one assistant turn reliably enough for request-driven context;
4. final UI text/timing for context lease warning;
5. recovery behavior when Internet disappears midway through a request.

These are implementation/live measurements, not unresolved architectural questions.