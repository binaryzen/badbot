"""
Session serialization and AES-GCM encryption.

encrypt_session() produces an opaque byte stream suitable for storage or
transmission. The stream is authenticated — any tampering raises InvalidTag
on decrypt. The session ID is stored as a plaintext prefix so it can be
read before decryption and fed into the GCM authentication check without
needing any external sidecar.

Wire format: [36-byte session_id ASCII] [12-byte nonce] [ciphertext + 16-byte GCM tag]

The session_id prefix is authenticated (AAD) but not encrypted — it binds
the ciphertext to its session. An archive from session A cannot be presented
as session B's archive without failing the authentication check.

Usage:
    from badbot.output import encrypt_session, decrypt_session

    ciphertext, key = encrypt_session(session)   # key = 32 random bytes
    data = decrypt_session(ciphertext, key)       # raises InvalidTag on tamper
"""
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .messages import serialize_message_ref, serialize_token
from .session import Session


def _build_payload(session: Session) -> dict:
    """Serialize session log + findings to a plain dict (all refs resolved)."""
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
                "token": serialize_token(entry.message, session.context),
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
                "token": serialize_message_ref(finding.message, session.context),
            }
            for finding in session.findings
        ],
    }


def encrypt_session(session: Session, key: bytes | None = None) -> tuple[bytes, bytes]:
    """
    Serialize and AES-GCM encrypt the session log + findings.

    Must be called before session.close() — context values must still be live.

    Returns:
        (encrypted_bytes, key)
        key is 32 random bytes if not supplied; caller is responsible for storing it.

    Associated data: session_id bytes bind the ciphertext to the session.
    """
    if key is None:
        key = os.urandom(32)

    plaintext = json.dumps(_build_payload(session), indent=2).encode()
    nonce = os.urandom(12)
    aad = session.id.encode()  # 36 ASCII bytes; authenticated but not encrypted

    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    # Prepend session_id as plaintext so decrypt_session can recover it
    # without a sidecar. The GCM tag covers it via AAD.
    return aad + nonce + ciphertext, key


def decrypt_session(data: bytes, key: bytes) -> dict:
    """
    Decrypt and return the session payload dict.
    Session ID is read from the plaintext prefix and authenticated via GCM AAD.
    Raises cryptography.exceptions.InvalidTag if the ciphertext has been tampered.
    """
    aad, nonce, ciphertext = data[:36], data[36:48], data[48:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, aad)
    return json.loads(plaintext)
