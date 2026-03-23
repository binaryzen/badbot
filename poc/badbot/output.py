"""
Session serialization and AES-GCM encryption.

encrypt_session() produces an opaque byte stream suitable for storage or
transmission. The stream is authenticated — any tampering raises InvalidTag
on decrypt. Associated data (session_id) binds the ciphertext to its session.

Wire format: [12-byte nonce][ciphertext + 16-byte GCM tag]

Usage:
    from badbot.output import encrypt_session, decrypt_session

    ciphertext, key = encrypt_session(session)       # key = 32 random bytes
    data = decrypt_session(ciphertext, key, session.id)  # raises on tamper
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
    aad = session.id.encode()

    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    return nonce + ciphertext, key


def decrypt_session(data: bytes, key: bytes, session_id: str) -> dict:
    """
    Decrypt and return the session payload dict.
    Raises cryptography.exceptions.InvalidTag if the ciphertext has been tampered.
    """
    nonce, ciphertext = data[:12], data[12:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, session_id.encode())
    return json.loads(plaintext)
