from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, ensure_runtime_schema


def get_db() -> Generator[Session, None, None]:
    ensure_runtime_schema()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def DBDep() -> Session:
    return Depends(get_db)


def CurrentUser():
    from app.core.security import get_current_user
    return Depends(get_current_user)


def AdminDep():
    from app.core.security import get_current_admin
    return Depends(get_current_admin)