"""
C-07 — Sequence Engine (minimal POC implementation)

Executes a sequence definition using a transitions-backed FSM. Each state
corresponds to a named step. The engine advances through states by executing
the step's HTTP request, extracting context values, checking for findings, and
triggering the FSM transition.

Raw context values are read in exactly two places:
  - _resolve_value(): at HTTP message construction time (URL, headers, body)
  - messages.render(): at CLI output time, before session.close()

Finding creation builds a MessageRef from ContextRef handles — no raw values
are read or embedded at that point.
"""
import re
from dataclasses import dataclass, field
from typing import Any

import httpx
import jwt as pyjwt
from jsonpath_ng import parse as jsonpath_parse
from transitions import Machine, MachineError

from .messages import MessageRef
from .session import Finding, LogEntry, Session


# ---------------------------------------------------------------------------
# Sequence definition data types (loaded from YAML by cli.py)
# ---------------------------------------------------------------------------

@dataclass
class ExtractionDef:
    field: str              # jsonpath expression e.g. "$.token"
    into: str               # context store key e.g. "auth_token"
    transform: str | None = None  # optional post-processing: "jwt_decode"


@dataclass
class FindingDef:
    severity: str
    urn: str                       # message URN e.g. "urn:badbot:poc:msg:bola_detected"
    params: dict[str, str]         # param name → context key (dot-notation supported)


@dataclass
class StepDef:
    name: str
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict | None = None
    body_format: str = "json"      # "json" or "form"
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
    # Template resolution — raw context values read only here
    # ------------------------------------------------------------------

    def _resolve_value(self, key: str) -> str:
        """
        Resolves a context key (dot-notation supported) to a raw string.
        Called only at HTTP message construction time.
        context.ref() handles dot-notation; context.value() navigates the path.
        """
        ref = self.session.context.ref(key)
        return str(self.session.context.value(ref))

    def _resolve(self, template: str) -> str:
        return re.sub(
            r"\{ctx:([^}]+)\}",
            lambda m: self._resolve_value(m.group(1)),
            template,
        )

    def _resolve_dict(self, d: dict) -> dict:
        return {k: self._resolve(str(v)) for k, v in d.items()}

    # ------------------------------------------------------------------
    # Extraction transforms
    # ------------------------------------------------------------------

    def _apply_transform(self, value: Any, transform: str) -> Any:
        if transform == "jwt_decode":
            return pyjwt.decode(
                value,
                options={"verify_signature": False},
                algorithms=["HS256"],
            )
        raise ValueError(f"Unknown transform: {transform!r}")

    # ------------------------------------------------------------------
    # Execution loop
    # ------------------------------------------------------------------

    def execute(self) -> None:
        while self.state not in ("completed", "failed"):
            step = self._step_map.get(self.state)
            if not step:
                self._log("TRANSITION", f"No step for state '{self.state}' — halting")
                self.fail()
                break
            self._execute_step(step)

    def _execute_step(self, step: StepDef) -> None:
        self._log("TRANSITION", f"Entered state '{step.name}'", step=step.name)

        url = self.base_url + self._resolve(step.path)
        headers = self._resolve_dict(step.headers)
        body = self._resolve_dict(step.body) if step.body else None

        try:
            with httpx.Client() as client:
                kwargs: dict = {"method": step.method, "url": url, "headers": headers}
                if body is not None:
                    kwargs["data" if step.body_format == "form" else "json"] = body
                response = client.request(**kwargs)
        except httpx.RequestError as exc:
            self._log("REQUEST", f"Request error: {exc}", step=step.name)
            self.fail()
            return

        self._log(
            "REQUEST",
            f"{step.method} {url} -> {response.status_code}",
            step=step.name,
            data={"status_code": response.status_code},
        )

        # Context extraction
        if response.is_success and step.extract:
            try:
                body_json = response.json()
            except Exception:
                body_json = {}

            for ext in step.extract:
                matches = jsonpath_parse(ext.field).find(body_json)
                if not matches:
                    self._log("EXTRACTION", f"'{ext.field}' not found", step=step.name)
                    self.fail()
                    return

                value = matches[0].value
                if ext.transform:
                    try:
                        value = self._apply_transform(value, ext.transform)
                        self._log("EXTRACTION", f"Stored '{ext.into}' (transform: {ext.transform})", step=step.name)
                    except Exception as exc:
                        self._log("EXTRACTION", f"Transform '{ext.transform}' failed: {exc}", step=step.name)
                        self.fail()
                        return
                else:
                    self._log("EXTRACTION", f"Stored '{ext.into}'", step=step.name)

                self.session.context.store(ext.into, value)

        # Finding check — builds MessageRef with ContextRef handles, no raw values read
        if step.expect_status is not None and response.status_code != step.expect_status:
            if step.finding_on_unexpected:
                fd = step.finding_on_unexpected
                params = {
                    name: self.session.context.ref(key)
                    for name, key in fd.params.items()
                }
                self.session.add_finding(Finding(
                    severity=fd.severity,
                    message=MessageRef.build(urn=fd.urn, params=params),
                    step=step.name,
                    state=self.state,
                ))

        # State transition
        try:
            self.advance() if step.on_success else self.complete()
        except MachineError as exc:
            self._log("TRANSITION", f"FSM error: {exc}", step=step.name)
            self.fail()

    def _log(self, kind: str, message: str, step: str | None = None, data: dict | None = None) -> None:
        self.session.record(LogEntry(
            kind=kind, message=message, step=step, state=self.state, data=data or {}
        ))
