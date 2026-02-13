import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, create_database
from app.models.user import User
from app.models.role import Role
from app.models.student_profile import StudentProfile
from app.core.security import hash_password


def test_user_model():
    print("🧪 تست مدل User...")

    create_database()

    db = SessionLocal()

    try:
        user_role = Role(name="user", description="کاربر تست")
        admin_role = Role(name="admin", description="ادمین تست")

        db.add(user_role)
        db.add(admin_role)
        db.commit()

        user1 = User(
            student_number="12345678",
            hashed_password=hash_password("12345678"),
            role_id=user_role.id
        )

        db.add(user1)
        db.commit()
        db.refresh(user1)

        print(f"✅ کاربر ایجاد شد: {user1}")
        print(f"   to_dict(): {user1.to_dict()}")

        profile1 = StudentProfile(
            user_id=user1.id,
            national_code="0012345678",
            phone_number="09121234567",
            gender="brother",
            address="آدرس تست"
        )

        db.add(profile1)
        db.commit()

        print(f"\n🧪 تست propertyها:")
        print(f"   is_admin: {user1.is_admin}")
        print(f"   can('read'): {user1.can('read')}")
        print(f"   can('delete'): {user1.can('delete')}")

        print(f"\n🧪 تست create_simple_user:")
        user2 = User.create_simple_user(
            student_number="87654321",
            password="87654321",
            db_session=db,
            role_name="user"
        )
        print(f"   کاربر ایجاد شد: {user2}")

        print(f"\n🧪 تست query:")
        users = db.query(User).all()
        print(f"   تعداد کاربران: {len(users)}")

        for u in users:
            print(f"   - {u.student_number} (ایجاد: {u.created_at})")

    except Exception as e:
        print(f"❌ خطا: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n🎯 تست مدل User کامل شد!")


if __name__ == "__main__":
    test_user_model()