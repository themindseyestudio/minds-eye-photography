import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from src.models.user import db
from src.routes.user import user_bp
from src.routes.admin import admin_bp
from src.routes.api import api_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Register all blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables and initial data
with app.app_context():
    db.create_all()
    
    # Create default categories if they don't exist
    from src.models.user import Category
    default_categories = [
        {'name': 'Nature', 'description': 'Natural landscapes and wildlife photography', 'sort_order': 1},
        {'name': 'Portrait', 'description': 'Portrait and people photography', 'sort_order': 2},
        {'name': 'Architecture', 'description': 'Buildings and architectural photography', 'sort_order': 3},
        {'name': 'Street', 'description': 'Street photography and urban scenes', 'sort_order': 4},
        {'name': 'Miscellaneous', 'description': 'Other photography work', 'sort_order': 5}
    ]
    
    for cat_data in default_categories:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(
                name=cat_data['name'],
                description=cat_data['description'],
                sort_order=cat_data['sort_order'],
                is_default=(cat_data['name'] == 'Nature')  # Set Nature as default
            )
            db.session.add(category)
    
    db.session.commit()

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

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve assets from the assets directory"""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

if __name__ == '__main__':
    import os
port = int(os.environ.get('PORT', 5001))
app.run(host='0.0.0.0', port=port, debug=True)

