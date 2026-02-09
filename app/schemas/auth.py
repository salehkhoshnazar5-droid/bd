from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

# Enum برای جنسیت
class GenderEnum(str, Enum):
    sister = "sister"
    brother = "brother"

# Schema برای درخواست ثبت نام
class RegisterRequest(BaseModel):
    first_name: str = Field(..., description="نام", min_length=2, max_length=50)
    last_name: str = Field(..., description="نام خانوادگی", min_length=2, max_length=50)
    student_number: str
    national_code: str
    phone_number: str
    gender: GenderEnum
    address: Optional[str] = None


# Schema برای درخواست ورود
class LoginRequest(BaseModel):
    student_number: str = Field(..., description="شماره دانشجویی")
    password: str = Field(..., description="رمز عبور")

    class Config:
        json_schema_extra = {
            "example": {
                "student_number": "4001234567",
                "password": "4001234567"
            }
        }

# Schema برای پاسخ توکن
class Token(BaseModel):
    access_token: str = Field(..., description="توکن دسترسی JWT")
    token_type: str = Field(default="bearer", description="نوع توکن")
    expires_in: Optional[int] = Field(default=3600, description="زمان انقضا به ثانیه")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }

# Schema برای پاسخ ثبت نام
class RegisterResponse(BaseModel):
    message: str = Field(..., description="پیام پاسخ")
    user_id: int = Field(..., description="شناسه کاربر ایجاد شده")
    student_number: str = Field(..., description="شماره دانشجویی")
    role: str = Field(..., description="نقش کاربر")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "ثبت‌نام با موفقیت انجام شد",
                "user_id": 1,
                "student_number": "4001234567",
                "role": "user"
            }
        }

