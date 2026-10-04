"""Role-based access to claim content by data sensitivity.

Every document carries a sensitivity label. Anything derived from a document (an extracted
field, a draft sentence, a summary) inherits the highest label of its inputs, so an
AI-generated summary is protected exactly like the medical record it was built from.
"""

from __future__ import annotations

from enum import IntEnum


class Sensitivity(IntEnum):
    INTERNAL = 1
    CONFIDENTIAL = 2          # police reports, fraud indicator output
    SPECIAL_CATEGORY = 3      # health data (GDPR Art. 9)


DOCUMENT_LABELS = {
    "claim_form": Sensitivity.INTERNAL,
    "repair_estimate": Sensitivity.INTERNAL,
    "police_report": Sensitivity.CONFIDENTIAL,
    "medical_note": Sensitivity.SPECIAL_CATEGORY,
}

FIELD_SOURCES = {
    "police_ref": "police_report", "police_incident_date": "police_report",
    "alcohol_positive": "police_report", "medical_amount": "medical_note",
}

# Highest label each role may read. Fraud investigators deliberately do not get health data
# by default; a supervisor can grant it case by case (logged).
CLEARANCE = {
    "adjuster": Sensitivity.SPECIAL_CATEGORY,
    "supervisor": Sensitivity.SPECIAL_CATEGORY,
    "investigator": Sensitivity.CONFIDENTIAL,
    "auditor": Sensitivity.INTERNAL,
    "governance": Sensitivity.INTERNAL,
}


def label_of(documents: list[str]) -> Sensitivity:
    return max((DOCUMENT_LABELS.get(d, Sensitivity.CONFIDENTIAL) for d in documents),
               default=Sensitivity.INTERNAL)


def field_label(name: str) -> Sensitivity:
    source = FIELD_SOURCES.get(name)
    return DOCUMENT_LABELS[source] if source else Sensitivity.INTERNAL


def allowed(role: str, label: Sensitivity, granted: Sensitivity | None = None) -> bool:
    return label <= max(CLEARANCE.get(role, Sensitivity.INTERNAL), granted or 0)
