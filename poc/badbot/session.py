"""
C-10 — Session Manager (minimal POC implementation)

In-memory only. Owns the context store and the execution log.
close() triggers context store wipe (FR-075).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .context_store import ContextStore


@dataclass
class LogEntry:
    kind: str                          # TRANSITION | REQUEST | EXTRACTION | FINDING
    message: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    step: str | None = None
    state: str | None = None
    data: dict = field(default_factory=dict)  # non-sensitive supplementary facts


@dataclass
class Finding:
    severity: str
    summary: str
    detail: str
    step: str | None = None
    state: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Session:
    def __init__(self, target: str):
        self.id = str(uuid.uuid4())
        self.target = target
        self.created_at = datetime.now(timezone.utc)
        self.context = ContextStore()
        self.log: list[LogEntry] = []
        self.findings: list[Finding] = []

    def record(self, entry: LogEntry) -> None:
        self.log.append(entry)

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)
        self.record(LogEntry(
            kind="FINDING",
            message=finding.summary,
            step=finding.step,
            state=finding.state,
            data={"severity": finding.severity},
        ))

    def close(self) -> None:
        """Wipe all sensitive context values from memory (FR-075)."""
        self.context.release_all()
