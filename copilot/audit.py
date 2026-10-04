"""Append-only audit log with a keyed hash chain and external anchors.

* Each entry stores an HMAC-SHA256 over its content and the previous entry's MAC, so editing,
  deleting, inserting or reordering entries breaks verification. Without the key an attacker
  cannot recompute valid MACs (a plain SHA-256 chain can simply be recomputed).
* ``checkpoint()`` returns the current head, which is written to a separate store the log's
  operators cannot rewrite (in production: a WORM bucket, a ticketing system or a notary).
  Even an insider who holds the key and rebuilds the whole chain is caught, because the rebuilt
  chain no longer matches the anchored heads.
* Timestamps must not go backwards, so back-dated insertions are rejected on append and flagged
  on verification.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

GENESIS = "0" * 64


def _mac(key: bytes, entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "mac"}
    data = json.dumps(body, sort_keys=True, default=str).encode()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class Anchor:
    seq: int
    mac: str
    time: str


@dataclass
class AnchorStore:
    """Stand-in for an external, append-only store of chain heads."""

    anchors: list[Anchor] = field(default_factory=list)

    def record(self, anchor: Anchor) -> None:
        if self.anchors and anchor.seq < self.anchors[-1].seq:
            raise ValueError("Anchors must move forward")
        self.anchors.append(anchor)


class AuditLog:
    def __init__(self, key: bytes | None = None, anchors: AnchorStore | None = None,
                 clock=lambda: datetime.now(timezone.utc)):
        self._key = key or os.urandom(32)
        self.anchors = anchors or AnchorStore()
        self._clock = clock
        self.entries: list[dict] = []

    def append(self, actor: str, event: str, claim_id: str | None, **details) -> dict:
        now = self._clock().isoformat(timespec="microseconds")
        if self.entries and now < self.entries[-1]["time"]:
            raise ValueError("Clock went backwards; refusing to append")
        entry = {
            "seq": len(self.entries),
            "time": now,
            "actor": actor,
            "event": event,
            "claim_id": claim_id,
            "details": details,
            "prev": self.entries[-1]["mac"] if self.entries else GENESIS,
        }
        entry["mac"] = _mac(self._key, entry)
        self.entries.append(entry)
        return entry

    def checkpoint(self) -> Anchor | None:
        if not self.entries:
            return None
        head = self.entries[-1]
        anchor = Anchor(head["seq"], head["mac"], head["time"])
        self.anchors.record(anchor)
        return anchor

    def verify(self) -> int | None:
        """Return the index of the first broken entry, or None if the log is intact."""
        prev, last_time = GENESIS, ""
        for i, e in enumerate(self.entries):
            if (e.get("seq") != i or e.get("prev") != prev or e.get("time", "") < last_time
                    or not hmac.compare_digest(e.get("mac", ""), _mac(self._key, e))):
                return i
            prev, last_time = e["mac"], e["time"]
        for a in self.anchors.anchors:
            if a.seq >= len(self.entries) or self.entries[a.seq]["mac"] != a.mac:
                return min(a.seq, len(self.entries))
        return None

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(e, default=str) for e in self.entries)
