"""
C-02 — Context Store (minimal POC implementation)

Enforces the value() / ref() boundary: raw values are accessible only via
value(), which is intended for use by the sequence engine at message
construction time, and by the message registry at render time. All other
consumers call ref() and receive an opaque handle.

ContextRef supports dot-notation paths (e.g. ref("claims.sub")) so that
nested fields within a stored dict can be referenced without exposing the
parent value or requiring a separate store entry per field.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContextRef:
    """
    Opaque handle to a stored context value, optionally navigating into
    a nested field via a dot-notation path.
    """
    key: str
    path: str | None = None  # e.g. "sub" for claims.sub


class ContextStore:
    def __init__(self):
        self._store: dict[str, Any] = {}

    def store(self, key: str, value: Any) -> ContextRef:
        self._store[key] = value
        return ContextRef(key=key)

    def ref(self, key: str) -> ContextRef:
        """
        Returns an opaque handle. Supports dot-notation: ref("claims.sub")
        returns ContextRef(key="claims", path="sub"). Does not expose any value.
        """
        parts = key.split(".", 1)
        base_key = parts[0]
        if base_key not in self._store:
            raise KeyError(f"No context value for key: {base_key!r}")
        return ContextRef(key=base_key, path=parts[1] if len(parts) > 1 else None)

    def value(self, ref: ContextRef) -> Any:
        """
        RESTRICTED — sequence engine and message registry use only.
        Resolves an opaque ref to its raw value, navigating any dot-path.
        """
        if ref.key not in self._store:
            raise KeyError(f"No context value for key: {ref.key!r}")
        val = self._store[ref.key]
        if ref.path:
            for part in ref.path.split("."):
                if isinstance(val, dict):
                    val = val[part]
                elif isinstance(val, list):
                    val = val[int(part)]
                else:
                    raise KeyError(f"Cannot navigate into {type(val).__name__} at '{part}'")
        return val

    def release(self, ref: ContextRef) -> None:
        self._store.pop(ref.key, None)

    def release_all(self) -> None:
        self._store.clear()
