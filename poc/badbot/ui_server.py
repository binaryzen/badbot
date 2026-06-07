"""
Badbot visualization UI server (C-13 POC — local only).

Routes
------
GET  /                       → index.html
GET  /api/sessions           → [{id, sequence_name, target, created_at, status, finding_count, ttp_mappings}]
GET  /api/sessions/{id}      → full session JSON (includes sequence, findings, log, visited_steps)
GET  /api/sequences          → [{name, description, ttp_mappings, inputs, step_names}]
GET  /api/sequences/{name}   → {name, description, ttp_mappings, inputs, steps}
GET  /api/coverage           → [{key, technique_id, sub_technique_id, owasp_alias, confidence, run_count, has_finding, sessions}]
POST /api/runs               → launch a sequence live: {sequence_name, target, inputs} → {id}
GET  /api/runs/{id}          → live run snapshot (same shape as a session, plus status="running")

Environment
-----------
BADBOT_SESSIONS_DIR   default: sessions  (relative to cwd)
BADBOT_SEQUENCES_DIR  default: sequences (relative to cwd)
"""
import json
import os
import threading
import time
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .cli import load_sequence, save_session_json, _step_to_dict
from .messages import render, render_token
from .sequence_engine import SequenceEngine, seed_inputs
from .session import Session

_SESSIONS_DIR = Path(os.environ.get("BADBOT_SESSIONS_DIR", "sessions"))
_SEQUENCES_DIR = Path(os.environ.get("BADBOT_SEQUENCES_DIR", "sequences"))
_UI_DIR = Path(__file__).parent / "ui"

app = FastAPI(title="badbot")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"],
)


@app.get("/")
def root():
    html = _UI_DIR / "index.html"
    if not html.exists():
        raise HTTPException(404, "UI not found")
    return FileResponse(str(html))


def _read_sessions() -> list[dict]:
    out: list[dict] = []
    if not _SESSIONS_DIR.exists():
        return out
    for p in sorted(_SESSIONS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


@app.get("/api/sessions")
def list_sessions():
    result = []
    for s in _read_sessions():
        result.append({
            "id": s.get("id"),
            "sequence_name": s.get("sequence_name"),
            "target": s.get("target"),
            "created_at": s.get("created_at"),
            "status": s.get("status"),
            "finding_count": len(s.get("findings", [])),
            "ttp_mappings": s.get("ttp_mappings", []),
        })
    return JSONResponse(result)


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    p = _SESSIONS_DIR / f"{session_id}.json"
    if not p.exists():
        raise HTTPException(404, "session not found")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


def _read_sequences() -> list[dict]:
    out: list[dict] = []
    if not _SEQUENCES_DIR.exists():
        return out
    for p in sorted(_SEQUENCES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
            out.append({
                "name": data.get("name", p.stem),
                "description": data.get("description", ""),
                "ttp_mappings": data.get("ttp_mappings", []),
                "inputs": data.get("inputs", []),
                "step_names": [s["name"] for s in data.get("steps", [])],
                "_path": str(p),
                "steps": [
                    {
                        "name": s["name"],
                        "method": s["method"],
                        "path": s["path"],
                        "on_success": s.get("on_success"),
                        "on_status": s.get("on_status") or {},
                        "repeat": s.get("repeat"),
                        "for_each": s.get("for_each"),
                        "expect_status": s.get("expect_status"),
                    }
                    for s in data.get("steps", [])
                ],
            })
        except Exception:
            pass
    return out


_INTERNAL_KEYS = {"_path"}


@app.get("/api/sequences")
def list_sequences():
    return JSONResponse([
        {k: v for k, v in s.items() if k not in _INTERNAL_KEYS and k != "steps"}
        for s in _read_sequences()
    ])


@app.get("/api/sequences/{name}")
def get_sequence(name: str):
    for s in _read_sequences():
        if s["name"] == name:
            return JSONResponse({k: v for k, v in s.items() if k not in _INTERNAL_KEYS})
    raise HTTPException(404, "sequence not found")


@app.get("/api/coverage")
def get_coverage():
    sessions = _read_sessions()
    buckets: dict[str, dict] = {}
    for session in sessions:
        for m in session.get("ttp_mappings", []):
            tid = m["technique_id"]
            sub = m.get("sub_technique_id")
            key = f"{tid}.{sub}" if sub else tid
            if key not in buckets:
                buckets[key] = {
                    "key": key,
                    "technique_id": tid,
                    "sub_technique_id": sub,
                    "owasp_alias": m.get("owasp_alias"),
                    "confidence": m.get("confidence", "full"),
                    "run_count": 0,
                    "has_finding": False,
                    "sessions": [],
                }
            b = buckets[key]
            b["run_count"] += 1
            if session.get("status") == "findings":
                b["has_finding"] = True
            b["sessions"].append({
                "id": session["id"],
                "sequence_name": session.get("sequence_name"),
                "status": session.get("status"),
            })
    return JSONResponse(list(buckets.values()))


# ---------------------------------------------------------------------------
# Live runs — launch a sequence from the UI and stream progress via polling
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    sequence_name: str
    target: str
    inputs: dict[str, str] = {}


_runs: dict[str, dict] = {}
_runs_lock = threading.Lock()


def _find_sequence_path(name: str) -> str | None:
    for s in _read_sequences():
        if s["name"] == name:
            return s["_path"]
    return None


@app.post("/api/runs")
def start_run(req: RunRequest):
    path = _find_sequence_path(req.sequence_name)
    if not path:
        raise HTTPException(404, f"sequence not found: {req.sequence_name}")

    sequence = load_sequence(path)
    session = Session(target=req.target)
    seed_inputs(session, sequence, req.inputs)

    run_id = session.id
    with _runs_lock:
        _runs[run_id] = {
            "id": run_id,
            "sequence_name": sequence.name,
            "target": req.target,
            "created_at": session.created_at.isoformat(),
            "status": "running",
            "ttp_mappings": [
                {
                    "technique_id": m.technique_id,
                    "sub_technique_id": m.sub_technique_id,
                    "owasp_alias": m.owasp_alias,
                    "confidence": m.confidence,
                }
                for m in sequence.ttp_mappings
            ],
            "findings": [],
            "log": [],
            "visited_steps": [],
            "sequence": {
                "name": sequence.name,
                "description": sequence.description,
                "steps": [_step_to_dict(s) for s in sequence.steps],
            },
        }

    thread = threading.Thread(target=_execute_run, args=(run_id, sequence, session), daemon=True)
    thread.start()
    return JSONResponse({"id": run_id})


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    with _runs_lock:
        run = _runs.get(run_id)
        if not run:
            raise HTTPException(404, "run not found")
        return JSONResponse(dict(run))


def _execute_run(run_id, sequence, session) -> None:
    run = _runs[run_id]
    engine = SequenceEngine(sequence=sequence, session=session, base_url=session.target)

    stop = threading.Event()
    watcher = threading.Thread(target=_watch_progress, args=(run_id, session, stop), daemon=True)
    watcher.start()

    try:
        engine.execute()
    except Exception as exc:
        with _runs_lock:
            run["status"] = "failed"
            run["error"] = str(exc)
    finally:
        stop.set()
        watcher.join(timeout=5)
        _finalize_run(run_id, session, sequence)


def _watch_progress(run_id, session, stop: threading.Event) -> None:
    """Poll session.log/session.findings and incrementally render new entries
    into the run registry — same render() / render_token() calls save_session_json
    makes in batch, just applied as entries appear so the UI can stream them."""
    run = _runs[run_id]
    log_idx = 0
    finding_idx = 0

    def drain():
        nonlocal log_idx, finding_idx
        while log_idx < len(session.log):
            entry = session.log[log_idx]
            log_idx += 1
            text = render_token(entry.message, session.context, clear=True)
            with _runs_lock:
                run["log"].append({
                    "id": entry.id,
                    "timestamp": entry.timestamp.isoformat(),
                    "kind": entry.kind,
                    "step": entry.step,
                    "text": text,
                })
                if entry.kind == "TRANSITION" and entry.step and entry.step not in run["visited_steps"]:
                    run["visited_steps"].append(entry.step)

        while finding_idx < len(session.findings):
            finding = session.findings[finding_idx]
            finding_idx += 1
            rendered = render(finding.message, session.context)
            with _runs_lock:
                run["findings"].append({
                    "id": finding.id,
                    "severity": finding.severity,
                    "step": finding.step,
                    "timestamp": finding.timestamp.isoformat(),
                    "summary": rendered["summary"],
                    "detail": rendered["detail"],
                    "ttp_refs": [
                        {
                            "technique_id": m.technique_id,
                            "sub_technique_id": m.sub_technique_id,
                            "owasp_alias": m.owasp_alias,
                            "confidence": m.confidence,
                        }
                        for m in finding.ttp_refs
                    ],
                })

    while not stop.is_set():
        drain()
        time.sleep(0.2)
    drain()  # final flush — entries appended between the last poll and execute() returning


def _finalize_run(run_id, session, sequence) -> None:
    with _runs_lock:
        run = _runs[run_id]
        if run["status"] == "running":
            # Mirrors save_session_json's status derivation — "blocked" means
            # the probe halted before its terminal state, so an empty findings
            # list is inconclusive rather than a clean result. See Session.outcome.
            if session.outcome != "completed":
                run["status"] = "blocked"
            elif session.findings:
                run["status"] = "findings"
            else:
                run["status"] = "completed"
    try:
        save_session_json(session, sequence, str(_SESSIONS_DIR))
    finally:
        session.close()
