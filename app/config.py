from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "eu-west-1"
    s3_bucket_name: str = ""
    cloudfront_domain: str = ""

    paystack_secret_key: str = ""
    paystack_public_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
