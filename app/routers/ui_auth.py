from typing import Optional

from pydantic import ValidationError
from fastapi import (
    APIRouter,
    Request,
    Form,
    HTTPException,
    status
)
from fastapi.responses import (
    RedirectResponse,
    HTMLResponse
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.deps import DBDep
from app.schemas.auth import RegisterRequest, GenderEnum
from app.services.auth_service import register_user, enforce_single_national_id_authentication, authenticate_user
from app.core.security import create_access_token
from app.core.confing import settings
from app.core.validators import validate_national_code
import logging

router = APIRouter(
    prefix="/ui-auth",
    tags=["UI Authentication"]
)

templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "سامانه مدیریت بسیج",
            "welcome_message": "به سامانه مدیریت بسیج دانشجویی خوش آمدید"
        }
    )


@router.get("/register", response_class=HTMLResponse)
async def show_register_page(
    request: Request,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "title": "ثبت‌نام در سامانه",
            "success_message": success_message,
            "error_message": error_message,
            "genders": [
                {"value": "brother", "label": "برادر"},
                {"value": "sister", "label": "خواهر"}
            ]
        }
    )


@router.post("/register", response_class=HTMLResponse)
async def submit_register(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    student_number: str = Form(...),
    national_code: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    address: Optional[str] = Form(""),
    db: Session = DBDep()
):
    try:
        gender_enum = GenderEnum(gender)

        register_data = RegisterRequest(
            first_name=first_name,
            last_name=last_name,
            student_number=student_number,
            national_code=national_code,
            phone_number=phone_number,
            gender=gender_enum,
            address=address or None
        )

        register_user(db, register_data)

        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "ورود به سامانه",
                "success_message": "ثبت‌نام با موفقیت انجام شد. لطفاً وارد شوید.",
                "student_number": student_number
            },
            status_code=status.HTTP_201_CREATED
        )

    except ValidationError as exc:
        validation_messages = [error.get("msg") for error in exc.errors()]
        error_message = " ".join(validation_messages) or "اطلاعات ثبت‌نام نامعتبر است."

    except ValueError:
        error_message = "جنسیت انتخاب‌شده معتبر نیست."

    except HTTPException as e:
        error_message = e.detail

    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "title": "ثبت‌نام در سامانه",
            "error_message": error_message,
            "form_data": {
                "first_name": first_name,
                "last_name": last_name,
                "student_number": student_number,
                "national_code": national_code,
                "phone_number": phone_number,
                "gender": gender,
                "address": address
            },
            "genders": [
                {"value": "brother", "label": "برادر"},
                {"value": "sister", "label": "خواهر"}
            ]
        },
        status_code=400
    )


@router.get("/login", response_class=HTMLResponse)
async def show_login_page(
    request: Request,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "title": "ورود به سامانه",
            "success_message": success_message,
            "error_message": error_message,
            "redirect_url": request.query_params.get(
                "redirect", "/ui/dashboard"
            )
        }
    )


@router.post("/login", response_class=HTMLResponse)
async def submit_login(
    request: Request,
    national_code: str = Form(...),
    password: str = Form(...),
    remember_me: Optional[str] = Form(None),
    redirect_url: Optional[str] = Form(None),
    db: Session = DBDep()
):
    logger.info("UI login attempt received")
    try:
        normalized_national_code = validate_national_code(national_code)
    except ValueError as exc:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "ورود به سامانه",
                "error_message": str(exc),
                "national_code": national_code,
                "redirect_url": redirect_url,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    user = authenticate_user(
        db,
        national_code=normalized_national_code,
        password=password,
        )
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "ورود به سامانه",
                "error_message": "در حال حاضر امکان ورود وجود ندارد. لطفاً دوباره تلاش کنید.",
                "national_code": national_code,
                "redirect_url": redirect_url,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    logger.info("UI login candidate lookup completed: user_found=%s", bool(user))

    if not user:
        logger.warning("UI login failed due to invalid credentials")
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "ورود به سامانه",
                "error_message": "کد ملی یا شماره دانشجویی نادرست است.",
                "national_code": national_code,
                "redirect_url": redirect_url,
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        logger.warning("UI login blocked for inactive user: user_id=%s", user.id)
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "ورود به سامانه",
                "error_message": "حساب کاربری شما غیرفعال شده است.",
                "national_code": national_code,
                "redirect_url": redirect_url,
            },
            status_code=status.HTTP_403_FORBIDDEN
        )

    try:
        enforce_single_national_id_authentication(db, user)
    except HTTPException as e:
        logger.exception("UI login post-authentication state update failed")
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "ورود به سامانه",
                "error_message": e.detail,
                "national_code": national_code,
                "redirect_url": redirect_url,
            },
            status_code=status.HTTP_403_FORBIDDEN
        )

    access_token = create_access_token(
        data={
            "sub": user.student_number,
            "user_id": user.id,
            "national_code": user.profile.national_code if user.profile else None
        }
    )

    max_age = 30 * 24 * 60 * 60 if remember_me else 24 * 60 * 60

    target_url = redirect_url or (
        "/admin/dashboard" if user.role and user.role.name == "admin" else "/ui-auth/dashboard"
    )

    logger.info("UI login success: user_id=%s", user.id)
    response = RedirectResponse(
        url=target_url,
        status_code=status.HTTP_303_SEE_OTHER
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,  # در production → True
        samesite="lax"
    )

    return response


@router.get("/logout")
async def logout_user():
    response = RedirectResponse(
        url="/ui-auth/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie("access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(
    request: Request
):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(
            url="/ui-auth/login?redirect=/ui-auth/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "title": "داشبورد کاربری",
            "message": "به داشبورد خوش آمدید"
        }
    )