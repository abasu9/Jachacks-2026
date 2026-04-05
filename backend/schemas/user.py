from datetime import date
from typing import List
from uuid import UUID
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    apr: List[float]
    pip: int
    joiningDate: date
    rank: float

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: UUID

    class Config:
        from_attributes = True
