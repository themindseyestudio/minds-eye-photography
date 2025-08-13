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

# Configure separate photography assets directory
PHOTOGRAPHY_ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'photography-assets')

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
    """Serve images from the separate photography assets directory"""
    try:
        return send_from_directory(PHOTOGRAPHY_ASSETS_DIR, filename)
    except FileNotFoundError:
        # Fallback to old location for backward compatibility during migration
        old_assets_dir = os.path.join(app.static_folder, 'assets')
        if os.path.exists(os.path.join(old_assets_dir, filename)):
            return send_from_directory(old_assets_dir, filename)
        return "Image not found", 404

@app.route('/api/portfolio')
def get_portfolio():
    """API endpoint to get portfolio data"""
    try:
        portfolio_file = os.path.join(app.static_folder, 'assets', 'portfolio-data.json')
        with open(portfolio_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        print(f"Error loading portfolio: {e}")
        return jsonify([])

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
