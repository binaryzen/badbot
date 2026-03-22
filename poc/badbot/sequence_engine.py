"""
C-07 — Sequence Engine (minimal POC implementation)

Executes a sequence definition using a transitions-backed FSM. Each state
corresponds to a named step. The engine advances through states by executing
the step's HTTP request, extracting context values, checking for findings, and
triggering the FSM transition.

The only place raw context values are resolved is _resolve(), which is called
solely at message construction time (URL, headers, body interpolation).
"""
import re
from dataclasses import dataclass, field

import httpx
from jsonpath_ng import parse as jsonpath_parse
from transitions import Machine, MachineError

from .context_store import ContextRef
from .session import Finding, LogEntry, Session


# ---------------------------------------------------------------------------
# Sequence definition data types (loaded from YAML by cli.py)
# ---------------------------------------------------------------------------

@dataclass
class ExtractionDef:
    field: str    # jsonpath expression e.g. "$.token"
    into: str     # context store key e.g. "auth_token"


@dataclass
class FindingDef:
    severity: str
    summary: str
    detail: str


@dataclass
class StepDef:
    name: str
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict | None = None
    extract: list[ExtractionDef] = field(default_factory=list)
    expect_status: int | None = None
    finding_on_unexpected: FindingDef | None = None
    on_success: str | None = None  # name of next state; None means terminal


@dataclass
class SequenceDef:
    name: str
    description: str
    steps: list[StepDef]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SequenceEngine:
    """
    Executes a SequenceDef against a target base URL.
    Findings and log entries are written to the provided Session.
    """

    def __init__(self, sequence: SequenceDef, session: Session, base_url: str):
        self.sequence = sequence
        self.session = session
        self.base_url = base_url.rstrip("/")
        self._step_map: dict[str, StepDef] = {s.name: s for s in sequence.steps}
        self._setup_fsm()

    def _setup_fsm(self) -> None:
        states = [s.name for s in self.sequence.steps] + ["completed", "failed"]

        transitions: list[dict] = [
            {"trigger": "fail",     "source": "*", "dest": "failed"},
            {"trigger": "complete", "source": "*", "dest": "completed"},
        ]
        for step in self.sequence.steps:
            if step.on_success:
                transitions.append({
                    "trigger": "advance",
                    "source": step.name,
                    "dest": step.on_success,
                })

        Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial=self.sequence.steps[0].name,
            ignore_invalid_triggers=False,
        )

    # ------------------------------------------------------------------
    # Template resolution — the only place raw context values are read
    # ------------------------------------------------------------------

    def _resolve(self, template: str) -> str:
        """
        Replaces {ctx:key} placeholders with raw values from the context store.
        Called only at HTTP message construction time.
        """
        def replacer(match: re.Match) -> str:
            key = match.group(1)
            ref = self.session.context.ref(key)
            return str(self.session.context.value(ref))

        return re.sub(r"\{ctx:([^}]+)\}", replacer, template)

    def _resolve_dict(self, d: dict) -> dict:
        return {k: self._resolve(str(v)) for k, v in d.items()}

    # ------------------------------------------------------------------
    # Execution loop
    # ------------------------------------------------------------------

    def execute(self) -> None:
        while self.state not in ("completed", "failed"):
            step = self._step_map.get(self.state)
            if not step:
                self._log("TRANSITION", f"No step definition for state '{self.state}' — halting")
                self.fail()
                break
            self._execute_step(step)

    def _execute_step(self, step: StepDef) -> None:
        self._log("TRANSITION", f"Entered state '{step.name}'", step=step.name)

        # Resolve templates — raw value access only here
        url = self.base_url + self._resolve(step.path)
        headers = self._resolve_dict(step.headers)
        body = self._resolve_dict(step.body) if step.body else None

        # Send request
        try:
            with httpx.Client() as client:
                response = client.request(
                    method=step.method,
                    url=url,
                    headers=headers,
                    json=body,
                )
        except httpx.RequestError as exc:
            self._log("REQUEST", f"Request error: {exc}", step=step.name)
            self.fail()
            return

        self._log(
            "REQUEST",
            f"{step.method} {url} → {response.status_code}",
            step=step.name,
            data={"status_code": response.status_code},
        )

        # Context extraction (response body values → context store)
        if response.is_success and step.extract:
            try:
                body_json = response.json()
            except Exception:
                body_json = {}

            for ext in step.extract:
                expr = jsonpath_parse(ext.field)
                matches = expr.find(body_json)
                if matches:
                    self.session.context.store(ext.into, matches[0].value)
                    # Log the key, never the value
                    self._log("EXTRACTION", f"Stored '{ext.into}'", step=step.name)
                else:
                    self._log(
                        "EXTRACTION",
                        f"Extraction failed: '{ext.field}' not found in response",
                        step=step.name,
                    )
                    self.fail()
                    return

        # Finding check
        if step.expect_status is not None and response.status_code != step.expect_status:
            if step.finding_on_unexpected:
                fd = step.finding_on_unexpected
                self.session.add_finding(Finding(
                    severity=fd.severity,
                    summary=fd.summary,
                    detail=fd.detail,
                    step=step.name,
                    state=self.state,
                ))

        # State transition
        try:
            if step.on_success:
                self.advance()
            else:
                self.complete()
        except MachineError as exc:
            self._log("TRANSITION", f"FSM error: {exc}", step=step.name)
            self.fail()

    def _log(self, kind: str, message: str, step: str | None = None, data: dict | None = None) -> None:
        self.session.record(LogEntry(
            kind=kind,
            message=message,
            step=step,
            state=self.state,
            data=data or {},
        ))
