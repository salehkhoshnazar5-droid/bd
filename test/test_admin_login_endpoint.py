import asyncio

from fastapi import HTTPException

from app.routers.admin_auth import admin_login


class DummyRequest:
    def __init__(self, content_type: str, payload):
        self.headers = {"content-type": content_type}
        self._payload = payload

    async def json(self):
        if isinstance(self._payload, dict):
            return self._payload
        raise ValueError("no json body")

    async def form(self):
        if isinstance(self._payload, dict):
            return self._payload
        raise ValueError("no form body")


def test_admin_login_accepts_form_urlencoded_password_body():
    request = DummyRequest("application/x-www-form-urlencoded", {"password": "admin123"})

    response = asyncio.run(admin_login(request))

    assert response["detail"] == "ورود ادمین موفق بود"


def test_admin_login_accepts_json_password_body():
    request = DummyRequest("application/json", {"password": "admin123"})

    response = asyncio.run(admin_login(request))

    assert response["detail"] == "ورود ادمین موفق بود"


def test_admin_login_rejects_wrong_password_with_401():
    request = DummyRequest("application/json", {"password": "wrong-password"})

    try:
        asyncio.run(admin_login(request))
        assert False, "Expected HTTPException for wrong password"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "رمز عبور ادمین اشتباه است"