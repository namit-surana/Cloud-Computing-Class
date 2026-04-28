import json
import base64
import boto3
import uuid

s3 = boto3.client("s3")
BUCKET = "b2-namit-a3-photos"


def lambda_handler(event, context):
    try:
        headers = event.get("headers") or {}
        custom_labels = (
            headers.get("x-amz-meta-customlabels")
            or headers.get("x-amz-meta-customLabels")
            or ""
        )
        content_type = headers.get("content-type") or headers.get("Content-Type") or "image/jpeg"

        qs = event.get("queryStringParameters") or {}
        filename = qs.get("filename") if qs else None
        if not filename:
            filename = f"upload-{uuid.uuid4()}.jpg"

        body = event.get("body", "")
        if event.get("isBase64Encoded", False):
            file_bytes = base64.b64decode(body)
        else:
            file_bytes = body.encode("utf-8")

        s3.put_object(
            Bucket=BUCKET,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
            Metadata={"customlabels": custom_labels}
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "uploaded", "key": filename})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }
