import requests
import boto3
from datetime import datetime
import time

YELP_API_KEY = 'bgWQazCCsCEH8bAy5tPDvny-PP3uUSsJdWYRUD12W52RMkpOShUz3lBUE8UqoPCiBj8SoBSWIn9iRY_6mAp3hDMLNmIQ5Zn-0TPcGm83LaXHrTMvbRLb_V8oMMGUaXYx'
HEADERS = {'Authorization': f'Bearer {YELP_API_KEY}'}

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')

CUISINES = ['Chinese', 'Japanese', 'Italian', 'Mexican', 'Indian']

def search_restaurants(cuisine, offset):
    url = 'https://api.yelp.com/v3/businesses/search'
    params = {
        'term': f'{cuisine} restaurants',
        'location': 'Manhattan, NY',
        'limit': 50,
        'offset': offset
    }
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json().get('businesses', [])

def save_to_dynamodb(business, cuisine):
    try:
        location = business.get('location', {})
        address_list = location.get('display_address', [])
        address = ', '.join(address_list)
        zip_code = location.get('zip_code', '')
        coords = business.get('coordinates', {})

        table.put_item(Item={
            'BusinessID': business['id'],
            'Name': business['name'],
            'Address': address,
            'Coordinates': {
                'Latitude': str(coords.get('latitude', '')),
                'Longitude': str(coords.get('longitude', ''))
            },
            'NumberOfReviews': business.get('review_count', 0),
            'Rating': str(business.get('rating', 0)),
            'ZipCode': zip_code,
            'Cuisine': cuisine,
            'insertedAtTimestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error saving {business.get('name')}: {e}")

seen_ids = set()

for cuisine in CUISINES:
    print(f"Scraping {cuisine}...")
    count = 0
    for offset in range(0, 200, 50):
        businesses = search_restaurants(cuisine, offset)
        for b in businesses:
            if b['id'] not in seen_ids:
                seen_ids.add(b['id'])
                save_to_dynamodb(b, cuisine)
                count += 1
        time.sleep(0.5)  # avoid rate limiting
    print(f"  Saved {count} {cuisine} restaurants")

print(f"Total unique restaurants: {len(seen_ids)}")
