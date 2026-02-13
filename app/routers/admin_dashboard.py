import logging
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.services.admin_auth_service import (
    authenticate_admin_password,
    create_admin_token,
    is_admin_authenticated,
)
from app.services.audit_service import get_audit_logs, get_simple_audit_stats



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



    recent_logs = get_audit_logs(db, limit=10)
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
            "recent_logs": recent_logs.get("logs", []),
            "stats": stats,
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

    return templates.TemplateResponse("admin/user_details.html", {"request": request, "user": user})


@router.get("/audit-logs", response_class=HTMLResponse)
def audit_logs_page(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="تعداد رکوردهای رد شده"),
    limit: int = Query(50, ge=1, le=200, description="تعداد رکوردهای قابل نمایش"),
    date_from: Optional[datetime] = Query(None, description="تاریخ شروع"),
    date_to: Optional[datetime] = Query(None, description="تاریخ پایان"),
    action: Optional[str] = Query(None, description="فیلتر بر اساس عمل"),
    user_id: Optional[int] = Query(None, description="فیلتر بر اساس کاربر"),

):

    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    result = get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        action=action,
        user_id=user_id,
    )

    return templates.TemplateResponse(
        "admin/audit_logs.html",
        {
            "request": request,
            "logs": result.get("logs", []),
            "total": result.get("total", 0),
            "skip": skip,
            "limit": limit,
            "has_more": result.get("has_more", False),
            "filters": {
                "user_id": user_id or "",
                "action": action or "",
                "date_from": date_from.isoformat() if date_from else "",
                "date_to": date_to.isoformat() if date_to else "",
            },
        },
    )

@router.get("/api/audit-logs", response_model=dict)
def list_audit_logs_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        action: Optional[str] = Query(None),
        user_id: Optional[int] = Query(None),
):
    return get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        action=action,
        user_id=user_id
    )

