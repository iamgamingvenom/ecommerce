from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Category, Product
from app.schemas import CategoryOut, ProductOut, ProductListItem

router = APIRouter(tags=["products"])


@router.get("/categories/", response_model=list[CategoryOut])
def list_public_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).all()


@router.get("/products/", response_model=list[ProductListItem])
def list_products(category_id: int | None = None, db: Session = Depends(get_db)):
    query = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.variants))
        .filter(Product.is_active == True)
    )  # noqa: E712
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.all()
    return [
        ProductListItem(
            id=product.id,
            name=product.name,
            slug=product.slug,
            base_price=product.base_price,
            is_active=product.is_active,
            category_id=product.category_id,
            category_name=product.category.name if product.category else None,
            image_url=next(
                (variant.image_url for variant in product.variants if variant.image_url),
                None,
            ),
        )
        for product in products
    ]


@router.get("/products/{slug}", response_model=ProductOut)
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
