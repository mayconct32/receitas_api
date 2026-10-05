from datetime import datetime

from pydantic import BaseModel, EmailStr


class Chef(BaseModel):
    chef_name: str
    email: EmailStr
    password: str


class UpdateChef(BaseModel):
    chef_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class ResponseChef(BaseModel):
    chef_id: str
    chef_name: str
    email: EmailStr
    create_at: datetime
    updated_at: datetime


