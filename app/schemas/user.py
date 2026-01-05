from typing import Optional, List
from pydantic import BaseModel, EmailStr
from uuid import UUID

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "CREW"
    is_active: Optional[bool] = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str
    assigned_vessel_imos: List[str] = [] # List of strings (IMOs)

# Properties to return to the UI
class UserResponse(UserBase):
    id: UUID
    assigned_vessel_imos: List[str] = [] # The API returns this list now

    class Config:
        from_attributes = True # updated from 'orm_mode' in Pydantic v2