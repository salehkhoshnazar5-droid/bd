from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.student import StudentProfileOut, StudentProfileUpdate


def get_my_profile(db: Session, current_user: User) -> StudentProfileOut:

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

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد")

    updates = data.dict(exclude_unset=True)

    if "phone_number" in updates:
        phone_conflict = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.phone_number == updates["phone_number"],
                StudentProfile.user_id != current_user.id,
            )
            .first()
        )
        if phone_conflict:
            raise HTTPException(status_code=400, detail="این شماره تلفن قبلاً ثبت شده است")

    if "national_code" in updates:
        national_code_conflict = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.national_code == updates["national_code"],
                StudentProfile.user_id != current_user.id,
            )
            .first()
        )
        if national_code_conflict:
            raise HTTPException(status_code=400, detail="کد ملی قبلاً ثبت شده است")

    for field, value in updates.items():
        setattr(profile, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="اطلاعات وارد شده تکراری است") from exc

    db.refresh(profile)

    return StudentProfileOut.from_orm(profile)
