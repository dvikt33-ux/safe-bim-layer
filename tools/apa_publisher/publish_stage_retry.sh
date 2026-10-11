#!/usr/bin/env bash
# Retry only the first TWO APA Publisher stages. Verified report commit is
# never rewritten. GitHub Actions canonical branch only; no force pushes.
set -euo pipefail
stage="${1:-}"
report_commit="${2:-}"
branch='research/apa-verified-results-hub-20261010'
ref="refs/heads/${branch}"
root='docs/research/apa-results'
if [[ "$stage" != 'reports' && "$stage" != 'receipts' ]]; then
  echo 'APA_STAGE_BLOCKED: stage must be reports or receipts' >&2; exit 2
fi
if [[ "${GITHUB_REF:-}" != "$ref" ||
      "${GITHUB_REPOSITORY:-}" != 'dvikt33-ux/safe-bim-layer' ||
      -z "${GITHUB_OUTPUT:-}" ]]; then
  echo 'APA_STAGE_BLOCKED: wrong workflow authority' >&2; exit 2
fi
if [[ "$stage" == 'receipts' && ! "$report_commit" =~ ^[a-f0-9]{40}$ ]]; then
  echo 'APA_STAGE_BLOCKED: missing pinned verified report commit' >&2; exit 2
fi
if [[ "$stage" == 'reports' ]]; then
  dirs=("$root/runs" "$root/generated")
  allowed="^($root/runs|$root/generated)/"
else
  dirs=("$root/receipts")
  allowed="^$root/receipts/"
fi
if git diff --name-only HEAD | grep -v -E "$allowed" | grep -q .; then
  echo 'APA_STAGE_BLOCKED: unrelated tracked edits' >&2; exit 2
fi
anchor="$(git rev-parse HEAD)"
for attempt in 1 2 3 4; do
  if [[ "$stage" == 'reports' ]]; then
    python tools/apa_controller/controller.py validate
    python tools/apa_controller/controller.py verify-inbox
    # Rebuild pending hashes against the latest remote source after retries.
    python tools/apa_publisher/publisher.py prepare
  else
    git merge-base --is-ancestor "$report_commit" HEAD || {
      echo 'APA_STAGE_BLOCKED: verified report commit missing' >&2; exit 1;
    }
    python tools/apa_publisher/publisher.py receipt --commit "$report_commit"
  fi
  git add -A -- "${dirs[@]}"
  if ! git diff --cached --quiet; then
    if [[ "$stage" == 'reports' ]]; then
      git commit -m 'ops(APA): publish immutable V2 runs and generated projections'
    else
      git commit -m 'ops(APA): record GitHub-verified V2 publication receipts'
    fi
  fi
  if git push origin "HEAD:$ref"; then
    echo "APA_STAGE_FAST_FORWARD stage=$stage attempt=$attempt"
    echo "sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  if [[ "$attempt" == '4' ]]; then
    echo "APA_STAGE_BLOCKED: bounded retry exhausted stage=$stage" >&2; exit 1
  fi
  git fetch --no-tags origin "$ref"
  remote="$(git rev-parse FETCH_HEAD)"
  if [[ "$remote" == "$anchor" ]]; then
    echo 'APA_STAGE_BLOCKED: rejected push without remote advancement' >&2; exit 1
  fi
  git merge-base --is-ancestor "$anchor" "$remote" || {
    echo 'APA_STAGE_BLOCKED: original anchor missing, never force push' >&2; exit 1;
  }
  if [[ "$stage" == 'receipts' ]]; then
    git merge-base --is-ancestor "$report_commit" "$remote" || {
      echo 'APA_STAGE_BLOCKED: verified report commit displaced' >&2; exit 1;
    }
  fi
  if ! git diff --quiet "$anchor" "$remote" -- tools/apa_publisher tools/apa_controller .github/workflows/apa-research-publisher.yml; then
    echo 'APA_STAGE_BLOCKED: executable code changed since validation' >&2; exit 1
  fi
  # New immutable files are allowed. Changes/deletions to old files are not.
  if git diff --name-status "$anchor" "$remote" -- "$root/runs" "$root/receipts" |
     awk '$1 != "A" {bad=1} END {exit !bad}'; then
    echo 'APA_STAGE_BLOCKED: existing immutable report or receipt mutated' >&2; exit 1
  fi
  count="$(git rev-list --count "${anchor}..HEAD")"
  if [[ "$count" -gt 1 ]]; then
    echo 'APA_STAGE_BLOCKED: multiple local commits after anchor' >&2; exit 1
  fi
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo 'APA_STAGE_BLOCKED: dirty checkout before retry' >&2; exit 1
  fi
  echo "APA_STAGE_RACE stage=$stage attempt=$attempt"
  # Reset ONLY the ephemeral Actions checkout, not the remote branch.
  git reset --hard "$remote"
  anchor="$remote"
done
