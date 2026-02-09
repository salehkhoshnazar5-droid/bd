from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import DBDep
from app.models.user import User

# تنظیمات
SECRET_KEY = "CHANGE_THIS_SECRET_KEY"  # در production تغییر دهید
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Exception
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="توکن نامعتبر یا منقضی شده است",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(password: str) -> str:
    """هش کردن رمز عبور."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """تأیید رمز عبور."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """ساخت توکن JWT."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = DBDep()

) -> User:
    """
    اعتبارسنجی توکن JWT و برگرداندن کاربر.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        student_number: str = payload.get("sub")
        national_code: str = payload.get("national_code")  # اضافه کردن کد ملی به payload

        if student_number is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.student_number == student_number).first()

    if user is None:
        raise credentials_exception

    return user


def get_current_admin(
        current_user: User = Depends(get_current_user),
):
    """
    Dependency برای اطمینان از admin بودن کاربر
    """
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما دسترسی لازم را ندارید"
        )
    return current_user
