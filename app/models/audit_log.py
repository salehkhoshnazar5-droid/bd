from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False, comment="عملیاتی که در سیستم انجام شده")
    entity = Column(String(50), nullable=True, comment="موجودیت (entity) که تغییر کرده")
    entity_id = Column(Integer, nullable=True, comment="شناسه موجودیت (entity) که تغییر کرده")

    description = Column(String(255), nullable=True, comment="توضیحات مربوط به عملیات")
    ip_address = Column(String(45), nullable=True, comment="آدرس IP کاربر که عملیات را انجام داده")
    created_at = Column(DateTime, default=datetime.now(timezone.utc), comment="زمان ایجاد لاگ")
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, created_at={self.created_at})>"

