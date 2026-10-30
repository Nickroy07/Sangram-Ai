"""Contact and Support Message Schemas."""

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema


class ContactRequest(BaseSchema):
    """Contact form submission payload."""

    name: str = Field(..., min_length=2, max_length=100, description="Sender name")
    email: EmailStr = Field(..., description="Sender contact email")
    subject: str = Field("General Inquiry", min_length=2, max_length=150, description="Inquiry topic")
    message: str = Field(..., min_length=10, max_length=5000, description="Message body")


class ContactResponse(BaseSchema):
    """Response returned upon contact dispatch."""

    success: bool = True
    message: str
