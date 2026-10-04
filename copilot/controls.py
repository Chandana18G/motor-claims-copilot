"""Incident response: named authority to pause a component while an incident is investigated.

Pausing never blocks claims handling. It removes the AI component from the path:

* ``fraud_model`` paused: no fraud score is produced; claims are handled without it.
* ``llm_drafter`` paused: drafts come from the deterministic template drafter.
* ``copilot`` paused: no draft or recommendation at all; adjusters work the claim manually.

Supervisors and the governance function may pause; only governance may resume, after the
incident is closed. Defined triggers (see ``copilot.monitoring``) pause automatically under
authority delegated in advance, and every change is written to the audit log.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copilot.audit import AuditLog
from copilot.identity import AuthorityError, Directory, Token

COMPONENTS = ("copilot", "llm_drafter", "fraud_model")


@dataclass
class Incident:
    trigger: str
    component: str
    detail: str
    open: bool = True


@dataclass
class Controls:
    directory: Directory
    audit: AuditLog
    paused: dict[str, str] = field(default_factory=dict)
    incidents: list[Incident] = field(default_factory=list)

    def is_paused(self, component: str) -> bool:
        return component in self.paused

    def pause(self, component: str, reason: str, by: Token) -> None:
        who = self.directory.verify(by)
        if who.role not in ("supervisor", "governance"):
            raise AuthorityError("Only a supervisor or the governance function can pause a component")
        self._pause(component, reason, who.staff_id)

    def open_incident(self, incident: Incident) -> None:
        """Automatic pause on a defined trigger (authority delegated in the incident procedure)."""
        self.incidents.append(incident)
        self._pause(incident.component, f"{incident.trigger}: {incident.detail}", "incident_procedure")

    def resume(self, component: str, by: Token) -> None:
        who = self.directory.verify(by)
        if who.role != "governance":
            raise AuthorityError("Only the governance function can resume a paused component")
        if any(i.open and i.component == component for i in self.incidents):
            raise AuthorityError("Close the open incident before resuming")
        self.paused.pop(component, None)
        self.audit.append(who.staff_id, "component_resumed", None, component=component)

    def close_incident(self, incident: Incident, by: Token, resolution: str) -> None:
        who = self.directory.verify(by)
        if who.role != "governance":
            raise AuthorityError("Only the governance function can close an incident")
        incident.open = False
        self.audit.append(who.staff_id, "incident_closed", None, trigger=incident.trigger, resolution=resolution)

    def _pause(self, component: str, reason: str, actor: str) -> None:
        if component not in COMPONENTS:
            raise ValueError(component)
        self.paused[component] = reason
        self.audit.append(actor, "component_paused", None, component=component, reason=reason)
