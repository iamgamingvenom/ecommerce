from fastapi import FastAPI, HTTPException, Depends
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import engine
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.routers import admin_router, products_router, cart_router, auth_router, settings_router, orders_router, addresses_router
from app.database import Base
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clothing Store API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your Vercel frontend URL before going live
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(settings_router)
app.include_router(orders_router)
app.include_router(addresses_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}



@app.post("/admin/migrate-add-is-admin")
def migrate_add_is_admin(secret: str):
    if secret != os.environ.get("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.commit()
    return {"status": "column added"}

@app.post("/admin/migrate-add-is-active")
def migrate_add_is_active(secret: str):
    if secret != os.environ.get("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    with engine.connect() as conn:
        # Note: SQLite has limited ALTER TABLE support, but adding a column with a default works
        conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        conn.commit()
    return {"status": "is_active column added"}

@app.post("/admin/migrate-categories-is-active")
def migrate_categories_is_active(secret: str):
    if secret != os.environ.get("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE categories ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        conn.commit()
    return {"status": "categories is_active column added"}

@app.post("/admin/promote-to-admin")
def promote_to_admin(email: str, secret: str, db: Session = Depends(get_db)):
    if secret != os.environ.get("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    db.commit()
    return {"status": f"{email} is now admin"}

@app.post("/admin/init-db")
def init_db(secret: str):
    if secret != os.environ.get("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    Base.metadata.create_all(bind=engine)
    return {"status": "tables created"}
