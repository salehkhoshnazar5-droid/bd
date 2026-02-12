from fastapi.testclient import TestClient
from app.main import app


def test_admin_login_accepts_form_urlencoded_password_body():
    # ایجاد یک شیء TestClient
    client = TestClient(app)

    # ارسال درخواست POST به مسیر login با داده‌های form-urlencoded
    response = client.post("/admin/login", data={"password": "admin123"})

    # بررسی اینکه آیا پاسخ درست است
    assert response.json() == {"detail": "ورود ادمین موفق بود"}


def test_admin_login_accepts_json_password_body():
    # ایجاد یک شیء TestClient
    client = TestClient(app)

    # ارسال درخواست POST به مسیر login با داده‌های JSON
    response = client.post("/admin/login", json={"password": "admin123"})

    # بررسی اینکه آیا پاسخ درست است
    assert response.json() == {"detail": "ورود ادمین موفق بود"}


def test_admin_login_rejects_wrong_password_with_401():
    # ایجاد یک شیء TestClient
    client = TestClient(app)

    # ارسال درخواست POST با رمز عبور اشتباه
    response = client.post("/admin/login", json={"password": "wrong-password"})

    # بررسی اینکه آیا خطای 401 بازگشت داده می‌شود
    assert response.status_code == 401
    assert response.json() == {"detail": "رمز عبور ادمین اشتباه است"}
