import os
import json
from flask import Blueprint, request, render_template_string, redirect, url_for, session, jsonify
from src.models.user import db

portfolio_mgmt_bp = Blueprint('portfolio_mgmt', __name__)

# REMOVED: All hardcoded file paths and JSON loading functions
# OLD CODE REMOVED:
# PORTFOLIO_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'portfolio-data-multicategory.json')
# CATEGORIES_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'categories-config.json')
# STATIC_ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets')

# REMOVED: load_categories_config() function - now uses database only
# REMOVED: load_portfolio_data() function - now uses database only
# REMOVED: save_portfolio_data() function - now uses database only

@portfolio_mgmt_bp.route('/admin/portfolio-management')
def portfolio_management():
    """Portfolio management admin interface - USES DATABASE ONLY"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    # Import here to avoid circular imports
    from src.models.user import PortfolioImage, Category
    
    # Get portfolio data from database (not JSON file)
    try:
        portfolio_images = PortfolioImage.query.all()
        portfolio_data = []
        for img in portfolio_images:
            portfolio_data.append({
                'id': img.id,
                'title': img.title,
                'description': img.description,
                'image': img.image_filename,
                'categories': [cat.name for cat in img.categories],
                'created_at': img.created_at.isoformat() if img.created_at else None
            })
    except Exception as e:
        print(f"Error loading portfolio data from database: {e}")
        portfolio_data = []
    
    # Get categories from database (not JSON file)
    try:
        categories = Category.query.all()
        categories_config = {
            'categories': [cat.name for cat in categories],
            'default_category': 'All',
            'category_order': [cat.name for cat in categories]
        }
        available_categories = [cat.name for cat in categories]
    except Exception as e:
        print(f"Error loading categories from database: {e}")
        # Fallback to default categories if database query fails
        categories_config = {
            'categories': ['Wildlife', 'Landscapes', 'Portraits', 'Events', 'Nature', 'Miscellaneous'],
            'default_category': 'All',
            'category_order': ['Wildlife', 'Landscapes', 'Portraits', 'Events', 'Nature', 'Miscellaneous']
        }
        available_categories = categories_config['categories']
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portfolio Management - Mind's Eye Photography</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #ff6b6b, #ee5a24);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .nav-buttons {
                padding: 20px;
                text-align: center;
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            .nav-buttons a {
                display: inline-block;
                margin: 0 10px;
                padding: 12px 24px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 25px;
                transition: all 0.3s ease;
            }
            .nav-buttons a:hover {
                background: #0056b3;
                transform: translateY(-2px);
            }
            .content {
                padding: 30px;
            }
            .portfolio-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .portfolio-item {
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
                background: #f9f9f9;
                transition: all 0.3s ease;
            }
            .portfolio-item:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }
            .portfolio-item img {
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .portfolio-item h3 {
                margin: 10px 0 5px 0;
                color: #333;
            }
            .portfolio-item p {
                color: #666;
                font-size: 0.9em;
                margin: 5px 0;
            }
            .categories {
                margin: 10px 0;
            }
            .category-tag {
                display: inline-block;
                background: #ff6b6b;
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                margin: 2px;
            }
            .delete-btn {
                background: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
                transition: background 0.3s ease;
            }
            .delete-btn:hover {
                background: #c82333;
            }
            .no-images {
                text-align: center;
                color: #666;
                font-style: italic;
                margin: 40px 0;
                font-size: 1.2em;
            }
            .stats {
                background: linear-gradient(135deg, #74b9ff, #0984e3);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .stats h2 {
                margin: 0 0 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖼️ Portfolio Management</h1>
                <p>Manage your photography portfolio - Database-driven (No more JSON files!)</p>
            </div>
            
            <div class="nav-buttons">
                <a href="/admin">🏠 Admin Dashboard</a>
                <a href="/admin/upload">📤 Upload Images</a>
                <a href="/admin/category-management">🏷️ Manage Categories</a>
                <a href="/admin/featured-image">⭐ Featured Image</a>
            </div>
            
            <div class="content">
                <div class="stats">
                    <h2>📊 Portfolio Statistics</h2>
                    <p><strong>Total Images:</strong> {{ portfolio_data|length }}</p>
                    <p><strong>Available Categories:</strong> {{ available_categories|length }}</p>
                    <p><strong>Data Source:</strong> Database (Persistent Storage) ✅</p>
                </div>
                
                {% if portfolio_data %}
                    <div class="portfolio-grid">
                        {% for item in portfolio_data %}
                        <div class="portfolio-item">
                            <img src="/photography-assets/{{ item.image }}" alt="{{ item.title }}" onerror="this.src='/assets/placeholder.jpg'">
                            <h3>{{ item.title }}</h3>
                            <p>{{ item.description }}</p>
                            <div class="categories">
                                {% for category in item.categories %}
                                    <span class="category-tag">{{ category }}</span>
                                {% endfor %}
                            </div>
                            <p><small>ID: {{ item.id }} | Created: {{ item.created_at or 'Unknown' }}</small></p>
                            <button class="delete-btn" onclick="deleteImage('{{ item.id }}')">🗑️ Delete</button>
                        </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="no-images">
                        <h2>📷 No portfolio images found</h2>
                        <p>Upload some images to get started!</p>
                        <a href="/admin/upload" style="color: #007bff;">Go to Upload Page</a>
                    </div>
                {% endif %}
            </div>
        </div>
        
        <script>
            function deleteImage(imageId) {
                if (confirm('Are you sure you want to delete this image?')) {
                    fetch('/admin/delete-portfolio-image', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image_id: imageId
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            location.reload();
                        } else {
                            alert('Error deleting image: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Error deleting image: ' + error);
                    });
                }
            }
        </script>
    </body>
    </html>
    ''', 
    portfolio_data=portfolio_data, 
    available_categories=available_categories,
    categories_config=categories_config
    )

@portfolio_mgmt_bp.route('/admin/delete-portfolio-image', methods=['POST'])
def delete_portfolio_image():
    """Delete portfolio image from database"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        from src.models.user import PortfolioImage
        
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({'success': False, 'error': 'No image ID provided'})
        
        # Find and delete the image from database
        image = PortfolioImage.query.get(image_id)
        if image:
            # Optionally delete the physical file
            try:
                image_path = os.path.join('/app/uploads', image.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting physical file: {e}")
            
            # Delete from database
            db.session.delete(image)
            db.session.commit()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Image not found'})
            
    except Exception as e:
        print(f"Error deleting portfolio image: {e}")
        return jsonify({'success': False, 'error': str(e)})

# API endpoint to get portfolio data (for frontend)
@portfolio_mgmt_bp.route('/api/portfolio-data')
def get_portfolio_data():
    """Get portfolio data from database for frontend"""
    try:
        from src.models.user import PortfolioImage
        
        images = PortfolioImage.query.all()
        portfolio_data = []
        
        for img in images:
            portfolio_data.append({
                'id': str(img.id),
                'title': img.title,
                'description': img.description,
                'image': img.image_filename,
                'categories': [cat.name for cat in img.categories],
                'created_at': img.created_at.isoformat() if img.created_at else None
            })
        
        return jsonify(portfolio_data)
        
    except Exception as e:
        print(f"Error getting portfolio data: {e}")
        return jsonify([])

# API endpoint to get categories (for frontend)
@portfolio_mgmt_bp.route('/api/categories')
def get_categories():
    """Get categories from database for frontend"""
    try:
        from src.models.user import Category
        
        categories = Category.query.all()
        category_list = [cat.name for cat in categories]
        
        return jsonify(category_list)
        
    except Exception as e:
        print(f"Error getting categories: {e}")
        # Return default categories if database fails
        return jsonify(['Wildlife', 'Landscapes', 'Portraits', 'Events', 'Nature', 'Miscellaneous'])

