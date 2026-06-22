from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.setting import SiteSetting
from app.core.deps import get_current_admin_user

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(SiteSetting).all()
    return {s.key: s.value for s in settings}

@router.patch("/admin")
def update_settings(
    payload: dict[str, str],
    db: Session = Depends(get_db),
    _ = Depends(get_current_admin_user)
):
    for key, value in payload.items():
        setting = db.query(SiteSetting).filter(SiteSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = SiteSetting(key=key, value=value)
            db.add(setting)
    
    db.commit()
    
    # Return updated settings
    settings = db.query(SiteSetting).all()
    return {s.key: s.value for s in settings}
