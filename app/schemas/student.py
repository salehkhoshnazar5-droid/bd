from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from app.core.validators import (
    validate_national_code,
    validate_phone_number,
    validate_student_number,
)

# Enum برای جنسیت
class GenderEnum(str, Enum):
    sister = "sister"
    brother = "brother"



# مدل پایه برای پروفایل دانشجو
class StudentProfileBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    national_code: str = Field(..., regex=r"^\d{10}$")
    student_number: str = Field(..., regex=r"^\d{9}$")
    phone_number: str = Field(..., regex=r"^09\d{9}$")
    gender: GenderEnum
    address: Optional[str] = Field(None, max_length=100)

    @validator("national_code", pre=True)
    def validate_national_code_field(cls, value: str) -> str:
        return validate_national_code(value)

    @validator("student_number", pre=True)
    def validate_student_number_field(cls, value: str) -> str:
        return validate_student_number(value)

    @validator("phone_number", pre=True)
    def validate_phone_number_field(cls, value: str) -> str:
        return validate_phone_number(value)

    class Config:
        orm_mode = True


# کلاس برای بروزرسانی پروفایل توسط دانشجو
class StudentProfileUpdate(BaseModel):
    national_code: Optional[str] = Field(None, regex=r"^\d{10}$")
    phone_number: Optional[str] = Field(None, regex=r"^09\d{9}$")
    gender: Optional[str] = None
    address: Optional[str] = Field(None, max_length=100)

    @validator("national_code", pre=True)
    def validate_national_code_update(cls, value: Optional[str]) -> Optional[str]:
        return validate_national_code(value)

    @validator("phone_number", pre=True)
    def validate_phone_number_update(cls, value: Optional[str]) -> Optional[str]:
        return validate_phone_number(value)

    @validator("gender")
    def validate_gender(cls, v):
        if v in ["خواهر", "sister"]:
            return "sister"
        elif v in ["برادر", "brother"]:
            return "brother"
        elif v is not None:
            raise ValueError("gender must be 'sister' or 'brother'")
        return v

    class Config:
        orm_mode = True


# کلاس برای بروزرسانی پروفایل توسط ادمین
class AdminStudentUpdate(StudentProfileBase):
    pass


# کلاس خروجی پروفایل دانشجویی (Student)
class StudentProfileOut(StudentProfileBase):
    id: int
    class Config:
        orm_mode = True


# مدل خروجی ساده برای ORM / دیتابیس
class StudentProfileOutDB(BaseModel):
    id: int
    student_number: str
    national_code: str
    phone_number: str
    gender: GenderEnum
    address: Optional[str]

    class Config:
        orm_mode = True