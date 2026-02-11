from typing import Optional

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from app.core.confing import settings
from app.core.deps import DBDep
from app.core.validators import validate_phone_number
from app.models.user import User

router = APIRouter(prefix="/ui/dashboard", tags=["UI Dashboard"])

templates = Jinja2Templates(directory="app/templates")


def _get_current_user_from_cookie(request: Request, db: Session) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None

    student_number = payload.get("sub")
    if not student_number:
        return None

    return (
        db.query(User)
        .options(joinedload(User.profile), joinedload(User.role))
        .filter(User.student_number == student_number)
        .first()
    )


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = DBDep()):
    user = _get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(
            url="/ui-auth/login?redirect=/ui/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": user,
            "profile": user.profile,
        },
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_view_page(request: Request, db: Session = DBDep()):
    user = _get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(
            url="/ui-auth/login?redirect=/ui/dashboard/profile",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "profile/view.html",
        {
            "request": request,
            "user": user,
            "profile": user.profile,
        },
    )


@router.get("/profile/edit", response_class=HTMLResponse)
async def profile_edit_page(
    request: Request,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = DBDep(),
):
    user = _get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(
            url="/ui-auth/login?redirect=/ui/dashboard/profile/edit",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "profile/edit.html",
        {
            "request": request,
            "user": user,
            "profile": user.profile,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


@router.post("/profile/edit", response_class=HTMLResponse)
async def profile_edit_submit(
    request: Request,
    phone_number: str = Form(...),
    address: Optional[str] = Form(None),
    db: Session = DBDep(),
):
    user = _get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(
            url="/ui-auth/login?redirect=/ui/dashboard/profile/edit",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    profile = user.profile
    if not profile:
        return templates.TemplateResponse(
            "profile/edit.html",
            {
                "request": request,
                "user": user,
                "profile": None,
                "error_message": "پروفایل کاربری یافت نشد.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        normalized_phone = validate_phone_number(phone_number)
    except ValueError as exc:
        return templates.TemplateResponse(
            "profile/edit.html",
            {
                "request": request,
                "user": user,
                "profile": profile,
                "error_message": str(exc),
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    profile.phone_number = normalized_phone
    profile.address = address.strip() if address else None

    db.commit()

    return RedirectResponse(
        url="/ui/dashboard/profile",
        status_code=status.HTTP_303_SEE_OTHER,
    )