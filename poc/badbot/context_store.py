"""
C-02 — Context Store (minimal POC implementation)

Enforces the value() / ref() boundary: raw values are accessible only via
value(), which is intended for use by the sequence engine at message
construction time, and by the message registry at render time. All other
consumers call ref() and receive an opaque handle.

ContextRef supports dot-notation paths (e.g. ref("claims.sub")) so that
nested fields within a stored dict can be referenced without exposing the
parent value or requiring a separate store entry per field.

Version history: each key maintains an ordered list of values. store() appends;
ref() captures the current version at call time. This ensures that a ContextRef
obtained before a key is overwritten will still resolve to the original value
at archive decrypt time — the context snapshot carries the full history, and
resolution uses the version number frozen into the ref.

Without versioning, overwriting a key would cause earlier log refs to silently
resolve to the later value, making the archive internally inconsistent.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContextRef:
    """
    Opaque handle to a stored context value, optionally navigating into
    a nested field via a dot-notation path.

    version pins this ref to a specific store() call for that key.
    A ref with version=0 resolves to the first value stored under the key;
    version=1 resolves to the second, etc.
    """
    key: str
    path: str | None = None   # e.g. "sub" for claims.sub
    version: int = 0          # index into the key's version history


class ContextStore:
    def __init__(self):
        # Each key maps to an ordered list of stored values (version history).
        self._store: dict[str, list[Any]] = {}

    def store(self, key: str, value: Any) -> ContextRef:
        """
        Store a value under key. If key already exists, appends a new version
        rather than overwriting. Returns a ContextRef pinned to this version.
        """
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(value)
        return ContextRef(key=key, version=len(self._store[key]) - 1)

    def ref(self, key: str) -> ContextRef:
        """
        Returns an opaque handle pinned to the current (latest) version.
        Supports dot-notation: ref("claims.sub") returns
        ContextRef(key="claims", path="sub", version=<current>).
        Does not expose any value.
        """
        parts = key.split(".", 1)
        base_key = parts[0]
        if base_key not in self._store:
            raise KeyError(f"No context value for key: {base_key!r}")
        version = len(self._store[base_key]) - 1
        return ContextRef(
            key=base_key,
            path=parts[1] if len(parts) > 1 else None,
            version=version,
        )

    def value(self, ref: ContextRef) -> Any:
        """
        RESTRICTED — sequence engine and message registry use only.
        Resolves an opaque ref to its raw value using the pinned version,
        then navigates any dot-path.
        """
        history = self._store.get(ref.key)
        if not history:
            raise KeyError(f"No context value for key: {ref.key!r}")
        if ref.version >= len(history):
            raise KeyError(
                f"Context key {ref.key!r} has {len(history)} version(s); "
                f"requested version {ref.version}"
            )
        val = history[ref.version]
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
