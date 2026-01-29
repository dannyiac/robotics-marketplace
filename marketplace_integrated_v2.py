#!/usr/bin/env python3
"""
Simplified Robotics Marketplace with Photo Database
Serves marketplace with real photos - fixed version
"""

from flask import Flask, send_file, jsonify, send_from_directory
from robotics_photo_db import RoboticsPhotoDatabase
from pathlib import Path
import os

app = Flask(__name__)

@app.route('/')
def marketplace():
    """Serve the marketplace HTML file."""
    return send_file('robotics-marketplace-DATABASE.html')


@app.route('/api/photo/<int:photo_id>')
def serve_photo(photo_id):
    """Serve photos from the database."""
    db = RoboticsPhotoDatabase()
    db.connect()
    
    db.cursor.execute("SELECT file_path FROM photos WHERE photo_id = ?", (photo_id,))
    result = db.cursor.fetchone()
    db.close()
    
    if result:
        photo_path = Path(result[0])
        if photo_path.exists():
            return send_file(photo_path, mimetype='image/jpeg')
    
    return "Photo not found", 404


@app.route('/api/database-robots')
def get_database_robots():
    """API endpoint to get all robots with photos from database."""
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
        # Get all photos for this robot
        db.cursor.execute("""
            SELECT photo_id, file_name, description
            FROM photos
            WHERE robot_id = ?
            ORDER BY upload_date DESC
        """, (robot['robot_id'],))
        
        photos = db.cursor.fetchall()
        photo_urls = [f"/api/photo/{p['photo_id']}" for p in photos]
        
        # If no photos, use placeholder
        if not photo_urls:
            photo_urls = [
                f"https://via.placeholder.com/400x300?text={robot['manufacturer']}+{robot['model_name']}"
            ]
        
        # Ensure we have at least 4 images for the gallery
        while len(photo_urls) < 4:
            photo_urls.append(photo_urls[0])
        
        # Build marketplace product object
        product = {
            'id': robot['robot_id'],
            'name': robot['model_name'],
            'vendor': robot['manufacturer'],
            'price': 'Contact for Quote',
            'priceNote': 'Custom pricing based on requirements',
            'image': photo_urls[0],
            'images': photo_urls[:4],
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
                          f"{robot['photo_count']} photo(s) available in database.",
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
    
    return jsonify(marketplace_products)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🛒 ROBOTICS MARKETPLACE - DATABASE INTEGRATED (SIMPLIFIED)")
    print("="*70)
    print("\n✓ Starting marketplace at http://localhost:8082")
    print("✓ API endpoint: http://localhost:8082/api/database-robots")
    print("✓ Photos served from: http://localhost:8082/api/photo/<id>")
    print("\nNext step: Update marketplace HTML to use /api/database-robots")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=8082)
