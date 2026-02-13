import os
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict

from fastapi import Request

from app.core.security import create_access_token, hash_password, verify_password

MAX_ADMIN_LOGIN_ATTEMPTS = int(os.getenv("ADMIN_MAX_LOGIN_ATTEMPTS", "5"))
ADMIN_LOCKOUT_MINUTES = int(os.getenv("ADMIN_LOCKOUT_MINUTES", "15"))

_ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH") or hash_password(
    os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123456")
)

_failed_attempts: Dict[str, Dict[str, datetime | int]] = {}
_attempts_lock = Lock()


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_locked_out(request: Request) -> tuple[bool, int]:
    key = _client_key(request)
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
    locked, minutes = is_locked_out(request)
    if locked:
        return False, f"ورود شما موقتاً قفل شده است. لطفاً {minutes} دقیقه دیگر تلاش کنید."

    if verify_password(password, _ADMIN_PASSWORD_HASH):
        clear_failed_attempts(request)
        return True, None

    key = _client_key(request)
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


def clear_failed_attempts(request: Request) -> None:
    with _attempts_lock:
        _failed_attempts.pop(_client_key(request), None)


def create_admin_token() -> str:
    return create_access_token(data={"sub": "admin", "role": "admin"})


def is_admin_authenticated(request: Request) -> bool:
    token = request.cookies.get("admin_access_token")
    if not token:
        return False

    try:
        from jose import JWTError, jwt
        from app.core.security import SECRET_KEY, ALGORITHM

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") == "admin" and payload.get("role") == "admin"
    except JWTError:
        return False