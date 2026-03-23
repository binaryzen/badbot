"""
C-13/C-14 — CLI entry point (minimal POC implementation)

Subcommands:
    run      Execute a sequence against a target
    decrypt  Recover and display a session archive

Usage:
    python -m badbot run <target_url> <sequence_file> [options]
    python -m badbot decrypt <archive> [--key <keyfile>]
                        Session ID is read from the plaintext archive prefix.

Run options:
    --clear-context     Resolve context refs in log output (default: tokenized/opaque)
    --output <file>     Write AES-GCM encrypted session archive to <file>
                        Decryption key written to <file>.key

Examples:
    python -m badbot run http://localhost:8000 sequences/auth_bola_probe.yaml
    python -m badbot run http://localhost:8000 sequences/auth_bola_probe.yaml --clear-context
    python -m badbot run http://localhost:8000 sequences/auth_bola_probe.yaml --output run.enc
    python -m badbot decrypt run.enc
    python -m badbot decrypt run.enc --key run.enc.key
"""
import argparse
import json
import sys

import yaml

from .messages import render, render_token
from .output import decrypt_session, encrypt_session
from .sequence_engine import BodyAssertionDef, ExtractionDef, FindingDef, LoopFindingDef, SequenceDef, SequenceEngine, StepDef
from .session import Session


# ---------------------------------------------------------------------------
# Sequence loader
# ---------------------------------------------------------------------------

def load_sequence(path: str) -> SequenceDef:
    with open(path) as f:
        data = yaml.safe_load(f)

    steps = []
    for s in data["steps"]:
        extractions = [
            ExtractionDef(field=e["field"], into=e["into"], transform=e.get("transform"))
            for e in s.get("extract", [])
        ]

        fd_data = s.get("finding_on_unexpected")
        finding_def = FindingDef(
            severity=fd_data["severity"],
            urn=fd_data["urn"],
            params=fd_data.get("params") or {},
        ) if fd_data else None

        body_assertions = []
        for ba in s.get("body_assertions", []):
            ba_fd_data = ba.get("finding_on_fail")
            ba_finding_def = FindingDef(
                severity=ba_fd_data["severity"],
                urn=ba_fd_data["urn"],
                params=ba_fd_data.get("params") or {},
            ) if ba_fd_data else None
            body_assertions.append(BodyAssertionDef(
                path=ba["path"],
                not_equals=ba.get("not_equals"),
                equals=ba.get("equals"),
                finding_on_fail=ba_finding_def,
            ))

        lf_data = s.get("loop_finding")
        loop_finding = LoopFindingDef(
            expect_status=lf_data["expect_status"],
            finding=FindingDef(
                severity=lf_data["finding"]["severity"],
                urn=lf_data["finding"]["urn"],
                params=lf_data["finding"].get("params") or {},
            ),
        ) if lf_data else None

        steps.append(StepDef(
            name=s["name"],
            method=s["method"],
            path=s["path"],
            headers=s.get("headers", {}),
            body=s.get("body"),
            body_format=s.get("body_format", "json"),
            extract=extractions,
            expect_status=s.get("expect_status"),
            finding_on_unexpected=finding_def,
            body_assertions=body_assertions,
            repeat=s.get("repeat"),
            loop_finding=loop_finding,
            on_success=s.get("on_success"),
        ))

    return SequenceDef(name=data["name"], description=data["description"], steps=steps)


# ---------------------------------------------------------------------------
# 'run' subcommand
# ---------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> None:
    session = Session(target=args.target)
    sequence = load_sequence(args.sequence)
    engine = SequenceEngine(sequence=sequence, session=session, base_url=args.target)

    print(f"Session : {session.id}")
    print(f"Sequence: {sequence.name}")
    print(f"Target  : {args.target}")
    mode_label = "clear" if args.clear_context else "tokenized"
    print(f"Output  : {mode_label}")
    print()

    engine.execute()

    # Encrypted archive — must happen before session.close() wipes context
    if args.output:
        encrypted, key = encrypt_session(session)
        with open(args.output, "wb") as f:
            f.write(encrypted)
        key_path = args.output + ".key"
        with open(key_path, "wb") as f:
            f.write(key)
        # Session ID sidecar — required as GCM associated data for decryption.
        # The ID is a UUID (non-sensitive); its purpose is to bind the ciphertext
        # to this session so a ciphertext cannot be replayed under a different ID.
        print(f"Session archive : {args.output}")
        print(f"Decryption key  : {key_path}")
        print()

    # Execution log
    print("=== Execution Log ===")
    for entry in session.log:
        step_tag = f"  [{entry.step}]" if entry.step else ""
        rendered = render_token(entry.message, session.context, clear=args.clear_context)
        print(f"  {entry.kind:<12}{step_tag} {rendered}")
    print()

    # Findings — render before session.close() wipes context
    if session.findings:
        print(f"=== Findings ({len(session.findings)}) ===")
        for finding in session.findings:
            rendered = render(finding.message, session.context)
            print(f"  [{finding.severity}] {rendered['summary']}")
            print(f"           {rendered['detail']}")
        session.close()
        sys.exit(1)
    else:
        print("=== No findings ===")
        session.close()
        sys.exit(0)


# ---------------------------------------------------------------------------
# 'decrypt' subcommand
# ---------------------------------------------------------------------------

def cmd_decrypt(args: argparse.Namespace) -> None:
    key_path = args.key if args.key else args.archive + ".key"

    try:
        with open(args.archive, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"error: archive not found: {args.archive}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(key_path, "rb") as f:
            key = f.read()
    except FileNotFoundError:
        print(f"error: key file not found: {key_path}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = decrypt_session(data, key)
    except Exception as exc:
        print(f"error: decryption failed — {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Session  : {payload['session_id']}")
    print(f"Target   : {payload['target']}")
    print(f"Created  : {payload['created_at']}")
    print()

    print("=== Execution Log ===")
    for entry in payload["log"]:
        step_tag = f"  [{entry['step']}]" if entry.get("step") else ""
        token = entry["token"]
        # Render recovered token: use registered log template if available,
        # otherwise fall back to generic "k=v" format.
        from .messages import _REGISTRY
        log_tmpl = _REGISTRY.get(token["urn"], {}).get("log", "")
        try:
            text = log_tmpl.format(**token["params"]) if log_tmpl else _format_token(token)
        except KeyError:
            text = _format_token(token)
        print(f"  {entry['kind']:<12}{step_tag} {text}")
    print()

    findings = payload.get("findings", [])
    if findings:
        print(f"=== Findings ({len(findings)}) ===")
        for finding in findings:
            token = finding["token"]
            from .messages import _REGISTRY
            summary_tmpl = _REGISTRY.get(token["urn"], {}).get("summary", "")
            detail_tmpl  = _REGISTRY.get(token["urn"], {}).get("detail", "")
            try:
                summary = summary_tmpl.format(**token["params"]) if summary_tmpl else _format_token(token)
                detail  = detail_tmpl.format(**token["params"])  if detail_tmpl  else ""
            except KeyError:
                summary = _format_token(token)
                detail = ""
            print(f"  [{finding['severity']}] {summary}")
            if detail:
                print(f"           {detail}")
    else:
        print("=== No findings ===")


def _format_token(token: dict) -> str:
    """Generic fallback: '[urn] k=v ...'"""
    parts = [f"{k}={v}" for k, v in token.get("params", {}).items()]
    return f"[{token['urn']}] {' '.join(parts)}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="badbot",
        description="Orchestrated API vulnerability probe",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- run --
    p_run = sub.add_parser("run", help="Execute a sequence against a target")
    p_run.add_argument("target", help="Base URL of the target (e.g. http://localhost:8000)")
    p_run.add_argument("sequence", help="Path to sequence YAML file")
    p_run.add_argument(
        "--clear-context",
        action="store_true",
        default=False,
        help="Resolve context refs in log output (default: tokenized/opaque)",
    )
    p_run.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write AES-GCM encrypted session archive to FILE",
    )

    # -- decrypt --
    p_dec = sub.add_parser("decrypt", help="Recover and display a session archive")
    p_dec.add_argument("archive", help="Path to encrypted session archive (.enc)")
    p_dec.add_argument(
        "--key",
        metavar="FILE",
        default=None,
        help="Path to key file (default: <archive>.key)",
    )

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "decrypt":
        cmd_decrypt(args)
