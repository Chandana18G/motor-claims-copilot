"""Append-only, hash-chained audit log.

Each entry stores the SHA-256 of the previous entry, so editing, deleting or reordering any
entry breaks verification from that point on.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

GENESIS = "0" * 64


def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class AuditLog:
    entries: list[dict] = field(default_factory=list)

    def append(self, actor: str, event: str, claim_id: str | None, **details) -> dict:
        entry = {
            "seq": len(self.entries),
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "actor": actor,
            "event": event,
            "claim_id": claim_id,
            "details": details,
            "prev": self.entries[-1]["hash"] if self.entries else GENESIS,
        }
        entry["hash"] = _digest(entry)
        self.entries.append(entry)
        return entry

    def verify(self) -> int | None:
        """Return the index of the first broken entry, or None if the chain is intact."""
        prev = GENESIS
        for i, e in enumerate(self.entries):
            if e.get("seq") != i or e.get("prev") != prev or e.get("hash") != _digest(e):
                return i
            prev = e["hash"]
        return None

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(e, default=str) for e in self.entries)
