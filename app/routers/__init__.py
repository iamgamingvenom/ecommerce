from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.cart import router as cart_router
from app.routers.admin import router as admin_router
from app.routers.settings import router as settings_router
from app.routers.orders import router as orders_router
from app.routers.addresses import router as addresses_router

__all__ = ["auth_router", "products_router", "cart_router", "admin_router", "settings_router", "orders_router", "addresses_router"]
