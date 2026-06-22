import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Cart, CartItem, ProductVariant, User, Order, OrderItem, OrderStatus
from app.schemas import OrderOut, OrderCreate, OrderInitializeOut, OrderVerifyPayload
from app.core.paystack import initialize_paystack_transaction, verify_paystack_transaction

router = APIRouter(prefix="/orders", tags=["orders"])


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("", response_model=OrderInitializeOut, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(db, user)
    
    # Load cart with variants
    cart_items = (
        db.query(CartItem)
        .options(joinedload(CartItem.variant))
        .filter(CartItem.cart_id == cart.id)
        .all()
    )
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    # Calculate total and check stock first
    total = Decimal("0.00")
    for item in cart_items:
        if item.variant.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough stock for variant: {item.variant.sku}"
            )
        total += item.variant.price * item.quantity
        
    shipping_fee = Decimal("10.00")
    total += shipping_fee

    # Create Order
    order = Order(
        user_id=user.id,
        address_id=payload.address_id,
        status=OrderStatus.pending,
        total_amount=total,
    )
    db.add(order)
    db.flush()  # Generate order.id

    # Create Order Items
    order_items = []
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            unit_price=item.variant.price,
        )
        db.add(order_item)
        order_items.append(order_item)

    # Initialize Paystack Transaction
    # Reference format: order_<id>_<uuid_suffix>
    reference = f"order_{order.id}_{uuid.uuid4().hex[:8]}"
    
    try:
        # Convert total to pesewas/cents (integer)
        amount_minor = int(total * 100)
        auth_url = initialize_paystack_transaction(user.email, amount_minor, reference)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment initialization failed: {e}")

    # Set Paystack Reference
    order.paystack_reference = reference
    
    # Clear user cart items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    
    db.commit()
    db.refresh(order)
    
    return {
        "order": order,
        "authorization_url": auth_url,
        "reference": reference,
    }


@router.post("/verify", response_model=OrderOut)
def verify_order(
    payload: OrderVerifyPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Find order
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.paystack_reference == payload.reference, Order.user_id == user.id)
        .first()
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status in [OrderStatus.paid, OrderStatus.processing]:
        return order
        
    # Verify Transaction with Paystack
    try:
        tx_data = verify_paystack_transaction(payload.reference)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payment verification failed: {e}")

    # Check status and amount
    # Paystack returns amount in minor units (e.g. pesewas)
    expected_amount_minor = int(order.total_amount * 100)
    
    if tx_data.get("status") == "success" and tx_data.get("amount") == expected_amount_minor:
        # Deduct inventory stock for purchased variants
        for item in order.items:
            variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
            if not variant:
                raise HTTPException(status_code=404, detail="Product variant not found")
            if variant.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Inventory checkout failed: {variant.sku} is out of stock"
                )
            variant.stock_quantity -= item.quantity
            
        # Update order status to paid (or processing)
        order.status = OrderStatus.paid
        db.commit()
        db.refresh(order)
        return order
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid transaction status or amount mismatch. Status: {tx_data.get('status')}"
        )


@router.get("", response_model=list[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
