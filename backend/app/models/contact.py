from pydantic import BaseModel, EmailStr, field_validator


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str

    @field_validator("name", "message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v
