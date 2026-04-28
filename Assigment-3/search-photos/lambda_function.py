import json
import re
import urllib.request
import boto3
import botocore.auth
import botocore.awsrequest
import botocore.session

REGION = "us-east-1"

OPENSEARCH_ENDPOINT = "https://search-photos-caibbvmcewhlkwj5dez2qsxqru.us-east-1.es.amazonaws.com"
OPENSEARCH_INDEX = "photos"

LEX_BOT_ID = "FNRVLBRKLP"
LEX_BOT_ALIAS_ID = "TSTALIASID"
LEX_LOCALE_ID = "en_US"

lex = boto3.client("lexv2-runtime", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def sign_and_post(path, body_dict):
    body = json.dumps(body_dict)
    url = f"{OPENSEARCH_ENDPOINT}{path}"

    session = botocore.session.get_session()
    creds = session.get_credentials().get_frozen_credentials()

    aws_req = botocore.awsrequest.AWSRequest(
        method="POST",
        url=url,
        data=body,
        headers={"Content-Type": "application/json"}
    )
    botocore.auth.SigV4Auth(creds, "es", REGION).add_auth(aws_req)

    req = urllib.request.Request(
        url=url,
        data=body.encode("utf-8"),
        headers=dict(aws_req.headers.items()),
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8")}


def extract_keywords(text):
    tokens = re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
    stop = {"show", "me", "photos", "photo", "with", "and", "in", "them", "of", "a", "the"}
    return [t for t in tokens if t not in stop]


def lex_disambiguate(query):
    try:
        resp = lex.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId=LEX_LOCALE_ID,
            sessionId="search-session",
            text=query
        )
        interpreted = resp.get("inputTranscript", query)
        return extract_keywords(interpreted)
    except Exception:
        return extract_keywords(query)


def search_photos(keywords):
    if not keywords:
        return []

    must_terms = [{"term": {"labels": kw}} for kw in keywords]
    query = {"query": {"bool": {"must": must_terms}}}

    status, data = sign_and_post(f"/{OPENSEARCH_INDEX}/_search", query)
    if status < 200 or status >= 300:
        raise Exception(f"OpenSearch search failed: {status} {data}")

    hits = data.get("hits", {}).get("hits", [])
    results = []

    for h in hits:
        src = h.get("_source", {})
        bucket = src.get("bucket")
        key = src.get("objectKey")
        if bucket and key:
            signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=3600
            )
            results.append({
                "url": signed_url,
                "labels": src.get("labels", [])
            })

    return results


def lambda_handler(event, context):
    try:
        q = (event.get("queryStringParameters") or {}).get("q", "").strip()
        if not q:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"results": []})
            }

        keywords = lex_disambiguate(q)
        results = search_photos(keywords) if keywords else []

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"results": results})
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
