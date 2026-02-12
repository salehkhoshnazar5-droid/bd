from datetime import datetime

from typing import Optional
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, Request, Query, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.confing import settings
from app.core.deps import get_db
from app.core.security import ALGORITHM, create_access_token
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.student import AdminStudentUpdate
from app.services import user_service
from app.services.auth_service import authenticate_user
from app.core.validators import validate_national_code, validate_student_number
# ایجاد router
router = APIRouter()
def get_templates() -> Jinja2Templates:
    return Jinja2Templates(directory="app/templates")


def get_current_admin_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نیاز به ورود")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        student_number: str = payload.get("sub")
        if not student_number:
            raise HTTPException(status_code=401, detail="توکن نامعتبر")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="توکن نامعتبر") from exc

    user = db.query(User).filter(User.student_number == student_number).first()
    if not user:
        raise HTTPException(status_code=401, detail="کاربر یافت نشد")
    if not user.role or user.role.name != "admin":
        raise HTTPException(status_code=403, detail="دسترسی فقط برای ادمین")
    return user


@router.get("/admin/login", response_class=HTMLResponse)
def show_admin_login(
    request: Request,
    error_message: Optional[str] = Query(None),
):
    return get_templates().TemplateResponse(
        "admin/login.html",
        {"request": request, "error_message": error_message},
    )


@router.post("/admin/login")
def admin_login(
    national_code: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        normalized_national_code = validate_national_code(national_code)
        normalized_student_number = validate_student_number(password)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/admin/login?error_message={quote(str(exc))}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = authenticate_user(db, normalized_national_code, normalized_student_number)
    if not user:
        return RedirectResponse(
            url="/admin/login?error_message=کد+ملی+یا+شماره+دانشجویی+اشتباه+است",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not user.is_active or not user.role or user.role.name != "admin":
        return RedirectResponse(
            url="/admin/login?error_message=شما+دسترسی+ادمین+ندارید",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    access_token = create_access_token(
        data={
            "sub": user.student_number,
            "user_id": user.id,
            "national_code": user.profile.national_code if user.profile else None,
            "role": user.role.name,
        }
    )

    response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response

templates = Jinja2Templates(directory="app/templates")


def get_current_admin_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نیاز به ورود")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        student_number: str = payload.get("sub")
        if not student_number:
            raise HTTPException(status_code=401, detail="توکن نامعتبر")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="توکن نامعتبر") from exc

    user = db.query(User).filter(User.student_number == student_number).first()
    if not user:
        raise HTTPException(status_code=401, detail="کاربر یافت نشد")
    if not user.role or user.role.name != "admin":
        raise HTTPException(status_code=403, detail="دسترسی فقط برای ادمین")
    return user

@router.get("/audit-logs", response_class=HTMLResponse)
def audit_logs_page(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_from_cookie),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
):
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if action:
        query = query.filter(AuditLog.action == action)

    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)

    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    logs = query.order_by(AuditLog.created_at.desc()).limit(500).all()


    for log in logs:
        if log.user:
            log.student_number = log.user.student_number
            log.national_code = log.user.profile.national_code if log.user.profile else None


    date_from_str = date_from.isoformat() if date_from else ""
    date_to_str = date_to.isoformat() if date_to else ""

    return templates.TemplateResponse(
        "admin/audit_logs.html",
        {
            "request": request,
            "logs": logs,
            "filters": {
                "user_id": user_id or "",
                "action": action or "",
                "date_from": date_from_str,
                "date_to": date_to_str,
            },
        },
    )



@router.get("/admin/students/manage", response_class=HTMLResponse)
def manage_students_page(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_from_cookie),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    edit_id: Optional[int] = Query(None),
    error_message: Optional[str] = Query(None),
    success_message: Optional[str] = Query(None),
):
    result = user_service.get_students_paginated(db, skip=skip, limit=limit)
    edit_student = user_service.get_student_by_id(db, edit_id) if edit_id else None
    return templates.TemplateResponse(
        "admin/student_management.html",
        {
            "request": request,
            "students": result["students"],
            "total": result["total"],
            "skip": skip,
            "limit": limit,
            "edit_student": edit_student,
            "error_message": error_message,
            "success_message": success_message,
        },
    )


@router.post("/admin/students/manage/add")
def add_student(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    student_number: str = Form(...),
    national_code: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    address: str = Form(""),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_from_cookie),
):
    try:
        payload = AdminStudentUpdate(
            first_name=first_name,
            last_name=last_name,
            student_number=student_number,
            national_code=national_code,
            phone_number=phone_number,
            gender=gender,
            address=address or None,
        )
        user_service.admin_create_student(db, payload)
        return RedirectResponse(
            "/admin/students/manage?success_message=دانشجو با موفقیت ایجاد شد",
            status_code=303,
        )
    except (HTTPException, ValueError) as exc:
        message = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return RedirectResponse(
            f"/admin/students/manage?error_message={message}",
            status_code=303,
        )


@router.post("/admin/students/manage/{student_id}/edit")
def edit_student(
    student_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    student_number: str = Form(...),
    national_code: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    address: str = Form(""),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_from_cookie),
):
    try:
        payload = AdminStudentUpdate(
            first_name=first_name,
            last_name=last_name,
            student_number=student_number,
            national_code=national_code,
            phone_number=phone_number,
            gender=gender,
            address=address or None,
        )
        user_service.admin_update_student(db, student_id, payload)
        return RedirectResponse(
            "/admin/students/manage?success_message=اطلاعات دانشجو بروزرسانی شد",
            status_code=303,
        )
    except (HTTPException, ValueError) as exc:
        message = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return RedirectResponse(
            f"/admin/students/manage?edit_id={student_id}&error_message={message}",
            status_code=303,
        )


@router.post("/admin/students/manage/{student_id}/delete")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_from_cookie),
):
    user_service.admin_delete_student(db, student_id)
    return RedirectResponse(
        "/admin/students/manage?success_message=دانشجو حذف شد",
        status_code=303,
    )