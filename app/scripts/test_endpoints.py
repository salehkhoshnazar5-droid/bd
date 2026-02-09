# scripts/test_endpoints.py
import requests
import json

BASE_URL = "http://localhost:8000"


def test_all_endpoints():
    """تست تمام endpoints."""

    print("🧪 تست تمام endpoints سیستم")
    print("=" * 60)

    # ۱. تست سلامت عمومی
    response = requests.get(f"{BASE_URL}/api/info")
    print(f"   GET /api/info - Status: {response.status_code}")
    if response.ok:
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    # ۲. تست endpoints تست
    print("\n2. تست endpoints تست:")
    endpoints = ["/test", "/test/auth", "/test/db", "/test/health"]

    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"   GET {endpoint} - Status: {response.status_code}")

    # ۳. تست auth برای دریافت توکن
    print("\n3. دریافت توکن برای تست endpoints محافظت شده:")
    login_data = {"username": "00000000", "password": "admin123"}  # ادمین پیش‌فرض

    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   ✅ توکن دریافت شد")

        # ۴. تست endpoints محافظت شده
        print("\n4. تست endpoints محافظت شده:")
        protected_endpoints = [
            "/test/me",
            "/test/admin",
            "/test/users",
            "/test/roles"
        ]

        for endpoint in protected_endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"   GET {endpoint} - Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if endpoint == "/test/users":
                    print(f"     تعداد کاربران: {data.get('total', 0)}")
                elif endpoint == "/test/roles":
                    print(f"     تعداد نقش‌ها: {data.get('total_roles', 0)}")

    else:
        print(f"   ❌ دریافت توکن ناموفق. ابتدا یک کاربر ایجاد کنید.")

        # ایجاد کاربر تستی
        print("\n📝 ایجاد کاربر تستی:")
        register_data = {
            "first_name": "کاربر",
            "last_name": "تستی",
            "student_number": "test12345",
            "national_code": "1111111111",
            "phone_number": "09111111111",
            "gender": "brother",
            "address": "آدرس تست"
        }

        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"   ثبت نام - Status: {response.status_code}")
        print(f"   Response: {response.json()}")


if __name__ == "__main__":
    test_all_endpoints()