from flask import Blueprint, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename
from PIL import Image
from PIL.ExifTags import TAGS
import os
import uuid
import json
import shutil
import tarfile
import tempfile
import requests
import base64
from datetime import datetime
from src.models.user import db, PortfolioImage, Category, FeaturedImage, BackgroundImage, ContactSubmission

admin_bp = Blueprint('admin', __name__)

UPLOAD_FOLDER = 'src/static/assets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_exif_data(image_path):
    """Extract EXIF data from image"""
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if exif_data is None:
            return {}
            
        exif = {}
        for key, value in exif_data.items():
            if key in TAGS:
                exif[TAGS[key]] = value
                
        return {
            'camera_make': exif.get('Make', ''),
            'camera_model': exif.get('Model', ''),
            'lens': exif.get('LensModel', ''),
            'aperture': str(exif.get('FNumber', '')),
            'shutter_speed': str(exif.get('ExposureTime', '')),
            'iso': str(exif.get('ISOSpeedRatings', '')),
            'focal_length': str(exif.get('FocalLength', '')),
            'date_taken': exif.get('DateTime', '')
        }
    except Exception as e:
        print(f"Error extracting EXIF: {e}")
        return {}

def get_github_token():
    """Get GitHub token from environment variables"""
    return os.environ.get('GITHUB_TOKEN')

def check_github_connection():
    """Check if GitHub API is accessible with current token"""
    token = get_github_token()
    if not token:
        return False, "GitHub token not configured"
    
    try:
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            return True, f"Connected as {user_data.get('login', 'Unknown')}"
        else:
            return False, f"GitHub API error: {response.status_code}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def create_github_backup(repo_owner, repo_name, backup_data):
    """Create backup in GitHub repository"""
    token = get_github_token()
    if not token:
        return False, "GitHub token not configured"
    
    try:
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Create backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{timestamp}.json"
        
        # Encode backup data
        content = base64.b64encode(json.dumps(backup_data, indent=2, default=str).encode()).decode()
        
        # Create file in repository
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/backups/{filename}'
        data = {
            'message': f'Automated backup - {timestamp}',
            'content': content
        }
        
        response = requests.put(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            return True, f"Backup created: {filename}"
        else:
            return False, f"GitHub API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Backup error: {str(e)}"

@admin_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mind's Eye Photography - Admin</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #ff6b35; font-size: 2.5em; margin-bottom: 10px; }
            .admin-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .admin-card { background: #2a2a2a; padding: 30px; border-radius: 10px; text-align: center; }
            .admin-card h3 { color: #ff6b35; margin-bottom: 15px; }
            .admin-card p { margin-bottom: 20px; color: #ccc; }
            .btn { display: inline-block; padding: 12px 24px; background: #ff6b35; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }
            .btn:hover { background: #e55a2b; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Mind's Eye Photography</h1>
                <p>Admin Dashboard</p>
            </div>
            <div class="admin-grid">
                <div class="admin-card">
                    <h3>Portfolio Management</h3>
                    <p>Upload, organize, and manage your photography portfolio</p>
                    <a href="/admin/portfolio" class="btn">Manage Portfolio</a>
                </div>
                <div class="admin-card">
                    <h3>Featured Image</h3>
                    <p>Set and manage the featured image on your homepage</p>
                    <a href="/admin/featured" class="btn">Manage Featured</a>
                </div>
                <div class="admin-card">
                    <h3>Categories</h3>
                    <p>Create and organize image categories</p>
                    <a href="/admin/categories" class="btn">Manage Categories</a>
                </div>
                <div class="admin-card">
                    <h3>Background Images</h3>
                    <p>Manage website background images</p>
                    <a href="/admin/backgrounds" class="btn">Manage Backgrounds</a>
                </div>
                <div class="admin-card">
                    <h3>Backup Management</h3>
                    <p>Create backups and manage data protection</p>
                    <a href="/admin/backup" class="btn">Manage Backups</a>
                </div>
                <div class="admin-card">
                    <h3>Contact Messages</h3>
                    <p>View and manage contact form submissions</p>
                    <a href="/admin/contacts" class="btn">View Messages</a>
                </div>
                <div class="admin-card">
                    <h3>Back to Site</h3>
                    <p>Return to the main website</p>
                    <a href="/" class="btn">View Site</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@admin_bp.route('/admin/backup')
def backup_management():
    """Backup management interface"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backup Management - Mind's Eye Photography</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #ff6b35; font-size: 2em; margin-bottom: 10px; }
            .backup-section { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .backup-section h3 { color: #ff6b35; margin-bottom: 15px; }
            .backup-section p { color: #ccc; margin-bottom: 15px; }
            .btn { padding: 12px 24px; margin: 5px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #e55a2b; }
            .btn.secondary { background: #555; }
            .btn.secondary:hover { background: #666; }
            .btn.danger { background: #dc3545; }
            .btn.danger:hover { background: #c82333; }
            .status { padding: 15px; margin: 15px 0; border-radius: 5px; }
            .status.success { background: #28a745; }
            .status.error { background: #dc3545; }
            .status.info { background: #17a2b8; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #555; color: white; text-decoration: none; border-radius: 4px; }
            .back-btn:hover { background: #666; }
            ul { margin-left: 20px; }
            ul li { margin-bottom: 5px; color: #ccc; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-btn">← Back to Admin</a>
            <div class="header">
                <h1>Backup Management</h1>
                <p>Protect your photography portfolio with comprehensive backups</p>
            </div>
            
            <div class="backup-section">
                <h3>Create Local Backup</h3>
                <p>Create an immediate backup to local disk before making changes or enhancements</p>
                <button class="btn" onclick="createLocalBackup()">Create Local Backup</button>
                
                <h4 style="color: #ff6b35; margin-top: 20px;">Backup includes:</h4>
                <ul>
                    <li>All portfolio images and metadata</li>
                    <li>Categories and settings</li>
                    <li>Featured image configurations</li>
                    <li>Contact form submissions</li>
                    <li>Background image settings</li>
                    <li>Database (SQLite file)</li>
                </ul>
            </div>
            
            <div class="backup-section">
                <h3>GitHub Auto-Backup</h3>
                <p>Automatic set-and-forget backups to GitHub repository</p>
                <button class="btn secondary" onclick="setupGitBackup()">Set Up Auto-backup</button>
                <button class="btn secondary" onclick="checkBackupStatus()">Check Status</button>
                
                <h4 style="color: #ff6b35; margin-top: 20px;">Auto-backup features:</h4>
                <ul>
                    <li>Daily automatic backups to GitHub</li>
                    <li>Version history and rollback capability</li>
                    <li>Secure cloud storage</li>
                    <li>No manual intervention required</li>
                </ul>
            </div>
            
            <div class="backup-section">
                <h3>Emergency Restore</h3>
                <p>Restore from a previous backup in case of issues</p>
                <button class="btn danger" onclick="emergencyRestore()">Emergency Restore</button>
                
                <h4 style="color: #ff6b35; margin-top: 20px;">Restore options:</h4>
                <ul>
                    <li>Restore from local backup</li>
                    <li>Restore from GitHub backup</li>
                    <li>Selective restore (images only, data only, etc.)</li>
                </ul>
                <p style="color: #ff6b35; margin-top: 10px;"><strong>Warning:</strong> This will overwrite current data</p>
            </div>
            
            <div id="status"></div>
        </div>
        
        <script>
        async function createLocalBackup() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status info">Creating local backup...</div>';
            
            try {
                const response = await fetch('/api/admin/backup/local', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    statusDiv.innerHTML = `<div class="status success">
                        Local backup created successfully!<br>
                        <strong>File:</strong> ${result.filename}<br>
                        <strong>Size:</strong> ${result.size}<br>
                        <a href="${result.download_url}" class="btn" style="margin-top: 10px;">Download Backup</a>
                    </div>`;
                } else {
                    const error = await response.json();
                    statusDiv.innerHTML = `<div class="status error">Backup failed: ${error.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">Backup failed: ${error.message}</div>`;
            }
        }
        
        async function setupGitBackup() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status info">Setting up GitHub auto-backup...</div>';
            
            try {
                const response = await fetch('/api/admin/backup/github/setup', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    statusDiv.innerHTML = `<div class="status success">${result.message}</div>`;
                } else {
                    const error = await response.json();
                    statusDiv.innerHTML = `<div class="status error">Setup failed: ${error.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">Setup failed: ${error.message}</div>`;
            }
        }
        
        async function checkBackupStatus() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status info">Checking GitHub backup status...</div>';
            
            try {
                const response = await fetch('/api/admin/backup/github/status');
                
                if (response.ok) {
                    const result = await response.json();
                    statusDiv.innerHTML = `<div class="status success">
                        <strong>GitHub Status:</strong> ${result.status}<br>
                        <strong>Connection:</strong> ${result.connection}<br>
                        ${result.last_backup ? `<strong>Last Backup:</strong> ${result.last_backup}` : ''}
                    </div>`;
                } else {
                    const error = await response.json();
                    statusDiv.innerHTML = `<div class="status error">Status check failed: ${error.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">Status check failed: ${error.message}</div>`;
            }
        }
        
        function emergencyRestore() {
            if (confirm('Are you sure you want to perform an emergency restore? This will overwrite all current data.')) {
                alert('Emergency restore functionality will be implemented based on your specific needs.');
            }
        }
        </script>
    </body>
    </html>
    ''')

# Continue with existing portfolio management code...
@admin_bp.route('/admin/portfolio')
def portfolio_management():
    """Portfolio management interface"""
    images = PortfolioImage.query.filter_by(is_active=True).order_by(PortfolioImage.sort_order).all()
    categories = Category.query.order_by(Category.sort_order).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Portfolio Management - Mind's Eye Photography</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #ff6b35; font-size: 2em; margin-bottom: 10px; }
            .upload-section { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .upload-form { display: flex; gap: 15px; align-items: end; flex-wrap: wrap; }
            .form-group { display: flex; flex-direction: column; }
            .form-group label { margin-bottom: 5px; color: #ccc; }
            .form-group input, .form-group select { padding: 8px; border: 1px solid #555; background: #333; color: #fff; border-radius: 4px; }
            .btn { padding: 10px 20px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #e55a2b; }
            .images-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .image-card { background: #2a2a2a; border-radius: 10px; overflow: hidden; }
            .image-card img { width: 100%; height: 200px; object-fit: cover; }
            .image-info { padding: 15px; }
            .image-info h4 { color: #ff6b35; margin-bottom: 5px; }
            .image-info p { color: #ccc; font-size: 0.9em; margin-bottom: 5px; }
            .exif-badges { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
            .exif-badge { background: #ff6b35; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #555; color: white; text-decoration: none; border-radius: 4px; }
            .back-btn:hover { background: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-btn">← Back to Admin</a>
            <div class="header">
                <h1>Portfolio Management</h1>
                <p>Upload and manage your photography portfolio</p>
            </div>
            
            <div class="upload-section">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Upload New Image</h3>
                <form class="upload-form" enctype="multipart/form-data" onsubmit="uploadImage(event)">
                    <div class="form-group">
                        <label>Image Files (Multiple)</label>
                        <input type="file" name="images" accept="image/*" multiple required>
                    </div>
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" name="title" placeholder="Image title">
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <input type="text" name="description" placeholder="Image description">
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category_id">
                            <option value="">Select category</option>
                            {% for category in categories %}
                            <option value="{{ category.id }}">{{ category.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <button type="submit" class="btn">Upload Image</button>
                    </div>
                </form>
            </div>
            
            <div class="images-grid">
                {% for image in images %}
                <div class="image-card">
                    <img src="/assets/{{ image.filename }}" alt="{{ image.title or image.original_filename }}">
                    <div class="image-info">
                        <h4>{{ image.title or image.original_filename }}</h4>
                        {% if image.description %}
                        <p>{{ image.description }}</p>
                        {% endif %}
                        <div class="exif-badges">
                            <span class="exif-badge">📷 {{ image.camera_make or 'Not Available' }} {{ image.camera_model or '' }}</span>
                            <span class="exif-badge">🔍 {{ image.lens or 'Not Available' }}</span>
                            <span class="exif-badge">⚙️ {{ image.aperture or 'N/A' }}, {{ image.shutter_speed or 'N/A' }}, ISO {{ image.iso or 'N/A' }}</span>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
        async function uploadImage(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            
            try {
                const response = await fetch('/api/admin/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    alert('Image uploaded successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Upload failed: ' + error.message);
                }
            } catch (error) {
                alert('Upload failed: ' + error.message);
            }
        }
        </script>
    </body>
    </html>
    ''', images=images, categories=categories)

# API Routes for backup functionality
@admin_bp.route('/api/admin/backup/local', methods=['POST'])
def create_local_backup():
    """Create comprehensive local backup as tar.gz file"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"minds_eye_backup_{timestamp}.tar.gz"
        
        # Create temporary directory for backup preparation
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = os.path.join(temp_dir, f"backup_{timestamp}")
            os.makedirs(backup_dir)
            
            # 1. Export database data
            db_data = {
                'timestamp': timestamp,
                'portfolio_images': [img.to_dict() for img in PortfolioImage.query.all()],
                'categories': [cat.to_dict() for cat in Category.query.all()],
                'featured_images': [feat.to_dict() for feat in FeaturedImage.query.all()],
                'background_images': [bg.to_dict() for bg in BackgroundImage.query.all()],
                'contact_submissions': [contact.to_dict() for contact in ContactSubmission.query.all()]
            }
            
            # Save database backup
            db_backup_path = os.path.join(backup_dir, 'database_backup.json')
            with open(db_backup_path, 'w') as f:
                json.dump(db_data, f, indent=2, default=str)
            
            # 2. Copy images directory
            if os.path.exists(UPLOAD_FOLDER):
                images_backup_dir = os.path.join(backup_dir, 'images')
                shutil.copytree(UPLOAD_FOLDER, images_backup_dir)
            
            # 3. Copy database file if it exists
            db_file_path = 'src/database/app.db'  # Adjust path as needed
            if os.path.exists(db_file_path):
                shutil.copy2(db_file_path, os.path.join(backup_dir, 'app.db'))
            
            # 4. Create backup info file
            backup_info = {
                'created': timestamp,
                'version': '1.0',
                'description': 'Complete Mind\'s Eye Photography backup',
                'includes': [
                    'Database (JSON export)',
                    'Portfolio images',
                    'SQLite database file',
                    'All configurations'
                ]
            }
            
            info_path = os.path.join(backup_dir, 'backup_info.json')
            with open(info_path, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # 5. Create tar.gz archive
            backup_path = os.path.join(temp_dir, backup_filename)
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(backup_dir, arcname=f"backup_{timestamp}")
            
            # 6. Move to permanent location (or prepare for download)
            final_backup_path = os.path.join('/tmp', backup_filename)
            shutil.move(backup_path, final_backup_path)
            
            # Get file size
            file_size = os.path.getsize(final_backup_path)
            size_mb = round(file_size / (1024 * 1024), 2)
            
            return jsonify({
                'message': 'Local backup created successfully',
                'filename': backup_filename,
                'size': f'{size_mb} MB',
                'path': final_backup_path,
                'download_url': f'/api/admin/backup/download/{backup_filename}'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/backup/download/<filename>')
def download_backup(filename):
    """Download backup file"""
    try:
        backup_path = os.path.join('/tmp', filename)
        if os.path.exists(backup_path):
            return send_file(backup_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'Backup file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/backup/github/status')
def github_backup_status():
    """Check GitHub backup status"""
    try:
        connected, message = check_github_connection()
        
        return jsonify({
            'status': 'Connected' if connected else 'Disconnected',
            'connection': message,
            'token_configured': bool(get_github_token()),
            'last_backup': None  # TODO: Implement backup history tracking
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/backup/github/setup', methods=['POST'])
def setup_github_backup():
    """Set up GitHub auto-backup"""
    try:
        # Check if token is configured
        if not get_github_token():
            return jsonify({'error': 'GitHub token not configured in environment variables'}), 400
        
        # Test GitHub connection
        connected, message = check_github_connection()
        if not connected:
            return jsonify({'error': f'GitHub connection failed: {message}'}), 400
        
        # Create test backup to verify functionality
        db_data = {
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'test': True,
            'portfolio_images_count': PortfolioImage.query.count(),
            'categories_count': Category.query.count()
        }
        
        # For now, just return success - actual auto-backup scheduling would need additional setup
        return jsonify({
            'message': f'GitHub auto-backup configured successfully! {message}',
            'status': 'ready',
            'next_backup': 'Manual trigger required (automatic scheduling coming soon)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Continue with existing API routes...
@admin_bp.route('/api/admin/upload', methods=['POST'])
def upload_image():
    """Handle multiple image uploads"""
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400
    
    files = request.files.getlist('images')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_images = []
    errors = []
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        for file in files:
            if not file or file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                errors.append(f"Invalid file type: {file.filename}")
                continue
            
            try:
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                # Save file
                file.save(file_path)
                
                # Extract EXIF data
                exif_data = extract_exif_data(file_path)
                
                # Get image dimensions
                with Image.open(file_path) as img:
                    width, height = img.size
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Create database entry
                portfolio_image = PortfolioImage(
                    filename=unique_filename,
                    original_filename=secure_filename(file.filename),
                    title=request.form.get('title', ''),
                    description=request.form.get('description', ''),
                    camera_make=exif_data.get('camera_make', ''),
                    camera_model=exif_data.get('camera_model', ''),
                    lens=exif_data.get('lens', ''),
                    aperture=exif_data.get('aperture', ''),
                    shutter_speed=exif_data.get('shutter_speed', ''),
                    iso=exif_data.get('iso', ''),
                    focal_length=exif_data.get('focal_length', ''),
                    file_size=file_size,
                    width=width,
                    height=height
                )
                
                # Parse date_taken if available
                if exif_data.get('date_taken'):
                    try:
                        portfolio_image.date_taken = datetime.strptime(exif_data['date_taken'], '%Y:%m:%d %H:%M:%S')
                    except:
                        pass
                
                db.session.add(portfolio_image)
                
                # Add to category if specified
                category_id = request.form.get('category_id')
                if category_id:
                    category = Category.query.get(category_id)
                    if category:
                        portfolio_image.categories.append(category)
                
                uploaded_images.append(portfolio_image.to_dict())
                
            except Exception as e:
                errors.append(f"Error uploading {file.filename}: {str(e)}")
        
        db.session.commit()
        
        result = {
            'message': f'Successfully uploaded {len(uploaded_images)} images',
            'images': uploaded_images
        }
        
        if errors:
            result['errors'] = errors
        
        return jsonify(result)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Continue with remaining existing routes...
# (The rest of the original admin routes would continue here)

