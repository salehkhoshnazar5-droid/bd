from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import hash_password
from app.models.role import Role
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.routers.admin_ui import admin_login

# Ensure relationships are registered
import app.models.audit_log  # noqa: F401


def make_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return testing_session_local()


def seed_admin_user(db):
    admin_role = Role(name="admin", description="admin")
    db.add(admin_role)
    db.flush()

    admin = User(
        student_number="123456789",
        hashed_password=hash_password("123456789"),
        role_id=admin_role.id,
        is_active=True,
    )
    db.add(admin)
    db.flush()

    profile = StudentProfile(
        user_id=admin.id,
        first_name="ادمین",
        last_name="سیستم",
        student_number="123456789",
        national_code="1234512345",
        phone_number="09120001111",
        gender="brother",
        address="تهران",
    )
    db.add(profile)
    db.commit()


def test_admin_login_returns_redirect_and_cookie():
    db = make_db_session()
    seed_admin_user(db)

    response = admin_login(
        national_code="1234512345",
        password="123456789",
        db=db,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"
    assert "access_token=" in response.headers.get("set-cookie", "")


def test_admin_login_invalid_credentials_redirects_to_login():
    db = make_db_session()

    response = admin_login(
        national_code="0000000000",
        password="123456789",
        db=db,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/login?error_message=")