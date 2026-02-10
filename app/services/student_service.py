from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.student import StudentProfileOut, StudentProfileUpdate


def get_my_profile(db: Session, current_user: User) -> StudentProfileOut:
    """
    دریافت پروفایل دانشجویی کاربر جاری.
    """
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد")

    return StudentProfileOut.from_orm(profile)


def update_my_profile(
    db: Session,
    current_user: User,
    data: StudentProfileUpdate
) -> StudentProfileOut:
    """
    بروزرسانی پروفایل دانشجویی کاربر جاری.
    """
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return StudentProfileOut.from_orm(profile)
