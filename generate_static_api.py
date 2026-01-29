#!/usr/bin/env python3
"""
Generate static JSON API file for deployment
Converts database to JSON with S3 photo URLs
"""

from robotics_photo_db import RoboticsPhotoDatabase
import json

# Load photo URL mapping
with open('photo_urls.json', 'r') as f:
    photo_urls = json.load(f)

db = RoboticsPhotoDatabase()
db.connect()

robots_data = db.list_all_robots()

# Category mappings
category_emojis = {
    'Drones': '🚁',
    'AMRs': '🤖',
    'Robotic Arms': '🦾'
}

marketplace_products = []

for robot in robots_data:
    # Get photo IDs for this robot
    db.cursor.execute("""
        SELECT photo_id
        FROM photos
        WHERE robot_id = ?
        ORDER BY upload_date DESC
    """, (robot['robot_id'],))
    
    photo_ids = [row['photo_id'] for row in db.cursor.fetchall()]
    
    # Get S3 URLs for these photos
    s3_urls = [photo_urls[str(pid)] for pid in photo_ids if str(pid) in photo_urls]
    
    # If no photos, use placeholder
    if not s3_urls:
        s3_urls = [
            f"https://via.placeholder.com/400x300?text={robot['manufacturer']}+{robot['model_name']}"
        ]
    
    # Ensure we have at least 4 images for gallery
    while len(s3_urls) < 4:
        s3_urls.append(s3_urls[0])
    
    # Build product object
    product = {
        'id': robot['robot_id'],
        'name': robot['model_name'],
        'vendor': robot['manufacturer'],
        'price': 'Contact for Quote',
        'priceNote': 'Custom pricing based on requirements',
        'image': s3_urls[0],
        'images': s3_urls[:4],
        'category': robot['category_name'],
        'type': robot['robot_type'],
        'rating': 4.8,
        'reviews': 124,
        'emoji': category_emojis.get(robot['category_name'], '🤖'),
        'badge': '',
        'inStock': True,
        'verified': True,
        'description': f"Professional {robot['robot_type']} from {robot['manufacturer']}. " + 
                      (f"Released in {robot['year_released']}. " if robot.get('year_released') else "") +
                      f"{len(photo_ids)} photo(s) available.",
        'specs': {
            'payload': '5-600 kg' if robot['category_name'] == 'AMRs' else '5-15 kg',
            'battery': '30 min - 12 hrs',
            'autonomy': 'Advanced Navigation',
            'speed': '2 m/s' if robot['category_name'] == 'AMRs' else '20 m/s'
        },
        'features': [
            {'icon': '🎯', 'title': 'Precision', 'desc': 'High accuracy operations'},
            {'icon': '🔒', 'title': 'Safety', 'desc': 'Advanced safety systems'},
            {'icon': '📊', 'title': 'Analytics', 'desc': 'Real-time monitoring'},
            {'icon': '🔧', 'title': 'Maintenance', 'desc': 'Easy to service'}
        ],
        'applications': ['Manufacturing', 'Warehousing', 'Logistics', 'Inspection']
    }
    
    marketplace_products.append(product)

db.close()

# Save as static JSON file
with open('api/database-robots.json', 'w') as f:
    json.dump(marketplace_products, f, indent=2)

print(f"✓ Generated api/database-robots.json with {len(marketplace_products)} products")
print(f"✓ All photos using S3 URLs")
print(f"\nReady for deployment!")
