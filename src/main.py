import os
import sys
import json
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from src.models.user import db
from src.routes.user import user_bp
from src.routes.contact import contact_bp
from src.routes.admin import admin_bp
from src.routes.background import background_bp
from src.routes.featured_image import featured_bp
from src.routes.portfolio_management import portfolio_mgmt_bp
from src.routes.category_management import category_mgmt_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configure photography assets directory (use static for Railway compatibility)
PHOTOGRAPHY_ASSETS_DIR = os.path.join(app.static_folder, 'assets')

# Ensure photography assets directory exists
os.makedirs(PHOTOGRAPHY_ASSETS_DIR, exist_ok=True)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(contact_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(background_bp)
app.register_blueprint(featured_bp)
app.register_blueprint(portfolio_mgmt_bp)
app.register_blueprint(category_mgmt_bp)

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/photography-assets/<path:filename>')
def serve_photography_assets(filename):
    """Serve images from the static assets directory"""
    try:
        return send_from_directory(PHOTOGRAPHY_ASSETS_DIR, filename)
    except FileNotFoundError:
        return "Image not found", 404

def load_featured_data():
    """Load featured image data from JSON file"""
    try:
        featured_file = os.path.join(app.static_folder, 'assets', 'featured-image.json')
        if os.path.exists(featured_file):
            with open(featured_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading featured data: {e}")
    return None

@app.route('/featured-image')
def featured_image_page():
    """Featured image page with Open Graph meta tags"""
    featured_data = load_featured_data()
    
    # Default values
    og_title = "Mind's Eye Photography - Where Moments Meet Imagination"
    og_description = "Professional wildlife and landscape photography by Rick Corey. Where moments meet imagination."
    og_image = "https://www.themindseyestudio.com/assets/logo.png"  # Default fallback
    og_url = "https://www.themindseyestudio.com/featured-image"
    
    # If we have featured data, use it for Open Graph
    if featured_data:
        og_title = f"{featured_data.get('title', 'Featured Image')} - Mind's Eye Photography"
        og_description = featured_data.get('description', og_description)
        if featured_data.get('image'):
            og_image = f"https://www.themindseyestudio.com/photography-assets/{featured_data['image']}"
    
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

