"""
C-13/C-14 — CLI entry point (minimal POC implementation)

Usage:
    python -m badbot <target_url> <sequence_file>

Example:
    python -m badbot http://localhost:8000 sequences/auth_bola_probe.yaml
"""
import sys

import yaml

from .sequence_engine import ExtractionDef, FindingDef, SequenceDef, SequenceEngine, StepDef
from .session import Session


def load_sequence(path: str) -> SequenceDef:
    with open(path) as f:
        data = yaml.safe_load(f)

    steps = []
    for s in data["steps"]:
        extractions = [
            ExtractionDef(field=e["field"], into=e["into"])
            for e in s.get("extract", [])
        ]

        fd_data = s.get("finding_on_unexpected")
        finding_def = FindingDef(
            severity=fd_data["severity"],
            summary=fd_data["summary"],
            detail=fd_data["detail"],
        ) if fd_data else None

        steps.append(StepDef(
            name=s["name"],
            method=s["method"],
            path=s["path"],
            headers=s.get("headers", {}),
            body=s.get("body"),
            extract=extractions,
            expect_status=s.get("expect_status"),
            finding_on_unexpected=finding_def,
            on_success=s.get("on_success"),
        ))

    return SequenceDef(name=data["name"], description=data["description"], steps=steps)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m badbot <target_url> <sequence_file>")
        sys.exit(1)

    target = sys.argv[1]
    sequence_path = sys.argv[2]

    session = Session(target=target)
    sequence = load_sequence(sequence_path)
    engine = SequenceEngine(sequence=sequence, session=session, base_url=target)

    print(f"Session : {session.id}")
    print(f"Sequence: {sequence.name}")
    print(f"Target  : {target}")
    print()

    engine.execute()
    session.close()

    print("=== Execution Log ===")
    for entry in session.log:
        step_tag = f"  [{entry.step}]" if entry.step else ""
        print(f"  {entry.kind:<12}{step_tag} {entry.message}")

    print()

    if session.findings:
        print(f"=== Findings ({len(session.findings)}) ===")
        for finding in session.findings:
            print(f"  [{finding.severity}] {finding.summary}")
            print(f"           {finding.detail}")
        sys.exit(1)
    else:
        print("=== No findings ===")
        sys.exit(0)
