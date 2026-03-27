"""
C-01 — Message Registry (minimal POC implementation)

Two token types live here:

  MessageRef   — for security findings: URN + ContextRef-only params.
                 render() resolves it at the CLI boundary before session.close().

  OutputToken  — for log entries: URN + mixed params (literal strings for
                 non-sensitive metadata, ContextRef handles for sensitive values).
                 render_token() respects the --clear-context mode:
                   default  → ContextRef params shown as <ref:key>, literals as-is
                   clear    → all params resolved; registered 'log' template used

serialize_token() / serialize_message_ref() fully resolve params for the
AES-GCM encrypted session stream (confidentiality is provided by encryption).

Raw context values are read in exactly two places in this module:
  - render()           (findings, called from CLI before session.close())
  - render_token()     (log tokens, called from CLI with clear=True)
  - serialize_token()  (called from output.py before session.close())
"""
from dataclasses import dataclass

from .context_store import ContextRef, ContextStore

# ---------------------------------------------------------------------------
# MessageRef — finding messages (ContextRef params only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MessageRef:
    """
    Opaque reference to a finding message template plus named context handles.
    Safe to store, log, serialize — contains no raw values.
    """
    urn: str
    params: tuple[tuple[str, ContextRef], ...]  # frozen: tuple of (name, ref) pairs

    @classmethod
    def build(cls, urn: str, params: dict[str, ContextRef]) -> "MessageRef":
        return cls(urn=urn, params=tuple(sorted(params.items())))

    def params_dict(self) -> dict[str, ContextRef]:
        return dict(self.params)


# ---------------------------------------------------------------------------
# OutputToken — log/output entries (literal or ContextRef params)
# ---------------------------------------------------------------------------

LogParam = str | ContextRef   # literal metadata string, or opaque context handle


@dataclass(frozen=True)
class OutputToken:
    """
    Structured log token: a URN plus named params that are either literal
    metadata strings (non-sensitive, always visible) or opaque ContextRef
    handles (sensitive, shown as <ref:key> in tokenized mode).

    Safe to store and serialize. Resolvable via render_token().
    """
    urn: str
    params: tuple[tuple[str, LogParam], ...]

    @classmethod
    def build(cls, urn: str, params: dict[str, LogParam]) -> "OutputToken":
        return cls(urn=urn, params=tuple(sorted(params.items())))

    def params_dict(self) -> dict[str, LogParam]:
        return dict(self.params)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, dict[str, str]] = {}


def register(urn: str, summary: str = "", detail: str = "", log: str = "") -> None:
    """
    Register a message template.
      summary / detail  — used by render() for finding messages
      log               — used by render_token() for log entries
    """
    _REGISTRY[urn] = {"summary": summary, "detail": detail, "log": log}


# ---------------------------------------------------------------------------
# Render / serialize — raw context values read only in these functions
# ---------------------------------------------------------------------------

def render(ref: MessageRef, context: ContextStore) -> dict[str, str]:
    """
    Resolves a MessageRef to rendered strings. Raw context values read here.
    Must be called before session.close() wipes the context store.
    """
    template = _REGISTRY.get(ref.urn)
    if not template:
        return {
            "summary": f"[unregistered message: {ref.urn}]",
            "detail":  f"[unregistered message: {ref.urn}]",
        }
    resolved = {name: str(context.value(ctx_ref)) for name, ctx_ref in ref.params_dict().items()}
    return {
        "summary": template["summary"].format(**resolved),
        "detail":  template["detail"].format(**resolved),
    }


def render_token(
    token: OutputToken,
    context: ContextStore | None = None,
    clear: bool = False,
) -> str:
    """
    Renders an OutputToken to a human-readable string.

    clear=False (default, tokenized mode):
      ContextRef params → <ref:key[.path]>  (opaque)
      Literal params    → shown as-is

    clear=True:
      All params resolved; registered 'log' template applied if available.
      Falls back to generic "k=v ..." format if no template or resolution fails.
    """
    def _resolve(param: LogParam) -> str:
        if isinstance(param, ContextRef):
            if clear and context is not None:
                return str(context.value(param))
            ref_str = f"{param.key}.{param.path}" if param.path else param.key
            return f"<ref:{ref_str}>"
        return str(param)

    resolved = {name: _resolve(p) for name, p in token.params_dict().items()}

    if clear:
        log_tmpl = _REGISTRY.get(token.urn, {}).get("log", "")
        if log_tmpl:
            try:
                return log_tmpl.format(**resolved)
            except KeyError:
                pass  # fall through to generic

    parts = [f"{k}={v}" for k, v in resolved.items()]
    return f"[{token.urn}] {' '.join(parts)}"


def serialize_token(token: OutputToken, context: ContextStore) -> dict:
    """
    Fully resolve an OutputToken to a JSON-serializable dict.
    Used by the encrypted session stream — confidentiality is provided by encryption.
    """
    resolved = {}
    for name, param in token.params_dict().items():
        if isinstance(param, ContextRef):
            try:
                resolved[name] = str(context.value(param))
            except KeyError:
                resolved[name] = f"<unresolvable:{param.key}>"
        else:
            resolved[name] = str(param)
    return {"urn": token.urn, "params": resolved}


def serialize_message_ref(ref: MessageRef, context: ContextStore) -> dict:
    """
    Fully resolve a MessageRef to a JSON-serializable dict.
    Used for findings in the encrypted session stream.
    """
    resolved = {}
    for name, ctx_ref in ref.params_dict().items():
        try:
            resolved[name] = str(context.value(ctx_ref))
        except KeyError:
            resolved[name] = f"<unresolvable:{ctx_ref.key}>"
    return {"urn": ref.urn, "params": resolved}


# ---------------------------------------------------------------------------
# Built-in finding message registrations
# ---------------------------------------------------------------------------

register(
    "urn:badbot:poc:msg:bola_detected",
    summary="BOLA: cross-user resource access succeeded",
    detail=(
        "Authenticated as alice (user_id=1) and requested /users/2/orders "
        "using alice's token. Server returned 200 with bob's order data. "
        "The authorization check validates token existence but does not "
        "verify that the token's owner matches the requested user_id."
    ),
)

register(
    "urn:badbot:poc:msg:privilege_escalation",
    summary="Privilege escalation: admin endpoint accessible without admin role",
    detail=(
        "Token issued to '{subject}' with scope '{scope}' and roles {roles} "
        "was accepted by /api/admin. The endpoint validates token authenticity "
        "but does not enforce role requirements."
    ),
)

# ---------------------------------------------------------------------------
# Built-in log token registrations
# ---------------------------------------------------------------------------

register("urn:badbot:poc:log:transition_enter",
         log="Entered state '{step}'")

register("urn:badbot:poc:log:transition_halt",
         log="No step for state '{state}' — halting")

register("urn:badbot:poc:log:transition_fsm_error",
         log="FSM error in '{step}': {error}")

register("urn:badbot:poc:log:request_sent",
         log="{method} {url} -> {status_code}")

register("urn:badbot:poc:log:request_error",
         log="Request error in '{step}': {error}")

register("urn:badbot:poc:log:extraction_ok",
         log="Stored '{key}'")

register("urn:badbot:poc:log:extraction_transform_ok",
         log="Stored '{key}' (transform: {transform})")

register("urn:badbot:poc:log:extraction_not_found",
         log="'{field}' not found in response")

register("urn:badbot:poc:log:extraction_transform_failed",
         log="Transform '{transform}' failed: {error}")

register("urn:badbot:poc:log:finding_recorded",
         log="Finding recorded [{severity}]: {urn}")

register("urn:badbot:poc:log:assertion_failed",
         log="Body assertion failed: {path} — expected not_equals={expected}, got={actual}")

register("urn:badbot:poc:log:loop_iteration",
         log="Iteration {n}/{total}: {method} {url} -> {status_code}")

register("urn:badbot:poc:log:loop_status_never_seen",
         log="Status {status} not observed after {count} requests")

register(
    "urn:badbot:poc:log:for_each_iteration",
    log="Iteration {n}/{total}: {into}={value} {method} {url} -> {status_code}",
)

register(
    "urn:badbot:poc:msg:rate_limit_not_enforced",
    summary="Rate limiting not enforced: endpoint accepted unlimited requests",
    detail=(
        "The endpoint returned 200 for every request in the probe sequence. "
        "No 429 Too Many Requests response was observed. Without rate limiting, "
        "the endpoint is exposed to enumeration, credential stuffing, and "
        "resource exhaustion attacks."
    ),
)

register(
    "urn:badbot:poc:msg:mass_assignment",
    summary="Mass assignment: server accepted and applied a client-supplied protected field",
    detail=(
        "Field '{path}' was submitted with value '{actual}' in the request body. "
        "The server stored and applied the value rather than ignoring it. "
        "Clients should not be able to influence server-controlled fields."
    ),
)

register(
    "urn:badbot:poc:msg:payment_bypass",
    summary="Workflow bypass: checkout confirmed without valid payment",
    detail=(
        "POST to /shop/cart/.../confirm returned a non-402 response without an "
        "accepted payment. The workflow enforcement check is missing or bypassable."
    ),
)

register(
    "urn:badbot:poc:msg:underpayment_accepted",
    summary="Underpayment accepted: server applied below-total payment as full payment",
    detail=(
        "POST to /shop/cart/.../pay returned 200 for an amount below the cart total. "
        "The server accepted the partial payment and marked the cart as paid rather "
        "than enforcing a minimum equal to the cart total."
    ),
)
