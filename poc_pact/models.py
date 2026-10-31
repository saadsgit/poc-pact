"""Domain models for captured connections and generated POC packs."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ConnectionDraft:
    contact_name: str = ""
    contact_role: str = ""
    contact_company: str = ""
    contact_country: str = ""
    contact_email: str = ""
    your_company: str = ""
    your_country: str = ""
    meeting_context: str = ""
    collaboration_idea: str = ""
    next_step: str = ""
    confidence_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PocPlan:
    title: str = ""
    problem: str = ""
    hypothesis: str = ""
    scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    duration: str = ""
    success_metrics: list[str] = field(default_factory=list)
    your_responsibilities: list[str] = field(default_factory=list)
    partner_responsibilities: list[str] = field(default_factory=list)
    milestones: list[dict[str, str]] = field(default_factory=list)
    risks_to_verify: list[str] = field(default_factory=list)
    immediate_next_step: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
