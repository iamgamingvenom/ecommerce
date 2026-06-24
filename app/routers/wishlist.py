from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.wishlist import WishlistItem
from app.models.user import User
from app.schemas.wishlist import WishlistCreate, WishlistOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/wishlist", tags=["wishlist"])

@router.get("", response_model=list[WishlistOut])
def get_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()
    result = []
    for item in items:
        # Assuming product variants might have images
        image_url = None
        if item.product and item.product.variants:
            for variant in item.product.variants:
                if variant.image_url:
                    image_url = variant.image_url
                    break
        
        result.append(WishlistOut(
            id=item.id,
            user_id=item.user_id,
            product_id=item.product_id,
            created_at=item.created_at,
            product_name=item.product.name if item.product else None,
            product_slug=item.product.slug if item.product else None,
            product_price=float(item.product.base_price) if item.product else None,
            product_image_url=image_url
        ))
    return result

@router.post("", response_model=WishlistOut)
def add_to_wishlist(payload: WishlistCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id, WishlistItem.product_id == payload.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already in wishlist")

    item = WishlistItem(user_id=current_user.id, product_id=payload.product_id)
    db.add(item)
    db.commit()
    db.refresh(item)

    image_url = None
    if item.product and item.product.variants:
        for variant in item.product.variants:
            if variant.image_url:
                image_url = variant.image_url
                break

    return WishlistOut(
        id=item.id,
        user_id=item.user_id,
        product_id=item.product_id,
        created_at=item.created_at,
        product_name=product.name,
        product_slug=product.slug,
        product_price=float(product.base_price),
        product_image_url=image_url
    )

@router.delete("/{item_id}", status_code=204)
def remove_from_wishlist(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    db.delete(item)
    db.commit()
    return None
