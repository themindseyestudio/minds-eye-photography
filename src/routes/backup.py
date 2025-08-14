import os
import json
import zipfile
import tempfile
import re
from datetime import datetime
from flask import Blueprint, request, send_file, redirect, url_for, session, render_template_string, jsonify
from werkzeug.utils import secure_filename

backup_bp = Blueprint('backup', __name__)

# Configuration paths
PHOTOGRAPHY_ASSETS_DIR = '/app/uploads'
STATIC_ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets')

def sanitize_filename(name):
    """Sanitize custom name for safe filename usage"""
    # Remove or replace unsafe characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove extra spaces and replace with underscores
    name = re.sub(r'\s+', '_', name.strip())
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Limit length
    if len(name) > 50:
        name = name[:50]
    # Ensure not empty
    if not name:
        name = 'backup'
    return name

def create_backup_zip():
    """Create a comprehensive backup ZIP file"""
    try:
        # Create temporary file for ZIP
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        # Create ZIP file
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # 1. Backup all portfolio images from persistent storage
            image_count = 0
            if os.path.exists(PHOTOGRAPHY_ASSETS_DIR):
                for root, dirs, files in os.walk(PHOTOGRAPHY_ASSETS_DIR):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                            file_path = os.path.join(root, file)
                            arcname = os.path.join('images', os.path.relpath(file_path, PHOTOGRAPHY_ASSETS_DIR))
                            zipf.write(file_path, arcname)
                            image_count += 1
            
            # 2. Backup JSON data files
            json_files = [
                'portfolio-data.json',
                'portfolio-data-multicategory.json', 
                'featured-image.json',
                'categories-config.json',
                'background-image.json'
            ]
            
            data_count = 0
            for json_file in json_files:
                json_path = os.path.join(STATIC_ASSETS_DIR, json_file)
                if os.path.exists(json_path):
                    zipf.write(json_path, os.path.join('data', json_file))
                    data_count += 1
            
            # 3. Create backup manifest
            manifest = {
                'backup_date': datetime.now().isoformat(),
                'backup_type': 'local_storage_optimized',
                'contents': {
                    'images': f'{image_count} portfolio images from persistent storage',
                    'data': f'{data_count} JSON data files (portfolio, featured, categories, background)',
                    'storage_optimization': 'No server storage used - optimized for local download'
                },
                'version': '2.0',
                'created_by': 'Mind\'s Eye Photography Local Backup System',
                'storage_strategy': 'Local storage priority with weekly GitHub data sync'
            }
            
            # Add manifest to ZIP
            manifest_json = json.dumps(manifest, indent=2)
            zipf.writestr('backup_manifest.json', manifest_json)
        
        return temp_zip.name
        
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

@backup_bp.route('/admin/backup')
def backup_admin():
    """Local storage optimized backup interface"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    # Get message from URL parameters
    message = request.args.get('message')
    message_type = request.args.get('message_type', 'info')
    
    backup_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Local Storage Backup System</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #000; 
                color: #fff; 
                margin: 0; 
                padding: 20px; 
            }
            .header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 30px; 
                padding-bottom: 20px; 
                border-bottom: 2px solid #ff6b35; 
            }
            .header h1 { 
                color: #ff6b35; 
                margin: 0; 
            }
            .btn { 
                background: #ff6b35; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                border: none; 
                cursor: pointer; 
                font-size: 14px; 
                display: inline-block;
            }
            .btn:hover { 
                background: #e55a2b; 
            }
            .btn-large {
                padding: 20px 40px;
                font-size: 18px;
                margin: 20px 0;
            }
            .backup-section { 
                background: #1a1a1a; 
                padding: 30px; 
                border-radius: 10px; 
                margin-bottom: 30px; 
                border: 2px solid #ff6b35; 
            }
            .custom-name-section {
                background: #2a2a2a;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                color: #ff6b35;
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 16px;
            }
            .form-group input {
                width: 100%;
                padding: 12px;
                background: #1a1a1a;
                border: 1px solid #555;
                border-radius: 5px;
                color: #fff;
                font-size: 16px;
                box-sizing: border-box;
            }
            .form-group input:focus {
                outline: none;
                border-color: #ff6b35;
            }
            .filename-preview {
                background: #3a3a3a;
                padding: 15px;
                border-radius: 5px;
                margin-top: 10px;
                border-left: 4px solid #ff6b35;
            }
            .preview-label {
                color: #ff6b35;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 5px;
            }
            .preview-filename {
                color: #fff;
                font-size: 16px;
                font-family: monospace;
                word-break: break-all;
            }
            .backup-info {
                background: #2a2a2a;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .info-item {
                background: #3a3a3a;
                padding: 15px;
                border-radius: 5px;
            }
            .info-label {
                color: #ff6b35;
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 14px;
            }
            .info-value {
                color: #fff;
                font-size: 14px;
                line-height: 1.4;
            }
            .message { 
                padding: 15px; 
                border-radius: 5px; 
                margin-bottom: 20px; 
            }
            .message.success { 
                background: #d4edda; 
                color: #155724; 
                border: 1px solid #c3e6cb; 
            }
            .message.error { 
                background: #f8d7da; 
                color: #721c24; 
                border: 1px solid #f5c6cb; 
            }
            .optimization-info {
                background: #1a4d1a;
                color: #90ee90;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border: 1px solid #2d7a2d;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
                color: #ff6b35;
            }
            .suggestions {
                margin-top: 10px;
            }
            .suggestion-btn {
                background: #555;
                color: #fff;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                margin-right: 10px;
                margin-bottom: 5px;
                cursor: pointer;
                font-size: 12px;
            }
            .suggestion-btn:hover {
                background: #666;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Local Storage Backup System</h1>
            <a href="/admin/dashboard" class="btn">Back to Admin Dashboard</a>
        </div>

        {% if message %}
            <div class="message {{ message_type }}">{{ message }}</div>
        {% endif %}

        <div class="optimization-info">
            <strong>🎯 Storage Optimized:</strong> Backups download directly to your local computer. No server storage used - maximizing space for your portfolio images!
        </div>

        <!-- CREATE BACKUP SECTION -->
        <div class="backup-section">
            <h2 style="color: #ff6b35; margin-bottom: 20px; text-align: center;">💾 Create Custom Named Backup</h2>
            <p style="color: #ccc; margin-bottom: 30px; font-size: 16px; text-align: center;">
                Create a complete backup with your custom name and automatic timestamp.
            </p>
            
            <form method="POST" action="/admin/backup/create" id="backupForm">
                <div class="custom-name-section">
                    <div class="form-group">
                        <label for="custom_name">Custom Backup Name:</label>
                        <input type="text" 
                               id="custom_name" 
                               name="custom_name" 
                               placeholder="e.g., weekly_backup, before_changes, portfolio_update"
                               value="backup"
                               maxlength="50"
                               oninput="updatePreview()">
                        
                        <div class="suggestions">
                            <strong style="color: #ff6b35; font-size: 14px;">Quick suggestions:</strong><br>
                            <button type="button" class="suggestion-btn" onclick="setCustomName('weekly_backup')">weekly_backup</button>
                            <button type="button" class="suggestion-btn" onclick="setCustomName('before_changes')">before_changes</button>
                            <button type="button" class="suggestion-btn" onclick="setCustomName('portfolio_update')">portfolio_update</button>
                            <button type="button" class="suggestion-btn" onclick="setCustomName('emergency_backup')">emergency_backup</button>
                            <button type="button" class="suggestion-btn" onclick="setCustomName('monthly_archive')">monthly_archive</button>
                        </div>
                    </div>
                    
                    <div class="filename-preview">
                        <div class="preview-label">📁 Download Filename Preview:</div>
                        <div class="preview-filename" id="filenamePreview">backup_20250813_143022.zip</div>
                    </div>
                </div>
                
                <div class="loading" id="loadingIndicator">
                    <p>🔄 Creating backup... This may take a few moments...</p>
                </div>
                
                <div style="text-align: center;">
                    <button type="submit" class="btn btn-large" onclick="showLoading()">
                        💾 Create & Download Backup
                    </button>
                </div>
            </form>
        </div>

        <!-- BACKUP INFO SECTION -->
        <div class="backup-info">
            <h3 style="color: #ff6b35; margin-bottom: 20px;">📋 Backup Contents & Strategy</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">📸 Portfolio Images</div>
                    <div class="info-value">All uploaded images from persistent storage (/app/uploads)</div>
                </div>
                <div class="info-item">
                    <div class="info-label">📊 Portfolio Data</div>
                    <div class="info-value">Image metadata, titles, descriptions, categories, and EXIF data</div>
                </div>
                <div class="info-item">
                    <div class="info-label">⭐ Featured Image</div>
                    <div class="info-value">Current featured image data including story content</div>
                </div>
                <div class="info-item">
                    <div class="info-label">🏷️ Categories</div>
                    <div class="info-value">Category configuration and organization settings</div>
                </div>
                <div class="info-item">
                    <div class="info-label">🖼️ Background Image</div>
                    <div class="info-value">Homepage background image configuration</div>
                </div>
                <div class="info-item">
                    <div class="info-label">💾 Local Storage Priority</div>
                    <div class="info-value">Downloads directly to your computer - no server storage used</div>
                </div>
            </div>
        </div>

        <div class="optimization-info">
            <strong>💡 Backup Strategy:</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li><strong>Local Storage:</strong> Primary backup method - download to your computer</li>
                <li><strong>Custom Naming:</strong> Organize backups with meaningful names + timestamps</li>
                <li><strong>Weekly GitHub Sync:</strong> Automated data-only backups to GitHub (coming soon)</li>
                <li><strong>Storage Optimization:</strong> No backup files stored on server - max space for images</li>
                <li><strong>Multiple Locations:</strong> Store backups on different devices/cloud services</li>
            </ul>
        </div>

        <script>
            function updatePreview() {
                const customName = document.getElementById('custom_name').value || 'backup';
                const sanitizedName = customName.replace(/[<>:"/\\|?*]/g, '_').replace(/\\s+/g, '_').replace(/^_+|_+$/g, '');
                const now = new Date();
                const timestamp = now.getFullYear().toString() + 
                                (now.getMonth() + 1).toString().padStart(2, '0') + 
                                now.getDate().toString().padStart(2, '0') + '_' +
                                now.getHours().toString().padStart(2, '0') + 
                                now.getMinutes().toString().padStart(2, '0') + 
                                now.getSeconds().toString().padStart(2, '0');
                
                const filename = `${sanitizedName}_${timestamp}.zip`;
                document.getElementById('filenamePreview').textContent = filename;
            }
            
            function setCustomName(name) {
                document.getElementById('custom_name').value = name;
                updatePreview();
            }
            
            function showLoading() {
                document.getElementById('loadingIndicator').style.display = 'block';
                document.querySelector('.btn-large').disabled = true;
                document.querySelector('.btn-large').textContent = 'Creating Backup...';
            }
            
            // Update preview on page load
            updatePreview();
            
            // Update preview every second to show current timestamp
            setInterval(updatePreview, 1000);
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(backup_html, message=message, message_type=message_type)

@backup_bp.route('/admin/backup/create', methods=['POST'])
def create_backup():
    """Create and download custom named backup ZIP file"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        # Get custom name from form
        custom_name = request.form.get('custom_name', 'backup').strip()
        
        # Sanitize custom name
        sanitized_name = sanitize_filename(custom_name)
        
        # Create backup ZIP
        backup_file = create_backup_zip()
        
        if backup_file:
            # Generate filename with custom name and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{sanitized_name}_{timestamp}.zip'
            
            # Send file for download
            return send_file(
                backup_file,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
        else:
            return redirect(url_for('backup.backup_admin', 
                                  message='Error creating backup file', 
                                  message_type='error'))
    
    except Exception as e:
        print(f"Error in backup creation: {e}")
        return redirect(url_for('backup.backup_admin', 
                              message=f'Backup failed: {e}', 
                              message_type='error'))

@backup_bp.route('/admin/backup/status')
def backup_status():
    """Get backup system status"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        # Count images
        image_count = 0
        total_size = 0
        if os.path.exists(PHOTOGRAPHY_ASSETS_DIR):
            for root, dirs, files in os.walk(PHOTOGRAPHY_ASSETS_DIR):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            image_count += 1
                            total_size += os.path.getsize(file_path)
        
        # Check data files
        data_files = []
        json_files = [
            'portfolio-data.json',
            'portfolio-data-multicategory.json', 
            'featured-image.json',
            'categories-config.json',
            'background-image.json'
        ]
        
        for json_file in json_files:
            json_path = os.path.join(STATIC_ASSETS_DIR, json_file)
            if os.path.exists(json_path):
                stat = os.stat(json_path)
                data_files.append({
                    'name': json_file,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        status = {
            'image_count': image_count,
            'total_image_size_mb': round(total_size / (1024 * 1024), 2),
            'data_files': data_files,
            'backup_ready': True,
            'storage_optimization': 'Local storage priority - no server backup files',
            'last_check': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e), 'backup_ready': False})

