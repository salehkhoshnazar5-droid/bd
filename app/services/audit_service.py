from fastapi import Request
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Optional

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

    actions = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .all()
    )

    actions_dict: Dict[str, int] = {
        action: count for action, count in actions
    }

    return {
        "total_logs": total_logs,
        "actions": actions_dict,
    }


def get_audit_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
) -> Dict:

    query = db.query(AuditLog)

    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()

    logs = (
        query
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "logs": logs,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


# ۴. تابع کمکی برای فرمت تاریخ در template
def format_datetime(dt: datetime) -> str:
    """فرمت کردن تاریخ برای نمایش"""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")



