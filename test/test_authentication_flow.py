from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.schemas.auth import RegisterRequest
from app.services.auth_service import authenticate_user, register_user

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