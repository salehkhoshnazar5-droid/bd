from pydantic import BaseModel, Field, validator
from typing import Optional
from app.core.validators import validate_phone_number

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
    phone_number: Optional[str] = Field(None, regex=r"^09\d{9}$")
    address: Optional[str] = Field(None, max_length=200)
    gender: Optional[str] = Field(None, regex="^(brother|sister)$")

    @validator("phone_number", pre=True)
    def validate_phone_number_field(cls, value: Optional[str]) -> Optional[str]:
        return validate_phone_number(value)

    class Config:
        schema_extra = {
            "example": {
                "phone_number": "09123456789",
                "address": "کرمان، بلوار هوانیوز",
                "gender": "brother"
            }
        }
