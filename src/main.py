import os
import sys
import json

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory, request, jsonify
from models.user import db
from routes.user import user_bp
from routes.contact import contact_bp
from routes.admin import admin_bp
from routes.background import background_bp
from routes.featured_image import featured_bp
from routes.portfolio_management import portfolio_mgmt_bp
from routes.category_management import category_mgmt_bp
from routes.backup import backup_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#F0SGvasgf$5SWG'

# Configure photography assets directory to use Railway persistent volume
PHOTOGRAPHY_ASSETS_DIR = '/app/uploads'

# Ensure photography assets directory exists
os.makedirs(PHOTOGRAPHY_ASSETS_DIR, exist_ok=True)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(contact_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(background_bp)
app.register_blueprint(featured_bp)
app.register_blueprint(portfolio_mgmt_bp)
app.register_blueprint(category_mgmt_bp)
app.register_blueprint(backup_bp)

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(__file__), "database", "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/photography-assets/<path:filename>')
def serve_photography_assets(filename):
    """Serve images from the Railway persistent volume"""
    try:
        return send_from_directory(PHOTOGRAPHY_ASSETS_DIR, filename)
    except FileNotFoundError:
        # Fallback to old location for backward compatibility during migration
        old_assets_dir = os.path.join(app.static_folder, 'assets')
        if os.path.exists(os.path.join(old_assets_dir, filename)):
            return send_from_directory(old_assets_dir, filename)
        return "Image not found", 404

# REMOVED: load_featured_data() function - now uses database only

@app.route('/featured-image')
def featured_image_page():
    """Featured image page with Open Graph meta tags - USES DATABASE ONLY"""
    # Import here to avoid circular imports
    from src.models.user import FeaturedImage
    
    # Default values
    og_title = "Mind's Eye Photography - Where Moments Meet Imagination"
    og_description = "Professional wildlife and landscape photography by Rick Corey. Where moments meet imagination."
    og_image = "https://www.themindseyestudio.com/assets/logo.png"  # Default fallback
    og_url = "https://www.themindseyestudio.com/featured-image"
    
    # Get featured image from database (not JSON file)
    try:
        featured_image = FeaturedImage.query.filter_by(is_active=True).first()
        if featured_image:
            og_title = f"{featured_image.title} - Mind's Eye Photography"
            og_description = featured_image.description or og_description
            if featured_image.image_filename:
                og_image = f"https://www.themindseyestudio.com/photography-assets/{featured_image.image_filename}"
    except Exception as e:
        print(f"Error loading featured image from database: {e}")
        # Use defaults if database query fails
    
    # Read the base index.html and inject Open Graph meta tags
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            html_content = f.read()
        
        # Inject Open Graph meta tags into the head section
        og_meta_tags = f'''
        <!-- Open Graph Meta Tags for Social Media -->
        <meta property="og:title" content="{og_title}">
        <meta property="og:description" content="{og_description}">
        <meta property="og:image" content="{og_image}">
        <meta property="og:url" content="{og_url}">
        <meta property="og:type" content="website">
        <meta property="og:site_name" content="Mind's Eye Photography">
        
        <!-- Twitter Card Meta Tags -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{og_title}">
        <meta name="twitter:description" content="{og_description}">
        <meta name="twitter:image" content="{og_image}">
        
        <!-- Facebook Meta Tags -->
        <meta property="fb:app_id" content="">
        
        <!-- Additional Meta Tags -->
        <meta name="description" content="{og_description}">
        <meta name="keywords" content="photography, wildlife, landscape, professional, Madison, Wisconsin">
        <meta name="author" content="Rick Corey">
        '''
        
        # Insert the meta tags before the closing </head> tag
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', og_meta_tags + '\n</head>')
        
        return html_content
    else:
        return "index.html not found", 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    
    # Special handling for featured-image route
    if path == 'featured-image':
        return featured_image_page()
    
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

