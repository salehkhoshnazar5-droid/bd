from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from fastapi import HTTPException
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog

if TYPE_CHECKING:
    from app.models.student_profile import StudentProfile


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, default=1)  # default=user
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    role = relationship("Role", back_populates="users")
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, student_number='{self.student_number}', role='{self.role.name if self.role else None}')>"

    def to_dict(self, include_profile=False, include_role=False):
        data = {
            "id": self.id,
            "student_number": self.student_number,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_role and self.role:
            data["role"] = {
                "id": self.role.id,
                "name": self.role.name,
                "description": self.role.description
            }

        if include_profile and self.profile:
            data["profile"] = {
                "national_code": self.profile.national_code,
                "phone_number": self.profile.phone_number,
                "gender": self.profile.gender,
                "address": self.profile.address
            }

        return data

    @property
    def is_admin(self):
        """بررسی اینکه آیا کاربر admin است یا نه."""
        return self.role and self.role.name == "admin"

    @property
    def is_moderator(self):
        """بررسی اینکه آیا کاربر moderator است یا نه."""
        return self.role and self.role.name == "moderator"

    def can(self, permission: str) -> bool:
        permissions_map = {
            "admin": ["create", "read", "update", "delete", "manage_users"],
            "moderator": ["create", "read", "update"],
            "user": ["read"]
        }

        return permission in permissions_map.get(self.role.name, [])

    @classmethod
    def create_simple_user(cls, student_number: str, password: str, db_session, role_name="user"):
        from app.core.security import hash_password
        from app.models.role import Role

        role = db_session.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError(f"نقش '{role_name}' وجود ندارد")

        user = cls(
            student_number=student_number,
            hashed_password=hash_password(password),
            role_id=role.id
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def check_unique(db, national_code: str, student_number: str, exclude_user_id: int = None):
        """بررسی تکراری بودن شماره دانشجویی یا کد ملی"""
        from app.models.student_profile import StudentProfile  # وارد کردن StudentProfile در اینجا برای جلوگیری از Circular Import

        user_query = db.query(User).filter(User.student_number == student_number)
        if exclude_user_id is not None:
            user_query = user_query.filter(User.id != exclude_user_id)
        if user_query.first():
            raise HTTPException(
                status_code=400,
                detail="شماره دانشجویی تکراری است",
            )

        conflict_query = db.query(StudentProfile).filter(StudentProfile.national_code == national_code)
        if exclude_user_id is not None:
            conflict_query = conflict_query.filter(StudentProfile.user_id != exclude_user_id)
        conflict = conflict_query.first()

        if conflict:
            raise HTTPException(
                status_code=400,
                detail="کد ملی یا شماره دانشجویی تکراری است"
            )
