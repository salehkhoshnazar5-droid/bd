from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Contact name")