"""
C-01 — Message Registry (minimal POC implementation)

MessageRef carries a URN and a map of named ContextRef handles — no raw values.
render() is the only place ContextRef handles are resolved to raw values for
output purposes. This is the POC equivalent of C-01.resolve() called from C-11.

Template strings use {param_name} placeholders, filled at render time only.
"""
from dataclasses import dataclass

from .context_store import ContextRef, ContextStore


@dataclass(frozen=True)
class MessageRef:
    """
    Opaque reference to a message template plus named context handles.
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
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, dict[str, str]] = {}


def register(urn: str, summary: str, detail: str) -> None:
    _REGISTRY[urn] = {"summary": summary, "detail": detail}


def render(ref: MessageRef, context: ContextStore) -> dict[str, str]:
    """
    Resolves a MessageRef to rendered strings. Raw context values are read
    here and only here — the POC equivalent of C-01.resolve() + C-11 render.
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


# ---------------------------------------------------------------------------
# Built-in message registrations
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
