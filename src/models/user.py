from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Association table for many-to-many relationship between PortfolioImage and Category
portfolio_categories = db.Table('portfolio_categories',
    db.Column('portfolio_image_id', db.Integer, db.ForeignKey('portfolio_image.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to portfolio images
    portfolio_images = db.relationship('PortfolioImage', secondary=portfolio_categories, back_populates='categories')

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'image_count': len(self.portfolio_images)
        }

class PortfolioImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)  # in bytes
    image_width = db.Column(db.Integer)
    image_height = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # EXIF data fields
    camera_make = db.Column(db.String(100))
    camera_model = db.Column(db.String(100))
    lens_model = db.Column(db.String(100))
    focal_length = db.Column(db.String(50))
    aperture = db.Column(db.String(50))
    shutter_speed = db.Column(db.String(50))
    iso = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime)
    
    # Relationship to categories
    categories = db.relationship('Category', secondary=portfolio_categories, back_populates='portfolio_images')

    def __repr__(self):
        return f'<PortfolioImage {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_filename': self.image_filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'categories': [cat.name for cat in self.categories],
            'exif_data': {
                'camera_make': self.camera_make,
                'camera_model': self.camera_model,
                'lens_model': self.lens_model,
                'focal_length': self.focal_length,
                'aperture': self.aperture,
                'shutter_speed': self.shutter_speed,
                'iso': self.iso,
                'date_taken': self.date_taken.isoformat() if self.date_taken else None
            }
        }

class FeaturedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)  # Only one can be active at a time
    
    # EXIF data fields
    camera_make = db.Column(db.String(100))
    camera_model = db.Column(db.String(100))
    lens_model = db.Column(db.String(100))
    focal_length = db.Column(db.String(50))
    aperture = db.Column(db.String(50))
    shutter_speed = db.Column(db.String(50))
    iso = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime)
    
    # Story/background information
    story_title = db.Column(db.String(200))
    story_content = db.Column(db.Text)
    location = db.Column(db.String(200))

    def __repr__(self):
        return f'<FeaturedImage {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_filename': self.image_filename,
            'original_filename': self.original_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'story_title': self.story_title,
            'story_content': self.story_content,
            'location': self.location,
            'exif_data': {
                'camera_make': self.camera_make,
                'camera_model': self.camera_model,
                'lens_model': self.lens_model,
                'focal_length': self.focal_length,
                'aperture': self.aperture,
                'shutter_speed': self.shutter_speed,
                'iso': self.iso,
                'date_taken': self.date_taken.isoformat() if self.date_taken else None
            }
        }

class BackgroundImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)  # Only one can be active at a time

    def __repr__(self):
        return f'<BackgroundImage {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'image_filename': self.image_filename,
            'original_filename': self.original_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

