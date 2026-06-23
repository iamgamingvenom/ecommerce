import redis
from app.config import settings

redis_url = settings.redis_url
if not redis_url.startswith("redis://") and not redis_url.startswith("rediss://"):
    redis_url = f"rediss://{redis_url}"

redis_client = redis.Redis.from_url(redis_url, decode_responses=True, ssl_cert_reqs="none" if redis_url.startswith("rediss://") else None)

def get_guest_cart(guest_id: str) -> dict:
    """Returns a dict of {variant_id (str): quantity (str)}"""
    key = f"cart:{guest_id}"
    return redis_client.hgetall(key)

def update_guest_cart_item(guest_id: str, variant_id: int, quantity: int):
    key = f"cart:{guest_id}"
    if quantity <= 0:
        redis_client.hdel(key, str(variant_id))
    else:
        redis_client.hset(key, str(variant_id), quantity)
    redis_client.expire(key, 604800)  # 7 days

def add_to_guest_cart(guest_id: str, variant_id: int, quantity: int):
    key = f"cart:{guest_id}"
    redis_client.hincrby(key, str(variant_id), quantity)
    redis_client.expire(key, 604800)

def remove_from_guest_cart(guest_id: str, variant_id: int):
    key = f"cart:{guest_id}"
    redis_client.hdel(key, str(variant_id))

def delete_guest_cart(guest_id: str):
    key = f"cart:{guest_id}"
    redis_client.delete(key)
