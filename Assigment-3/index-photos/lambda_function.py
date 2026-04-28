import json
import urllib.parse
import urllib.request
import boto3
import botocore.auth
import botocore.awsrequest
import botocore.session
from datetime import datetime, timezone

REGION = "us-east-1"
OPENSEARCH_ENDPOINT = "https://search-photos-caibbvmcewhlkwj5dez2qsxqru.us-east-1.es.amazonaws.com"
OPENSEARCH_INDEX = "photos"

s3 = boto3.client("s3", region_name=REGION)
rekognition = boto3.client("rekognition", region_name=REGION)


def normalize_labels(labels):
    out, seen = [], set()
    for l in labels:
        v = (l or "").strip().lower()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def signed_opensearch_put(path, body):
    session = botocore.session.get_session()
    creds = session.get_credentials().get_frozen_credentials()

    url = f"{OPENSEARCH_ENDPOINT}{path}"
    aws_req = botocore.awsrequest.AWSRequest(
        method="PUT",
        url=url,
        data=body,
        headers={"Content-Type": "application/json"}
    )

    signer = botocore.auth.SigV4Auth(creds, "es", REGION)
    signer.add_auth(aws_req)

    headers = dict(aws_req.headers.items())
    http_req = urllib.request.Request(
        url=url,
        data=body.encode("utf-8"),
        headers=headers,
        method="PUT"
    )

    try:
        with urllib.request.urlopen(http_req, timeout=10) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def lambda_handler(event, context):
    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        created_ts = record.get("eventTime") or datetime.now(timezone.utc).isoformat()

        print(f"Bucket={bucket}, Key={key}")

        obj = s3.get_object(Bucket=bucket, Key=key)
        image_bytes = obj["Body"].read()

        rek = rekognition.detect_labels(
            Image={"Bytes": image_bytes},
            MaxLabels=20,
            MinConfidence=70
        )
        rek_labels = [x.get("Name", "") for x in rek.get("Labels", [])]

        head = s3.head_object(Bucket=bucket, Key=key)
        custom_raw = (head.get("Metadata", {}) or {}).get("customlabels", "")
        custom_labels = [x.strip() for x in custom_raw.split(",") if x.strip()]

        labels = normalize_labels(rek_labels + custom_labels)

        doc = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimestamp": created_ts,
            "labels": labels
        }

        doc_id = urllib.parse.quote(f"{bucket}/{key}", safe="")
        path = f"/{OPENSEARCH_INDEX}/_doc/{doc_id}"
        status, text = signed_opensearch_put(path, json.dumps(doc))

        if not (200 <= status < 300):
            raise Exception(f"OpenSearch error {status}: {text}")

        print(f"Indexed successfully: {bucket}/{key}")
        return {"statusCode": 200, "body": json.dumps({"ok": True, "doc": doc})}

    except Exception as e:
        print(f"LF1 error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
