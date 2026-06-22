from pydantic import BaseModel
from typing import Optional

class AddressCreate(BaseModel):
    line1: str
    city: str
    region: str
    phone: str
    is_default: Optional[bool] = False

class AddressUpdate(BaseModel):
    line1: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    phone: Optional[str] = None
    is_default: Optional[bool] = None

class AddressOut(BaseModel):
    id: int
    user_id: int
    line1: str
    city: str
    region: str
    phone: str
    is_default: bool

    class Config:
        from_attributes = True
