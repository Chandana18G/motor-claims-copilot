"""Staff identities, roles and signed tokens.

A deployment would take identities from the insurer's identity provider (SSO). This module
stands in for that: tokens are HMAC-signed by a key the AI components never receive, carry a
role and an expiry, and are re-checked against the staff directory on every use, so a revoked
or re-roled person loses authority immediately.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import asdict, dataclass

ROLES = ("adjuster", "supervisor", "investigator", "auditor", "governance")


class AuthorityError(Exception):
    """Raised when a step would bypass human decision authority."""


@dataclass(frozen=True)
class Token:
    staff_id: str
    role: str
    expires: float
    mac: str


def _mac(key: bytes, payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, default=str).encode()
    return hmac.new(key, body, hashlib.sha256).hexdigest()


class Directory:
    def __init__(self, key: bytes | None = None, ttl_seconds: float = 8 * 3600):
        self._key = key or os.urandom(32)
        self._ttl = ttl_seconds
        self._staff: dict[str, str] = {}

    def register(self, staff_id: str, role: str) -> None:
        if role not in ROLES:
            raise ValueError(f"Unknown role {role!r}")
        self._staff[staff_id] = role

    def revoke(self, staff_id: str) -> None:
        self._staff.pop(staff_id, None)

    def issue(self, staff_id: str, now: float | None = None) -> Token:
        if staff_id not in self._staff:
            raise AuthorityError(f"{staff_id} is not a registered member of staff")
        expires = (time.time() if now is None else now) + self._ttl
        role = self._staff[staff_id]
        return Token(staff_id, role, expires, _mac(self._key, {"s": staff_id, "r": role, "e": expires}))

    def verify(self, token: object, now: float | None = None) -> Token:
        if not isinstance(token, Token):
            raise AuthorityError("A signed staff token is required")
        expected = _mac(self._key, {"s": token.staff_id, "r": token.role, "e": token.expires})
        if not hmac.compare_digest(expected, token.mac):
            raise AuthorityError("Token signature is invalid")
        if (time.time() if now is None else now) > token.expires:
            raise AuthorityError("Token has expired")
        if self._staff.get(token.staff_id) != token.role:
            raise AuthorityError("Token role no longer matches the staff directory")
        return token

    def seal(self, record: object) -> str:
        return _mac(self._key, {"sealed": asdict(record) if hasattr(record, "__dataclass_fields__") else record})

    def check_seal(self, record: object, seal: str) -> bool:
        return hmac.compare_digest(self.seal(record), seal)
