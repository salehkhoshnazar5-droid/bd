from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.schemas.auth import RegisterRequest
from app.services.auth_service import (
    authenticate_user,
    enforce_single_national_id_authentication,
    register_user,
)

# Ensure SQLAlchemy relationships are fully registered for tests
import app.models.audit_log  # noqa: F401
import app.models.role  # noqa: F401
import app.models.student_profile  # noqa: F401
import app.models.user  # noqa: F401


def make_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return testing_session_local()


def test_register_then_authenticate_with_national_code_and_student_number():
    db = make_db_session()
    payload = RegisterRequest(
        first_name="علی",
        last_name="رضایی",
        student_number="123456789",
        national_code="0123456789",
        phone_number="09123456789",
        gender="brother",
        address="تهران",
    )

    register_user(db, payload)

    authenticated_user = authenticate_user(db, "0123456789", "123456789")

    assert authenticated_user is not None
    assert authenticated_user.student_number == "123456789"


def test_authenticate_user_fails_with_wrong_student_number():
    db = make_db_session()
    payload = RegisterRequest(
        first_name="فاطمه",
        last_name="محمدی",
        student_number="987654321",
        national_code="1111122222",
        phone_number="09111111111",
        gender="sister",
        address="قم",
    )

    register_user(db, payload)

    authenticated_user = authenticate_user(db, "1111122222", "123456789")

    assert authenticated_user is None


def test_enforce_single_national_id_authentication_is_idempotent_for_valid_user_logins():
    db = make_db_session()
    payload = RegisterRequest(
        first_name="مهدی",
        last_name="کاظمی",
        student_number="555666777",
        national_code="2222233333",
        phone_number="09351234567",
        gender="brother",
        address="اصفهان",
    )

    user = register_user(db, payload)

    # First successful authentication marks the profile as authenticated
    enforce_single_national_id_authentication(db, user)

    refreshed_user = authenticate_user(db, "2222233333", "555666777")
    assert refreshed_user is not None
    assert refreshed_user.profile.has_authenticated is True

    # Subsequent successful logins should not be blocked
    enforce_single_national_id_authentication(db, refreshed_user)

    authenticated_again = authenticate_user(db, "2222233333", "555666777")
    assert authenticated_again is not None
    assert authenticated_again.student_number == "555666777"


def test_authenticate_admin_user_with_non_numeric_password():
    db = make_db_session()

    from app.models.role import Role
    from app.models.user import User
    from app.models.student_profile import StudentProfile
    from app.core.security import hash_password

    admin_role = Role(name="admin", description="Administrator")
    db.add(admin_role)
    db.flush()

    admin_user = User(
        student_number="000000000",
        hashed_password=hash_password("admin123"),
        role_id=admin_role.id,
    )
    db.add(admin_user)
    db.flush()

    profile = StudentProfile(
        user_id=admin_user.id,
        first_name="ادمین",
        last_name="سیستم",
        national_code="0000000000",
        student_number="000000000",
        phone_number="09120000000",
        gender="brother",
        address="دفتر",
    )
    db.add(profile)
    db.commit()

    authenticated_user = authenticate_user(db, "0000000000", "admin123")

    assert authenticated_user is not None
    assert authenticated_user.id == admin_user.id


def test_authenticate_admin_user_rejects_wrong_password():
    db = make_db_session()

    from app.models.role import Role
    from app.models.user import User
    from app.models.student_profile import StudentProfile
    from app.core.security import hash_password

    admin_role = Role(name="admin", description="Administrator")
    db.add(admin_role)
    db.flush()

    admin_user = User(
        student_number="000000000",
        hashed_password=hash_password("admin123"),
        role_id=admin_role.id,
    )
    db.add(admin_user)
    db.flush()

    profile = StudentProfile(
        user_id=admin_user.id,
        first_name="ادمین",
        last_name="سیستم",
        national_code="0000000000",
        student_number="000000000",
        phone_number="09120000000",
        gender="brother",
        address="دفتر",
    )
    db.add(profile)
    db.commit()

    authenticated_user = authenticate_user(db, "0000000000", "wrong-password")

    assert authenticated_user is None