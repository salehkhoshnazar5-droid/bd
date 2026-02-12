from fastapi.testclient import TestClient
from app.main import app  # اپ FastAPI خود را وارد کنید

def test_admin_auth_rejects_invalid_password_with_error_message():
    # ایجاد یک شیء TestClient
    client = TestClient(app)

    # ارسال درخواست POST به مسیر مناسب برای تست
    response = client.post("/admin/authenticate", data={"password": "wrong-password"})

    # بررسی اینکه آیا پاسخ درست است
    assert response.status_code == 400  # وضعیت خطا در صورت رمز عبور اشتباه
    assert "رمز عبور ادمین اشتباه است" in response.json()["detail"]

def test_admin_auth_locks_after_five_failed_attempts():
    # ایجاد یک شیء TestClient
    global response
    client = TestClient(app)

    # ارسال درخواست‌های اشتباه
    for _ in range(5):
        response = client.post("/admin/authenticate", data={"password": "wrong-password"})

    # بررسی اینکه آیا پس از 5 تلاش اشتباه قفل شده است
    assert response.status_code == 400
    assert "قفل" in response.json()["detail"]

def test_admin_auth_accepts_default_password_and_creates_token():
    # ایجاد یک شیء TestClient
    client = TestClient(app)

    # ارسال درخواست با رمز عبور درست
    response = client.post("/admin/authenticate", data={"password": "admin123456"})

    # بررسی اینکه آیا وارد شده است
    assert response.status_code == 200
    assert "admin_access_token" in response.cookies  # بررسی اینکه توکن در کوکی‌ها وجود دارد

    # بررسی اینکه آیا توکن معتبر است
    token = response.cookies["admin_access_token"]
    response = client.get("/admin/profile", cookies={"admin_access_token": token})
    assert response.status_code == 200  # بررسی وضعیت در صورت تایید ورود
