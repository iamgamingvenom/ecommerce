from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Product
from app.schemas import ProductOut, ProductListItem

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductListItem])
def list_products(category_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Product).filter(Product.is_active == True)  # noqa: E712
    if category_id:
        query = query.filter(Product.category_id == category_id)
    return query.all()


@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(joinedload(Product.variants))
        .filter(Product.slug == slug, Product.is_active == True)  # noqa: E712
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
