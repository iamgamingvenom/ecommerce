from decimal import Decimal

from pydantic import BaseModel


class VariantOut(BaseModel):
    id: int
    size: str
    color: str
    sku: str
    price: Decimal
    stock_quantity: int
    image_url: str | None = None

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    base_price: Decimal
    is_active: bool
    variants: list[VariantOut] = []

    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    base_price: Decimal
    is_active: bool

    class Config:
        from_attributes = True
