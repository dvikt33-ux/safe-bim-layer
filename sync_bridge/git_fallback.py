"""Narrow git fetch of one bridge ref. Not pull, reset, or a full sync."""
from __future__ import annotations

import re

NEEDS_AUTH = 'NEEDS_AUTH'
_SECRET = re.compile(r'(ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|Bearer\s+\S+|token[=:]\S+)', re.I)


class GitFallbackError(RuntimeError):
    pass


def redact(text: str) -> str:
    return _SECRET.sub('[redacted]', text or '')


def narrow_fetch(ref: str, runner) -> dict:
    if not isinstance(ref, str) or not ref or ref.startswith('-') or '..' in ref:
        raise GitFallbackError('refused ref')
    argv = ['git', 'fetch', 'origin', ref]
    if any(word in argv for word in ('pull', 'reset', '--all')):
        raise GitFallbackError('broad git sync is refused')
    result = runner(argv)
    stderr = redact(getattr(result, 'stderr', '') or '')
    if any(marker in stderr.lower() for marker in ('authentication', 'could not read username', 'invalid credentials', 'auth')):
        return {'status': NEEDS_AUTH, 'argv': argv, 'stderr': stderr}
    if getattr(result, 'code', 1) != 0:
        return {'status': 'ERROR', 'argv': argv, 'stderr': stderr}
    return {'status': 'FETCHED', 'argv': argv, 'stderr': stderr}
