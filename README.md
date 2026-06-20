# Clothing store backend (FastAPI)

## Stack
- FastAPI
- MySQL (AWS RDS)
- Redis (AWS ElastiCache) — wired up via REDIS_URL, not yet used in code
- S3 (product images) — bucket configured via env vars, upload helper not yet written
- Paystack (payments) — keys configured via env vars, webhook not yet written

## Local setup

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in real values:
   ```
   cp .env.example .env
   ```

3. Create the database tables (no Alembic migration yet — this is a quick way to
   get started, switch to Alembic once the schema stabilizes):
   ```
   python -c "from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)"
   ```

4. Run the dev server:
   ```
   uvicorn app.main:app --reload
   ```

5. Open http://localhost:8000/docs for the interactive API docs.

## What's implemented
- `POST /auth/register` — create an account
- `POST /auth/login` — get a JWT access token (OAuth2 password flow, so it works
  directly in the Swagger UI's "Authorize" button)
- `GET /products/` — list active products, optional `category_id` filter
- `GET /products/{slug}` — product detail with variants
- `GET /cart/` — view the logged-in user's cart
- `POST /cart/items` — add a variant to the cart
- `DELETE /cart/items/{item_id}` — remove a cart item

## What's not implemented yet (next steps)
- Orders router: create an order from the cart, kick off a Paystack transaction
- Paystack webhook endpoint to confirm payment and flip order status
- S3 upload helper for product images (admin-side)
- Redis-backed guest cart (currently cart requires login)
- Alembic migrations
- Admin endpoints for managing products/variants/stock

## Deployment notes
- `Dockerfile` included — builds straight onto AWS App Runner or ECS Fargate
- Point `DATABASE_URL` at your RDS MySQL endpoint and `REDIS_URL` at your
  ElastiCache endpoint — both need to be reachable from wherever this container
  runs (same VPC / VPC connector)
- Set real values for all secrets via App Runner's environment variable config
  or AWS Secrets Manager — don't bake `.env` into the image
