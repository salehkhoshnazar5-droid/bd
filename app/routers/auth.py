from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.deps import DBDep, CurrentUser, get_db
from app.schemas.auth import RegisterRequest, Token, RegisterResponse
from app.schemas.user import UserOut
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_token_for_user,
    enforce_single_national_id_authentication
)
from app.models.user import User
from app.core.validators import validate_national_code

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ثبت نام کاربر جدید",
    description=(
            "ثبت نام کاربر جدید با شماره دانشجویی، کد ملی و شماره تماس معتبر. "
            "اعتبارسنجی طول فیلدها برای کد ملی (۱۰ رقم)، شماره دانشجویی (۹ رقم) "
            "و شماره تماس (۱۱ رقم) اعمال می‌شود."
    ),
    responses={
        400: {"description": "اطلاعات تکراری یا نامعتبر است."},
        422: {"description": "خطای اعتبارسنجی داده‌ها."}
    }
)
async def register(
        data: RegisterRequest,
        db: Session = DBDep()
):
    user = register_user(db=db, data=data)
    return {
        "message": "ثبت‌نام با موفقیت انجام شد",
        "user_id": user.id,
        "student_number": user.student_number,
        "role": user.role.name
    }


@router.post(
    "/login",
    response_model=Token,
    summary="ورود و دریافت توکن"
)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = DBDep()
):
    try:
        national_code = validate_national_code(form_data.username)
        password = form_data.password
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = str(exc)
        ) from exc
    user = authenticate_user(
        db,
        national_code=national_code,
        password=password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="کد ملی یا شماره دانشجویی اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال شده است"
        )
    enforce_single_national_id_authentication(db, user)

    return create_token_for_user(user)


@router.get(
    "/me",
    response_model=UserOut,
    summary="دریافت اطلاعات کاربر جاری"
)
async def get_me(
        current_user: User = CurrentUser()
):
    return current_user

@router.get("/check/{student_number}")
async def check_student_number(student_number: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.student_number == student_number).first()
    return {"available": existing_user is None}

