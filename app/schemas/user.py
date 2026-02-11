from pydantic import BaseModel, Field, validator
from typing import Optional
from app.core.validators import validate_phone_number, validate_gender


class UserOut(BaseModel):
    id: int
    student_number: str
    role_id: int
    is_active: bool
    profile: Optional[dict] = None

    class Config:
        orm_mode = True

# Schema برای بروزرسانی پروفایل کاربر
class ProfileUpdate(BaseModel):
    phone_number: Optional[str] = Field(None)
    address: Optional[str] = Field(None, max_length=200)
    gender: Optional[str] = Field(None)

    @validator("phone_number", pre=True)
    def validate_phone_number_field(cls, value: Optional[str]) -> Optional[str]:
        return validate_phone_number(value)

    @validator("gender")
    def validate_gender_field(cls, value: Optional[str]) -> Optional[str]:
        return validate_gender(value)

    class Config:
        schema_extra = {
            "example": {
                "phone_number": "09123456789",
                "address": "کرمان، بلوار هوانیوز",
                "gender": "brother"
            }
        }
