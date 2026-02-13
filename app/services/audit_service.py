from fastapi import Request
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from app.models.audit_log import AuditLog
from app.models.user import User


def create_audit_log(
        db: Session,
        action: str,
        request: Request,
        user: User | None = None,
        entity: str | None = None,
        entity_id: int | None = None,
        description: str | None = None,
):
    log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        description=description,
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()


def get_simple_audit_stats(db: Session) -> Dict:
    total_logs = db.query(AuditLog).count()

    total_changes = (
            db.query(func.count(AuditLog.id))
            .filter(AuditLog.action.in_(["create", "update", "delete"]))
            .scalar()
            or 0
    )

    return {
        "total_logs": total_logs,
        "total_changes": total_changes,
    }

def _gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int | Any, int | Any, int | Any]:
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy -= 1600
    gm -= 1
    gd -= 1

    g_day_no = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    for i in range(gm):
        g_day_no += g_days_in_month[i]
    if gm > 1 and ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        g_day_no += 1
    g_day_no += gd

    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053


    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    jm = 0
    while jm < 11 and j_day_no >= j_days_in_month[jm]:
        j_day_no -= j_days_in_month[jm]
        jm += 1

    jd = j_day_no + 1
    return jy, jm + 1, jd


def format_persian_datetime(dt: datetime, include_time: bool = False) -> str:
    if not dt:
        return ""
    jy, jm, jd = _gregorian_to_jalali(dt.year, dt.month, dt.day)
    date_part = f"{jy:04d}-{jm:02d}-{jd:02d}"
    if include_time:
        return f"{date_part} {dt.strftime('%H:%M:%S')}"
    return date_part


