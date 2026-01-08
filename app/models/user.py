from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    profile_photo: Optional[str] = None
    phone: Optional[str] = None
    college: Optional[str] = None

class UserCreate(UserBase):
    uid: str

class UserUpdate(BaseModel):
    phone: Optional[str] = None
    college: Optional[str] = None

class User(UserBase):
    uid: str
    created_at: datetime
    last_login: datetime
