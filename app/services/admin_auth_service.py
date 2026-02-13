import os
import logging
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict
from jose import JWTError, jwt
from fastapi import Request

from app.core.security import create_access_token, hash_password, verify_password, SECRET_KEY, ALGORITHM

MAX_ADMIN_LOGIN_ATTEMPTS = int(os.getenv("ADMIN_MAX_LOGIN_ATTEMPTS", "5"))
ADMIN_LOCKOUT_MINUTES = int(os.getenv("ADMIN_LOCKOUT_MINUTES", "15"))
logger = logging.getLogger(__name__)

def _looks_like_bcrypt_hash(value: str) -> bool:
    return value.startswith(("$2a$", "$2b$", "$2y$")) and len(value) >= 60


def _resolve_admin_password_hash() -> str:
    configured_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if configured_hash:
        if _looks_like_bcrypt_hash(configured_hash):
            logger.debug("Using ADMIN_PASSWORD_HASH from environment for admin auth.")
            return configured_hash

        logger.warning(
            "ADMIN_PASSWORD_HASH is set but does not look like a bcrypt hash; "
            "treating it as plain password and hashing once at startup."
        )
        return hash_password(configured_hash)

    fallback_password = os.getenv("ADMIN_LOGIN_PASSWORD") or os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123456")
    logger.debug("ADMIN_PASSWORD_HASH not set; deriving hash from ADMIN_LOGIN_PASSWORD/ADMIN_DEFAULT_PASSWORD.")
    return hash_password(fallback_password)


_ADMIN_PASSWORD_HASH = _resolve_admin_password_hash()

_failed_attempts: Dict[str, Dict[str, datetime | int]] = {}
_attempts_lock = Lock()


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _client_identifier(request: Request) -> str:
    return get_client_identifier(request)

def _client_key(request: Request) -> str:
    """Backward-compatible alias used by older callers."""
    return get_client_identifier(request)

def is_locked_out(request: Request) -> tuple[bool, int]:
    key = _client_identifier(request)
    now = datetime.now(timezone.utc)

    with _attempts_lock:
        entry = _failed_attempts.get(key)
        if not entry:
            return False, 0

        locked_until = entry.get("locked_until")
        if isinstance(locked_until, datetime) and locked_until > now:
            remaining_seconds = int((locked_until - now).total_seconds())
            return True, max(1, remaining_seconds // 60)

        if isinstance(locked_until, datetime) and locked_until <= now:
            _failed_attempts.pop(key, None)

    return False, 0


def authenticate_admin_password(request: Request, password: str) -> tuple[bool, str | None]:
    try:
        normalized_password = password.strip()
        locked, minutes = is_locked_out(request)
        if locked:
            return False, f"ورود شما موقتاً قفل شده است. لطفاً {minutes} دقیقه دیگر تلاش کنید."

        password_matches = verify_password(normalized_password, _ADMIN_PASSWORD_HASH)
        logger.debug(
            "Admin password verification result=%s client=%s raw_len=%d normalized_len=%d hash_prefix=%s",
            password_matches,
            get_client_identifier(request),
            len(password),
            len(normalized_password),
            _ADMIN_PASSWORD_HASH[:7],
        )

        if password_matches:
            clear_failed_attempts(request)
            return True, None

        key = get_client_identifier(request)
        now = datetime.now(timezone.utc)

        with _attempts_lock:
            entry = _failed_attempts.get(key, {"count": 0, "locked_until": None})
            entry["count"] = int(entry["count"]) + 1

            if entry["count"] >= MAX_ADMIN_LOGIN_ATTEMPTS:
                entry["locked_until"] = now + timedelta(minutes=ADMIN_LOCKOUT_MINUTES)
                _failed_attempts[key] = entry
                return (
                    False,
                    f"به دلیل ورود ناموفق متوالی، دسترسی شما به مدت {ADMIN_LOCKOUT_MINUTES} دقیقه قفل شد.",
                )

            _failed_attempts[key] = entry
            remaining = MAX_ADMIN_LOGIN_ATTEMPTS - int(entry["count"])

        return False, f"رمز عبور ادمین اشتباه است. {remaining} تلاش دیگر باقی مانده است."
    except Exception:
        logger.exception("admin authentication failed unexpectedly")
        return False, "خطای داخلی در احراز هویت مدیر. لطفاً دوباره تلاش کنید."


def clear_failed_attempts(request: Request) -> None:
    with _attempts_lock:
        _failed_attempts.pop(get_client_identifier(request), None)


def create_admin_token() -> str:
    return create_access_token(data={"sub": "admin", "role": "admin"})


def is_admin_authenticated(request: Request) -> bool:
    token = request.cookies.get("admin_access_token")
    if not token:
        return False

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") == "admin" and payload.get("role") == "admin"
    except JWTError as e:
        logger.exception("خطای پردازش توکن JWT رخ داده است.")
        return False
