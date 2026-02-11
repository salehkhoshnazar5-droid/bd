from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user

# Ensure SQLAlchemy relationships are fully registered for tests
import app.models.audit_log  # noqa: F401
import app.models.role  # noqa: F401
import app.models.student_profile  # noqa: F401
import app.models.user  # noqa: F401


def make_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def valid_payload(**overrides):
    payload = {
        "first_name": "علی",
        "last_name": "رضایی",
        "student_number": "123456789",
        "national_code": "0123456789",
        "phone_number": "09123456789",
        "gender": "brother",
        "address": "تهران",
    }
    payload.update(overrides)
    return payload


def test_register_request_accepts_exact_digit_lengths():
    data = RegisterRequest(**valid_payload())

    assert data.student_number == "123456789"
    assert data.national_code == "0123456789"
    assert data.phone_number == "09123456789"


def test_register_request_rejects_invalid_national_code_message():
    try:
        RegisterRequest(**valid_payload(national_code="12345abcde"))
        assert False, "ValidationError expected"
    except ValidationError as exc:
        assert "کد ملی معتبر نیست" in str(exc)


def test_register_request_rejects_invalid_student_number():
    try:
        RegisterRequest(**valid_payload(student_number="12345abcd"))
        assert False, "ValidationError expected"
    except ValidationError as exc:
        assert "شماره دانشجویی باید ۹ رقم باشد" in str(exc)


def test_register_request_rejects_invalid_phone_number():
    try:
        RegisterRequest(**valid_payload(phone_number="09123abc890"))
        assert False, "ValidationError expected"
    except ValidationError as exc:
        assert "شماره تماس باید ۱۱ رقم باشد" in str(exc)


def test_register_user_enforces_uniqueness_for_all_fields():
    db = make_db_session()

    first_user = RegisterRequest(**valid_payload())
    register_user(db, first_user)

    duplicate_student = RegisterRequest(**valid_payload(
        student_number="123456789",
        national_code="1111111111",
        phone_number="09999999999",
    ))
    try:
        register_user(db, duplicate_student)
        assert False, "HTTPException expected"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "این شماره دانشجویی قبلاً ثبت شده است"

    duplicate_national_code = RegisterRequest(**valid_payload(
        student_number="987654321",
        national_code="0123456789",
        phone_number="09888888888",
    ))
    try:
        register_user(db, duplicate_national_code)
        assert False, "HTTPException expected"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "این کد ملی قبلاً ثبت شده است"

    duplicate_phone = RegisterRequest(**valid_payload(
        student_number="456456456",
        national_code="2222222222",
        phone_number="09123456789",
    ))
    try:
        register_user(db, duplicate_phone)
        assert False, "HTTPException expected"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "این شماره تلفن قبلاً ثبت شده است"