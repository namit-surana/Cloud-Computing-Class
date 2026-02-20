import boto3
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

OPENSEARCH_HOST = 'search-restaurants-ast5q53wlfspfzawtitvljlsoq.us-east-1.es.amazonaws.com'
MASTER_USER = 'admin'
MASTER_PASS = 'Samkit@27'

os_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': 443}],
    http_auth=(MASTER_USER, MASTER_PASS),
    use_ssl=True,
    verify_certs=True,
    timeout=60
)

# Create index if it doesn't exist
if not os_client.indices.exists(index='restaurants'):
    os_client.indices.create(index='restaurants', body={
        "mappings": {
            "properties": {
                "BusinessID": {"type": "keyword"},
                "Cuisine":    {"type": "keyword"}
            }
        }
    })
    print("Index created")
else:
    print("Index already exists")

# Load from DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')

response = table.scan()
items = response['Items']

while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items.extend(response['Items'])

print(f"Indexing {len(items)} restaurants...")

# Bulk index
actions = [
    {
        "_index": "restaurants",
        "_id": item['BusinessID'],
        "_source": {
            "BusinessID": item['BusinessID'],
            "Cuisine": item['Cuisine']
        }
    }
    for item in items
]

success, failed = bulk(os_client, actions)
print(f"Done! Indexed: {success}, Failed: {failed}")
