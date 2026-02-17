from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

class Contact(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Contact name")
    url: Optional[HttpUrl] = Field(default=None, description="Contact website URL")
    email: Optional[str] = Field(default=None, description="Contact email")

    class Config:
        from_attributes = True  # جایگزین 'orm_mode'
        json_schema_extra = {  # جایگزین 'schema_extra'
            "example": {
                "name": "John Doe",
                "url": "http://johndoe.com",
                "email": "john.doe@example.com"
            }
        }
        extra = "allow"