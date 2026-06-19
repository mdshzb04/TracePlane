import pytest

from app.core import encryption
from app.core.config import settings


def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "test-encryption-key-for-provider-secrets")
    monkeypatch.setattr(settings, "SECRET_KEY", "different-jwt-secret-key-for-tests-32c")
    encryption.encryption_self_test()
    ciphertext = encryption.encrypt_secret("sk-test-openai-key")
    assert encryption.decrypt_secret(ciphertext) == "sk-test-openai-key"


def test_legacy_secret_key_fallback(monkeypatch):
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "")
    monkeypatch.setattr(settings, "SECRET_KEY", "legacy-secret-key-for-tests-min-32-chars")
    legacy_cipher = encryption.encrypt_secret("sk-legacy-key")
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "new-stable-encryption-key-for-prod")
    plaintext, needs_reencrypt = encryption.decrypt_secret_with_migration(legacy_cipher)
    assert plaintext == "sk-legacy-key"
    assert needs_reencrypt is True


def test_decrypt_failure_is_actionable(monkeypatch):
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "key-a-for-encryption-tests-min-len")
    monkeypatch.setattr(settings, "SECRET_KEY", "key-a-for-encryption-tests-min-len")
    ciphertext = encryption.encrypt_secret("sk-test")
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "key-b-for-encryption-tests-min-len")
    monkeypatch.setattr(settings, "SECRET_KEY", "key-b-for-encryption-tests-min-len")
    with pytest.raises(ValueError, match="Reconnect the provider"):
        encryption.decrypt_secret(ciphertext)
