"""Prompt-injection guard for submitted documents.

Claim documents are untrusted input. Lines that try to instruct the model are removed before
any text reaches extraction or drafting, and every hit is reported for the audit log. Pattern
matching is a first line of defence, not a guarantee; the architectural controls (policy-scoped
retrieval, no access to other claims, no authority to decide) are what limit the damage when a
pattern is missed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PATTERNS = [
    r"\bignore (all |any )?(previous|prior|above) instructions\b",
    r"\bdisregard (the|all|any) .{0,40}(instructions|policy|wording)\b",
    r"^\s*(system|assistant)\s*:",
    r"<!--.*(assistant|system).*-->",
    r"\b(admin|developer|god) mode\b",
    r"\b(reveal|print|show|output) .{0,40}(medical notes|addresses|fraud score|other claimants)",
    r"\brecommend approval\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in PATTERNS]


@dataclass(frozen=True)
class InjectionFinding:
    document: str
    line: str


def scan(documents: dict[str, str]) -> tuple[dict[str, str], list[InjectionFinding]]:
    """Return documents with suspicious lines removed, plus what was removed."""
    clean: dict[str, str] = {}
    findings: list[InjectionFinding] = []
    for name, text in documents.items():
        kept = []
        for line in text.splitlines():
            if any(p.search(line) for p in _COMPILED):
                findings.append(InjectionFinding(name, line.strip()))
            else:
                kept.append(line)
        clean[name] = "\n".join(kept)
    return clean, findings
