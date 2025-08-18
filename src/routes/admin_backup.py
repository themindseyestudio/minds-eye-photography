from flask import Blueprint, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
from PIL import Image
from PIL.ExifTags import TAGS
import os
import uuid
from datetime import datetime
from src.models.user import db, PortfolioImage, Category, FeaturedImage, BackgroundImage, ContactSubmission

from flask import Blueprint, request, jsonify, render_template_string

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

@admin_bp.route('/admin/categories')
def category_management():
    """Category management interface"""
    categories = Category.query.order_by(Category.sort_order).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Category Management - Mind's Eye Photography</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #ff6b35; font-size: 2em; margin-bottom: 10px; }
            .form-section { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; color: #ccc; }
            .form-group input, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #555; background: #333; color: #fff; border-radius: 4px; }
            .btn { padding: 10px 20px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #e55a2b; }
            .categories-list { background: #2a2a2a; padding: 20px; border-radius: 10px; }
            .category-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #444; }
            .category-item:last-child { border-bottom: none; }
            .category-info h4 { color: #ff6b35; }
            .category-info p { color: #ccc; font-size: 0.9em; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #555; color: white; text-decoration: none; border-radius: 4px; }
            .back-btn:hover { background: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-btn">← Back to Admin</a>
            <div class="header">
                <h1>Category Management</h1>
                <p>Create and organize image categories</p>
            </div>
            
            <div class="form-section">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Add New Category</h3>
                <form onsubmit="addCategory(event)">
                    <div class="form-group">
                        <label>Category Name</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn">Add Category</button>
                </form>
            </div>
            
            <div class="categories-list">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Existing Categories</h3>
                {% for category in categories %}
                <div class="category-item">
                    <div class="category-info">
                        <h4>{{ category.name }}{% if category.is_default %} <span style="color: #28a745;">(Default)</span>{% endif %}</h4>
                        {% if category.description %}
                        <p>{{ category.description }}</p>
                        {% endif %}
                    </div>
                    <div style="display: flex; gap: 10px;">
                        {% if not category.is_default %}
                        <button class="btn" style="background: #28a745;" onclick="setDefault({{ category.id }}, '{{ category.name }}')">Set Default</button>
                        {% endif %}
                        <button class="btn" style="background: #dc3545;" onclick="deleteCategory({{ category.id }}, '{{ category.name }}')">Delete</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
        async function addCategory(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            
            try {
                const response = await fetch('/api/admin/categories', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    alert('Category added successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Failed to add category: ' + error.message);
                }
            } catch (error) {
                alert('Failed to add category: ' + error.message);
            }
        }
        
        async function setDefault(categoryId, categoryName) {
            if (!confirm(`Set "${categoryName}" as the default category for homepage display?`)) return;
            
            try {
                const response = await fetch(`/api/admin/categories/${categoryId}/default`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    alert('Default category updated successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function deleteCategory(categoryId, categoryName) {
            if (!confirm(`Delete category "${categoryName}"? This action cannot be undone.`)) return;
            
            try {
                const response = await fetch(`/api/admin/categories/${categoryId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    alert('Category deleted successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        </script>
    </body>
    </html>
    ''', categories=categories)

@admin_bp.route('/api/admin/categories', methods=['POST'])
def add_category():
    """Add new category"""
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            return jsonify({'error': 'Category name is required'}), 400
        
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': 'Category already exists'}), 400
        
        category = Category(
            name=name,
            description=description,
            sort_order=Category.query.count()
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category added successfully',
            'category': category.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/backgrounds')
def background_management():
    """Background image management"""
    images = PortfolioImage.query.filter_by(is_active=True).all()
    current_background = BackgroundImage.query.filter_by(is_active=True).first()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Background Management - Mind's Eye Photography</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #ff6b35; font-size: 2em; margin-bottom: 10px; }
            .current-bg { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .bg-preview { width: 100%; height: 200px; background-size: cover; background-position: center; border-radius: 8px; margin-bottom: 15px; }
            .images-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .image-card { background: #2a2a2a; border-radius: 10px; overflow: hidden; cursor: pointer; transition: transform 0.2s; }
            .image-card:hover { transform: translateY(-5px); }
            .image-card img { width: 100%; height: 180px; object-fit: cover; }
            .image-info { padding: 15px; }
            .image-info h4 { color: #ff6b35; margin-bottom: 5px; }
            .btn { padding: 10px 20px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #e55a2b; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #555; color: white; text-decoration: none; border-radius: 4px; }
            .back-btn:hover { background: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-btn">← Back to Admin</a>
            <div class="header">
                <h1>Background Image Management</h1>
                <p>Select any image from your portfolio to use as the website background</p>
            </div>
            
            {% if current_background %}
            <div class="current-bg">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Current Background Image</h3>
                <div class="bg-preview" style="background-image: url('/assets/{{ current_background.portfolio_image.filename }}');"></div>
                <h4>{{ current_background.portfolio_image.title or current_background.portfolio_image.original_filename }}</h4>
                <button class="btn" onclick="removeBackground()">Remove Background</button>
            </div>
            {% endif %}
            
            <div style="background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Select Background Image</h3>
                <p style="color: #ccc;">Click on any image below to set it as the website background</p>
            </div>
            
            <div class="images-grid">
                {% for image in images %}
                <div class="image-card" onclick="setBackground({{ image.id }}, '{{ image.title or image.original_filename }}')">
                    <img src="/assets/{{ image.filename }}" alt="{{ image.title or image.original_filename }}">
                    <div class="image-info">
                        <h4>{{ image.title or image.original_filename }}</h4>
                        {% if image.description %}
                        <p style="color: #ccc; font-size: 0.9em;">{{ image.description }}</p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
        async function setBackground(imageId, title) {
            if (!confirm(`Set "${title}" as the website background?`)) return;
            
            try {
                const response = await fetch('/api/admin/background', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_id: imageId })
                });
                
                if (response.ok) {
                    alert('Background image updated successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function removeBackground() {
            if (!confirm('Remove the current background image?')) return;
            
            try {
                const response = await fetch('/api/admin/background', {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    alert('Background removed successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        </script>
    </body>
    </html>
    ''', images=images, current_background=current_background)

@admin_bp.route('/admin/featured')
def featured_management():
    """Featured image management"""
    images = PortfolioImage.query.filter_by(is_active=True).all()
    current_featured = FeaturedImage.query.filter_by(is_active=True).first()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Featured Image Management - Mind's Eye Photography</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #ff6b35; font-size: 2em; margin-bottom: 10px; }
            .current-featured { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .featured-preview { width: 100%; height: 300px; background-size: cover; background-position: center; border-radius: 8px; margin-bottom: 15px; }
            .story-section { margin-top: 20px; }
            .story-section textarea { width: 100%; height: 100px; padding: 10px; border-radius: 5px; border: 1px solid #555; background: #333; color: #fff; }
            .images-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .image-card { background: #2a2a2a; border-radius: 10px; overflow: hidden; cursor: pointer; transition: transform 0.2s; }
            .image-card:hover { transform: translateY(-5px); }
            .image-card img { width: 100%; height: 180px; object-fit: cover; }
            .image-info { padding: 15px; }
            .image-info h4 { color: #ff6b35; margin-bottom: 5px; }
            .btn { padding: 10px 20px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #e55a2b; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #555; color: white; text-decoration: none; border-radius: 4px; }
            .back-btn:hover { background: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-btn">← Back to Admin</a>
            <div class="header">
                <h1>Featured Image Management</h1>
                <p>Select an image and add "The story behind this image" for the homepage</p>
            </div>
            
            {% if current_featured %}
            <div class="current-featured">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Current Featured Image</h3>
                <div class="featured-preview" style="background-image: url('/assets/{{ current_featured.portfolio_image.filename }}');"></div>
                <h4>{{ current_featured.portfolio_image.title or current_featured.portfolio_image.original_filename }}</h4>
                <div class="story-section">
                    <h4 style="color: #ff6b35; margin-bottom: 10px;">The Story Behind This Image</h4>
                    <textarea id="currentStory" placeholder="Enter the story behind this image...">{{ current_featured.story or '' }}</textarea>
                    <br>
                    <button class="btn" onclick="updateStory({{ current_featured.id }})">Update Story</button>
                </div>
            </div>
            {% endif %}
            
            <div style="background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: #ff6b35; margin-bottom: 15px;">Select Featured Image</h3>
                <p style="color: #ccc;">Click on any image below to set it as the featured image</p>
            </div>
            
            <div class="images-grid">
                {% for image in images %}
                <div class="image-card" onclick="setFeatured({{ image.id }}, '{{ image.title or image.original_filename }}')">
                    <img src="/assets/{{ image.filename }}" alt="{{ image.title or image.original_filename }}">
                    <div class="image-info">
                        <h4>{{ image.title or image.original_filename }}</h4>
                        {% if image.description %}
                        <p style="color: #ccc; font-size: 0.9em;">{{ image.description }}</p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
        async function setFeatured(imageId, title) {
            const story = prompt(`Enter the story behind "${title}":`);
            if (story === null) return;
            
            try {
                const response = await fetch('/api/admin/featured', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_id: imageId, story: story })
                });
                
                if (response.ok) {
                    alert('Featured image set successfully!');
                    location.reload();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function updateStory(featuredId) {
            const story = document.getElementById('currentStory').value;
            
            try {
                const response = await fetch(`/api/admin/featured/${featuredId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ story: story })
                });
                
                if (response.ok) {
                    alert('Story updated successfully!');
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        </script>
    </body>
    </html>
    ''', images=images, current_featured=current_featured)

@admin_bp.route('/admin/backup')
def backup_management():
    """Backup management"""
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
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #ff6b35; font-size: 2em; margin-bottom: 10px; }
            .backup-section { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .backup-section h3 { color: #ff6b35; margin-bottom: 15px; }
            .btn { padding: 12px 24px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #e55a2b; }
            .btn.secondary { background: #555; }
            .btn.secondary:hover { background: #666; }
            .btn.danger { background: #dc3545; }
            .btn.danger:hover { background: #c82333; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #555; color: white; text-decoration: none; border-radius: 4px; }
            .back-btn:hover { background: #666; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .status.success { background: #28a745; }
            .status.error { background: #dc3545; }
            ul { margin-left: 20px; }
            li { margin: 5px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-btn">← Back to Admin</a>
            <div class="header">
                <h1>Backup Management</h1>
                <p>Manage your website backups and data</p>
            </div>
            
            <div class="backup-section">
                <h3>Immediate Local Backup</h3>
                <p>Create an immediate backup of all your data and images to local storage</p>
                <button class="btn" onclick="createBackup()">Create Backup Now</button>
                
                <h4 style="color: #ff6b35; margin-top: 20px;">Backup includes:</h4>
                <ul>
                    <li>All portfolio images and metadata</li>
                    <li>Categories and settings</li>
                    <li>Featured image configurations</li>
                    <li>Contact form submissions</li>
                    <li>Background image settings</li>
                </ul>
            </div>
            
            <div class="backup-section">
                <h3>GitHub Auto-Backup</h3>
                <p>Automatic set-and-forget backups to GitHub repository</p>
                <button class="btn secondary" onclick="setupGitBackup()">Setup Auto-Backup</button>
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
        async function createBackup() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status">Creating backup...</div>';
            
            try {
                const response = await fetch('/api/admin/backup', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    statusDiv.innerHTML = `<div class="status success">Backup created successfully: ${result.filename}</div>`;
                } else {
                    const error = await response.json();
                    statusDiv.innerHTML = `<div class="status error">Backup failed: ${error.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">Backup failed: ${error.message}</div>`;
            }
        }
        
        function setupGitBackup() {
            alert('GitHub auto-backup setup will be implemented in the next version.');
        }
        
        function checkBackupStatus() {
            alert('Backup status check will be implemented in the next version.');
        }
        
        function emergencyRestore() {
            if (confirm('Are you sure you want to perform an emergency restore? This will overwrite all current data.')) {
                alert('Emergency restore will be implemented in the next version.');
            }
        }
        </script>
    </body>
    </html>
    ''')

# API Routes for admin functionality
@admin_bp.route('/api/admin/featured', methods=['POST'])
def set_featured_image():
    """Set featured image with story"""
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        story = data.get('story', '')
        
        if not image_id:
            return jsonify({'error': 'Image ID required'}), 400
        
        image = PortfolioImage.query.get_or_404(image_id)
        
        # Deactivate current featured image
        current_featured = FeaturedImage.query.filter_by(is_active=True).first()
        if current_featured:
            current_featured.is_active = False
        
        # Create new featured image
        featured = FeaturedImage(
            portfolio_image_id=image_id,
            story=story,
            is_active=True
        )
        
        db.session.add(featured)
        db.session.commit()
        
        return jsonify({'message': 'Featured image set successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/featured/<int:featured_id>', methods=['PUT'])
def update_featured_story(featured_id):
    """Update featured image story"""
    try:
        featured = FeaturedImage.query.get_or_404(featured_id)
        data = request.get_json()
        
        featured.story = data.get('story', featured.story)
        db.session.commit()
        
        return jsonify({'message': 'Story updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/background', methods=['POST'])
def set_background_image():
    """Set background image"""
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({'error': 'Image ID required'}), 400
        
        image = PortfolioImage.query.get_or_404(image_id)
        
        # Deactivate current background
        current_bg = BackgroundImage.query.filter_by(is_active=True).first()
        if current_bg:
            current_bg.is_active = False
        
        # Create new background
        background = BackgroundImage(
            portfolio_image_id=image_id,
            is_active=True
        )
        
        db.session.add(background)
        db.session.commit()
        
        return jsonify({'message': 'Background image set successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/background', methods=['DELETE'])
def remove_background_image():
    """Remove background image"""
    try:
        current_bg = BackgroundImage.query.filter_by(is_active=True).first()
        if current_bg:
            current_bg.is_active = False
            db.session.commit()
        
        return jsonify({'message': 'Background removed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/backup', methods=['POST'])
def create_backup():
    """Create immediate backup"""
    try:
        import json
        import shutil
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.json"
        backup_path = os.path.join('backups', backup_filename)
        
        # Create backups directory
        os.makedirs('backups', exist_ok=True)
        
        # Collect all data
        backup_data = {
            'timestamp': timestamp,
            'portfolio_images': [img.to_dict() for img in PortfolioImage.query.all()],
            'categories': [cat.to_dict() for cat in Category.query.all()],
            'featured_images': [feat.to_dict() for feat in FeaturedImage.query.all()],
            'background_images': [bg.to_dict() for bg in BackgroundImage.query.all()],
            'contact_submissions': [contact.to_dict() for contact in ContactSubmission.query.all()]
        }
        
        # Save backup
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        # Also copy images directory
        if os.path.exists(UPLOAD_FOLDER):
            backup_images_path = os.path.join('backups', f"images_{timestamp}")
            shutil.copytree(UPLOAD_FOLDER, backup_images_path)
        
        return jsonify({
            'message': 'Backup created successfully',
            'filename': backup_filename,
            'path': backup_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/categories/<int:category_id>/default', methods=['POST'])
def set_default_category(category_id):
    """Set category as default"""
    try:
        # Remove current default
        current_default = Category.query.filter_by(is_default=True).first()
        if current_default:
            current_default.is_default = False
        
        # Set new default
        category = Category.query.get_or_404(category_id)
        category.is_default = True
        
        db.session.commit()
        
        return jsonify({'message': 'Default category updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete category"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # Don't allow deleting default category
        if category.is_default:
            return jsonify({'error': 'Cannot delete default category'}), 400
        
        # Remove category associations from images
        for image in category.portfolio_images:
            image.categories.remove(category)
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'message': 'Category deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

