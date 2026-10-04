"""Schema-constrained extraction of claim facts from documents.

Every field is parsed into a typed value and validated. A field that cannot be parsed is
reported as missing rather than guessed, and facts that appear in more than one document are
cross-checked so conflicts are surfaced instead of silently resolved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

ESTIMATE_TOLERANCE = 0.20


@dataclass
class Extracted:
    claim_id: str | None = None
    policy_id: str | None = None
    incident_date: date | None = None
    police_incident_date: date | None = None
    form_estimate: float | None = None
    repair_estimate: float | None = None
    vehicle_value: float | None = None
    police_ref: str | None = None
    alcohol_positive: bool | None = None
    driver_licensed: bool | None = None
    commercial_use: bool | None = None
    medical_amount: float | None = None
    missing: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _find(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else None


def _money(raw: str | None, name: str, out: Extracted) -> float | None:
    if raw is None:
        return None
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        out.errors.append(f"{name}: not a number ({raw!r})")
        return None
    if not 0 <= value <= 1_000_000:
        out.errors.append(f"{name}: out of range ({value})")
        return None
    return value


def _date(raw: str | None, name: str, out: Extracted) -> date | None:
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        out.errors.append(f"{name}: not an ISO date ({raw!r})")
        return None


def _yes_no(raw: str | None) -> bool | None:
    if raw is None:
        return None
    return {"yes": True, "no": False, "positive": True, "negative": False}.get(raw.lower())


def extract(documents: dict[str, str]) -> Extracted:
    out = Extracted()
    form = documents.get("claim_form")
    estimate = documents.get("repair_estimate")
    police = documents.get("police_report")
    medical = documents.get("medical_note")

    if form is None:
        out.missing.append("claim_form")
    else:
        out.claim_id = _find(r"^Claim reference:\s*(\S+)", form)
        out.policy_id = _find(r"^Policy number:\s*(\S+)", form)
        out.incident_date = _date(_find(r"^Date of incident:\s*(\S+)", form), "incident_date", out)
        out.form_estimate = _money(_find(r"^Estimated repair cost:\s*([\d.,]+)", form), "form_estimate", out)
        out.driver_licensed = _yes_no(_find(r"^Driver licensed:\s*(\w+)", form))
        out.commercial_use = _yes_no(_find(r"^Vehicle used for business:\s*(\w+)", form))

    if estimate is None:
        out.missing.append("repair_estimate")
    else:
        out.repair_estimate = _money(_find(r"^Total repair estimate:\s*([\d.,]+)", estimate), "repair_estimate", out)
        out.vehicle_value = _money(_find(r"^Vehicle market value:\s*([\d.,]+)", estimate), "vehicle_value", out)

    if police is not None:
        out.police_ref = _find(r"^Reference:\s*(\S+)", police)
        out.police_incident_date = _date(_find(r"^Date of incident:\s*(\S+)", police), "police_incident_date", out)
        out.alcohol_positive = _yes_no(_find(r"^Alcohol test:\s*(\w+)", police))
        if out.police_ref is None:
            out.missing.append("police_ref")

    if medical is not None:
        out.medical_amount = _money(_find(r"^Treatment cost:\s*([\d.,]+)", medical), "medical_amount", out)

    for name in ("claim_id", "policy_id", "incident_date", "repair_estimate", "vehicle_value"):
        if getattr(out, name) is None and name not in out.missing:
            out.missing.append(name)

    if out.form_estimate and out.repair_estimate:
        gap = abs(out.form_estimate - out.repair_estimate) / out.repair_estimate
        if gap > ESTIMATE_TOLERANCE:
            out.conflicts.append(
                f"Repair cost differs by {gap:.0%} between claim form ({out.form_estimate:.2f} EUR) "
                f"and workshop estimate ({out.repair_estimate:.2f} EUR)")
    if out.incident_date and out.police_incident_date and out.incident_date != out.police_incident_date:
        out.conflicts.append(
            f"Incident date is {out.incident_date} on the claim form but "
            f"{out.police_incident_date} in the police report")
    return out
