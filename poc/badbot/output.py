"""
Session serialization and AES-GCM encryption.

Archives contain two independently-encrypted sections under a single key:

  Token stream    — log entries and findings with params as descriptors.
                    Literals: {"__lit": "value"}
                    Context refs: {"__ref": "key"} or {"__ref": "key", "path": "sub"}
                    Contains no raw context values — safe to share without the
                    context snapshot (refs render as <ref:key> when unresolved).

  Context snapshot — raw context store values. This is the sensitive section.
                     Redaction policy applies here when implemented (FR-004).
                     Decrypt the token stream without this section to keep
                     context values opaque.

Both sections are encrypted with different AAD so they cannot be swapped or
detached and re-attached to a different archive.

Wire format:
  [36 bytes : session_id ASCII]          -- plaintext; AAD base for both sections
  [12 bytes : token nonce]
  [4 bytes  : token ciphertext length, big-endian uint32]
  [N bytes  : token ciphertext + 16-byte GCM tag]
  [12 bytes : context nonce]
  [remaining: context ciphertext + 16-byte GCM tag]

AAD:
  token section   : session_id + b":tokens"
  context section : session_id + b":context"

Usage:
    encrypted, key = encrypt_session(session)
    token_stream, context_snapshot = decrypt_session(encrypted, key)
    # token_stream and context_snapshot are dicts; context_snapshot may be None
    # if decryption of the context section is skipped (--tokens-only).
"""
import json
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .context_store import ContextRef
from .messages import OutputToken
from .session import Session


# ---------------------------------------------------------------------------
# Param descriptor serialization
# ---------------------------------------------------------------------------

def _serialize_params(params: tuple) -> dict:
    """
    Serialize OutputToken or MessageRef params to JSON-safe descriptor dicts.

    OutputToken params may be str (literal) or ContextRef.
    MessageRef params are always ContextRef.

    Result shape per param:
      literal   → {"__lit": "value"}
      ref       → {"__ref": "key", "version": n}
                  optionally with "path": "sub.field" for dot-notation refs

    The version number is frozen into the ref at context.ref() call time,
    ensuring refs captured before a key is overwritten resolve to the
    correct historical value rather than the latest.
    """
    result = {}
    for name, param in params:
        if isinstance(param, ContextRef):
            desc: dict = {"__ref": param.key, "version": param.version}
            if param.path:
                desc["path"] = param.path
            result[name] = desc
        else:
            result[name] = {"__lit": str(param)}
    return result


# ---------------------------------------------------------------------------
# Token stream construction (no context values)
# ---------------------------------------------------------------------------

def _build_token_stream(session: Session) -> dict:
    """
    Build the token stream section. Params are descriptors — no raw values.
    Safe to decrypt and share without the context snapshot.
    """
    return {
        "session_id": session.id,
        "target": session.target,
        "created_at": session.created_at.isoformat(),
        "log": [
            {
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat(),
                "kind": entry.kind,
                "step": entry.step,
                "state": entry.state,
                "token": {
                    "urn": entry.message.urn,
                    "params": _serialize_params(entry.message.params),
                },
            }
            for entry in session.log
        ],
        "findings": [
            {
                "id": finding.id,
                "timestamp": finding.timestamp.isoformat(),
                "severity": finding.severity,
                "step": finding.step,
                "state": finding.state,
                "token": {
                    "urn": finding.message.urn,
                    "params": _serialize_params(finding.message.params),
                },
            }
            for finding in session.findings
        ],
    }


# ---------------------------------------------------------------------------
# Context snapshot construction
# ---------------------------------------------------------------------------

def _build_context_snapshot(session: Session) -> dict:
    """
    Build the context snapshot section. Contains the full version history
    for each key — a list of all values stored under that key in order.

    Resolution uses {"__ref": key, "version": n} to index into the list,
    ensuring refs captured before a key was overwritten resolve correctly.

    Redaction policy (FR-004 — not yet implemented) will filter here.
    """
    return {
        "values": {k: list(v) for k, v in session.context._store.items()},
        "redacted": [],   # placeholder for redaction manifest (FR-005)
    }


# ---------------------------------------------------------------------------
# Param resolution
# ---------------------------------------------------------------------------

def resolve_params(params_desc: dict, context_values: dict) -> dict[str, str]:
    """
    Resolve a token's param descriptor dict against a context values dict.
    Returns a plain {name: resolved_string} dict for template rendering.

    {"__lit": v}                         → str(v)
    {"__ref": k, "version": n}           → str(context_values[k][n])
    {"__ref": k, "version": n, "path": p}→ navigate dot-path p into that value
    Missing key or out-of-range version  → "<missing:key[n]>"

    Version-indexed lookup ensures refs captured before a key was overwritten
    resolve to the historically correct value, not the current one.
    """
    resolved = {}
    for name, desc in params_desc.items():
        if "__lit" in desc:
            resolved[name] = str(desc["__lit"])
        elif "__ref" in desc:
            key = desc["__ref"]
            version = desc.get("version", 0)
            history = context_values.get(key)
            if not history or version >= len(history):
                resolved[name] = f"<missing:{key}[{version}]>"
            else:
                val = history[version]
                path = desc.get("path")
                if path:
                    for part in path.split("."):
                        if isinstance(val, dict):
                            val = val.get(part, f"<missing:{part}>")
                        elif isinstance(val, list):
                            try:
                                val = val[int(part)]
                            except (IndexError, ValueError):
                                val = f"<missing:{part}>"
                                break
                resolved[name] = str(val)
        else:
            resolved[name] = "<unknown>"
    return resolved


def render_token_dict(
    token: dict,
    context_values: dict | None = None,
) -> str:
    """
    Render a serialized token dict to a human-readable string.

    context_values=None  → refs shown as <ref:key[.path]> (opaque)
    context_values={}    → refs resolved (or <missing:key> if absent)

    Applies the registered log template if available; falls back to k=v format.
    """
    from .messages import _REGISTRY

    if context_values is not None:
        resolved = resolve_params(token["params"], context_values)
    else:
        # Opaque mode: show literals as-is, refs as <ref:...>
        resolved = {}
        for name, desc in token["params"].items():
            if "__lit" in desc:
                resolved[name] = str(desc["__lit"])
            else:
                key = desc.get("__ref", "?")
                path = desc.get("path")
                ver = desc.get("version", 0)
                label = f"{key}.{path}" if path else key
                resolved[name] = f"<ref:{label}[{ver}]>"

    log_tmpl = _REGISTRY.get(token["urn"], {}).get("log", "")
    if log_tmpl:
        try:
            return log_tmpl.format(**resolved)
        except KeyError:
            pass

    parts = [f"{k}={v}" for k, v in resolved.items()]
    return f"[{token['urn']}] {' '.join(parts)}"


def render_finding_dict(
    token: dict,
    context_values: dict | None = None,
) -> dict[str, str]:
    """
    Render a finding token dict to {"summary": ..., "detail": ...}.
    context_values=None leaves refs opaque in the rendered text.
    """
    from .messages import _REGISTRY

    if context_values is not None:
        resolved = resolve_params(token["params"], context_values)
    else:
        resolved = {}
        for name, desc in token["params"].items():
            if "__lit" in desc:
                resolved[name] = str(desc["__lit"])
            else:
                key = desc.get("__ref", "?")
                path = desc.get("path")
                ver = desc.get("version", 0)
                label = f"{key}.{path}" if path else key
                resolved[name] = f"<ref:{label}[{ver}]>"

    tmpl = _REGISTRY.get(token["urn"], {})
    try:
        summary = tmpl.get("summary", "").format(**resolved) or f"[{token['urn']}]"
        detail  = tmpl.get("detail",  "").format(**resolved)
    except KeyError:
        summary = f"[{token['urn']}] " + " ".join(f"{k}={v}" for k, v in resolved.items())
        detail  = ""
    return {"summary": summary, "detail": detail}


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

def _encrypt_section(plaintext: bytes, key: bytes, aad: bytes) -> bytes:
    """AES-GCM encrypt a section. Returns nonce + ciphertext + tag."""
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def encrypt_session(session: Session, key: bytes | None = None) -> tuple[bytes, bytes]:
    """
    Produce a two-section AES-GCM archive.
    Must be called before session.close() — context values must still be live.

    Returns (archive_bytes, key). key is 32 random bytes if not supplied.
    """
    if key is None:
        key = os.urandom(32)

    sid = session.id.encode()   # 36 bytes, plaintext prefix and AAD base

    token_plain   = json.dumps(_build_token_stream(session),   indent=2).encode()
    context_plain = json.dumps(_build_context_snapshot(session), indent=2).encode()

    token_section   = _encrypt_section(token_plain,   key, sid + b":tokens")
    context_section = _encrypt_section(context_plain, key, sid + b":context")

    # Wire: session_id | token_len(4) | token_section | context_section
    token_len = struct.pack(">I", len(token_section))
    return sid + token_len + token_section + context_section, key


# ---------------------------------------------------------------------------
# Decryption
# ---------------------------------------------------------------------------

def decrypt_session(
    data: bytes,
    key: bytes,
    tokens_only: bool = False,
) -> tuple[dict, dict | None]:
    """
    Decrypt and return (token_stream, context_snapshot).

    tokens_only=True skips context decryption; context_snapshot is None.
    Raises cryptography.exceptions.InvalidTag if either section is tampered.
    """
    sid = data[:36]
    token_len = struct.unpack(">I", data[36:40])[0]
    token_section   = data[40 : 40 + token_len]
    context_section = data[40 + token_len :]

    token_nonce, token_ct   = token_section[:12], token_section[12:]
    token_plain = AESGCM(key).decrypt(token_nonce, token_ct, sid + b":tokens")
    token_stream = json.loads(token_plain)

    if tokens_only:
        return token_stream, None

    ctx_nonce, ctx_ct = context_section[:12], context_section[12:]
    ctx_plain = AESGCM(key).decrypt(ctx_nonce, ctx_ct, sid + b":context")
    context_snapshot = json.loads(ctx_plain)

    return token_stream, context_snapshot
