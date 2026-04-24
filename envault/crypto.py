"""AES-GCM encryption/decryption for .env file contents."""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # AES-256


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=2**14, r=8, p=1)
    return kdf.derive(passphrase.encode())


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext and return a base64-encoded ciphertext bundle.

    Bundle format: base64(salt || nonce || ciphertext)
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    bundle = salt + nonce + ciphertext
    return base64.b64encode(bundle).decode()


def decrypt(encoded_bundle: str, passphrase: str) -> str:
    """Decrypt a base64-encoded bundle and return the plaintext."""
    bundle = base64.b64decode(encoded_bundle.encode())
    salt = bundle[:SALT_SIZE]
    nonce = bundle[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = bundle[SALT_SIZE + NONCE_SIZE:]
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()
