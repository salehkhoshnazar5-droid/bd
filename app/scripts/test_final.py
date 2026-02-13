import requests

BASE_URL = "http://localhost:8000"


def test_final_system():

    print("🧪 تست نهایی سیستم مدیریت بسیج")
    print("=" * 60)

    endpoints = [
        ("/", "صفحه اصلی"),
        ("/health", "سلامت سیستم"),
        ("/api/info", "اطلاعات API"),
        ("/docs", "مستندات Swagger"),
        ("/ui-auth", "رابط کاربری"),
        ("/test", "صفحه تست"),
        ("/auth/register", "ثبت نام API"),
        ("/auth/login", "ورود API")
    ]

    for endpoint, description in endpoints:
        try:
            if endpoint == "/docs":
                response = requests.get(f"{BASE_URL}{endpoint}", allow_redirects=True)
            else:
                response = requests.get(f"{BASE_URL}{endpoint}")

            print(f"✅ {description}: {endpoint}")
            print(f"   Status: {response.status_code}")

            if endpoint == "/docs" and response.status_code == 200:
                print("   📚 Swagger UI loaded successfully")

        except Exception as e:
            print(f"❌ {description}: {endpoint}")
            print(f"   Error: {e}")

    print("\n🎯 سیستم آماده است! دستورات:")
    print("1. اجرای سرور: uvicorn app.main:app --reload")
    print("2. مشاهده مستندات: http://localhost:8000/docs")
    print("3. رابط کاربری: http://localhost:8000/ui-auth")
    print("4. ایجاد ادمین: python scripts/create_admin.py")


if __name__ == "__main__":
    test_final_system()