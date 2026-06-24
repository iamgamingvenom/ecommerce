from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut
from app.core.deps import get_current_user

router = APIRouter(tags=["reviews"])

@router.get("/products/{slug}/reviews", response_model=list[ReviewOut])
def get_product_reviews(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = db.query(Review).filter(Review.product_id == product.id).order_by(Review.created_at.desc()).all()
    
    # map user_name
    result = []
    for r in reviews:
        result.append(ReviewOut(
            id=r.id,
            product_id=r.product_id,
            user_id=r.user_id,
            user_name=r.user.name,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at
        ))
    return result

@router.post("/products/{product_id}/reviews", response_model=ReviewOut)
def create_product_review(
    product_id: int, 
    payload: ReviewCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Review).filter(Review.product_id == product_id, Review.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")

    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewOut(
        id=review.id,
        product_id=review.product_id,
        user_id=review.user_id,
        user_name=current_user.name,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at
    )
