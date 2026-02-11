from types import SimpleNamespace

from app.services import admin_auth_service


class DummyRequest:
    def __init__(self, ip: str):
        self.headers = {"x-forwarded-for": ip}
        self.client = SimpleNamespace(host=ip)
        self.cookies = {}


def test_admin_auth_rejects_invalid_password_with_error_message():
    request = DummyRequest("10.10.10.1")

    authenticated, message = admin_auth_service.authenticate_admin_password(request, "wrong-password")

    assert authenticated is False
    assert "رمز عبور ادمین اشتباه است" in message


def test_admin_auth_locks_after_five_failed_attempts():
    global authenticated
    request = DummyRequest("10.10.10.2")

    last_message = None
    for _ in range(5):
        authenticated, last_message = admin_auth_service.authenticate_admin_password(request, "wrong-password")

    assert authenticated is False
    assert "قفل" in last_message


def test_admin_auth_accepts_default_password_and_creates_token():
    request = DummyRequest("10.10.10.3")

    authenticated, message = admin_auth_service.authenticate_admin_password(request, "admin123456")

    assert authenticated is True
    assert message is None

    token = admin_auth_service.create_admin_token()
    request.cookies["admin_access_token"] = token

    assert admin_auth_service.is_admin_authenticated(request) is True