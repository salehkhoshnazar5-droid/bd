from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.role import Role
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.student import StudentProfileUpdate
from app.services.student_service import update_my_profile


def make_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return testing_session_local()


def _create_user_with_profile(db, student_number: str, national_code: str, phone_number: str):
    role = db.query(Role).filter(Role.name == "user").first()
    if role is None:
        role = Role(name="user", description="کاربر عادی")
        db.add(role)
        db.flush()

    user = User(student_number=student_number, hashed_password="hashed", role_id=role.id)
    db.add(user)
    db.flush()

    profile = StudentProfile(
        user_id=user.id,
        first_name="علی",
        last_name="کاربر",
        national_code=national_code,
        student_number=student_number,
        phone_number=phone_number,
        gender="brother",
        address="تهران",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def test_update_my_profile_rejects_duplicate_phone_number():
    db = make_db_session()

    _create_user_with_profile(db, "100000001", "0012345678", "09120000001")
    user = _create_user_with_profile(db, "100000002", "0012345679", "09120000002")

    try:
        update_my_profile(db, user, StudentProfileUpdate(phone_number="09120000001"))
        assert False, "Expected HTTPException for duplicate phone number"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "شماره تلفن" in exc.detail