import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)

_DECRYPT_ERROR = (
    "Stored provider credentials cannot be decrypted. "
    "Reconnect the provider in Settings → Providers."
)


def _fernet_from_material(material: str) -> Fernet:
    """Build a Fernet instance from a dedicated key or arbitrary secret string."""
    raw = material.strip()
    if not raw:
        raise ValueError("Encryption material must not be empty")
    # Accept a pre-generated Fernet key (44 url-safe chars).
    if len(raw) == 44 and raw.endswith("="):
        try:
            return Fernet(raw.encode("utf-8"))
        except Exception:
            pass
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _fernet_candidates() -> list[tuple[str, Fernet]]:
    """Ordered Fernet keys used for decrypt (primary first, then legacy fallbacks)."""
    candidates: list[tuple[str, Fernet]] = []
    seen: set[str] = set()

    def add(label: str, material: str) -> None:
        material = material.strip()
        if not material or material in seen:
            return
        seen.add(material)
        candidates.append((label, _fernet_from_material(material)))

    if settings.ENCRYPTION_KEY.strip():
        add("encryption_key", settings.ENCRYPTION_KEY)
    add("secret_key", settings.SECRET_KEY)
    return candidates


def primary_fernet() -> Fernet:
    if settings.ENCRYPTION_KEY.strip():
        return _fernet_from_material(settings.ENCRYPTION_KEY)
    return _fernet_from_material(settings.SECRET_KEY)


def encrypt_secret(value: str) -> str:
    return primary_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    plaintext, _ = decrypt_secret_with_migration(value)
    return plaintext


def decrypt_secret_with_migration(value: str) -> tuple[str, bool]:
    """
    Decrypt a stored secret.

    Returns (plaintext, needs_reencrypt) where needs_reencrypt is True when an
    older/legacy Fernet key was used so callers can rewrite storage.
    """
    token = value.strip()
    if not token:
        raise ValueError(_DECRYPT_ERROR)

    candidates = _fernet_candidates()
    if not candidates:
        raise ValueError(_DECRYPT_ERROR)

    primary_label, primary = candidates[0]
    last_exc: InvalidToken | None = None

    for label, fernet in candidates:
        try:
            plaintext = fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            needs_reencrypt = label != primary_label
            if needs_reencrypt:
                logger.info("Decrypted secret with legacy key %s; will re-encrypt", label)
            return plaintext, needs_reencrypt
        except InvalidToken as exc:
            last_exc = exc
            continue

    logger.warning("Failed to decrypt stored secret with %d key candidate(s)", len(candidates))
    raise ValueError(_DECRYPT_ERROR) from last_exc


def encryption_self_test() -> None:
    """Validate encrypt/decrypt roundtrip at startup."""
    sample = "traceplane-encryption-self-test"
    roundtrip = decrypt_secret(encrypt_secret(sample))
    if roundtrip != sample:
        raise RuntimeError("Encryption self-test failed")
