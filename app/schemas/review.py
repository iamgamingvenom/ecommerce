from pydantic import BaseModel, Field
from datetime import datetime

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None

class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    user_name: str
    rating: int
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True
