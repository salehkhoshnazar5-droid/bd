from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.security import get_current_admin
from app.schemas.student import StudentProfileOut, AdminStudentUpdate
from app.services import user_service
from app.models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin)],
)

@router.get("/students", response_model=list[StudentProfileOut])
def list_students(db: Session = Depends(get_db)):
    return user_service.get_all_students(db)

@router.get("/students/{student_id}", response_model=StudentProfileOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return user_service.get_student_by_id(db, student_id)

@router.post("/students", response_model=StudentProfileOut, status_code=201)
def create_student(data: AdminStudentUpdate, db: Session = Depends(get_db)):
    return user_service.admin_create_student(db, data)

@router.put("/students/{student_id}", response_model=StudentProfileOut)
def update_student(
    student_id: int,
    data: AdminStudentUpdate,
     db: Session = Depends(get_db),
):

    return user_service.admin_update_student(db, student_id, data)

@router.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    user_service.admin_delete_student(db, student_id)
    return None