#!/usr/bin/env python3
"""
Photo Gallery Viewer for Robotics Database
View all uploaded photos in a beautiful gallery
"""

from flask import Flask, render_template_string, send_file
from robotics_photo_db import RoboticsPhotoDatabase
from pathlib import Path

app = Flask(__name__)

# HTML Template for Gallery
GALLERY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Robotics Photo Gallery</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .stats {
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .stats h2 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .filters {
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .filter-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .filter-btn:hover, .filter-btn.active {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        
        .photo-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        
        .photo-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        .photo-image {
            width: 100%;
            height: 300px;
            object-fit: cover;
            background: #f0f0f0;
        }
        
        .photo-info {
            padding: 20px;
        }
        
        .photo-title {
            font-size: 18px;
            font-weight: 700;
            color: #333;
            margin-bottom: 8px;
        }
        
        .photo-robot {
            font-size: 14px;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .photo-meta {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
        }
        
        .meta-tag {
            background: #f0f0f0;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            color: #666;
        }
        
        .photo-description {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
            line-height: 1.5;
        }
        
        .category-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-drones {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .badge-amrs {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        
        .badge-robotic-arms {
            background: #e8f5e9;
            color: #388e3c;
        }
        
        .no-photos {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 12px;
            color: #666;
            font-size: 18px;
        }
        
        .lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .lightbox.active {
            display: flex;
        }
        
        .lightbox-image {
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
            border-radius: 8px;
        }
        
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 30px;
            color: white;
            font-size: 40px;
            cursor: pointer;
            background: rgba(255,255,255,0.1);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.3s;
        }
        
        .lightbox-close:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Robotics Photo Gallery</h1>
        
        <div class="stats">
            <h2>Database Statistics</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ stats.total_photos }}</div>
                    <div class="stat-label">Total Photos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.by_category.get('Drones', 0) }}</div>
                    <div class="stat-label">Drone Photos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.by_category.get('AMRs', 0) }}</div>
                    <div class="stat-label">AMR Photos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.by_category.get('Robotic Arms', 0) }}</div>
                    <div class="stat-label">Robotic Arm Photos</div>
                </div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <button class="filter-btn active" onclick="filterCategory('all')">All</button>
                <button class="filter-btn" onclick="filterCategory('Drones')">Drones</button>
                <button class="filter-btn" onclick="filterCategory('AMRs')">AMRs</button>
                <button class="filter-btn" onclick="filterCategory('Robotic Arms')">Robotic Arms</button>
            </div>
        </div>
        
        {% if photos %}
        <div class="gallery" id="gallery">
            {% for photo in photos %}
            <div class="photo-card" data-category="{{ photo.category_name }}" onclick="openLightbox('{{ photo.photo_id }}')">
                <img src="/photo/{{ photo.photo_id }}" alt="{{ photo.description or photo.file_name }}" class="photo-image">
                <div class="photo-info">
                    <div class="category-badge badge-{{ photo.category_name.lower().replace(' ', '-') }}">
                        {{ photo.category_name }}
                    </div>
                    <div class="photo-title">{{ photo.file_name }}</div>
                    <div class="photo-robot">
                        {{ photo.manufacturer }} {{ photo.model_name }}
                    </div>
                    {% if photo.description %}
                    <div class="photo-description">{{ photo.description }}</div>
                    {% endif %}
                    <div class="photo-meta">
                        <span class="meta-tag">{{ photo.photo_type }}</span>
                        <span class="meta-tag">{{ photo.upload_date }}</span>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-photos">
            <h2>📸 No photos yet!</h2>
            <p>Upload some photos using the upload interface.</p>
        </div>
        {% endif %}
    </div>
    
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img src="" alt="" class="lightbox-image" id="lightbox-img">
    </div>
    
    <script>
        function filterCategory(category) {
            const cards = document.querySelectorAll('.photo-card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            cards.forEach(card => {
                if (category === 'all' || card.dataset.category === category) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        function openLightbox(photoId) {
            const lightbox = document.getElementById('lightbox');
            const img = document.getElementById('lightbox-img');
            img.src = '/photo/' + photoId;
            lightbox.classList.add('active');
        }
        
        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
        }
        
        // Close lightbox on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeLightbox();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def gallery():
    """Display photo gallery."""
    db = RoboticsPhotoDatabase()
    db.connect()
    
    # Get all photos with robot info
    photos = db.search_photos()
    stats = db.get_statistics()
    
    db.close()
    
    return render_template_string(GALLERY_HTML, photos=photos, stats=stats)


@app.route('/photo/<int:photo_id>')
def serve_photo(photo_id):
    """Serve a specific photo."""
    db = RoboticsPhotoDatabase()
    db.connect()
    
    # Get photo info
    db.cursor.execute("SELECT file_path FROM photos WHERE photo_id = ?", (photo_id,))
    result = db.cursor.fetchone()
    db.close()
    
    if result:
        photo_path = Path(result[0])
        if photo_path.exists():
            return send_file(photo_path, mimetype='image/jpeg')
    
    return "Photo not found", 404


if __name__ == '__main__':
    print("\n" + "="*70)
    print("📸 ROBOTICS PHOTO GALLERY VIEWER")
    print("="*70)
    print("\n✓ Starting gallery at http://localhost:8081")
    print("✓ View all your uploaded photos")
    print("✓ Filter by category")
    print("✓ Click photos to enlarge")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=8081)
