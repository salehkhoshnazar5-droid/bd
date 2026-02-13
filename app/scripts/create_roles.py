import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.core.database import SessionLocal, create_database
from app.models.role import Role


def create_default_roles():
    print("=" * 50)
    print("📝 ایجاد نقش‌های پیش‌فرض سیستم بسیج")
    print("=" * 50)

    create_database()

    db = SessionLocal()

    default_roles = [
        {
            "name": "user",
            "description": "کاربر عادی سیستم - دانشجو"
        },
        {
            "name": "admin",
            "description": "مدیر سیستم - دسترسی کامل"
        }
    ]

    created_count = 0
    for role_data in default_roles:
        role_name = role_data["name"]

        existing_role = db.query(Role).filter(Role.name == role_name).first()

        if not existing_role:
            role = Role(
                name=role_name,
                description=role_data["description"]
            )
            db.add(role)
            created_count += 1
            print(f"✅ نقش '{role_name}' ایجاد شد")
        else:
            print(f"ℹ️ نقش '{role_name}' از قبل وجود دارد")

    db.commit()
    db.close()

    print("=" * 50)
    print(f"🎯 عملیات کامل شد. {created_count} نقش جدید ایجاد شد.")
    print("=" * 50)


if __name__ == "__main__":
    create_default_roles()