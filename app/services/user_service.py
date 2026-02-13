from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.student_profile import StudentProfile
from app.models.user import User
from app.models.role import Role
from app.schemas.student import StudentProfileUpdate, AdminStudentUpdate
from app.core.security import hash_password


def _check_uniqueness(
    db: Session,
    national_code: str,
    student_number: str,
    exclude_user_id: int,
):

    conflict = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id != exclude_user_id,
            (StudentProfile.national_code == national_code)
            | (StudentProfile.student_number == student_number),
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کد ملی یا شماره دانشجویی تکراری است",
        )

    user_conflict = (
        db.query(User)
        .filter(User.student_number == student_number, User.id != exclude_user_id)
        .first()
    )
    if user_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="شماره دانشجویی تکراری است",
        )


def get_my_profile(db: Session, user: User) -> StudentProfile:

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد")
    return profile


def update_my_profile(
    db: Session,
    user: User,
    data: StudentProfileUpdate,
) -> StudentProfile:

    profile = get_my_profile(db, user)
    national_code = data.national_code if data.national_code is not None else profile.national_code
    _check_uniqueness(
        db,
        national_code,
        profile.student_number,
        user.id,
    )

    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile



def get_all_students(db: Session):
    return db.query(StudentProfile).order_by(StudentProfile.student_number.asc()).all()


def get_students_paginated(db: Session, *, skip: int = 0, limit: int = 50):
    query = db.query(StudentProfile).order_by(StudentProfile.student_number.asc())
    total = query.count()
    students = query.offset(skip).limit(limit).all()
    return {"total": total, "students": students}


def get_student_by_id(db: Session, student_id: int) -> StudentProfile:

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.id == student_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="دانشجو یافت نشد")
    return profile


def admin_update_student(
    db: Session,
    student_id: int,
    data: AdminStudentUpdate,
) -> StudentProfile:

    profile = get_student_by_id(db, student_id)

    _check_uniqueness(
        db,
        data.national_code,
        data.student_number,
        profile.user_id,
    )

    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    if profile.user:
        profile.user.student_number = data.student_number

    db.commit()
    db.refresh(profile)
    return profile

def admin_create_student(db: Session, data: AdminStudentUpdate) -> StudentProfile:
    _check_uniqueness(db, data.national_code, data.student_number, exclude_user_id=0)

    existing_national_code = (
        db.query(StudentProfile)
        .filter(StudentProfile.national_code == data.national_code)
        .first()
    )
    if existing_national_code:
        raise HTTPException(status_code=400, detail="کد ملی قبلاً ثبت شده است")

    existing_phone = (
        db.query(StudentProfile)
        .filter(StudentProfile.phone_number == data.phone_number)
        .first()
    )
    if existing_phone:
        raise HTTPException(status_code=400, detail="شماره تماس قبلاً ثبت شده است")

    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(name="user", description="کاربر عادی")
        db.add(user_role)
        db.flush()

    user = User(
        student_number=data.student_number,
        hashed_password=hash_password(data.student_number),
        role_id=user_role.id,
    )
    db.add(user)
    db.flush()

    profile = StudentProfile(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        student_number=data.student_number,
        national_code=data.national_code,
        phone_number=data.phone_number,
        gender=data.gender.value if hasattr(data.gender, "value") else data.gender,
        address=data.address,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def admin_delete_student(db: Session, student_id: int) -> None:
    profile = get_student_by_id(db, student_id)
    user = profile.user
    db.delete(profile)
    if user:
        db.delete(user)
    db.commit()




