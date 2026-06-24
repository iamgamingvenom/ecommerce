from pydantic import BaseModel
from datetime import datetime
from app.models.order import OrderStatus

class OrderItemOut(BaseModel):
    id: int
    variant_id: int
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    user_id: int
    address_id: int
    status: OrderStatus
    total_amount: float
    created_at: datetime
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    address_id: int


class OrderInitializeOut(BaseModel):
    order: OrderOut
    authorization_url: str
    reference: str


class OrderVerifyPayload(BaseModel):
    reference: str

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
