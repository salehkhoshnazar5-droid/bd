import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.core.deps import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.admin_auth_service import (
    authenticate_admin_password,
    create_admin_token,
    is_admin_authenticated,
)
from app.services.audit_service import format_persian_datetime, get_simple_audit_stats



router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)




@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request, error_message: Optional[str] = None):
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "error_message": error_message,
            "is_blocked": False,
            "blocked_until": None,
        },
    )


@router.post("/login", response_class=HTMLResponse)
def admin_login_submit(request: Request, password: str = Form(...)):
    authenticated, error_message = authenticate_admin_password(request, password)
    if not authenticated:

        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error_message": error_message,
                "is_blocked": False,
                "blocked_until": None,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="admin_access_token",
        value=create_admin_token(),
        max_age=60 * 60,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.post("/authenticate")
def admin_authenticate(request: Request, password: str = Form(...)):
    authenticated, error_message = authenticate_admin_password(request, password)
    if not authenticated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    response = JSONResponse(content={"detail": "ورود ادمین موفق بود"})
    response.set_cookie(
        key="admin_access_token",
        value=create_admin_token(),
        max_age=60 * 60,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.get("/logout")
def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_access_token")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)



    stats = get_simple_audit_stats(db)

    users = (
        db.query(User)
        .options(joinedload(User.profile), joinedload(User.role))
        .order_by(User.created_at.desc())
        .limit(50)
        .all()
    )
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "users": users,
            "stats": stats,
            "format_persian_datetime": format_persian_datetime,
        },
    )

@router.get("/profile")
def admin_profile(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نیاز به ورود مدیر")

    return {"detail": "پروفایل ادمین", "is_admin": True}


@router.get("/users/{user_id}", response_class=HTMLResponse)
def admin_user_details(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    user = (
        db.query(User)
        .options(joinedload(User.profile), joinedload(User.role))
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")


    return templates.TemplateResponse(
        "admin/user_details.html",
        {
            "request": request,
            "user": user,
            "format_persian_datetime": format_persian_datetime,
            "user_total_changes": db.query(AuditLog).filter(AuditLog.user_id == user.id).count(),
        },
    )


