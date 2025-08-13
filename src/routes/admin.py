import os
import json
import uuid
import os
from datetime import datetime
from flask import Blueprint, request, render_template_string, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from ..config import PHOTOGRAPHY_ASSETS_DIR, PORTFOLIO_DATA_FILE, CATEGORIES_CONFIG_FILE, get_image_url

admin_bp = Blueprint('admin', __name__)

# Admin password
ADMIN_PASSWORD = "mindseye2025"

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
    """Save portfolio data to both JSON files for frontend compatibility"""
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(PORTFOLIO_DATA_FILE), exist_ok=True)
        
        # Save to multicategory file (admin uses this)
        with open(PORTFOLIO_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Admin saved portfolio data to multicategory file: {PORTFOLIO_DATA_FILE}")
        
        # Also save to regular portfolio-data.json (frontend uses this)
        regular_portfolio_file = os.path.join(os.path.dirname(PORTFOLIO_DATA_FILE), 'portfolio-data.json')
        with open(regular_portfolio_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Admin saved portfolio data to regular file: {regular_portfolio_file}")
        
        return True
    except Exception as e:
        print(f"❌ Admin error saving portfolio data: {e}")
        return False

@admin_bp.route('/admin')
def admin_login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_dashboard'))
    
    login_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mind's Eye Photography - Admin</title>
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
                padding: 30px; 
                border-radius: 10px; 
                text-align: center; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
            }
            h1 { color: #ff6b35; margin-bottom: 10px; }
            h2 { margin-bottom: 20px; }
            input { 
                width: 200px; 
                padding: 10px; 
                margin: 10px 0; 
                border: 1px solid #555; 
                border-radius: 5px; 
                background: #333; 
                color: #fff; 
            }
            button { 
                width: 220px; 
                padding: 10px; 
                background: #ff6b35; 
                color: #fff; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px;
            }
            .error { color: #ff4444; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Mind's Eye Photography</h1>
            <h2>Admin Login</h2>
            <form method="POST" action="/admin/login">
                <div>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
                <div>
                    <button type="submit">Login</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    '''
    
    return login_html

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login"""
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin.admin_dashboard'))
    else:
        return redirect(url_for('admin.admin_login'))

@admin_bp.route('/admin/logout')
def admin_logout():
    """Handle admin logout"""
    session.pop('admin_logged_in', None)
    return redirect('/')  # Redirect to main site

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    # Load portfolio data and categories
    portfolio_data = load_portfolio_data()
    categories_config = load_categories_config()
    available_categories = categories_config['categories']
    
    return render_template_string(dashboard_html, 
                                portfolio_data=portfolio_data,
                                available_categories=available_categories,
                                message=request.args.get('message'),
                                message_type=request.args.get('message_type', 'success'))

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
                
                # Save file to separate photography assets directory
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
        save_portfolio_data(portfolio_data)
        
        # Redirect with success message
        message = f"{uploaded_count} image(s) uploaded successfully!" if uploaded_count > 1 else "Image uploaded successfully!"
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
    """Delete image"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        image_id = request.form.get('image_id')
        portfolio_data = load_portfolio_data()
        
        # Find and remove the image
        for i, item in enumerate(portfolio_data):
            if item.get('id') == image_id:
                # Delete the image file from photography assets directory
                image_path = os.path.join(PHOTOGRAPHY_ASSETS_DIR, item.get('image', ''))
                if os.path.exists(image_path):
                    os.remove(image_path)
                
                # Remove from portfolio data
                portfolio_data.pop(i)
                save_portfolio_data(portfolio_data)
                break
        
        return redirect(url_for('admin.admin_dashboard') + '?message=Image deleted successfully!&message_type=success')
        
    except Exception as e:
        print(f"Delete error: {e}")
        return redirect(url_for('admin.admin_dashboard') + '?message=Delete failed&message_type=error')

# Dashboard HTML template with dynamic categories and multi-image upload
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
            border-bottom: 2px solid #333; 
        }
        h1 { color: #ff6b35; margin: 0; }
        .logout-btn { 
            background: #ff4444; 
            color: #fff; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
        }
        .form-container { 
            background: #222; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
        }
        .form-group { margin-bottom: 15px; }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            color: #ff6b35; 
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
        .checkbox-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 5px;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #fff;
            cursor: pointer;
            padding: 8px;
            background: #333;
            border-radius: 4px;
            border: 1px solid #555;
        }
        .checkbox-label:hover {
            background: #444;
        }
        .checkbox-label input[type="checkbox"] {
            width: auto;
            margin: 0;
        }
        button { 
            background: #ff6b35; 
            color: #fff; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px; 
        }
        .portfolio-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-top: 20px; 
        }
        .portfolio-item { 
            background: #222; 
            border-radius: 10px; 
            overflow: hidden; 
        }
        .portfolio-item img { 
            width: 100%; 
            height: 200px; 
            object-fit: cover; 
        }
        .portfolio-info { padding: 15px; }
        .portfolio-info h3 { 
            margin: 0 0 10px 0; 
            color: #ff6b35; 
        }
        .delete-btn { 
            background: #ff4444; 
            color: #fff; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 4px; 
            cursor: pointer; 
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
        .admin-links {
            margin-bottom: 20px;
        }
        .admin-links a {
            display: inline-block;
            background: #444;
            color: #fff;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 5px;
            margin-right: 10px;
        }
        .multi-upload-info {
            background: #1a4d1a;
            color: #90ee90;
            padding: 10px;
            border-radius: 4px;
            margin-top: 5px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Mind's Eye Photography - Admin</h1>
        <a href="/admin/logout" class="logout-btn">Logout</a>
    </div>
    
    <div class="admin-links">
        <a href="/admin/background">🖼️ Background Management</a>
        <a href="/admin/featured">⭐ Featured Image</a>
        <a href="/admin/portfolio-management">📁 Portfolio Management</a>
        <a href="/admin/category-management">🏷️ Category Management</a>
    </div>
    
    {% if message %}
    <div class="message {{ message_type }}-message">
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
            
            <button type="submit">Upload Image(s)</button>
        </form>
    </div>
    
    <div>
        <h2>Current Portfolio ({{ portfolio_data|length }} images)</h2>
        <div class="portfolio-grid">
            {% for item in portfolio_data %}
            <div class="portfolio-item">
                <img src="/photography-assets/{{ item.image }}" alt="{{ item.title }}">
                <div class="portfolio-info">
                    <h3>{{ item.title }}</h3>
                    <p>{{ item.description }}</p>
                    <p><strong>Categories:</strong> {{ item.get('categories', [item.get('category', 'Unknown')]) | join(', ') }}</p>
                    <form method="POST" action="/admin/delete" style="margin-top: 10px;">
                        <input type="hidden" name="image_id" value="{{ item.id }}">
                        <button type="submit" class="delete-btn" onclick="return confirm('Delete this image?')">Delete</button>
                    </form>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

