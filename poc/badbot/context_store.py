"""
C-02 — Context Store (minimal POC implementation)

Enforces the value() / ref() boundary: raw values are accessible only via
value(), which is intended for use by the sequence engine at message
construction time. All other consumers call ref() and receive an opaque handle.

In the full implementation this boundary would be enforced at the type level
(value() raises a type error for callers outside the sequence engine). In the
POC it is enforced by convention and documented restriction.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContextRef:
    """Opaque handle to a stored context value. Carries no raw data."""
    key: str


class ContextStore:
    def __init__(self):
        self._store: dict[str, Any] = {}

    def store(self, key: str, value: Any) -> ContextRef:
        self._store[key] = value
        return ContextRef(key=key)

    def value(self, ref: ContextRef) -> Any:
        """
        RESTRICTED — sequence engine use only.
        Resolves an opaque ref to its raw value at message construction time.
        """
        if ref.key not in self._store:
            raise KeyError(f"No context value for key: {ref.key!r}")
        return self._store[ref.key]

    def ref(self, key: str) -> ContextRef:
        """Returns an opaque handle. Does not expose the raw value."""
        if key not in self._store:
            raise KeyError(f"No context value for key: {key!r}")
        return ContextRef(key=key)

    def release(self, ref: ContextRef) -> None:
        self._store.pop(ref.key, None)

    def release_all(self) -> None:
        self._store.clear()
