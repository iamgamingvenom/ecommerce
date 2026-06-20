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

class CategoryCreate(BaseModel):
    name: str
    slug: str


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class VariantCreate(BaseModel):
    size: str
    color: str
    sku: str
    price: Decimal
    stock_quantity: int = 0
    image_url: str | None = None


class VariantUpdate(BaseModel):
    price: Decimal | None = None
    stock_quantity: int | None = None
    image_url: str | None = None


class ProductCreate(BaseModel):
    category_id: int
    name: str
    slug: str
    description: str | None = None
    base_price: Decimal


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_price: Decimal | None = None
    is_active: bool | None = None
    category_id: int | None = None
