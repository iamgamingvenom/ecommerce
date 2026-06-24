from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", backref="wishlist_items")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_wishlist'),
    )
