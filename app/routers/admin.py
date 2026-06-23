from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.models import Category, Product, ProductVariant, User, Order, OrderItem, CartItem, MediaAsset
from app.schemas import (
    CategoryCreate, CategoryUpdate, CategoryOut,
    ProductCreate, ProductUpdate, ProductOut,
    VariantCreate, VariantUpdate, VariantOut,
    MediaAssetOut,
)
from app.schemas.user import UserOut
from app.schemas.order import OrderOut
from app.core.s3 import upload_image_to_s3, delete_image_from_s3

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    slug = payload.slug.strip().lower().replace(" ", "-")
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category slug already exists")

    category = Category(name=payload.name, slug=slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return db.query(Category).all()


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Prevent deletion if products exist
    products_count = db.query(Product).filter(Product.category_id == category_id).count()
    if products_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category because it contains products. Please delete or reassign the products first, or toggle the category to Inactive."
        )

    db.delete(category)
    db.commit()
    return None


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    slug = payload.slug.strip().lower().replace(" ", "-")
    existing = db.query(Product).filter(Product.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product slug already exists")

    product = Product(
        category_id=payload.category_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        base_price=payload.base_price,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    for variant in product.variants:
        if db.query(CartItem).filter(CartItem.variant_id == variant.id).first() or \
           db.query(OrderItem).filter(OrderItem.variant_id == variant.id).first():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete product because it has variants in a user's cart or order history. Please toggle it to Inactive instead."
            )

    db.delete(product)
    db.commit()
    return None


@router.post("/products/{product_id}/variants", response_model=VariantOut, status_code=201)
def create_variant(
    product_id: int,
    payload: VariantCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(ProductVariant).filter(ProductVariant.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    variant = ProductVariant(
        product_id=product_id,
        size=payload.size,
        color=payload.color,
        sku=payload.sku,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        image_url=payload.image_url,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.patch("/variants/{variant_id}", response_model=VariantOut)
def update_variant(
    variant_id: int,
    payload: VariantUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)

    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/variants/{variant_id}", status_code=204)
def delete_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
        
    if db.query(CartItem).filter(CartItem.variant_id == variant_id).first() or \
       db.query(OrderItem).filter(OrderItem.variant_id == variant_id).first():
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete variant because it is in a user's cart or order history. Please set stock to 0 instead."
        )

    db.delete(variant)
    db.commit()
    return None


@router.patch("/admin/variants/{variant_id}", response_model=VariantOut, include_in_schema=False)
def update_variant_admin_alias(
    variant_id: int,
    payload: VariantUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return update_variant(variant_id=variant_id, payload=payload, db=db, _=_)


@router.delete("/admin/variants/{variant_id}", status_code=204, include_in_schema=False)
def delete_variant_admin_alias(
    variant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return delete_variant(variant_id=variant_id, db=db, _=_)


@router.post("/upload-image", response_model=MediaAssetOut)
def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    url = upload_image_to_s3(file.file, file.content_type, file.filename)
    
    media = MediaAsset(filename=file.filename, s3_url=url)
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.get("/media-assets", response_model=list[MediaAssetOut])
def list_media_assets(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return db.query(MediaAsset).order_by(MediaAsset.created_at.desc()).all()


@router.delete("/media-assets/{media_id}", status_code=204)
def delete_media_asset(
    media_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    media = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")
    
    # Delete from S3
    delete_image_from_s3(media.s3_url)
    
    db.delete(media)
    db.commit()
    return None

@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return db.query(User).all()

@router.patch("/users/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if "is_active" in payload:
        user.is_active = payload["is_active"]
    
    db.commit()
    db.refresh(user)
    return user

@router.get("/users/{user_id}/orders", response_model=list[OrderOut])
def list_user_orders(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    return orders