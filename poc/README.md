# badbot POC

Vertical slice implementing a BOLA detection sequence end-to-end:
authenticate → extract token and user_id into context store → probe own resource → probe another user's resource with the same token → emit finding when the server returns 200 instead of 403.

## What this exercises

| Component | POC file | What's validated |
|---|---|---|
| C-02 Context Store | `badbot/context_store.py` | `value()` / `ref()` boundary; opaque handles everywhere except message construction |
| C-07 Sequence Engine | `badbot/sequence_engine.py` | FSM execution loop via `transitions`; context extraction; finding emission; `_resolve()` as the sole raw-value access point |
| C-10 Session | `badbot/session.py` | Log recording; finding collection; `close()` wipes context |
| C-13/C-14 CLI | `badbot/cli.py` | YAML sequence loading; output; exit codes |

## Setup

```bash
cd poc
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

**Terminal 1 — start the mock server:**
```bash
uvicorn server.main:app --port 8000
```

**Terminal 2 — run the sequence:**
```bash
python -m badbot http://localhost:8000 sequences/auth_bola_probe.yaml
```

## Expected output

```
Session : <uuid>
Sequence: auth_bola_probe
Target  : http://localhost:8000

=== Execution Log ===
  TRANSITION   [authenticate] Entered state 'authenticate'
  REQUEST      [authenticate] POST http://localhost:8000/auth → 200
  EXTRACTION   [authenticate] Stored 'auth_token'
  EXTRACTION   [authenticate] Stored 'user_id'
  TRANSITION   [probe_own] Entered state 'probe_own'
  REQUEST      [probe_own] GET http://localhost:8000/users/1/orders → 200
  TRANSITION   [probe_other] Entered state 'probe_other'
  REQUEST      [probe_other] GET http://localhost:8000/users/2/orders → 200
  FINDING      [probe_other] BOLA: cross-user resource access succeeded

=== Findings (1) ===
  [HIGH] BOLA: cross-user resource access succeeded
         Authenticated as alice (user_id=1) and requested /users/2/orders ...
```

Exit code 1 when findings are present; 0 when clean.

## What the mock server does

`POST /auth` — validates credentials, returns `{token, user_id}`.
`GET /users/{id}/orders` — validates that the token exists, but **does not check that the token's owner matches the requested `user_id`**. This is the intentional BOLA vulnerability the sequence is designed to detect.

## Architecture notes

- `auth_token` and `user_id` are stored in the context store and never appear in the execution log — only the key names do.
- Template resolution (`{ctx:key}`) happens solely in `SequenceEngine._resolve()`, which calls `context.value()` — the only place in the codebase where raw values are read.
- All other log entries and findings reference keys or opaque handles only.
- `session.close()` at the end of `cli.main()` calls `context.release_all()`, clearing all values from memory.
