#!/usr/bin/env python3
"""
Integrated Robotics Marketplace with Photo Database
Serves the marketplace website with real photos from the database
"""

from flask import Flask, render_template_string, send_file, jsonify
from robotics_photo_db import RoboticsPhotoDatabase
from pathlib import Path
import json

app = Flask(__name__)

# Read the original HTML file
with open('robotics-marketplace-FIXED.html', 'r') as f:
    MARKETPLACE_HTML = f.read()


@app.route('/')
def marketplace():
    """Serve the marketplace with database integration."""
    # Get robots and photos from database
    db = RoboticsPhotoDatabase()
    db.connect()
    
    robots_data = db.list_all_robots()
    
    # Get photos for each robot
    robots_with_photos = []
    for robot in robots_data:
        # Get all photos for this robot
        db.cursor.execute("""
            SELECT photo_id, file_path, file_name, description, photo_type
            FROM photos
            WHERE robot_id = ?
            ORDER BY upload_date DESC
        """, (robot['robot_id'],))
        
        photos = db.cursor.fetchall()
        photo_urls = [f"/api/photo/{p['photo_id']}" for p in photos] if photos else []
        
        robots_with_photos.append({
            'robot_id': robot['robot_id'],
            'name': f"{robot['manufacturer']} {robot['model_name']}",
            'manufacturer': robot['manufacturer'],
            'model': robot['model_name'],
            'type': robot['robot_type'],
            'category': robot['category_name'],
            'year': robot['year_released'],
            'photo_count': robot['photo_count'],
            'photos': photo_urls
        })
    
    db.close()
    
    # Inject database data into the HTML
    # We'll add a script that replaces the hardcoded products with database products
    database_script = f"""
    <script>
    // Database-driven products
    const databaseRobots = {json.dumps(robots_with_photos)};
    
    // Convert database robots to marketplace product format
    const databaseProducts = databaseRobots.map(robot => {{
        const categoryEmojis = {{
            'Drones': '🚁',
            'AMRs': '🤖',
            'Robotic Arms': '🦾'
        }};
        
        return {{
            id: robot.robot_id,
            name: robot.model,
            vendor: robot.manufacturer,
            price: 'Contact for Quote',
            priceNote: 'Custom pricing based on fleet size',
            image: robot.photos[0] || 'https://via.placeholder.com/400x300?text=' + robot.name,
            images: robot.photos.length > 0 ? robot.photos : [
                'https://via.placeholder.com/400x300?text=' + robot.name,
                'https://via.placeholder.com/400x300?text=' + robot.name,
                'https://via.placeholder.com/400x300?text=' + robot.name,
                'https://via.placeholder.com/400x300?text=' + robot.name
            ],
            category: robot.category,
            type: robot.type,
            rating: 4.8,
            reviews: 124,
            emoji: categoryEmojis[robot.category] || '🤖',
            inStock: true,
            verified: true,
            description: `Professional ${{robot.type}} from ${{robot.manufacturer}}. Year: ${{robot.year || 'N/A'}}. ${{robot.photo_count}} photos available in database.`,
            specs: {{
                payload: robot.category === 'Drones' ? '5-10 kg' : robot.category === 'AMRs' ? '250-600 kg' : '5-15 kg',
                battery: robot.category === 'Drones' ? '30-45 min' : '8-12 hrs',
                autonomy: 'Advanced SLAM',
                speed: robot.category === 'Drones' ? '20 m/s' : robot.category === 'AMRs' ? '2 m/s' : 'N/A'
            }},
            features: [
                {{ icon: '🎯', title: 'Precision', desc: 'High accuracy operations' }},
                {{ icon: '🔒', title: 'Safety', desc: 'Advanced safety features' }},
                {{ icon: '📊', title: 'Analytics', desc: 'Real-time monitoring' }},
                {{ icon: '🔧', title: 'Maintenance', desc: 'Easy to service' }}
            ],
            applications: ['Manufacturing', 'Warehousing', 'Logistics', 'Inspection']
        }};
    }});
    
    // Replace the original products array with database products
    // This will be injected before the renderProducts() call
    console.log('Loaded ' + databaseProducts.length + ' robots from database');
    products = databaseProducts;
    </script>
    """
    
    # Insert the database script before the closing </body> tag
    # We need to inject it before renderProducts() is called
    html_with_db = MARKETPLACE_HTML.replace(
        '// Initial render\n        renderProducts();',
        database_script + '\n        // Initial render\n        renderProducts();'
    )
    
    return html_with_db


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


@app.route('/api/robots')
def get_robots():
    """API endpoint to get all robots with photos."""
    db = RoboticsPhotoDatabase()
    db.connect()
    
    robots_data = db.list_all_robots()
    
    robots_with_photos = []
    for robot in robots_data:
        db.cursor.execute("""
            SELECT photo_id, file_name, description
            FROM photos
            WHERE robot_id = ?
        """, (robot['robot_id'],))
        
        photos = [dict(p) for p in db.cursor.fetchall()]
        
        robots_with_photos.append({
            'robot_id': robot['robot_id'],
            'manufacturer': robot['manufacturer'],
            'model_name': robot['model_name'],
            'robot_type': robot['robot_type'],
            'category_name': robot['category_name'],
            'year_released': robot['year_released'],
            'photo_count': robot['photo_count'],
            'photos': photos
        })
    
    db.close()
    return jsonify(robots_with_photos)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🛒 ROBOTICS MARKETPLACE - DATABASE INTEGRATED")
    print("="*70)
    print("\n✓ Starting marketplace at http://localhost:8082")
    print("✓ Displaying robots from your photo database")
    print("✓ Photos will show from your uploads")
    print(f"\nYour marketplace now has REAL photos from the database!")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=8082)
