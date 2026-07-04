"""The consent machinery: proposals and arming (§4 rings 2 and 3).

Every steering act — a story flip, a text relay, a launch, a project
lifecycle step — is a *proposal*: an explicit preview sent to chat,
executed only when the owner taps approval on that exact proposal.
Proposals are single-use, expire, and die with the process (a
restart voids anything not yet approved — the safe default).

Arming is the ring-3 boundary, engineered rather than promised:
per-tmux-session, default TTL 15 minutes, capped, auto-expiring at
the moment of use, visible via status, revocable in one message,
everything off by default. It persists in runtime state so a
restart cannot silently *lose* the owner's view of what is armed —
expiry is enforced on every read either way.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from .runtime import RuntimeState, iso, parse_iso

PROPOSAL_TTL_SECONDS = 15 * 60
ARM_DEFAULT_MINUTES = 15  # §4 ring 3
ARM_MAX_MINUTES = 60


class Proposal:
    def __init__(
        self, kind: str, preview: str, payload: dict, expires_at: datetime
    ) -> None:
        self.id = secrets.token_hex(4)
        self.kind = kind
        self.preview = preview
        self.payload = payload
        self.expires_at = expires_at


class ProposalBook:
    """In-memory, single-use, expiring proposals."""

    def __init__(self) -> None:
        self._open: dict[str, Proposal] = {}

    def add(
        self, kind: str, preview: str, payload: dict, now: datetime
    ) -> Proposal:
        proposal = Proposal(
            kind,
            preview,
            payload,
            now + timedelta(seconds=PROPOSAL_TTL_SECONDS),
        )
        self._open[proposal.id] = proposal
        return proposal

    def take(self, proposal_id: str, now: datetime) -> Proposal | None:
        """Claim a proposal for execution — single use, expiry-checked."""
        proposal = self._open.pop(proposal_id, None)
        if proposal is None or now > proposal.expires_at:
            return None
        return proposal

    def discard(self, proposal_id: str) -> bool:
        return self._open.pop(proposal_id, None) is not None


class Arming:
    """Per-session, visible, expiring grants over tmux sessions."""

    def __init__(self, state: RuntimeState) -> None:
        self._state = state

    def arm(
        self, session: str, now: datetime, minutes: int = ARM_DEFAULT_MINUTES
    ) -> datetime:
        minutes = max(1, min(int(minutes), ARM_MAX_MINUTES))
        expires = now + timedelta(minutes=minutes)
        self._state.armed[session] = iso(expires)
        self._state.save()
        return expires

    def disarm(self, session: str) -> bool:
        present = session in self._state.armed
        if present:
            del self._state.armed[session]
            self._state.save()
        return present

    def is_armed(self, session: str, now: datetime) -> bool:
        expires = parse_iso(self._state.armed.get(session))
        if expires is None or now > expires:
            if session in self._state.armed:
                del self._state.armed[session]
                self._state.save()
            return False
        return True

    def status(self, now: datetime) -> list[tuple[str, str]]:
        """(session, expires-at) for every currently armed session."""
        out = []
        for session in sorted(self._state.armed):
            if self.is_armed(session, now):
                out.append((session, self._state.armed[session]))
        return out
