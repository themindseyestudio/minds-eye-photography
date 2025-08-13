from flask import Blueprint, request, redirect, url_for, session, render_template_string, jsonify
import os
import json
from flask import Blueprint, request, render_template_string, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import uuid
from ..config import PHOTOGRAPHY_ASSETS_DIR, PORTFOLIO_DATA_FILE, LEGACY_ASSETS_DIR

background_bp = Blueprint('background', __name__)

# Configuration
BACKGROUND_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'background-config.json')

def get_current_background():
    """Get current background image filename"""
    try:
        if os.path.exists(BACKGROUND_CONFIG_FILE):
            with open(BACKGROUND_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('background_image', 'madison-skyline-landscape.jpg')
    except:
        pass
    return 'madison-skyline-landscape.jpg'

def set_background_image(filename):
    """Set the current background image"""
    config = {'background_image': filename}
    os.makedirs(os.path.dirname(BACKGROUND_CONFIG_FILE), exist_ok=True)
    with open(BACKGROUND_CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def load_portfolio_data():
    """Load portfolio data from JSON file"""
    try:
        if os.path.exists(PORTFOLIO_DATA_FILE):
            with open(PORTFOLIO_DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading portfolio data: {e}")
    return []

@background_bp.route('/admin/background')
def background_manager():
    """Enhanced background management page with portfolio selection"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    current_bg = get_current_background()
    portfolio_data = load_portfolio_data()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Background Manager - Mind's Eye Photography</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #1a1a1a; 
                color: #fff; 
            }
            .header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 30px; 
                padding-bottom: 20px; 
                border-bottom: 2px solid #333; 
            }
            .header h1 { color: #ff6b35; margin: 0; }
            .nav-links { display: flex; gap: 15px; }
            .nav-links a { 
                color: #fff; 
                text-decoration: none; 
                padding: 8px 16px; 
                background: #333; 
                border-radius: 4px; 
            }
            .nav-links a:hover { background: #555; }
            .current-bg { 
                margin-bottom: 30px; 
                padding: 20px; 
                background: #2a2a2a; 
                border-radius: 8px; 
            }
            .current-bg img { 
                max-width: 300px; 
                max-height: 200px; 
                border-radius: 4px; 
            }
            .section { 
                background: #2a2a2a; 
                padding: 20px; 
                border-radius: 8px; 
                margin-bottom: 20px; 
            }
            .form-group { margin-bottom: 15px; }
            .form-group label { 
                display: block; 
                margin-bottom: 5px; 
                color: #ff6b35; 
                font-weight: bold; 
            }
            .form-group input { 
                width: 100%; 
                padding: 10px; 
                border: 1px solid #555; 
                border-radius: 4px; 
                background: #333; 
                color: #fff; 
            }
            button { 
                background: #ff6b35; 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                font-size: 16px; 
                margin-right: 10px;
            }
            button:hover { background: #e55a2b; }
            .portfolio-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
                gap: 15px; 
                margin-top: 20px; 
            }
            .portfolio-item { 
                background: #333; 
                border-radius: 8px; 
                overflow: hidden; 
                position: relative;
            }
            .portfolio-item img { 
                width: 100%; 
                height: 150px; 
                object-fit: cover; 
            }
            .portfolio-item .info { 
                padding: 10px; 
            }
            .portfolio-item h4 { 
                margin: 0 0 5px 0; 
                color: #ff6b35; 
                font-size: 14px;
            }
            .portfolio-item .categories {
                font-size: 12px;
                color: #999;
                margin-bottom: 10px;
            }
            .set-bg-btn {
                background: #28a745;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 12px;
                width: 100%;
            }
            .set-bg-btn:hover { background: #218838; }
            .current-indicator {
                position: absolute;
                top: 5px;
                right: 5px;
                background: #ff6b35;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Background Manager</h1>
            <div class="nav-links">
                <a href="/admin/dashboard">← Back to Dashboard</a>
                <a href="/admin/logout">Logout</a>
            </div>
        </div>
        
        <div class="current-bg">
            <h2>Current Background</h2>
            <img src="/photography-assets/{{ current_bg }}" alt="Current Background">
            <p><strong>File:</strong> {{ current_bg }}</p>
        </div>
        
        <div class="section">
            <h2>Upload New Background</h2>
            <form method="POST" action="/admin/background/upload" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="background">Background Image (JPG/PNG)</label>
                    <input type="file" id="background" name="background" accept="image/*" required>
                    <p style="font-size: 12px; color: #999;">Recommended: 1920x1080 or larger landscape image</p>
                </div>
                <button type="submit">Upload Background</button>
            </form>
        </div>
        
        <div class="section">
            <h2>Select from Portfolio</h2>
            <p style="color: #999; margin-bottom: 20px;">Choose any image from your portfolio to use as the background</p>
            
            <div class="portfolio-grid">
                {% for item in portfolio_data %}
                <div class="portfolio-item">
                    {% if item.image == current_bg %}
                    <div class="current-indicator">CURRENT</div>
                    {% endif %}
                    <img src="/photography-assets/{{ item.image }}" alt="{{ item.title }}">
                    <div class="info">
                        <h4>{{ item.title }}</h4>
                        <div class="categories">{{ item.get('categories', [item.get('category', 'Unknown')]) | join(', ') }}</div>
                        <form method="POST" action="/admin/background/set-from-portfolio" style="margin: 0;">
                            <input type="hidden" name="image_filename" value="{{ item.image }}">
                            <button type="submit" class="set-bg-btn" 
                                    {% if item.image == current_bg %}disabled style="background: #666; cursor: not-allowed;"{% endif %}>
                                {% if item.image == current_bg %}Current Background{% else %}Set as Background{% endif %}
                            </button>
                        </form>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(html, current_bg=current_bg, portfolio_data=portfolio_data)

@background_bp.route('/admin/background/upload', methods=['POST'])
def upload_background():
    """Upload new background image"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        background_file = request.files.get('background')
        
        if not background_file or not background_file.filename:
            return redirect(url_for('background.background_manager'))
        
        # Generate filename
        unique_id = str(uuid.uuid4())[:8]
        filename = f"background-{unique_id}.jpg"
        
        # Save file
        file_path = os.path.join(STATIC_ASSETS_DIR, filename)
        background_file.save(file_path)
        
        # Update background config
        set_background_image(filename)
        
        return redirect(url_for('background.background_manager'))
        
    except Exception as e:
        return redirect(url_for('background.background_manager'))

@background_bp.route('/admin/background/set-from-portfolio', methods=['POST'])
def set_background_from_portfolio():
    """Set background image from portfolio selection"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        image_filename = request.form.get('image_filename')
        
        if not image_filename:
            return redirect(url_for('background.background_manager'))
        
        # Verify the image exists in the photography assets directory
        image_path = os.path.join(PHOTOGRAPHY_ASSETS_DIR, image_filename)
        if not os.path.exists(image_path):
            # Fallback to old location for backward compatibility
            old_image_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', image_filename)
            if not os.path.exists(old_image_path):
                return redirect(url_for('background.background_manager'))
        
        # Update background config
        set_background_image(image_filename)
        
        return redirect(url_for('background.background_manager'))
        
    except Exception as e:
        return redirect(url_for('background.background_manager'))

@background_bp.route('/api/background')
def get_background_api():
    """API endpoint to get current background"""
    return jsonify({'background_image': get_current_background()})

