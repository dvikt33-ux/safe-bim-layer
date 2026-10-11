#!/usr/bin/env python3
"""Read-only canonical APA Publisher workflow health check.

A scheduled GitHub Actions run fails if the newest canonical Publisher run
failed/cancelled/needs action or is stuck >45 minutes. No GitHub writes,
no Slack tokens, no claim/status changes and no local Archicad dependency.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "dvikt33-ux/safe-bim-layer"
BRANCH = "research/apa-verified-results-hub-20261010"
WORKFLOW = "apa-research-publisher.yml"
MAX_ACTIVE_MINUTES = 45
ACTIVE = {"queued", "in_progress", "pending", "waiting", "requested"}
GOOD = {"success"}
FAIL = {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}


class WatchdogError(RuntimeError):
    pass


def parse_utc(value):
    if not isinstance(value, str) or not value:
        raise WatchdogError("Missing workflow timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WatchdogError("Invalid workflow timestamp") from exc
    if result.tzinfo is None:
        raise WatchdogError("Workflow timestamp lacks timezone")
    return result.astimezone(timezone.utc)


def inspect(runs, now=None, max_active_minutes=MAX_ACTIVE_MINUTES):
    """Inspect newest branch-scoped run; older failures do not poison new success."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(runs, list) or not runs:
        raise WatchdogError("No canonical publisher workflow runs")
    canonical = []
    for run in runs:
        if not isinstance(run, dict):
            raise WatchdogError("Malformed Publisher run")
        if run.get("head_branch") == BRANCH:
            if not isinstance(run.get("id"), int) or run["id"] <= 0:
                raise WatchdogError("Invalid Publisher run ID")
            canonical.append(run)
    if not canonical:
        raise WatchdogError("No Publisher runs on canonical branch")
    # GitHub API promises newest-first but determine by timestamp ourselves.
    newest = max(canonical, key=lambda r: (parse_utc(r.get("created_at")), r["id"]))
    status = newest.get("status")
    conclusion = newest.get("conclusion")
    created = parse_utc(newest.get("created_at"))
    seconds = (now - created).total_seconds()
    if seconds < -300:
        raise WatchdogError("Publisher run timestamp lies in future")
    minutes = max(0, seconds / 60)
    proof = {"run_id": newest["id"], "status": status, "conclusion": conclusion,
             "age_minutes": round(minutes, 1),
             "run_url": f"https://github.com/{REPO}/actions/runs/{newest['id']}"}
    if status in ACTIVE:
        if minutes > max_active_minutes:
            return {**proof, "health": "STUCK", "reason": "Publisher has been active too long"}
        return {**proof, "health": "RUNNING", "reason": "Publisher currently processing"}
    if status != "completed":
        raise WatchdogError("Unknown Publisher status: " + repr(status))
    if conclusion in GOOD:
        return {**proof, "health": "HEALTHY", "reason": "Latest Publisher completed successfully"}
    if conclusion in FAIL:
        return {**proof, "health": "FAILED", "reason": "Latest Publisher requires recovery"}
    raise WatchdogError("Unknown completed Publisher conclusion: " + repr(conclusion))


def fetch_runs(token):
    if not token:
        raise WatchdogError("GITHUB_TOKEN is required")
    url = (f"https://api.github.com/repos/{REPO}/actions/workflows/"
           f"{WORKFLOW}/runs?branch={quote(BRANCH, safe='')}&per_page=30")
    request = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "APA-Publisher-Watchdog",
    })
    try:
        with urlopen(request, timeout=20) as response:
            data = response.read(1048577)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise WatchdogError("GitHub API unavailable") from exc
    if len(data) > 1048576:
        raise WatchdogError("GitHub API response too large")
    try:
        obj = json.loads(data)
    except (UnicodeDecodeError, ValueError) as exc:
        raise WatchdogError("Invalid GitHub API JSON") from exc
    if not isinstance(obj, dict) or not isinstance(obj.get("workflow_runs"), list):
        raise WatchdogError("Invalid GitHub Actions API schema")
    return obj["workflow_runs"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-active-minutes", type=int, default=MAX_ACTIVE_MINUTES)
    args = parser.parse_args()
    if not (15 <= args.max_active_minutes <= 180):
        parser.error("invalid active timeout")
    try:
        outcome = inspect(fetch_runs(os.environ.get("GITHUB_TOKEN")), max_active_minutes=args.max_active_minutes)
        healthy = outcome["health"] in {"HEALTHY", "RUNNING"}
    except WatchdogError as exc:
        outcome = {"health": "UNKNOWN", "reason": str(exc)}
        healthy = False
    text = json.dumps(outcome, ensure_ascii=False, sort_keys=True)
    print(text, flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("### APA Publisher watchdog\n\n\`\`\`json\n" + json.dumps(outcome, indent=2) + "\n\`\`\`\n")
    if not healthy:
        sys.exit(1)


if __name__ == "__main__":
    main()
