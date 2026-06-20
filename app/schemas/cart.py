from decimal import Decimal

from pydantic import BaseModel


class CartItemCreate(BaseModel):
    variant_id: int
    quantity: int = 1


class CartItemOut(BaseModel):
    id: int
    variant_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: int
    items: list[CartItemOut]
    subtotal: Decimal
