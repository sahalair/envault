"""Unit tests for envault.crypto encryption/decryption."""

import pytest
from cryptography.exceptions import InvalidTag
from envault.crypto import encrypt, decrypt

PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "DB_HOST=localhost\nDB_PORT=5432\nDB_PASSWORD=hunter2\n"


def test_encrypt_returns_string():
    result = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_produces_different_ciphertexts():
    """Each call should produce a unique ciphertext due to random salt/nonce."""
    c1 = encrypt(PLAINTEXT, PASSPHRASE)
    c2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert c1 != c2


def test_decrypt_roundtrip():
    encoded = encrypt(PLAINTEXT, PASSPHRASE)
    recovered = decrypt(encoded, PASSPHRASE)
    assert recovered == PLAINTEXT


def test_decrypt_wrong_passphrase_raises():
    encoded = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(InvalidTag):
        decrypt(encoded, "wrong-passphrase")


def test_decrypt_tampered_data_raises():
    encoded = encrypt(PLAINTEXT, PASSPHRASE)
    # Flip a character near the end of the bundle
    tampered = encoded[:-4] + "XXXX"
    with pytest.raises(Exception):
        decrypt(tampered, PASSPHRASE)


def test_empty_plaintext_roundtrip():
    encoded = encrypt("", PASSPHRASE)
    assert decrypt(encoded, PASSPHRASE) == ""
