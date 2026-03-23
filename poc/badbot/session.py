"""
C-10 — Session Manager (minimal POC implementation)

In-memory only. Owns the context store and the execution log.
close() triggers context store wipe (FR-075).

Finding.message is a MessageRef — an opaque reference carrying ContextRef
handles, not resolved strings. Raw values are never embedded in findings.

LogEntry.message is an OutputToken — a structured URN + params token.
The log records URNs and literal metadata; sensitive values are carried
only as ContextRef handles (opaque in tokenized output mode).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .context_store import ContextStore
from .messages import MessageRef, OutputToken


@dataclass
class LogEntry:
    kind: str                          # TRANSITION | REQUEST | EXTRACTION | FINDING
    message: OutputToken
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    step: str | None = None
    state: str | None = None


@dataclass
class Finding:
    severity: str
    message: MessageRef                # opaque — no raw values
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
        # Log records URN and severity only — never rendered text or raw param values
        self.record(LogEntry(
            kind="FINDING",
            message=OutputToken.build(
                "urn:badbot:poc:log:finding_recorded",
                {"severity": finding.severity, "urn": finding.message.urn},
            ),
            step=finding.step,
            state=finding.state,
        ))

    def close(self) -> None:
        """Wipe all sensitive context values from memory (FR-075)."""
        self.context.release_all()
