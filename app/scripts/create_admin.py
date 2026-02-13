import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.student_profile import StudentProfile
from app.core.security import hash_password


def create_admin_user():
    db = SessionLocal()

    admin_role = db.query(Role).filter(Role.name == "admin").first()

    if not admin_role:
        print("❌ نقش admin وجود ندارد. اول roles را ایجاد کنید.")
        return

    admin_user = db.query(User).filter(User.student_number == "00000000").first()

    if admin_user:
        print("ℹ️ کاربر ادمین از قبل وجود دارد")
        return admin_user

    admin_user = User(
        student_number="00000000",
        hashed_password=hash_password("admin123"),
        role_id=admin_role.id
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    profile = StudentProfile(
        user_id=admin_user.id,
        national_code="0000000000",
        phone_number="09120000000",
        gender="brother",
        address="دفتر مرکزی"
    )

    db.add(profile)
    db.commit()

    print("✅ کاربر ادمین ایجاد شد:")
    print(f"   شماره دانشجویی: 00000000")
    print(f"   رمز عبور: admin123")
    print(f"   نقش: admin")

    db.close()
    return admin_user


if __name__ == "__main__":
    create_admin_user()