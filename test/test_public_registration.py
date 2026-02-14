import asyncio
import os

from fastapi import BackgroundTasks
from starlette.requests import Request

os.environ.setdefault("ADMIN_LOGIN_PASSWORD", "test-admin")

from app.routers import public_registration


def _make_request(path: str = "/public/register", scheme: str = "https", host: str = "example.com"):
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"host", host.encode())],
        "scheme": scheme,
        "client": ("127.0.0.1", 12345),
        "server": (host, 443),
    }
    return Request(scope)


def test_https_detection_accepts_forwarded_proto():
    request = _make_request(scheme="http")
    request.scope["headers"].append((b"x-forwarded-proto", b"https"))

    assert public_registration._is_https_request(request) is True


def test_submit_public_registration_rejects_invalid_email():
    request = _make_request()
    response = asyncio.run(
        public_registration.submit_public_registration(
            request=request,
            background_tasks=BackgroundTasks(),
            full_name="John Doe",
            email="invalid-email",
            password="Strong!123",
            accept_terms="on",
        )
    )

    assert response.status_code == 400


def test_submit_public_registration_redirects_on_success():
    request = _make_request()
    response = asyncio.run(
        public_registration.submit_public_registration(
            request=request,
            background_tasks=BackgroundTasks(),
            full_name="John Doe",
            email="john@example.com",
            password="Strong!123",
            accept_terms="on",
        )
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/public/thank-you")