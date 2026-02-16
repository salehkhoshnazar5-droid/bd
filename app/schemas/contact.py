from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Contact(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Contact name")
    url: Optional[HttpUrl] = Field(default=None, description="Contact website URL")
    email: Optional[str] = Field(default=None, description="Contact email")

    class Config:
        extra = "allow"