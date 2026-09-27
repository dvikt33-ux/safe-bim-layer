# TRANSPORT / SYNC RESEARCH — passes 181–190

Date: 2026-09-28
Scope: quickest and safest connection between ordinary ChatGPT, Safe BIM and Archicad while preserving an out-of-box UX.
No product code changes. No Live BIM writes.

## Pass 181 — pure local bridge feasibility
A pure local path is ideal for Palette ↔ Safe BIM runtime because it removes network latency and external failure modes. Windows named pipes are a strong candidate for full-trust desktop processes; they support duplex IPC and ACL-based access control. Local filesystem notifications are a secondary option for queue folders.

Decision: use local IPC for all components on the workstation. Do not use GitHub between the Archicad palette and local Safe BIM runtime.

## Pass 182 — can ordinary ChatGPT read a local Git repo directly?
Current OpenAI product documentation says ordinary ChatGPT does not directly connect to a local MCP server; local/private MCP requires a supported secure tunnel. Desktop Work can access local files when permission is granted, but web/mobile Work cannot directly access local computer files. This project intentionally avoids consuming Work for routine BIM interaction.

Decision: for the current ordinary-Chat workflow, a purely local Git repository is not sufficient to make project state readable by ChatGPT. Some cloud-visible bridge or supported remote connector is required.

## Pass 183 — GitHub Desktop as transport
GitHub Desktop is a GUI client around Git repositories and authentication, not a deterministic message transport API. A local clone is useful as cache/history, but ChatGPT cannot see an unpushed local commit. Relying on GitHub Desktop background fetch/push timing would create undefined latency and state freshness.

Decision: GitHub Desktop may help bootstrap authentication, but Safe BIM must not depend on the GitHub Desktop process or UI for queue delivery.

## Pass 184 — private GitHub cloud round-trip
A private repository remains a practical cross-boundary mailbox because ChatGPT already has a GitHub connector and Safe BIM can publish/fetch small machine-readable files. Git commits provide a coherent external transaction boundary.

Decision: use GitHub only for the WAN boundary ChatGPT ↔ workstation, not for high-frequency intra-workstation traffic.

## Pass 185 — REST conditional polling
GitHub explicitly recommends authenticated conditional requests with ETag/If-None-Match for polling; unchanged 304 responses avoid primary-rate-limit cost. Requests should be serialized and back off on secondary limits.

Decision: conditional polling is the preferred v0.1 remote notification mechanism if Safe BIM has authenticated API access.

## Pass 186 — direct GitHub webhook to workstation
Webhooks are event-driven and reduce polling, but GitHub must be able to reach an HTTPS endpoint. A normal workstation behind NAT/firewall does not provide that endpoint automatically. Webhook signatures must be validated with a secret.

Decision: direct webhook is excellent technically but conflicts with the zero-manual-setup/no-public-ingress requirement unless a relay/tunnel is provisioned automatically.

## Pass 187 — webhook relay/tunnel alternatives
GitHub documents Smee for development only and explicitly says not to use it in production. Tailscale Funnel, ngrok, Cloudflare Tunnel and similar systems can expose a local receiver, but each adds another agent/account/service, security surface and setup/availability dependency.

Decision: reject third-party tunnel as mandatory architecture. Keep webhook relay as an optional future acceleration layer only.

## Pass 188 — self-hosted GitHub Actions runner as push-like transport
A self-hosted runner maintains outbound connectivity and can receive jobs, but it is a much larger execution environment than a mailbox watcher. GitHub warns about persistent compromise risk on self-hosted runners. It would also require runner registration/configuration.

Decision: reject for Safe BIM transport. Too heavyweight and too much remote execution authority.

## Pass 189 — Git fetch polling vs REST polling
A dedicated local clone can `git fetch` using Git/GCM credentials and avoids writing an API token into the add-on. However fetch is a heavier protocol operation than an ETag check and creates more repository plumbing. It is still a useful fallback when API auth is unavailable but ordinary Git auth already works.

Decision:
1. preferred: authenticated conditional REST head check;
2. fallback: narrow `git fetch` of the bridge branch;
3. never use full repository pull/reset for each poll.

## Pass 190 — local first / cloud minimal architecture
The winning split is:

```text
Archicad Palette
  ↕ local named pipe
Safe BIM Bridge Service
  ↕
SQLite + local context cache + local queue
  ↕ only coherent request/response envelopes
Private GitHub bridge repository
  ↕
ChatGPT GitHub connector
```

The project model is read and indexed locally. The cloud contains only the context needed for a task, not a continuously streamed copy of every edit.

### Source notes
- GitHub webhook handling/validation/best practices: official GitHub docs.
- GitHub conditional REST requests/rate-limit best practices: official GitHub docs.
- Git Credential Manager storage/auth: official GCM/GitHub docs.
- Windows named pipes and directory change notifications: Microsoft Learn.
- Local ChatGPT/MCP/local-file limitations: current OpenAI Help Center.
