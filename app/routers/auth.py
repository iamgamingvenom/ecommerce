from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.models import User, CartItem
from app.schemas import UserCreate, UserOut, Token
from app.core.deps import get_current_user
from app.routers.cart import get_or_create_cart
from app.core.redis_client import get_guest_cart, delete_guest_cart

router = APIRouter(prefix="/auth", tags=["auth"])

def merge_guest_cart(db: Session, user: User, guest_id: str):
    raw_cart = get_guest_cart(guest_id)
    if not raw_cart:
        return
        
    db_cart = get_or_create_cart(db, user)
    
    for var_id_str, qty_str in raw_cart.items():
        variant_id = int(var_id_str)
        quantity = int(qty_str)
        
        existing_item = db.query(CartItem).filter(CartItem.cart_id == db_cart.id, CartItem.variant_id == variant_id).first()
        if existing_item:
            existing_item.quantity += quantity
        else:
            db.add(CartItem(cart_id=db_cart.id, variant_id=variant_id, quantity=quantity))
            
    db.commit()
    delete_guest_cart(guest_id)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate, 
    db: Session = Depends(get_db),
    x_guest_id: str | None = Header(None, alias="X-Guest-ID")
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    if x_guest_id:
        merge_guest_cart(db, user, x_guest_id)
        
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    x_guest_id: str | None = Header(None, alias="X-Guest-ID")
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(subject=user.email)
    
    if x_guest_id:
        merge_guest_cart(db, user, x_guest_id)
        
    return Token(access_token=token)

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
