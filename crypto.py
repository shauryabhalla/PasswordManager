"""
crypto.py — Encryption/decryption helpers using Fernet + PBKDF2.

Handles:
  - Deriving an encryption key from a master password + salt
  - Encrypting/decrypting the password store JSON
  - First-run salt generation
"""

import os
import json
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_FILE = "salt.bin"
PASSWORDS_FILE = "passwords.enc"
SALT_LENGTH = 32
KDF_ITERATIONS = 600_000  # OWASP recommended minimum for PBKDF2-SHA256


def _get_app_dir() -> str:
    """Return the directory where this script lives (co-located data files)."""
    return os.path.dirname(os.path.abspath(__file__))


def _salt_path() -> str:
    return os.path.join(_get_app_dir(), SALT_FILE)


def _passwords_path() -> str:
    return os.path.join(_get_app_dir(), PASSWORDS_FILE)


def _ensure_salt() -> bytes:
    """Load existing salt or generate a new one on first run."""
    path = _salt_path()
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    salt = os.urandom(SALT_LENGTH)
    with open(path, "wb") as f:
        f.write(salt)
    return salt


def derive_key(master_password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from the master password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))
    return key


def load_passwords(master_password: str) -> list[dict]:
    """
    Decrypt and return the password list from passwords.enc.

    Returns an empty list if the file doesn't exist yet (first run).
    Raises ValueError if the master password is wrong.
    """
    salt = _ensure_salt()
    key = derive_key(master_password, salt)
    fernet = Fernet(key)

    path = _passwords_path()
    if not os.path.exists(path):
        # First run — create an empty encrypted store
        save_passwords(master_password, [])
        return []

    with open(path, "rb") as f:
        encrypted = f.read()

    try:
        decrypted = fernet.decrypt(encrypted)
    except InvalidToken:
        raise ValueError("Wrong master password or corrupted data.")

    return json.loads(decrypted.decode("utf-8"))


def save_passwords(master_password: str, passwords: list[dict]) -> None:
    """Encrypt and write the password list to passwords.enc."""
    salt = _ensure_salt()
    key = derive_key(master_password, salt)
    fernet = Fernet(key)

    plaintext = json.dumps(passwords, indent=2).encode("utf-8")
    encrypted = fernet.encrypt(plaintext)

    with open(_passwords_path(), "wb") as f:
        f.write(encrypted)


def change_master_password(old_password: str, new_password: str) -> list[dict]:
    """
    Verify old_password against the existing vault, then re-encrypt
    everything under new_password using a freshly generated salt.

    Raises ValueError if old_password is wrong.
    """
    passwords = load_passwords(old_password)

    # Fresh salt so the new key isn't derived alongside the old one.
    salt = os.urandom(SALT_LENGTH)
    with open(_salt_path(), "wb") as f:
        f.write(salt)

    save_passwords(new_password, passwords)
    return passwords


def decrypt_to_temp(master_password: str) -> str:
    """
    Decrypt passwords.enc to a temporary JSON file for editing.
    Returns the path to the temp file.
    """
    passwords = load_passwords(master_password)
    temp_path = os.path.join(_get_app_dir(), "passwords_TEMP.json")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(passwords, f, indent=2)
    return temp_path


def encrypt_from_temp(master_password: str) -> list[dict]:
    """
    Read the temporary JSON file, re-encrypt it, delete the temp file.
    Returns the updated password list.
    """
    temp_path = os.path.join(_get_app_dir(), "passwords_TEMP.json")
    if not os.path.exists(temp_path):
        raise FileNotFoundError("Temporary password file not found.")

    with open(temp_path, "r", encoding="utf-8") as f:
        passwords = json.load(f)

    save_passwords(master_password, passwords)

    # Securely-ish delete the temp file
    os.remove(temp_path)
    return passwords
