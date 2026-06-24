from pydantic import BaseModel
from datetime import datetime

class WishlistCreate(BaseModel):
    product_id: int

class WishlistOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    created_at: datetime
    product_name: str | None = None
    product_slug: str | None = None
    product_price: float | None = None
    product_image_url: str | None = None

    class Config:
        from_attributes = True
