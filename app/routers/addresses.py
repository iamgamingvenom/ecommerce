from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/addresses", tags=["addresses"])

@router.post("", response_model=AddressOut, status_code=201)
def create_address(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # If this is the first address, make it default
    existing_count = db.query(Address).filter(Address.user_id == user.id).count()
    is_default = payload.is_default if existing_count > 0 else True
    
    # If setting to default, unset other defaults
    if is_default:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})

    address = Address(
        user_id=user.id,
        line1=payload.line1,
        city=payload.city,
        region=payload.region,
        phone=payload.phone,
        is_default=is_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

@router.get("", response_model=list[AddressOut])
def list_addresses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.id.desc()).all()

@router.delete("/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
        
    db.delete(address)
    db.commit()
    return None
