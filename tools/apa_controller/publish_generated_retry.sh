#!/usr/bin/env bash
# Rebuild canonical controller views from the latest GitHub plan on push races.
# Never force-push, alter main, or touch PLN/APX.
set -euo pipefail
branch='research/apa-verified-results-hub-20261010'
ref="refs/heads/${branch}"
projection_path='docs/research/apa-results/control/generated'
if [[ "${GITHUB_REF:-}" != "$ref" || "${GITHUB_REPOSITORY:-}" != 'dvikt33-ux/safe-bim-layer' ]]; then
  echo 'CONTROLLER_PUSH_BLOCKED: not canonical GitHub Actions context' >&2
  exit 2
fi
if [[ ! -n "${GITHUB_OUTPUT:-}" ]]; then
  echo 'CONTROLLER_PUSH_BLOCKED: missing GITHUB_OUTPUT' >&2
  exit 2
fi
if ! git diff --quiet || ! git diff --cached --quiet; then
  if git diff --name-only HEAD | grep -v -E "^${projection_path}/" | grep -q .; then
    echo 'CONTROLLER_PUSH_BLOCKED: unexpected tracked changes' >&2
    exit 2
  fi
fi
# All earlier immutable reports/receipts must already be committed and verified.
anchor="$(git rev-parse HEAD)"
max_attempts=4
for ((attempt=1; attempt<=max_attempts; attempt++)); do
  python tools/apa_controller/controller.py validate
  python tools/apa_controller/controller.py verify-inbox
  python tools/apa_controller/controller.py build
  git add -A -- "$projection_path"
  if ! git diff --cached --quiet; then
    git commit -m 'ops(APA): rebuild authoritative task board and cross-chat context'
  fi
  if git push origin "HEAD:${ref}"; then
    echo "CONTROLLER_PUSH_VERIFIED_FAST_FORWARD attempt=${attempt}"
    echo "sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  echo "CONTROLLER_PUSH_RACE attempt=${attempt} retrying latest controller state" >&2
  if (( attempt == max_attempts )); then
    echo 'CONTROLLER_PUSH_BLOCKED: bounded retry budget exhausted' >&2
    exit 1
  fi
  git fetch --no-tags origin "$ref"
  if ! git merge-base --is-ancestor "$anchor" FETCH_HEAD; then
    echo 'CONTROLLER_PUSH_BLOCKED: original verified anchor absent from remote' >&2
    exit 1
  fi
  if [[ "$(git rev-list --count "${anchor}..HEAD")" -gt 1 ]]; then
    echo 'CONTROLLER_PUSH_BLOCKED: unexpected local commits since verified anchor' >&2
    exit 1
  fi
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo 'CONTROLLER_PUSH_BLOCKED: dirty checkout before regeneration' >&2
    exit 1
  fi
  # Only discard unpushed generated-view commit in ephemeral GitHub Actions.
  git reset --hard FETCH_HEAD
  anchor="$(git rev-parse HEAD)"
done
