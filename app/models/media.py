from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    s3_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
