import uuid
import boto3

from app.config import settings

s3_client = boto3.client("s3", region_name=settings.aws_region)


def upload_image_to_s3(file_obj, content_type: str, original_filename: str) -> str:
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "jpg"
    key = f"products/{uuid.uuid4()}.{extension}"

    s3_client.upload_fileobj(
        file_obj,
        settings.s3_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    return f"https://{settings.cloudfront_domain}/{key}"