from datetime import datetime
from pydantic import BaseModel


class MediaAssetOut(BaseModel):
    id: int
    filename: str
    s3_url: str
    created_at: datetime

    class Config:
        from_attributes = True
