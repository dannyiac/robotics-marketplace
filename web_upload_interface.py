#!/usr/bin/env python3
"""
Complete Web Upload Interface for Robotics Photos
Includes drag-and-drop, bulk upload, and preview
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
from robotics_photo_db import RoboticsPhotoDatabase
import os
from pathlib import Path
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'

# Ensure upload folder exists
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# HTML Template with drag-and-drop upload
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Robotics Photo Upload</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 30px; }
        
        .upload-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .drop-zone {
            border: 3px dashed #ccc;
            border-radius: 12px;
            padding: 60px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #fafafa;
        }
        
        .drop-zone:hover, .drop-zone.dragover {
            border-color: #4CAF50;
            background: #f0f8f0;
        }
        
        .drop-zone-text {
            font-size: 18px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .upload-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }
        
        .upload-btn:hover { background: #45a049; }
        .upload-btn:disabled { background: #ccc; cursor: not-allowed; }
        
        .form-group {
            margin: 20px 0;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        .form-group select, .form-group input, .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .preview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .preview-card {
            position: relative;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .preview-card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        
        .preview-info {
            padding: 10px;
            background: white;
            font-size: 12px;
            color: #666;
        }
        
        .remove-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            cursor: pointer;
            font-size: 18px;
        }
        
        .success-msg {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
            display: none;
        }
        
        .error-msg {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
            display: none;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Robotics Photo Upload</h1>
        
        <div class="upload-section">
            <h2>Upload Photos</h2>
            
            <div class="form-group">
                <label for="robot-select">Select Robot:</label>
                <select id="robot-select" required>
                    <option value="">-- Choose a robot --</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="photo-type">Photo Type:</label>
                <select id="photo-type">
                    <option value="general">General</option>
                    <option value="front view">Front View</option>
                    <option value="side view">Side View</option>
                    <option value="top view">Top View</option>
                    <option value="in operation">In Operation</option>
                    <option value="detail shot">Detail Shot</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="tags">Tags (comma-separated):</label>
                <input type="text" id="tags" placeholder="e.g., aerial, 4k, outdoor">
            </div>
            
            <div class="form-group">
                <label for="description">Description:</label>
                <textarea id="description" rows="3" placeholder="Describe the photo..."></textarea>
            </div>
            
            <div class="drop-zone" id="drop-zone">
                <div class="drop-zone-text">
                    📁 Drag & drop photos here or click to browse
                </div>
                <div style="color: #999; font-size: 14px;">
                    Supports: JPG, PNG, GIF, WebP (max 50MB)
                </div>
                <input type="file" id="file-input" multiple accept="image/*" style="display: none;">
            </div>
            
            <div class="progress-bar" id="progress-bar">
                <div class="progress-fill" id="progress-fill">0%</div>
            </div>
            
            <div class="preview-grid" id="preview-grid"></div>
            
            <button class="upload-btn" id="upload-btn" disabled>
                Upload Photos
            </button>
            
            <div class="success-msg" id="success-msg"></div>
            <div class="error-msg" id="error-msg"></div>
        </div>
    </div>
    
    <script>
        let selectedFiles = [];
        
        // Load robots
        fetch('/api/robots')
            .then(r => r.json())
            .then(robots => {
                const select = document.getElementById('robot-select');
                robots.forEach(robot => {
                    const option = document.createElement('option');
                    option.value = robot.robot_id;
                    option.textContent = `${robot.manufacturer} ${robot.model_name} (${robot.category_name})`;
                    select.appendChild(option);
                });
            });
        
        // Drag and drop
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(files) {
            selectedFiles = Array.from(files);
            displayPreviews();
            document.getElementById('upload-btn').disabled = selectedFiles.length === 0;
        }
        
        function displayPreviews() {
            const grid = document.getElementById('preview-grid');
            grid.innerHTML = '';
            
            selectedFiles.forEach((file, index) => {
                const card = document.createElement('div');
                card.className = 'preview-card';
                
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                
                const info = document.createElement('div');
                info.className = 'preview-info';
                info.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                
                const removeBtn = document.createElement('button');
                removeBtn.className = 'remove-btn';
                removeBtn.textContent = '×';
                removeBtn.onclick = () => {
                    selectedFiles.splice(index, 1);
                    displayPreviews();
                    document.getElementById('upload-btn').disabled = selectedFiles.length === 0;
                };
                
                card.appendChild(img);
                card.appendChild(info);
                card.appendChild(removeBtn);
                grid.appendChild(card);
            });
        }
        
        // Upload
        document.getElementById('upload-btn').addEventListener('click', async () => {
            const robotId = document.getElementById('robot-select').value;
            if (!robotId) {
                alert('Please select a robot');
                return;
            }
            
            const photoType = document.getElementById('photo-type').value;
            const tags = document.getElementById('tags').value;
            const description = document.getElementById('description').value;
            
            const progressBar = document.getElementById('progress-bar');
            const progressFill = document.getElementById('progress-fill');
            progressBar.style.display = 'block';
            
            let uploaded = 0;
            
            for (const file of selectedFiles) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('robot_id', robotId);
                formData.append('photo_type', photoType);
                formData.append('tags', tags);
                formData.append('description', description);
                
                try {
                    const response = await fetch('/api/upload_photo', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        uploaded++;
                        const percent = Math.round((uploaded / selectedFiles.length) * 100);
                        progressFill.style.width = percent + '%';
                        progressFill.textContent = percent + '%';
                    }
                } catch (error) {
                    console.error('Upload error:', error);
                }
            }
            
            // Show success
            const successMsg = document.getElementById('success-msg');
            successMsg.textContent = `Successfully uploaded ${uploaded} of ${selectedFiles.length} photos!`;
            successMsg.style.display = 'block';
            
            // Reset
            setTimeout(() => {
                selectedFiles = [];
                displayPreviews();
                progressBar.style.display = 'none';
                progressFill.style.width = '0%';
                document.getElementById('upload-btn').disabled = true;
                fileInput.value = '';
            }, 2000);
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/robots')
def get_robots():
    db = RoboticsPhotoDatabase()
    db.connect()
    robots = db.list_all_robots()
    db.close()
    return jsonify(robots)


@app.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file'}), 400
    
    # Save temporarily
    filename = secure_filename(file.filename)
    temp_path = Path(app.config['UPLOAD_FOLDER']) / filename
    file.save(temp_path)
    
    try:
        db = RoboticsPhotoDatabase()
        db.connect()
        
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else None
        tags = [t.strip() for t in tags if t.strip()] if tags else None
        
        photo_id = db.add_photo(
            robot_id=int(request.form.get('robot_id')),
            source_file=str(temp_path),
            photo_type=request.form.get('photo_type', 'general'),
            description=request.form.get('description'),
            tags=tags
        )
        
        db.close()
        return jsonify({'success': True, 'photo_id': photo_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🤖 ROBOTICS PHOTO UPLOAD INTERFACE")
    print("="*70)
    print("\n✓ Server starting at http://localhost:5000")
    print("✓ Drag & drop photos to upload")
    print("✓ Supports bulk uploads")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=8080)
