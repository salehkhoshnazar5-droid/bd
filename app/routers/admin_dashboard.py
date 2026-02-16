import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, joinedload
from app.core.database import ensure_noor_program_schema
from app.core.deps import get_db
from app.models.audit_log import AuditLog
from app.models.noor_program import LightPathStudent, QuranClass, QuranClassRequest
from app.models.user import User
from app.services.admin_auth_service import (
    authenticate_admin_password,
    create_admin_token,
    is_admin_authenticated,
)
from app.services.audit_service import create_audit_log, format_persian_datetime, get_simple_audit_stats



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

def _query_with_noor_schema_repair(db: Session, build_query):
    try:
        return build_query().all()
    except OperationalError:
        db.rollback()
        logger.exception("Noor program query failed; attempting schema repair and retry")
        ensure_noor_program_schema()
        return build_query().all()

def _build_quran_request_lookup(records: list[QuranClassRequest]) -> dict[int, QuranClassRequest]:
    latest_by_user: dict[int, QuranClassRequest] = {}
    for request_item in records:
        if request_item.user_id is None:
            continue
        existing = latest_by_user.get(request_item.user_id)
        if existing is None or (request_item.created_at and existing.created_at and request_item.created_at > existing.created_at):
            latest_by_user[request_item.user_id] = request_item
    return latest_by_user

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

    quran_class_requests = _query_with_noor_schema_repair(
        db,
        lambda: db.query(QuranClassRequest)
        .order_by(QuranClassRequest.created_at.desc())
        .limit(200),
    )

    quran_classes = _query_with_noor_schema_repair(
        db,
        lambda: db.query(QuranClass)
        .order_by(QuranClass.created_at.desc()),
    )

    light_path_students = _query_with_noor_schema_repair(
        db,
        lambda: db.query(LightPathStudent)
        .order_by(LightPathStudent.created_at.desc())
        .limit(100),
    )

    users_count = db.query(User).count()
    light_path_students_count = len(light_path_students)
    total_users = users_count + light_path_students_count

    deleted_events = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "delete",
            AuditLog.entity.in_(["light_path_student", "quran_scholar"]),
        )
        .count()
    )
    all_events = len(light_path_students) + len(quran_class_requests)
    total_events = all_events + deleted_events


    latest_request_by_user = _build_quran_request_lookup(quran_class_requests)
    light_path_rows = []
    for student in light_path_students:
        latest_request = latest_request_by_user.get(student.user_id) if student.user_id else None
        light_path_rows.append(
            {
                "record": student,
                "level": latest_request.level if latest_request else "-",
                "status": "فعال" if student.user_id else "ناشناس",
            }
        )


    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "users": users,
            "stats": stats,
            "quran_class_requests": quran_class_requests,
            "quran_classes": quran_classes,
            "light_path_rows": light_path_rows,
            "total_users": total_users,
            "users_count": users_count,
            "light_path_students_count": light_path_students_count,
            "total_events": total_events,
            "format_persian_datetime": format_persian_datetime,
        },
    )


@router.post("/light-path-students")
def create_light_path_student(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    enrollment_date: date = Form(...),
    is_active: str = Form("active"),
    student_number: str = Form(""),
    db: Session = Depends(get_db),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    record = LightPathStudent(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=email.strip(),
        phone_number=phone_number.strip(),
        enrollment_date=enrollment_date,
        is_active=is_active == "active",
        student_number=student_number.strip() or None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    create_audit_log(
        db=db,
        action="create",
        request=request,
        entity="light_path_student",
        entity_id=record.id,
        description="دانشجوی مسیر نور توسط مدیر ایجاد شد",
    )

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/quran-classes")
def create_quran_class(
    request: Request,
    title: str = Form(...),
    level: int = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    if level not in range(1, 10):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="سطح باید بین ۱ تا ۹ باشد")

    db.add(
        QuranClass(
            title=title.strip(),
            level=level,
            description=description.strip() or None,
        )
    )
    db.commit()

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/quran-classes/{class_id}/edit")
def edit_quran_class(
    class_id: int,
    request: Request,
    title: str = Form(...),
    level: int = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    class_record = db.query(QuranClass).filter(QuranClass.id == class_id).first()
    if class_record is None:
        raise HTTPException(status_code=404, detail="کلاس یافت نشد")

    if level not in range(1, 10):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="سطح باید بین ۱ تا ۹ باشد")

    class_record.title = title.strip()
    class_record.level = level
    class_record.description = description.strip() or None
    db.commit()

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/quran-classes/{class_id}/delete")
def delete_quran_class(class_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    class_record = db.query(QuranClass).filter(QuranClass.id == class_id).first()
    if class_record:
        db.delete(class_record)
        db.commit()

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/quran-requests/{request_id}/delete")
def delete_quran_class_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    record = db.query(QuranClassRequest).filter(QuranClassRequest.id == request_id).first()
    if record:
        record_id = record.id
        db.delete(record)
        db.commit()
        create_audit_log(
            db=db,
            action="delete",
            request=request,
            entity="quran_scholar",
            entity_id=record_id,
            description="دانشور آموزش نور حذف شد",
        )

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/light-path-students/{student_id}/edit")
def edit_light_path_student(
    student_id: int,
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    enrollment_date: date = Form(...),
    is_active: str = Form("active"),
    student_number: str = Form(""),
    db: Session = Depends(get_db),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    record = db.query(LightPathStudent).filter(LightPathStudent.id == student_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="دانشجو یافت نشد")

    record.first_name = first_name.strip()
    record.last_name = last_name.strip()
    record.email = email.strip()
    record.phone_number = phone_number.strip()
    record.enrollment_date = enrollment_date
    record.is_active = is_active == "active"
    record.student_number = student_number.strip() or None
    db.commit()

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/light-path-students/{student_id}/delete")
def delete_light_path_student(student_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    record = db.query(LightPathStudent).filter(LightPathStudent.id == student_id).first()
    if record:
        record_id = record.id
        db.delete(record)
        db.commit()
        create_audit_log(
            db=db,
            action="delete",
            request=request,
            entity="light_path_student",
            entity_id=record_id,
            description="دانشجوی مسیر نور حذف شد",
        )

    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/profile")
def admin_profile(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نیاز به ورود مدیر")

    return {"detail": "پروفایل ادمین", "is_admin": True}


@router.get("/users/{user_id}", response_class=HTMLResponse)
def admin_user_details(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

