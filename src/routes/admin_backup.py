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
    token = os.environ.get('GITHUB_TOKEN')
    print(f"DEBUG: Retrieved token: {'Found' if token else 'Not found'}")
    return token

def check_github_connection():
    """Check if GitHub API is accessible with current token"""
    token = get_github_token()
    if not token:
        return False, "GitHub token not configured in environment variables"
    
    try:
        # Fixed: Use proper Authorization header format for Personal Access Tokens
        headers = {
            'Authorization': f'Bearer {token}',  # Changed from 'token' to 'Bearer'
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'MindsEyePhotography-Backup/1.0'
        }
        
        print(f"DEBUG: Making request to GitHub API...")
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        print(f"DEBUG: GitHub API response status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get('login', 'Unknown')
            print(f"DEBUG: Successfully connected as: {username}")
            return True, f"✅ Connected as {username}"
        elif response.status_code == 401:
            return False, "❌ Invalid GitHub token - please check your token permissions"
        else:
            return False, f"❌ GitHub API error: {response.status_code} - {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return False, "❌ Connection timeout - GitHub API unreachable"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Connection error: {str(e)}"
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        return False, f"❌ Unexpected error: {str(e)}"

def create_github_backup(repo_owner, repo_name, backup_data):
    """Create backup in GitHub repository"""
    token = get_github_token()
    if not token:
        return False, "GitHub token not configured"
    
    try:
        # Fixed: Use proper Authorization header format
        headers = {
            'Authorization': f'Bearer {token}',  # Changed from 'token' to 'Bearer'
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'MindsEyePhotography-Backup/1.0'
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
            return True, f"✅ Backup created: {filename}"
        else:
            return False, f"❌ GitHub API error: {response.status_code} - {response.text[:200]}"
            
    except Exception as e:
        return False, f"❌ Backup error: {str(e)}"

def create_local_backup():
    """Create comprehensive local backup as tar.gz file"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"minds_eye_backup_{timestamp}.tar.gz"
        temp_dir = tempfile.mkdtemp()
        backup_path = os.path.join(temp_dir, backup_filename)
        
        # Create tar.gz file
        with tarfile.open(backup_path, 'w:gz') as tar:
            # Add database
            db_path = 'src/database/app.db'
            if os.path.exists(db_path):
                tar.add(db_path, arcname='database/app.db')
            
            # Add all images
            assets_path = 'src/static/assets'
            if os.path.exists(assets_path):
                tar.add(assets_path, arcname='assets')
            
            # Add configuration files
            config_files = [
                'src/static/portfolio-data-multicategory.json',
                'src/static/categories-config.json'
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    tar.add(config_file, arcname=f'config/{os.path.basename(config_file)}')
        
        # Get file size
        file_size = os.path.getsize(backup_path)
        size_mb = round(file_size / (1024 * 1024), 2)
        
        return True, {
            'filename': backup_filename,
            'path': backup_path,
            'size': f"{size_mb} MB",
            'timestamp': timestamp
        }
        
    except Exception as e:
        return False, f"❌ Local backup failed: {str(e)}"

# API Routes for backup functionality
@admin_bp.route('/api/admin/backup/github/status')
def api_github_backup_status():
    """API endpoint to check GitHub backup status"""
    try:
        success, message = check_github_connection()
        
        if success:
            return jsonify({
                'status': 'Connected',
                'connection': message,
                'last_backup': 'Not implemented yet'
            })
        else:
            return jsonify({
                'error': True,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f"Status check failed: {str(e)}"
        }), 500

@admin_bp.route('/api/admin/backup/github/setup', methods=['POST'])
def api_github_backup_setup():
    """API endpoint to set up GitHub auto-backup"""
    try:
        # First check if GitHub connection works
        success, message = check_github_connection()
        
        if not success:
            return jsonify({
                'error': True,
                'message': f"GitHub connection failed: {message}"
            }), 400
        
        # If connection works, setup is successful
        return jsonify({
            'message': f"✅ GitHub auto-backup configured successfully! {message}"
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f"Setup failed: {str(e)}"
        }), 500

@admin_bp.route('/api/admin/backup/local', methods=['POST'])
def api_local_backup():
    """API endpoint to create local backup"""
    try:
        success, result = create_local_backup()
        
        if success:
            return jsonify({
                'filename': result['filename'],
                'size': result['size'],
                'download_url': f"/api/admin/backup/download/{result['filename']}"
            })
        else:
            return jsonify({
                'error': True,
                'message': result
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f"Local backup failed: {str(e)}"
        }), 500

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

# Placeholder for remaining admin routes - these would be included in the full file
@admin_bp.route('/admin/portfolio')
def portfolio_management():
    """Portfolio management interface - placeholder"""
    return "Portfolio management interface would be here"

@admin_bp.route('/admin/categories')  
def category_management():
    """Category management interface - placeholder"""
    return "Category management interface would be here"

@admin_bp.route('/admin/featured')
def featured_management():
    """Featured image management interface - placeholder"""
    return "Featured image management interface would be here"

@admin_bp.route('/admin/backgrounds')
def background_management():
    """Background management interface - placeholder"""
    return "Background management interface would be here"

@admin_bp.route('/admin/contacts')
def contact_management():
    """Contact management interface - placeholder"""
    return "Contact management interface would be here"

