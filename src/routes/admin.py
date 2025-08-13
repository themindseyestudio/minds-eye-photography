import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, render_template_string, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

# Use Railway persistent volume for photography assets
PHOTOGRAPHY_ASSETS_DIR = '/app/uploads'
PORTFOLIO_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'portfolio-data-multicategory.json')
CATEGORIES_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'categories-config.json')

def get_image_url(filename):
    """Get the URL for an image file"""
    return f"/photography-assets/{filename}"

def load_categories_config():
    """Load categories configuration"""
    try:
        if os.path.exists(CATEGORIES_CONFIG_FILE):
            with open(CATEGORIES_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading categories config: {e}")
    
    # Default configuration
    return {
        'categories': ['Wildlife', 'Landscapes', 'Portraits', 'Events', 'Nature', 'Miscellaneous'],
        'default_category': 'All',
        'category_order': ['Wildlife', 'Landscapes', 'Portraits', 'Events', 'Nature', 'Miscellaneous']
    }

def load_portfolio_data():
    """Load portfolio data from JSON file"""
    try:
        if os.path.exists(PORTFOLIO_DATA_FILE):
            with open(PORTFOLIO_DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading portfolio data: {e}")
    return []

def save_portfolio_data(data):
    """Save portfolio data to JSON file"""
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(PORTFOLIO_DATA_FILE), exist_ok=True)
        
        # Save to multicategory file (admin uses this)
        with open(PORTFOLIO_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved portfolio data to multicategory file: {PORTFOLIO_DATA_FILE}")
        
        # Also save to regular portfolio-data.json (frontend uses this)
        regular_portfolio_file = os.path.join(os.path.dirname(PORTFOLIO_DATA_FILE), 'portfolio-data.json')
        with open(regular_portfolio_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved portfolio data to regular file: {regular_portfolio_file}")
        
        return True
    except Exception as e:
        print(f"Error saving portfolio data: {e}")
        return False

@admin_bp.route('/admin')
def admin_login():
    """Admin login page"""
    return render_template_string(login_html)

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Updated authentication credentials
    if username == 'mindseye' and password == 'mindseye2025':
        session['admin_logged_in'] = True
        return redirect(url_for('admin.admin_dashboard'))
    else:
        return render_template_string(login_html, error="Invalid credentials")


@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    # Load data
    portfolio_data = load_portfolio_data()
    categories_config = load_categories_config()
    available_categories = categories_config['categories']
    
    # Get message from URL parameters
    message = request.args.get('message')
    message_type = request.args.get('message_type', 'info')
    
    return render_template_string(dashboard_html, 
                                portfolio_data=portfolio_data,
                                available_categories=available_categories,
                                message=message,
                                message_type=message_type)

@admin_bp.route('/admin/upload', methods=['POST'])
def admin_upload():
    """Handle image upload (single or multiple)"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        categories = request.form.getlist('categories')
        image_files = request.files.getlist('image')
        
        # Load data
        portfolio_data = load_portfolio_data()
        categories_config = load_categories_config()
        available_categories = categories_config['categories']
        
        # Validation
        if not title:
            return render_template_string(dashboard_html, 
                                        portfolio_data=portfolio_data,
                                        available_categories=available_categories,
                                        message="Please enter an image title", 
                                        message_type="error")
        
        if not description:
            return render_template_string(dashboard_html, 
                                        portfolio_data=portfolio_data,
                                        available_categories=available_categories,
                                        message="Please enter a description", 
                                        message_type="error")
        
        if not categories:
            return render_template_string(dashboard_html, 
                                        portfolio_data=portfolio_data,
                                        available_categories=available_categories,
                                        message="Please select at least one category", 
                                        message_type="error")
        
        if not image_files or not any(f.filename for f in image_files):
            return render_template_string(dashboard_html, 
                                        portfolio_data=portfolio_data,
                                        available_categories=available_categories,
                                        message="Please select at least one image file", 
                                        message_type="error")
        
        uploaded_count = 0
        
        # Process each image file
        for image_file in image_files:
            if image_file and image_file.filename:
                # Generate filename
                unique_id = str(uuid.uuid4())[:8]
                safe_title = secure_filename(title.lower().replace(' ', '-'))
                if uploaded_count > 0:
                    safe_title = f"{safe_title}-{uploaded_count + 1}"
                
                file_extension = os.path.splitext(image_file.filename)[1].lower()
                if not file_extension:
                    file_extension = '.jpg'
                filename = f"{safe_title}-{unique_id}{file_extension}"
                
                # Save file to Railway persistent volume
                os.makedirs(PHOTOGRAPHY_ASSETS_DIR, exist_ok=True)
                final_path = os.path.join(PHOTOGRAPHY_ASSETS_DIR, filename)
                image_file.save(final_path)
                
                # Create new portfolio entry with multi-category support
                new_entry = {
                    "id": safe_title + "-" + unique_id,
                    "title": f"{title} {uploaded_count + 1}" if len([f for f in image_files if f.filename]) > 1 else title,
                    "description": description,
                    "image": filename,
                    "categories": categories,  # Store as array
                    "created_at": datetime.now().isoformat()
                }
                
                # Add to portfolio
                portfolio_data.append(new_entry)
                uploaded_count += 1
        
        # Save portfolio data
        message = f"Uploaded: {uploaded_count}, Portfolio entries: {len(portfolio_data)}"
        save_result = save_portfolio_data(portfolio_data)
        
        # Redirect with success message
        message = f"{uploaded_count} image(s) uploaded successfully to persistent storage! Save result: {save_result}"
        return redirect(url_for('admin.admin_dashboard') + f'?message={message}&message_type=success')
        
    except Exception as e:
        print(f"Upload error: {e}")  # Debug logging
        portfolio_data = load_portfolio_data()
        categories_config = load_categories_config()
        available_categories = categories_config['categories']
        return render_template_string(dashboard_html, 
                                    portfolio_data=portfolio_data,
                                    available_categories=available_categories,
                                    message=f"Upload failed: {str(e)}", 
                                    message_type="error")

@admin_bp.route('/admin/delete', methods=['POST'])
def admin_delete():
    """Delete single image (legacy support)"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        image_id = request.form.get('image_id')
        portfolio_data = load_portfolio_data()
        
        # Find and remove the image
        for i, item in enumerate(portfolio_data):
            if item.get('id') == image_id:
                # Delete the physical file from persistent storage
                image_path = os.path.join(PHOTOGRAPHY_ASSETS_DIR, item.get('image', ''))
                if os.path.exists(image_path):
                    os.remove(image_path)
                
                # Remove from portfolio data
                portfolio_data.pop(i)
                break
        
        # Save updated data
        save_portfolio_data(portfolio_data)
        return redirect(url_for('admin.admin_dashboard') + '?message=Image deleted successfully&message_type=success')
        
    except Exception as e:
        print(f"Delete error: {e}")
        return redirect(url_for('admin.admin_dashboard') + '?message=Delete failed&message_type=error')

@admin_bp.route('/admin/bulk-delete', methods=['POST'])
def admin_bulk_delete():
    """AJAX bulk delete for multiple images"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Get selected image IDs from JSON request
        data = request.get_json()
        if not data or 'image_ids' not in data:
            return jsonify({'success': False, 'message': 'No image IDs provided'})
        
        image_ids = data['image_ids']
        if not image_ids:
            return jsonify({'success': False, 'message': 'No images selected'})
        
        portfolio_data = load_portfolio_data()
        deleted_count = 0
        
        # Delete images in reverse order to maintain indices
        for i in range(len(portfolio_data) - 1, -1, -1):
            item = portfolio_data[i]
            if item.get('id') in image_ids:
                # Delete the physical file from persistent storage
                image_path = os.path.join(PHOTOGRAPHY_ASSETS_DIR, item.get('image', ''))
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        print(f"Error deleting file {image_path}: {e}")
                
                # Remove from portfolio data
                portfolio_data.pop(i)
                deleted_count += 1
        
        # Save updated data
        if save_portfolio_data(portfolio_data):
            return jsonify({
                'success': True, 
                'message': f'Successfully deleted {deleted_count} image(s)',
                'deleted_count': deleted_count
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save changes'})
            
    except Exception as e:
        print(f"Bulk delete error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@admin_bp.route('/admin/logout')
def admin_logout():
    """Admin logout - redirect to homepage instead of login"""
    session.pop('admin_logged_in', None)
    return redirect('/')  # Redirect to homepage instead of login page

# HTML Templates
login_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #000; 
            color: #fff; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .login-container { 
            background: #222; 
            padding: 40px; 
            border-radius: 10px; 
            box-shadow: 0 0 20px rgba(255, 107, 53, 0.3); 
        }
        .login-container h1 { 
            text-align: center; 
            color: #ff6b35; 
            margin-bottom: 30px; 
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            color: #ccc; 
        }
        .form-group input { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #555; 
            border-radius: 4px; 
            background: #333; 
            color: #fff; 
            box-sizing: border-box; 
        }
        .form-group input:focus { 
            border-color: #ff6b35; 
            outline: none; 
        }
        button { 
            width: 100%; 
            padding: 12px; 
            background: #ff6b35; 
            color: #fff; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px; 
        }
        button:hover { 
            background: #e55a2b; 
        }
        .error { 
            color: #ff6b6b; 
            text-align: center; 
            margin-top: 10px; 
        }
        .credentials-info {
            background: #1a4d1a;
            color: #90ee90;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Mind's Eye Photography Admin</h1>
        <div class="credentials-info">
            <strong>Updated Login Credentials:</strong>  

            Username: mindseye  

            Password: mindseye2025
        </div>
        <form method="POST" action="/admin/login">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''
# Enhanced Dashboard HTML template with bulk delete functionality
dashboard_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
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
        .logout-btn { 
            background: #666; 
            color: #fff; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
        }
        .logout-btn:hover { 
            background: #555; 
        }
        
        /* Navigation Menu */
        .admin-nav {
            background: #333;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .admin-nav h2 {
            color: #ff6b35;
            margin: 0 0 15px 0;
            font-size: 20px;
        }
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .nav-item {
            background: #444;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            transition: background 0.3s;
        }
        .nav-item:hover {
            background: #555;
        }
        .nav-item a {
            color: #fff;
            text-decoration: none;
            display: block;
        }
        .nav-item h3 {
            color: #ff6b35;
            margin: 0 0 10px 0;
            font-size: 18px;
        }
        .nav-item p {
            margin: 0;
            color: #ccc;
            font-size: 14px;
        }
        
        .form-container { 
            background: #222; 
            padding: 30px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
        }
        .form-container h2 { 
            color: #ff6b35; 
            margin-top: 0; 
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            color: #ccc; 
            font-weight: bold; 
        }
        .form-group input, .form-group textarea { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #555; 
            border-radius: 4px; 
            background: #333; 
            color: #fff; 
            box-sizing: border-box; 
        }
        .form-group input:focus, .form-group textarea:focus { 
            border-color: #ff6b35; 
            outline: none; 
        }
        .checkbox-group { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 15px; 
            margin-top: 10px; 
        }
        .checkbox-label { 
            display: flex; 
            align-items: center; 
            color: #ccc; 
            cursor: pointer; 
        }
        .checkbox-label input { 
            width: auto; 
            margin-right: 8px; 
        }
        button { 
            background: #ff6b35; 
            color: #fff; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px; 
        }
        button:hover { 
            background: #e55a2b; 
        }
        
        /* Bulk Actions */
        .bulk-actions {
            background: #333;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            position: sticky;
            top: 20px;
            z-index: 100;
        }
        .bulk-actions h3 {
            margin: 0 0 15px 0;
            color: #ff6b35;
        }
        .bulk-controls {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .select-all-btn, .clear-all-btn, .bulk-delete-btn {
            background: #666;
            color: #fff;
            border: none;
            padding: 10px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .bulk-delete-btn {
            background: #dc3545;
        }
        .bulk-delete-btn:hover {
            background: #c82333;
        }
        .bulk-delete-btn:disabled {
            background: #666;
            cursor: not-allowed;
        }
        .selected-count {
            color: #ff6b35;
            font-weight: bold;
        }
        
        .portfolio-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-top: 20px; 
        }
        .portfolio-item { 
            background: #333; 
            border-radius: 10px; 
            overflow: hidden; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            position: relative;
        }
        .portfolio-item.selected {
            border: 3px solid #ff6b35;
            box-shadow: 0 0 15px rgba(255, 107, 53, 0.5);
        }
        .portfolio-item img { 
            width: 100%; 
            height: 200px; 
            object-fit: cover; 
        }
        .portfolio-item-content { 
            padding: 15px; 
        }
        .portfolio-item h3 { 
            margin: 0 0 10px 0; 
            color: #ff6b35; 
            font-size: 18px; 
        }
        .portfolio-item p { 
            margin: 5px 0; 
            color: #ccc; 
            font-size: 14px; 
        }
        .portfolio-item .categories { 
            margin: 10px 0; 
        }
        .category-tag { 
            display: inline-block; 
            background: #ff6b35; 
            color: #fff; 
            padding: 3px 8px; 
            border-radius: 12px; 
            font-size: 12px; 
            margin-right: 5px; 
            margin-bottom: 5px; 
        }
        .delete-btn { 
            background: #dc3545; 
            color: #fff; 
            padding: 8px 16px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 14px; 
            margin-top: 10px; 
        }
        .delete-btn:hover { 
            background: #c82333; 
        }
        .message { 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }
        .success-message { 
            background: #2d5a2d; 
            color: #90ee90; 
        }
        .error-message { 
            background: #5a2d2d; 
            color: #ff9090; 
        }
        .multi-upload-info {
            background: #1a4d1a;
            color: #90ee90;
            padding: 10px;
            border-radius: 4px;
            margin-top: 5px;
            font-size: 14px;
        }
        
        /* Selection checkbox */
        .selection-checkbox {
            position: absolute;
            top: 10px;
            left: 10px;
            width: 20px;
            height: 20px;
            z-index: 10;
        }
        
        /* Loading indicator */
        .loading {
            display: none;
            color: #ff6b35;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Mind's Eye Photography Admin Dashboard</h1>
        <a href="/admin/logout" class="logout-btn">Logout</a>
    </div>
    
    <!-- Admin Navigation Menu -->
    <div class="admin-nav">
        <h2>🛠️ Admin Tools</h2>
        <div class="nav-grid">
            <div class="nav-item">
                <a href="/admin/portfolio-management">
                    <h3>📸 Portfolio Management</h3>
                    <p>Edit existing images, update titles, descriptions, and categories</p>
                </a>
            </div>
            <div class="nav-item">
                <a href="/admin/background">
                    <h3>🖼️ Background Management</h3>
                    <p>Change the homepage background image</p>
                </a>
            </div>
            <div class="nav-item">
                <a href="/admin/category-management">
                    <h3>🏷️ Category Management</h3>
                    <p>Add, remove, and organize portfolio categories</p>
                </a>
            </div>
            <div class="nav-item">
                <a href="/admin/featured-image">
                    <h3>⭐ Featured Image</h3>
                    <p>Manage the weekly featured image section</p>
                </a>
            </div>
        </div>
    
    {% if message %}
    <div class="message {{ 'success-message' if message_type == 'success' else 'error-message' }}">
        {{ message }}
    </div>
    {% endif %}
    
    <div class="form-container">
        <h2>Upload New Images</h2>
        <form method="POST" action="/admin/upload" enctype="multipart/form-data">
            <div class="form-group">
                <label for="image">Image Files (JPG/PNG) - Select Multiple</label>
                <input type="file" id="image" name="image" accept="image/*" multiple required>
                <div class="multi-upload-info">
                    ✨ <strong>Multi-Upload:</strong> Hold Ctrl (Windows) or Cmd (Mac) to select multiple images at once!  

                    📁 <strong>Persistent Storage:</strong> Images are now saved to Railway's persistent volume and will not disappear!  

                    🔐 <strong>New Login:</strong> Username: mindseye | Password: mindseye2025
                </div>
                <small style="color: #999;">Please add watermark before upload: "© 2025 Mind's Eye Photography"</small>
            </div>
            
            <div class="form-group">
                <label for="title">Base Title</label>
                <input type="text" id="title" name="title" placeholder="e.g., Sunset Over Lake" required>
                <small style="color: #999;">For multiple images, numbers will be added automatically (e.g., "Sunset Over Lake 1", "Sunset Over Lake 2")</small>
            </div>
            
            <div class="form-group">
                <label for="description">Description</label>
                <textarea id="description" name="description" rows="3" placeholder="Brief description (applies to all uploaded images)" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="categories">Categories (Select multiple)</label>
                <div class="checkbox-group">
                    {% for category in available_categories %}
                    <label class="checkbox-label">
                        <input type="checkbox" name="categories" value="{{ category }}"> {{ category }}
                    </label>
                    {% endfor %}
                </div>
                <small style="color: #999;">All uploaded images will be assigned to the selected categories</small>
            </div>
            
            <button type="submit">Upload Image(s) to Persistent Storage</button>
        </form>
    </div>
    
    <!-- Bulk Actions -->
    <div class="

