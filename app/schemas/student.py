from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, validator
from app.core.validators import (
validate_gender,
    validate_national_code,
    validate_phone_number,
    validate_student_number,
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

    model_config = ConfigDict(from_attributes=True)


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


    model_config = ConfigDict(from_attributes=True)


class AdminStudentUpdate(StudentProfileBase):
    pass


class StudentProfileOut(StudentProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StudentProfileOutDB(BaseModel):
    id: int
    student_number: str
    national_code: str
    phone_number: str
    gender: GenderEnum
    address: Optional[str]

    model_config = ConfigDict(from_attributes=True)