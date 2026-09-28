"""Per-user pipe admission. A foreign Windows session is not a peer.

Session isolation remains the policy. Several Archicad instances may share
this user session; a different SID or session is still denied.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PeerIdentity:
    user_sid: str
    session_id: str


def sddl_for_user(user_sid: str) -> str:
    """Protected DACL: only this user SID gets generic-all. No Everyone, no remote."""
    if not isinstance(user_sid, str) or not user_sid.startswith('S-1-'):
        raise ValueError('user SID required')
    return f'D:P(A;;GA;;;{user_sid})'


SESSION_ISOLATION = True


def admit_peer(owner: PeerIdentity, peer: PeerIdentity) -> bool:
    return (isinstance(peer.user_sid, str) and isinstance(peer.session_id, str)
            and peer.user_sid == owner.user_sid and peer.session_id == owner.session_id
            and peer.session_id != '' and peer.user_sid != '')
