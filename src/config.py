"""
Configuration file for Mind's Eye Photography
Centralizes asset directory paths for easy management
"""
import os

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'src', 'static')

# Separate photography assets directory (outside website structure)
PHOTOGRAPHY_ASSETS_DIR = os.path.join(BASE_DIR, '..', 'photography-assets')

# Data files (keep with website for easy admin updates)
PORTFOLIO_DATA_FILE = os.path.join(STATIC_DIR, 'assets', 'portfolio-data-multicategory.json')
CATEGORIES_CONFIG_FILE = os.path.join(STATIC_DIR, 'assets', 'categories-config.json')
FEATURED_DATA_FILE = os.path.join(STATIC_DIR, 'assets', 'featured-image.json')

# Legacy paths for backward compatibility
LEGACY_ASSETS_DIR = os.path.join(STATIC_DIR, 'assets')

# URL paths for serving images
PHOTOGRAPHY_ASSETS_URL_PREFIX = '/photography-assets/'
LEGACY_ASSETS_URL_PREFIX = '/static/assets/'

def get_image_url(filename):
    """
    Get the URL for an image file
    Returns new photography-assets URL format
    """
    return f"{PHOTOGRAPHY_ASSETS_URL_PREFIX}{filename}"

def get_legacy_image_url(filename):
    """
    Get the legacy URL for an image file
    Used for backward compatibility during migration
    """
    return f"{LEGACY_ASSETS_URL_PREFIX}{filename}"

