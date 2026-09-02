"""Хэширование паролей (без внешних нативных зависимостей)."""

import hashlib
import secrets

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, digest = hashed.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    ).hex()
    return secrets.compare_digest(check, digest)
