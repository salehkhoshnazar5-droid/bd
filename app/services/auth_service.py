# app/services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
from app.models.user import User
from app.models.role import Role
from app.models.student_profile import StudentProfile
from app.schemas.auth import RegisterRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


def register_user(db: Session, data: RegisterRequest):
    """
    ثبت کاربر جدید در سیستم.

    Args:
        db: Session دیتابیس
        data: اطلاعات ثبت نام (RegisterRequest)
    """


    existing_user = db.query(User).filter(
        User.student_number == data.student_number
    ).first()


    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="شماره دانشجویی قبلاً ثبت شده است"
        )

    # پیدا کردن نقش کاربر عادی
    role = db.query(Role).filter(Role.name == "user").first()

    if not role:
        # اگر نقش user وجود ندارد، آن را ایجاد کنید
        role = Role(name="user", description="کاربر عادی")
        db.add(role)
        db.commit()
        db.refresh(role)

    # رمز عبور برابر با شماره دانشجویی
    hashed_password = hash_password(data.student_number[:72])

    # ایجاد کاربر
    user = User(
        student_number=data.student_number,
        hashed_password=hashed_password,
        role_id=role.id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # ایجاد پروفایل دانشجویی
    profile = StudentProfile(
        user_id=user.id,
        national_code=data.national_code,
        phone_number=data.phone_number,
        gender=data.gender.value if hasattr(data.gender, 'value') else data.gender,
        address=data.address
    )

    db.add(profile)
    db.commit()

    return user


def authenticate_user(db: Session, student_number: str, password: str):
    """
    احراز هویت کاربر با شماره دانشجویی و رمز عبور.

    Args:
        db: Session دیتابیس
        student_number: شماره دانشجویی
        password: رمز عبور

    Returns:
        User or None: کاربر پیدا شده یا None
    """
    # پیدا کردن کاربر
    user = db.query(User).filter(
        User.student_number == student_number
    ).first()

    # بررسی وجود کاربر و صحت رمز عبور (که در اینجا باید برابر با شماره دانشجویی باشد)
    if not user or not verify_password(password, user.hashed_password):
        return None

    return user
def create_token_for_user(user: User):
    """ ایجاد توکن JWT برای کاربر. Args: user: شیء کاربر Returns: dict: توکن دسترسی """
    access_token_expires =\
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( data={
        "sub": user.student_number,
        "user_id": user.id,
        "role": user.role.name if user.role else
        "user" },
                                        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }








