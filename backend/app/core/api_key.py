import hashlib
import secrets


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, key_hash, key_prefix)."""
    raw = secrets.token_urlsafe(32)
    full_key = f"aoh_{raw}"
    key_hash = hash_api_key(full_key)
    key_prefix = full_key[:12]
    return full_key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
