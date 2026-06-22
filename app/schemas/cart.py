from decimal import Decimal

from pydantic import BaseModel


class CartItemCreate(BaseModel):
    variant_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    variant_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product_id: int
    product_name: str
    product_slug: str
    size: str
    color: str
    image_url: str | None = None

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: int
    items: list[CartItemOut]
    subtotal: Decimal
