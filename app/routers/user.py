from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.deps import get_db
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", response_model=UserOut)
def read_user_me(
        current_user: User = Depends(get_current_user),
):

    return current_user



@router.get("/{user_id}", response_model=UserOut)
def read_user_by_id(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):

    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="دسترسی غیرمجاز",
        )

    user = db.query(User).filter(User.id == user_id).first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربر یافت نشد",
        )

    return user
