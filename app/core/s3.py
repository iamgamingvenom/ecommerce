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


def delete_image_from_s3(s3_url: str):
    try:
        domain = settings.cloudfront_domain
        prefix = f"https://{domain}/"
        if s3_url.startswith(prefix):
            key = s3_url[len(prefix):]
            s3_client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=key,
            )
    except Exception as e:
        print(f"Failed to delete {s3_url} from S3: {e}")