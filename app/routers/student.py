from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.schemas.student import StudentProfileOut, StudentProfileUpdate
from app.services import student_service
from app.models.user import User

router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/me", response_model=StudentProfileOut)
def read_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return student_service.get_my_profile(db, current_user)


@router.put("/me", response_model=StudentProfileOut)
def update_my_profile(
    data: StudentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return student_service.update_my_profile(db, current_user, data)
