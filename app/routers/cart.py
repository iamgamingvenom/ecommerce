from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, get_optional_user
from app.core.redis_client import (
    get_guest_cart,
    add_to_guest_cart,
    update_guest_cart_item,
    remove_from_guest_cart
)
from app.database import get_db
from app.models import Cart, CartItem, ProductVariant, User
from app.schemas import CartItemCreate, CartItemUpdate, CartOut, CartItemOut

router = APIRouter(prefix="/cart", tags=["cart"])

def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def serialize_db_cart(cart: Cart) -> CartOut:
    items = []
    subtotal = 0
    for item in cart.items:
        unit_price = item.variant.price
        line_total = unit_price * item.quantity
        subtotal += line_total
        items.append(
            CartItemOut(
                id=item.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price=unit_price,
                line_total=line_total,
                product_id=item.variant.product.id,
                product_name=item.variant.product.name,
                product_slug=item.variant.product.slug,
                size=item.variant.size,
                color=item.variant.color,
                image_url=item.variant.image_url,
            )
        )
    return CartOut(id=cart.id, items=items, subtotal=subtotal)

def serialize_redis_cart(guest_id: str, db: Session) -> CartOut:
    raw_cart = get_guest_cart(guest_id)
    items = []
    subtotal = 0
    
    # We use a mock ID for the cart (0) and items since they aren't in DB
    for var_id_str, qty_str in raw_cart.items():
        variant_id = int(var_id_str)
        quantity = int(qty_str)
        
        variant = db.query(ProductVariant).options(joinedload(ProductVariant.product)).filter(ProductVariant.id == variant_id).first()
        if not variant:
            continue
            
        unit_price = variant.price
        line_total = unit_price * quantity
        subtotal += line_total
        items.append(
            CartItemOut(
                id=variant_id,  # For guest cart, item.id = variant_id
                variant_id=variant_id,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
                product_id=variant.product.id,
                product_name=variant.product.name,
                product_slug=variant.product.slug,
                size=variant.size,
                color=variant.color,
                image_url=variant.image_url,
            )
        )
    items.sort(key=lambda x: x.variant_id)
    return CartOut(id=0, items=items, subtotal=subtotal)

def load_db_cart(db: Session, cart_id: int) -> Cart:
    return (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.variant).joinedload(ProductVariant.product))
        .filter(Cart.id == cart_id)
        .first()
    )


@router.get("/", response_model=CartOut)
def view_cart(
    db: Session = Depends(get_db), 
    user: User | None = Depends(get_optional_user),
    x_guest_id: str | None = Header(None, alias="X-Guest-ID")
):
    if user:
        cart = get_or_create_cart(db, user)
        db.refresh(cart)
        cart = load_db_cart(db, cart.id)
        return serialize_db_cart(cart)
    elif x_guest_id:
        return serialize_redis_cart(x_guest_id, db)
    else:
        return CartOut(id=0, items=[], subtotal=0)


@router.post("/items", response_model=CartOut)
def add_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    x_guest_id: str | None = Header(None, alias="X-Guest-ID")
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")
    if variant.stock_quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    if user:
        cart = get_or_create_cart(db, user)
        existing_item = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.variant_id == payload.variant_id)
            .first()
        )
        if existing_item:
            existing_item.quantity += payload.quantity
        else:
            db.add(CartItem(cart_id=cart.id, variant_id=payload.variant_id, quantity=payload.quantity))
        db.commit()
        cart = load_db_cart(db, cart.id)
        return serialize_db_cart(cart)
    elif x_guest_id:
        add_to_guest_cart(x_guest_id, payload.variant_id, payload.quantity)
        return serialize_redis_cart(x_guest_id, db)
    else:
        raise HTTPException(status_code=401, detail="Must be logged in or provide X-Guest-ID")


@router.patch("/items/{item_id}", response_model=CartOut)
def update_item_quantity(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    x_guest_id: str | None = Header(None, alias="X-Guest-ID")
):
    if user:
        cart = get_or_create_cart(db, user)
        item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        if payload.quantity <= 0:
            db.delete(item)
            db.commit()
            return serialize_db_cart(load_db_cart(db, cart.id))

        variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        if variant.stock_quantity < payload.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")

        item.quantity = payload.quantity
        db.commit()
        return serialize_db_cart(load_db_cart(db, cart.id))
    elif x_guest_id:
        variant_id = item_id
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        if variant.stock_quantity < payload.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")
            
        update_guest_cart_item(x_guest_id, variant_id, payload.quantity)
        return serialize_redis_cart(x_guest_id, db)
    else:
        raise HTTPException(status_code=401, detail="Must be logged in or provide X-Guest-ID")


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    x_guest_id: str | None = Header(None, alias="X-Guest-ID")
):
    if user:
        cart = get_or_create_cart(db, user)
        item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        db.delete(item)
        db.commit()
        return serialize_db_cart(load_db_cart(db, cart.id))
    elif x_guest_id:
        remove_from_guest_cart(x_guest_id, item_id)
        return serialize_redis_cart(x_guest_id, db)
    else:
        raise HTTPException(status_code=401, detail="Must be logged in or provide X-Guest-ID")
