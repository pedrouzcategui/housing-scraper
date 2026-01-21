from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass


PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 310_000
PBKDF2_SALT_BYTES = 16
PBKDF2_HASH_BYTES = 32


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(encoded: str) -> bytes:
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty")

    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=PBKDF2_HASH_BYTES,
    )

    return "pbkdf2_{alg}${iter}${salt}${hash}".format(
        alg=PBKDF2_ALGORITHM,
        iter=PBKDF2_ITERATIONS,
        salt=_b64url_encode(salt),
        hash=_b64url_encode(derived),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations, salt_b64, hash_b64 = stored_hash.split("$", 3)
        if not scheme.startswith("pbkdf2_"):
            return False

        alg = scheme.removeprefix("pbkdf2_")
        iter_int = int(iterations)
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(hash_b64)

        derived = hashlib.pbkdf2_hmac(
            alg,
            password.encode("utf-8"),
            salt,
            iter_int,
            dklen=len(expected),
        )
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def _get_secret_key() -> str:
    # In production, set JWT_SECRET_KEY.
    return os.getenv("JWT_SECRET_KEY", "dev-insecure-secret")


@dataclass(frozen=True)
class TokenPayload:
    sub: str
    exp: int


def create_access_token(*, subject: str, expires_in_seconds: int = 60 * 60) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"sub": str(subject), "exp": now + int(expires_in_seconds)}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    signature = hmac.new(
        _get_secret_key().encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> TokenPayload:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(
            _get_secret_key().encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(_b64url_decode(sig_b64), expected_sig):
            raise ValueError("Invalid token signature")

        payload = json.loads(_b64url_decode(payload_b64))
        sub = payload.get("sub")
        exp = payload.get("exp")
        if not sub or not isinstance(exp, int):
            raise ValueError("Invalid token payload")
        if int(time.time()) >= exp:
            raise ValueError("Token expired")

        return TokenPayload(sub=str(sub), exp=int(exp))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Invalid token") from exc
