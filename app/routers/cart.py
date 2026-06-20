from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Cart, CartItem, ProductVariant, User
from app.schemas import CartItemCreate, CartOut, CartItemOut

router = APIRouter(prefix="/cart", tags=["cart"])


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def serialize_cart(cart: Cart) -> CartOut:
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
            )
        )
    return CartOut(id=cart.id, items=items, subtotal=subtotal)


@router.get("/", response_model=CartOut)
def view_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user)
    db.refresh(cart)
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.variant))
        .filter(Cart.id == cart.id)
        .first()
    )
    return serialize_cart(cart)


@router.post("/items", response_model=CartOut)
def add_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")
    if variant.stock_quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

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

    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.variant))
        .filter(Cart.id == cart.id)
        .first()
    )
    return serialize_cart(cart)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(db, user)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()

    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.variant))
        .filter(Cart.id == cart.id)
        .first()
    )
    return serialize_cart(cart)
