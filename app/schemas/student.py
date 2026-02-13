from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from app.core.validators import (
    validate_national_code,
    validate_phone_number,
    validate_student_number, validate_gender,
)

class GenderEnum(str, Enum):
    sister = "sister"
    brother = "brother"



class StudentProfileBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    national_code: str = Field(...)
    student_number: str = Field(...)
    phone_number: str = Field(...)
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


class StudentProfileUpdate(BaseModel):
    national_code: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    gender: Optional[str] = None
    address: Optional[str] = Field(None, max_length=100)

    @validator("national_code", pre=True)
    def validate_national_code_update(cls, value: Optional[str]) -> Optional[str]:
        return validate_national_code(value)

    @validator("phone_number", pre=True)
    def validate_phone_number_update(cls, value: Optional[str]) -> Optional[str]:
        return validate_phone_number(value)

    @validator("gender")
    def validate_gender_field(cls, value: Optional[str]) -> Optional[str]:
        return validate_gender(value)


    class Config:
        orm_mode = True


class AdminStudentUpdate(StudentProfileBase):
    pass


class StudentProfileOut(StudentProfileBase):
    id: int
    class Config:
        orm_mode = True


class StudentProfileOutDB(BaseModel):
    id: int
    student_number: str
    national_code: str
    phone_number: str
    gender: GenderEnum
    address: Optional[str]

    class Config:
        orm_mode = True