"""Schema-constrained extraction of claim facts from documents.

Every field is parsed into a typed value and validated. A field that cannot be parsed is
reported as missing rather than guessed, and facts that appear in more than one document are
cross-checked so conflicts are surfaced instead of silently resolved.

Supported layouts: English and German labelled forms (ISO or dd.mm.yyyy dates, 1,234.56 or
1.234,56 amounts). OCR confusions in numbers (O/0, l/1, S/5) are normalised. Free-text letters
are not parsed; their fields come back as missing, so the copilot abstains.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

ESTIMATE_TOLERANCE = 0.20

LABELS = {
    "claim_id": [r"Claim reference", r"Schadennummer"],
    "policy_id": [r"Policy number", r"Versicherungsschein-Nr\."],
    "incident_date": [r"Date of incident", r"Schadentag"],
    "form_estimate": [r"Estimated repair cost", r"Geschätzte Reparaturkosten"],
    "driver_licensed": [r"Driver licensed", r"Fahrerlaubnis vorhanden"],
    "commercial_use": [r"Vehicle used for business", r"Gewerbliche Nutzung"],
    "repair_estimate": [r"Total repair estimate", r"Reparaturkosten gesamt"],
    "vehicle_value": [r"Vehicle market value", r"Wiederbeschaffungswert"],
    "police_ref": [r"Reference", r"Aktenzeichen"],
    "police_incident_date": [r"Date of incident", r"Unfalltag"],
    "alcohol": [r"Alcohol test", r"Atemalkoholtest"],
    "medical_amount": [r"Treatment cost", r"Behandlungskosten"],
}

_YES_NO = {"yes": True, "ja": True, "positive": True, "positiv": True,
           "no": False, "nein": False, "negative": False, "negativ": False}
_OCR_DIGITS = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "S": "5"})


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


def _find(key: str, text: str) -> str | None:
    for label in LABELS[key]:
        m = re.search(rf"^{label}:\s*(.+?)\s*$", text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1)
    return None


def parse_money(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = raw.replace("EUR", "").strip().translate(_OCR_DIGITS).replace(" ", "")
    if not re.fullmatch(r"[\d.,]+", s):
        return None
    if re.search(r",\d{2}$", s):          # German: 1.234,56
        s = s.replace(".", "").replace(",", ".")
    else:                                  # English: 1,234.56
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(raw: str | None) -> date | None:
    if raw is None:
        return None
    s = raw.strip().translate(_OCR_DIGITS)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _money(key: str, text: str, out: Extracted) -> float | None:
    raw = _find(key, text)
    value = parse_money(raw)
    if raw is not None and value is None:
        out.errors.append(f"{key}: not a number ({raw!r})")
    if value is not None and not 0 <= value <= 1_000_000:
        out.errors.append(f"{key}: out of range ({value})")
        return None
    return value


def _date(key: str, text: str, out: Extracted) -> date | None:
    raw = _find(key, text)
    value = parse_date(raw)
    if raw is not None and value is None:
        out.errors.append(f"{key}: not a date ({raw!r})")
    return value


def _yes_no(key: str, text: str) -> bool | None:
    raw = _find(key, text)
    return _YES_NO.get(raw.lower()) if raw else None


def extract(documents: dict[str, str]) -> Extracted:
    out = Extracted()
    form = documents.get("claim_form")
    estimate = documents.get("repair_estimate")
    police = documents.get("police_report")
    medical = documents.get("medical_note")

    if form is None:
        out.missing.append("claim_form")
    else:
        out.claim_id = _find("claim_id", form)
        out.policy_id = _find("policy_id", form)
        out.incident_date = _date("incident_date", form, out)
        out.form_estimate = _money("form_estimate", form, out)
        out.driver_licensed = _yes_no("driver_licensed", form)
        out.commercial_use = _yes_no("commercial_use", form)

    if estimate is None:
        out.missing.append("repair_estimate")
    else:
        out.repair_estimate = _money("repair_estimate", estimate, out)
        out.vehicle_value = _money("vehicle_value", estimate, out)

    if police is not None:
        out.police_ref = _find("police_ref", police)
        out.police_incident_date = _date("police_incident_date", police, out)
        out.alcohol_positive = _yes_no("alcohol", police)
        if out.police_ref is None:
            out.missing.append("police_ref")
        if out.alcohol_positive is None:
            out.missing.append("alcohol_test")

    if medical is not None:
        out.medical_amount = _money("medical_amount", medical, out)
        if out.medical_amount is None:
            out.missing.append("medical_amount")

    for name in ("claim_id", "policy_id", "incident_date", "repair_estimate", "vehicle_value",
                 "driver_licensed", "commercial_use"):
        if getattr(out, name) is None and name not in out.missing:
            out.missing.append(name)

    if out.form_estimate and out.repair_estimate:
        gap = abs(out.form_estimate - out.repair_estimate) / out.repair_estimate
        if gap > ESTIMATE_TOLERANCE:
            out.conflicts.append(
                f"Repair cost differs by {gap:.0%} between claim form ({out.form_estimate:.2f} EUR) "
                f"and workshop estimate ({out.repair_estimate:.2f} EUR)")
    if out.repair_estimate and out.vehicle_value and out.repair_estimate > out.vehicle_value * 1.5:
        out.conflicts.append(
            f"Repair estimate ({out.repair_estimate:.2f} EUR) is implausibly high for a vehicle "
            f"valued at {out.vehicle_value:.2f} EUR")
    if out.incident_date and out.police_incident_date and out.incident_date != out.police_incident_date:
        out.conflicts.append(
            f"Incident date is {out.incident_date} on the claim form but "
            f"{out.police_incident_date} in the police report")
    if out.errors:
        out.conflicts.extend(f"Unreadable value: {e}" for e in out.errors)
    return out
