import os
import json
from flask import Blueprint, request, render_template_string, redirect, url_for, session, jsonify
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from ..config import PHOTOGRAPHY_ASSETS_DIR, PORTFOLIO_DATA_FILE

featured_bp = Blueprint('featured', __name__)

# File paths
FEATURED_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'featured-image.json')
STATIC_ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets')

def load_featured_data():
    """Load featured image data from JSON file"""
    try:
        if os.path.exists(FEATURED_DATA_FILE):
            with open(FEATURED_DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading featured data: {e}")
    return None

def save_featured_data(data):
    """Save featured image data to JSON file"""
    try:
        os.makedirs(os.path.dirname(FEATURED_DATA_FILE), exist_ok=True)
        with open(FEATURED_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving featured data: {e}")
        return False

def extract_exif_data(image_path):
    """Extract EXIF data from image"""
    try:
        print(f"Extracting EXIF from: {image_path}")
        with Image.open(image_path) as img:
            exif_dict = img._getexif()
            
            if exif_dict is not None:
                exif = {TAGS[key]: value for key, value in exif_dict.items() if key in TAGS}
                print(f"Found EXIF tags: {list(exif.keys())}")
                
                # Format camera make/model
                make = exif.get('Make', '').strip()
                model = exif.get('Model', '').strip()
                camera = f"{make} {model}".strip() if make or model else 'Unknown'
                
                # Format aperture
                aperture = exif.get('FNumber', 'Unknown')
                if aperture != 'Unknown' and isinstance(aperture, (int, float)):
                    aperture = f"{aperture:.1f}"
                elif aperture != 'Unknown' and hasattr(aperture, 'real'):
                    aperture = f"{float(aperture):.1f}"
                
                # Format shutter speed
                shutter = exif.get('ExposureTime', 'Unknown')
                if shutter != 'Unknown' and isinstance(shutter, (int, float)):
                    if shutter >= 1:
                        shutter = f"{shutter:.1f}"
                    else:
                        shutter = f"1/{int(1/shutter)}"
                elif shutter != 'Unknown' and hasattr(shutter, 'real'):
                    shutter_val = float(shutter)
                    if shutter_val >= 1:
                        shutter = f"{shutter_val:.1f}"
                    else:
                        shutter = f"1/{int(1/shutter_val)}"
                
                # Extract specific EXIF data
                camera_info = {
                    'camera': camera,
                    'lens': exif.get('LensModel', exif.get('Lens', 'Unknown')),
                    'aperture': str(aperture),
                    'shutter_speed': str(shutter),
                    'iso': str(exif.get('ISOSpeedRatings', exif.get('ISO', 'Unknown'))),
                    'date_taken': exif.get('DateTime', exif.get('DateTimeOriginal', 'Unknown')),
                    'gps_info': 'Unknown'  # Simplified for now
                }
                
                print(f"Extracted EXIF: {camera_info}")
                return camera_info
            else:
                print("No EXIF data found in image")
                return {}
    except Exception as e:
        print(f"Error extracting EXIF data: {e}")
        return {}

@featured_bp.route('/api/featured')
def get_featured_image():
    """API endpoint to get current featured image data"""
    featured_data = load_featured_data()
    return jsonify(featured_data)

@featured_bp.route('/admin/featured')
def featured_admin():
    """Featured image admin interface"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        # Load portfolio and featured data
        from .admin import load_portfolio_data
        portfolio_data = load_portfolio_data()
        featured_data = load_featured_data()
        
        admin_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Featured Image Management</title>
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
                }
                .btn:hover { 
                    background: #e55a2b; 
                }
                .current-featured { 
                    background: #1a1a1a; 
                    padding: 20px; 
                    border-radius: 10px; 
                    margin-bottom: 30px; 
                    border: 2px solid #ff6b35; 
                }
                .portfolio-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
                    gap: 20px; 
                    margin-top: 20px; 
                }
                .portfolio-item { 
                    background: #1a1a1a; 
                    border-radius: 10px; 
                    overflow: hidden; 
                    transition: transform 0.3s; 
                    border: 2px solid transparent; 
                }
                .portfolio-item:hover { 
                    transform: scale(1.05); 
                    border-color: #ff6b35; 
                }
                .portfolio-item img { 
                    width: 100%; 
                    height: 150px; 
                    object-fit: cover; 
                }
                .portfolio-item-info { 
                    padding: 15px; 
                }
                .portfolio-item h3 { 
                    margin: 0 0 10px 0; 
                    color: #ff6b35; 
                    font-size: 16px; 
                }
                .portfolio-item p { 
                    margin: 0 0 15px 0; 
                    color: #ccc; 
                    font-size: 14px; 
                    line-height: 1.4; 
                }
                .categories { 
                    margin-bottom: 15px; 
                }
                .category-tag { 
                    background: #ff6b35; 
                    color: white; 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 12px; 
                    margin-right: 5px; 
                    margin-bottom: 5px; 
                    display: inline-block; 
                }
                .set-featured-btn { 
                    background: #28a745; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 12px; 
                    width: 100%; 
                }
                .set-featured-btn:hover { 
                    background: #218838; 
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
                .exif-info { 
                    background: #2a2a2a; 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin-top: 15px; 
                }
                .exif-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 10px; 
                    margin-top: 10px; 
                }
                .exif-item { 
                    background: #3a3a3a; 
                    padding: 10px; 
                    border-radius: 5px; 
                }
                .exif-label { 
                    color: #ff6b35; 
                    font-weight: bold; 
                    font-size: 12px; 
                    text-transform: uppercase; 
                }
                .exif-value { 
                    color: #fff; 
                    font-size: 14px; 
                    margin-top: 5px; 
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Featured Image Management</h1>
                <a href="/admin" class="btn">Back to Admin Dashboard</a>
            </div>

            {% if message %}
                <div class="message {{ message_type }}">{{ message }}</div>
            {% endif %}

            {% if featured_data %}
                <div class="current-featured">
                    <h2 style="color: #ff6b35; margin-bottom: 15px;">Current Featured Image</h2>
                    <div style="display: flex; gap: 20px; align-items: flex-start;">
                        <img src="/photography-assets/{{ featured_data.image }}" 
                             alt="{{ featured_data.title }}" 
                             style="width: 300px; height: 200px; object-fit: cover; border-radius: 8px;">
                        <div style="flex: 1;">
                            <h3 style="color: #fff; margin: 0 0 10px 0;">{{ featured_data.title }}</h3>
                            <p style="color: #ccc; margin: 0 0 15px 0;">{{ featured_data.description }}</p>
                            <div class="categories">
                                {% for category in featured_data.categories %}
                                    <span class="category-tag">{{ category }}</span>
                                {% endfor %}
                            </div>
                            {% if featured_data.exif_data %}
                                <div class="exif-info">
                                    <h4 style="color: #ff6b35; margin: 0 0 10px 0;">EXIF Data</h4>
                                    <div class="exif-grid">
                                        {% if featured_data.exif_data.camera %}
                                            <div class="exif-item">
                                                <div class="exif-label">Camera</div>
                                                <div class="exif-value">{{ featured_data.exif_data.camera }}</div>
                                            </div>
                                        {% endif %}
                                        {% if featured_data.exif_data.lens %}
                                            <div class="exif-item">
                                                <div class="exif-label">Lens</div>
                                                <div class="exif-value">{{ featured_data.exif_data.lens }}</div>
                                            </div>
                                        {% endif %}
                                        {% if featured_data.exif_data.aperture %}
                                            <div class="exif-item">
                                                <div class="exif-label">Aperture</div>
                                                <div class="exif-value">f/{{ featured_data.exif_data.aperture }}</div>
                                            </div>
                                        {% endif %}
                                        {% if featured_data.exif_data.shutter_speed %}
                                            <div class="exif-item">
                                                <div class="exif-label">Shutter Speed</div>
                                                <div class="exif-value">{{ featured_data.exif_data.shutter_speed }}s</div>
                                            </div>
                                        {% endif %}
                                        {% if featured_data.exif_data.iso %}
                                            <div class="exif-item">
                                                <div class="exif-label">ISO</div>
                                                <div class="exif-value">{{ featured_data.exif_data.iso }}</div>
                                            </div>
                                        {% endif %}
                                        {% if featured_data.exif_data.date_taken %}
                                            <div class="exif-item">
                                                <div class="exif-label">Date Taken</div>
                                                <div class="exif-value">{{ featured_data.exif_data.date_taken }}</div>
                                            </div>
                                        {% endif %}
                                        {% if featured_data.exif_data.gps_info %}
                                            <div class="exif-item">
                                                <div class="exif-label">Location</div>
                                                <div class="exif-value">{{ featured_data.exif_data.gps_info }}</div>
                                            </div>
                                        {% endif %}
                                    </div>
                                </div>
                            {% endif %}
                            <p style="color: #888; font-size: 12px; margin-top: 15px;">
                                Set on: {{ featured_data.set_date }}
                            </p>
                        </div>
                    </div>
                </div>
            {% else %}
                <div class="current-featured">
                    <h2 style="color: #ff6b35; margin-bottom: 15px;">No Featured Image Set</h2>
                    <p style="color: #ccc;">Select an image from the portfolio below to set as featured.</p>
                </div>
            {% endif %}

            <h2 style="color: #ff6b35; margin-bottom: 20px;">Portfolio Images</h2>
            <div class="portfolio-grid">
                {% for image in portfolio_data %}
                    <div class="portfolio-item">
                        <img src="/photography-assets/{{ image.image }}" alt="{{ image.title }}">
                        <div class="portfolio-item-info">
                            <h3>{{ image.title }}</h3>
                            <p>{{ image.description }}</p>
                            <div class="categories">
                                {% for category in image.categories %}
                                    <span class="category-tag">{{ category }}</span>
                                {% endfor %}
                            </div>
                            <form method="POST" action="/admin/featured/set" style="margin: 0;">
                                <input type="hidden" name="image_id" value="{{ image.id }}">
                                <button type="submit" class="set-featured-btn">Set as Featured</button>
                            </form>
                        </div>
                    </div>
                {% endfor %}
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(admin_html, 
                                    portfolio_data=portfolio_data,
                                    featured_data=featured_data,
                                    message=request.args.get('message'),
                                    message_type=request.args.get('message_type', 'success'))
        
    except Exception as e:
        return f"Error loading featured admin: {str(e)}"

@featured_bp.route('/admin/featured/set', methods=['POST'])
def set_featured_image():
    """Set an image as featured"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        image_id = request.form.get('image_id')
        
        # Load portfolio data to find the selected image
        from .admin import load_portfolio_data
        portfolio_data = load_portfolio_data()
        
        selected_image = None
        for image in portfolio_data:
            if image['id'] == image_id:
                selected_image = image
                break
        
        if not selected_image:
            return redirect(url_for('featured.featured_admin', message='Image not found', message_type='error'))
        
        # Create featured image data with EXIF extraction
        featured_data = {
            'id': selected_image['id'],
            'title': selected_image['title'],
            'description': selected_image['description'],
            'image': selected_image['image'],
            'categories': selected_image['categories'],
            'exif_data': extract_exif_data(os.path.join(PHOTOGRAPHY_ASSETS_DIR, selected_image['image'])),
            'set_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save featured data
        if save_featured_data(featured_data):
            return redirect(url_for('featured.featured_admin', message='Featured image set successfully!', message_type='success'))
        else:
            return redirect(url_for('featured.featured_admin', message='Error saving featured image', message_type='error'))
            
    except Exception as e:
        return redirect(url_for('featured.featured_admin', message=f'Error: {str(e)}', message_type='error'))

