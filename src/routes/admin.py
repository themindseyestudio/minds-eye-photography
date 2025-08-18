from flask import Blueprint, render_template_string, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json
import sqlite3
from datetime import datetime
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
import zipfile
from src.models.user import db, PortfolioImage, Category, FeaturedImage, BackgroundImage

admin_bp = Blueprint('admin', __name__)

def get_exif_data(image_path):
    """Extract EXIF data from image"""
    try:
        image = Image.open(image_path)
        exifdata = image.getexif()
        
        exif_dict = {}
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)
            if isinstance(data, bytes):
                data = data.decode()
            exif_dict[tag] = data
            
        return {
            'camera': exif_dict.get('Make', 'Not Available'),
            'lens': exif_dict.get('LensModel', 'Not Available'),
            'settings': f"f/{exif_dict.get('FNumber', 'N/A')} {exif_dict.get('ExposureTime', 'N/A')}s ISO{exif_dict.get('ISOSpeedRatings', 'N/A')}"
        }
    except:
        return {
            'camera': 'Not Available',
            'lens': 'Not Available', 
            'settings': 'Not Available'
        }

@admin_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - Mind's Eye Photography</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .header h1 {
                color: #ff6b35;
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
            }
            
            .admin-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-bottom: 2rem;
            }
            
            .admin-card {
                background: #2a2a2a;
                padding: 2rem;
                border-radius: 10px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            
            .admin-card:hover {
                transform: translateY(-5px);
            }
            
            .admin-card h3 {
                color: #ff6b35;
                font-size: 1.5rem;
                margin-bottom: 1rem;
            }
            
            .admin-card p {
                color: #ccc;
                margin-bottom: 1.5rem;
            }
            
            .btn {
                display: inline-block;
                padding: 0.75rem 1.5rem;
                background: #ff6b35;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s ease;
                border: none;
                cursor: pointer;
                font-size: 1rem;
            }
            
            .btn:hover {
                background: #e55a2b;
            }
            
            .back-link {
                display: inline-block;
                margin-bottom: 2rem;
                color: #ff6b35;
                text-decoration: none;
                padding: 0.5rem 1rem;
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            .back-link:hover {
                background: #3a3a3a;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Site</a>
            
            <div class="header">
                <h1>Mind's Eye Photography Admin Dashboard</h1>
                <p>Manage your photography website</p>
            </div>
            
            <div class="admin-grid">
                <div class="admin-card">
                    <h3>Portfolio Management</h3>
                    <p>Upload, organize, and manage your photography portfolio</p>
                    <a href="/admin/portfolio" class="btn">Manage Portfolio</a>
                </div>
                
                <div class="admin-card">
                    <h3>Featured Image Management</h3>
                    <p>Set and manage the featured image on your homepage</p>
                    <a href="/admin/featured" class="btn">Manage Featured</a>
                </div>
                
                <div class="admin-card">
                    <h3>Category Management</h3>
                    <p>Add, edit, and organize your portfolio categories</p>
                    <a href="/admin/categories" class="btn">Manage Categories</a>
                </div>
                
                <div class="admin-card">
                    <h3>Background Image Management</h3>
                    <p>Set the background image for your website</p>
                    <a href="/admin/backgrounds" class="btn">Manage Background</a>
                </div>
                
                <div class="admin-card">
                    <h3>Backup Management</h3>
                    <p>Backup and restore your website data</p>
                    <a href="/admin/backup" class="btn">Manage Backups</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@admin_bp.route('/admin/portfolio')
def portfolio_management():
    """Portfolio management with EXACT layout from screenshots"""
    images = PortfolioImage.query.all()
    categories = Category.query.all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portfolio Management - Mind's Eye Photography</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .back-link {
                display: inline-block;
                margin-bottom: 2rem;
                color: #ff6b35;
                text-decoration: none;
                padding: 0.5rem 1rem;
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            .header h1 {
                color: #ff6b35;
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            
            /* Bulk Operations */
            .bulk-operations {
                background: #333;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .bulk-operations h3 {
                color: #ff6b35;
                margin-bottom: 1rem;
            }
            
            .bulk-controls {
                display: flex;
                gap: 1rem;
                margin-bottom: 1rem;
                flex-wrap: wrap;
            }
            
            .bulk-controls button {
                padding: 0.5rem 1rem;
                background: #555;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            
            .bulk-controls button:hover {
                background: #666;
            }
            
            .bulk-categories {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            
            .bulk-categories label {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: #ccc;
                font-size: 0.9rem;
            }
            
            .btn {
                padding: 0.75rem 1.5rem;
                background: #ff6b35;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                border: none;
                cursor: pointer;
                font-size: 1rem;
                transition: background 0.3s ease;
            }
            
            .btn:hover {
                background: #e55a2b;
            }
            
            /* Image Grid */
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
            }
            
            .image-card {
                background: #2a2a2a;
                border-radius: 10px;
                overflow: hidden;
                position: relative;
            }
            
            .image-card img {
                width: 100%;
                height: 200px;
                object-fit: cover;
            }
            
            .image-info {
                padding: 1rem;
            }
            
            .image-title {
                color: #ff6b35;
                font-size: 1.2rem;
                margin-bottom: 0.5rem;
            }
            
            .image-description {
                color: #ccc;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }
            
            .current-categories {
                margin-bottom: 1rem;
            }
            
            .current-categories h4 {
                color: #ff6b35;
                font-size: 1rem;
                margin-bottom: 0.5rem;
            }
            
            .category-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            
            .category-tag {
                background: #ff6b35;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 15px;
                font-size: 0.8rem;
            }
            
            .update-categories {
                margin-bottom: 1rem;
            }
            
            .update-categories h4 {
                color: #ff6b35;
                font-size: 1rem;
                margin-bottom: 0.5rem;
            }
            
            .category-checkboxes-card {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            
            .category-checkboxes-card label {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: #ccc;
                font-size: 0.85rem;
            }
            
            .image-actions {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
            }
            
            .btn-small {
                padding: 0.5rem 1rem;
                background: #ff6b35;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.85rem;
                text-decoration: none;
                display: inline-block;
            }
            
            .btn-small:hover {
                background: #e55a2b;
            }
            
            .btn-danger {
                background: #dc3545;
            }
            
            .btn-danger:hover {
                background: #c82333;
            }
            
            .bulk-checkbox {
                position: absolute;
                top: 10px;
                left: 10px;
                transform: scale(1.2);
            }
            
            .selected {
                border: 3px solid #ff6b35;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-link">← Back to Admin</a>
            
            <div class="header">
                <h1>Portfolio Management</h1>
            </div>
            
            <!-- Upload New Images -->
            <div class="bulk-operations" style="margin-bottom: 2rem;">
                <h3>Upload New Images</h3>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div style="margin-bottom: 1rem;">
                        <label style="color: #ccc; display: block; margin-bottom: 0.5rem;">Image Files (JPG/PNG) - Select Multiple</label>
                        <input type="file" name="images" multiple accept="image/*" style="width: 100%; padding: 0.5rem; background: #555; color: white; border: none; border-radius: 5px;">
                        <div style="color: #4CAF50; margin-top: 0.5rem; font-size: 0.9rem;">
                            ✨ Multi-Upload: Hold Ctrl (Windows) or Cmd (Mac) to select multiple images at once!<br>
                            📁 Persistent Storage: Images are now saved to Railway's persistent volume and will not disappear!
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="color: #ccc; display: block; margin-bottom: 0.5rem;">Base Title</label>
                        <input type="text" name="title" placeholder="e.g., Sunset Over Lake" style="width: 100%; padding: 0.5rem; background: #555; color: white; border: none; border-radius: 5px;">
                        <div style="color: #ccc; font-size: 0.8rem; margin-top: 0.25rem;">For multiple images, numbers will be added automatically (e.g., "Sunset Over Lake 1", "Sunset Over Lake 2")</div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="color: #ccc; display: block; margin-bottom: 0.5rem;">Description</label>
                        <textarea name="description" placeholder="Brief description (applies to all uploaded images)" style="width: 100%; padding: 0.5rem; background: #555; color: white; border: none; border-radius: 5px; height: 80px; resize: vertical;"></textarea>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="color: #ccc; display: block; margin-bottom: 0.5rem;">Categories (Select multiple)</label>
                        <div class="bulk-categories">
                            {% for category in categories %}
                            <label>
                                <input type="checkbox" name="categories" value="{{ category.id }}">
                                {{ category.name }}
                            </label>
                            {% endfor %}
                        </div>
                        <div style="color: #ccc; font-size: 0.8rem; margin-top: 0.25rem;">All uploaded images will be assigned to the selected categories</div>
                    </div>
                    
                    <button type="submit" class="btn">Upload Image(s) to Persistent Storage</button>
                </form>
            </div>
            
            <!-- Bulk Operations -->
            <div class="bulk-operations">
                <h3>Bulk Operations</h3>
                <div class="bulk-controls">
                    <button onclick="selectAll()">Select All</button>
                    <button onclick="clearAll()">Clear All</button>
                    <span style="color: #ccc;">Select multiple images to update their categories at once</span>
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <label style="color: #ccc;">Set categories for selected images:</label>
                    <div class="bulk-categories">
                        {% for category in categories %}
                        <label>
                            <input type="checkbox" name="bulkCategories" value="{{ category.id }}">
                            {{ category.name }}
                        </label>
                        {% endfor %}
                    </div>
                </div>
                
                <button onclick="updateSelectedImages()" class="btn">Update Selected Images</button>
            </div>

            <!-- Current Portfolio -->
            <div style="margin-bottom: 2rem;">
                <h2 style="color: #ff6b35; margin-bottom: 1rem;">Current Portfolio ({{ images|length }} images)</h2>
                
                <div class="image-grid">
                    {% for image in images %}
                    <div class="image-card" id="card-{{ image.id }}">
                        <input type="checkbox" class="bulk-checkbox" value="{{ image.id }}" onchange="toggleSelection({{ image.id }})">
                        <img src="/assets/{{ image.filename }}" alt="{{ image.title or image.original_filename }}">
                        
                        <div class="image-info">
                            <div class="image-title">{{ image.title or image.original_filename }}</div>
                            <div class="image-description">{{ image.description or 'No description' }}</div>
                            
                            <div class="current-categories">
                                <h4>Current Categories:</h4>
                                <div class="category-tags">
                                    {% for category in image.categories %}
                                    <span class="category-tag">{{ category.name }}</span>
                                    {% endfor %}
                                </div>
                            </div>
                            
                            <div class="update-categories">
                                <h4>Update Categories:</h4>
                                <div class="category-checkboxes-card">
                                    {% for category in categories %}
                                    <label>
                                        <input type="checkbox" name="imageCategories-{{ image.id }}" value="{{ category.id }}" 
                                               {% if category in image.categories %}checked{% endif %}>
                                        {{ category.name }}
                                    </label>
                                    {% endfor %}
                                </div>
                            </div>
                            
                            <div class="image-actions">
                                <button class="btn-small" onclick="editTitleDescription({{ image.id }})">Edit Title/Description</button>
                                <button class="btn-small" onclick="updateImageCategories({{ image.id }})">Update Categories</button>
                                <button class="btn-small btn-danger" onclick="deleteImage({{ image.id }})">Delete</button>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <script>
            // Upload form handler
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData();
                const fileInput = document.querySelector('input[name="images"]');
                const titleInput = document.querySelector('input[name="title"]');
                const descriptionInput = document.querySelector('textarea[name="description"]');
                const categoryCheckboxes = document.querySelectorAll('input[name="categories"]:checked');
                
                // Check if files are selected
                if (!fileInput.files.length) {
                    alert('Please select at least one image to upload.');
                    return;
                }
                
                // Add files
                for (let i = 0; i < fileInput.files.length; i++) {
                    formData.append('images', fileInput.files[i]);
                }
                
                // Add other form data
                formData.append('title', titleInput.value || 'Untitled');
                formData.append('description', descriptionInput.value || '');
                
                // Add selected categories
                categoryCheckboxes.forEach(cb => {
                    formData.append('categories', cb.value);
                });
                
                // Show loading message
                const submitBtn = document.querySelector('#uploadForm button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Uploading...';
                submitBtn.disabled = true;
                
                try {
                    const response = await fetch('/api/admin/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(`✅ SUCCESS: ${result.message}`);
                        // Reset form
                        document.getElementById('uploadForm').reset();
                        // Reload page to show new images
                        location.reload();
                    } else {
                        alert(`❌ UPLOAD FAILED: ${result.error}`);
                        if (result.errors && result.errors.length > 0) {
                            alert('Detailed errors:\\n' + result.errors.join('\\n'));
                        }
                    }
                } catch (error) {
                    alert(`❌ UPLOAD FAILED: ${error.message}`);
                } finally {
                    // Restore button
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            });
            
            // Bulk operations
            function selectAll() {
                const checkboxes = document.querySelectorAll('.bulk-checkbox');
                checkboxes.forEach(cb => {
                    cb.checked = true;
                    toggleSelection(cb.value);
                });
            }
            
            function clearAll() {
                const checkboxes = document.querySelectorAll('.bulk-checkbox');
                checkboxes.forEach(cb => {
                    cb.checked = false;
                    toggleSelection(cb.value);
                });
            }
            
            function toggleSelection(imageId) {
                const card = document.getElementById('card-' + imageId);
                const checkbox = card.querySelector('.bulk-checkbox');
                
                if (checkbox.checked) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            }
            
            async function updateSelectedImages() {
                const selectedImages = [];
                const checkboxes = document.querySelectorAll('.bulk-checkbox:checked');
                
                checkboxes.forEach(cb => {
                    selectedImages.push(cb.value);
                });
                
                if (selectedImages.length === 0) {
                    alert('Please select at least one image');
                    return;
                }
                
                const selectedCategories = [];
                const categoryCheckboxes = document.querySelectorAll('input[name="bulkCategories"]:checked');
                categoryCheckboxes.forEach(cb => {
                    selectedCategories.push(cb.value);
                });
                
                try {
                    const response = await fetch('/api/admin/bulk-update-categories', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            image_ids: selectedImages,
                            category_ids: selectedCategories
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Categories updated successfully!');
                        location.reload();
                    } else {
                        alert('Update failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Update failed: ' + error.message);
                }
            }
            
            // Individual image operations
            async function editTitleDescription(imageId) {
                const newTitle = prompt('Enter new title:');
                if (newTitle === null) return;
                
                const newDescription = prompt('Enter new description:');
                if (newDescription === null) return;
                
                try {
                    const response = await fetch(`/api/admin/image/${imageId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            title: newTitle,
                            description: newDescription
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Image updated successfully!');
                        location.reload();
                    } else {
                        alert('Update failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Update failed: ' + error.message);
                }
            }
            
            async function updateImageCategories(imageId) {
                const selectedCategories = [];
                const checkboxes = document.querySelectorAll(`input[name="imageCategories-${imageId}"]:checked`);
                
                checkboxes.forEach(cb => {
                    selectedCategories.push(cb.value);
                });
                
                try {
                    const response = await fetch(`/api/admin/image/${imageId}/categories`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            category_ids: selectedCategories
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Categories updated successfully!');
                        location.reload();
                    } else {
                        alert('Update failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Update failed: ' + error.message);
                }
            }
            
            async function deleteImage(imageId) {
                if (!confirm('Are you sure you want to delete this image?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/admin/image/${imageId}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Image deleted successfully!');
                        location.reload();
                    } else {
                        alert('Delete failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Delete failed: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    ''', images=images, categories=categories)

@admin_bp.route('/admin/categories')
def category_management():
    """Category management"""
    categories = Category.query.all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Category Management - Mind's Eye Photography</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .back-link {
                display: inline-block;
                margin-bottom: 2rem;
                color: #ff6b35;
                text-decoration: none;
                padding: 0.5rem 1rem;
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            .header h1 {
                color: #ff6b35;
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            
            .add-category {
                background: #2a2a2a;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .add-category h2 {
                color: #ff6b35;
                margin-bottom: 1rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: #ccc;
            }
            
            .form-group input {
                width: 100%;
                padding: 0.75rem;
                background: #3a3a3a;
                border: 1px solid #555;
                border-radius: 5px;
                color: #fff;
            }
            
            .btn {
                padding: 0.75rem 1.5rem;
                background: #ff6b35;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                transition: background 0.3s ease;
            }
            
            .btn:hover {
                background: #e55a2b;
            }
            
            .categories-list {
                background: #2a2a2a;
                padding: 2rem;
                border-radius: 10px;
            }
            
            .categories-list h2 {
                color: #ff6b35;
                margin-bottom: 1rem;
            }
            
            .category-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                background: #3a3a3a;
                margin-bottom: 1rem;
                border-radius: 5px;
            }
            
            .category-name {
                font-size: 1.2rem;
                color: #fff;
            }
            
            .default-indicator {
                color: #ff6b35;
                font-weight: bold;
            }
            
            .category-actions {
                display: flex;
                gap: 0.5rem;
            }
            
            .btn-small {
                padding: 0.5rem 1rem;
                background: #ff6b35;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.85rem;
            }
            
            .btn-small:hover {
                background: #e55a2b;
            }
            
            .btn-danger {
                background: #dc3545;
            }
            
            .btn-danger:hover {
                background: #c82333;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-link">← Back to Admin</a>
            
            <div class="header">
                <h1>Category Management</h1>
            </div>
            
            <!-- Add Category -->
            <div class="add-category">
                <h2>Add New Category</h2>
                <form id="addCategoryForm">
                    <div class="form-group">
                        <label>Category Name</label>
                        <input type="text" id="categoryName" name="name" required>
                    </div>
                    <button type="submit" class="btn">Add Category</button>
                </form>
            </div>
            
            <!-- Categories List -->
            <div class="categories-list">
                <h2>Existing Categories</h2>
                <div style="margin-bottom: 1rem; color: #ccc;">
                    <strong>Note:</strong> The default category will be displayed on the homepage when visitors first arrive.
                </div>
                
                {% for category in categories %}
                <div class="category-item">
                    <div class="category-name">
                        {{ category.name }}
                        {% if category.is_default %}
                        <span class="default-indicator">(Default)</span>
                        {% endif %}
                    </div>
                    <div class="category-actions">
                        {% if not category.is_default %}
                        <button class="btn-small" onclick="setDefault({{ category.id }})">Set Default</button>
                        {% endif %}
                        <button class="btn-small btn-danger" onclick="deleteCategory({{ category.id }})">Delete</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
            // Add category
            document.getElementById('addCategoryForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const name = document.getElementById('categoryName').value;
                
                try {
                    const response = await fetch('/api/admin/categories', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ name: name })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Category added successfully!');
                        location.reload();
                    } else {
                        alert('Failed to add category: ' + result.error);
                    }
                } catch (error) {
                    alert('Failed to add category: ' + error.message);
                }
            });
            
            // Set default category
            async function setDefault(categoryId) {
                try {
                    const response = await fetch(`/api/admin/categories/${categoryId}/set-default`, {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Default category updated!');
                        location.reload();
                    } else {
                        alert('Failed to set default: ' + result.error);
                    }
                } catch (error) {
                    alert('Failed to set default: ' + error.message);
                }
            }
            
            // Delete category
            async function deleteCategory(categoryId) {
                if (!confirm('Are you sure you want to delete this category?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/admin/categories/${categoryId}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Category deleted successfully!');
                        location.reload();
                    } else {
                        alert('Failed to delete category: ' + result.error);
                    }
                } catch (error) {
                    alert('Failed to delete category: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    ''', categories=categories)

@admin_bp.route('/admin/featured')
def featured_management():
    """Featured image management with proper story input"""
    images = PortfolioImage.query.all()
    featured = FeaturedImage.query.first()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Featured Image Management - Mind's Eye Photography</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .back-link {
                display: inline-block;
                margin-bottom: 2rem;
                color: #ff6b35;
                text-decoration: none;
                padding: 0.5rem 1rem;
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            .header h1 {
                color: #ff6b35;
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            
            .current-featured {
                background: #2a2a2a;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .current-featured h2 {
                color: #ff6b35;
                margin-bottom: 1rem;
            }
            
            .featured-display {
                display: flex;
                gap: 2rem;
                align-items: flex-start;
            }
            
            .featured-image {
                flex: 0 0 300px;
            }
            
            .featured-image img {
                width: 100%;
                border-radius: 10px;
            }
            
            .featured-info {
                flex: 1;
            }
            
            .featured-title {
                color: #ff6b35;
                font-size: 1.5rem;
                margin-bottom: 1rem;
            }
            
            .featured-story {
                color: #ccc;
                line-height: 1.8;
                margin-bottom: 1rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: #ccc;
                font-weight: bold;
            }
            
            .form-group textarea {
                width: 100%;
                padding: 1rem;
                background: #3a3a3a;
                border: 1px solid #555;
                border-radius: 5px;
                color: #fff;
                font-family: Arial, sans-serif;
                resize: vertical;
            }
            
            .btn {
                padding: 0.75rem 1.5rem;
                background: #ff6b35;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                transition: background 0.3s ease;
            }
            
            .btn:hover {
                background: #e55a2b;
            }
            
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
            }
            
            .image-card {
                background: #2a2a2a;
                border-radius: 10px;
                overflow: hidden;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            
            .image-card:hover {
                transform: translateY(-5px);
            }
            
            .image-card img {
                width: 100%;
                height: 200px;
                object-fit: cover;
            }
            
            .image-info {
                padding: 1rem;
            }
            
            .image-title {
                color: #ff6b35;
                font-size: 1.1rem;
                margin-bottom: 0.5rem;
            }
            
            .image-description {
                color: #ccc;
                font-size: 0.9rem;
            }
            
            .selected-image {
                border: 3px solid #ff6b35;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-link">← Back to Admin</a>
            
            <div class="header">
                <h1>Featured Image Management</h1>
            </div>
            
            <!-- Current Featured Image -->
            {% if featured %}
            <div class="current-featured">
                <h2>Current Featured Image</h2>
                <div class="featured-display">
                    <div class="featured-image">
                        <img src="/assets/{{ featured.portfolio_image.filename }}" alt="{{ featured.portfolio_image.title }}">
                    </div>
                    <div class="featured-info">
                        <div class="featured-title">{{ featured.portfolio_image.title }}</div>
                        <div class="featured-story">{{ featured.story or 'No story added yet.' }}</div>
                        
                        <form id="updateStoryForm">
                            <div class="form-group">
                                <label>The Story Behind This Image</label>
                                <textarea id="storyText" name="story" rows="6" placeholder="Tell the story behind this image...">{{ featured.story or '' }}</textarea>
                                <small style="color: #ccc;">This story will be displayed underneath the featured image on your homepage along with EXIF data.</small>
                            </div>
                            <button type="submit" class="btn">Update Story</button>
                        </form>
                    </div>
                </div>
            </div>
            {% endif %}
            
            <!-- Select Featured Image -->
            <div style="background: #2a2a2a; padding: 2rem; border-radius: 10px;">
                <h2 style="color: #ff6b35; margin-bottom: 1rem;">Select Featured Image</h2>
                <p style="color: #ccc; margin-bottom: 2rem;">Click on any image below to set it as the featured image</p>
                
                <div class="image-grid">
                    {% for image in images %}
                    <div class="image-card {% if featured and featured.portfolio_image.id == image.id %}selected-image{% endif %}" 
                         onclick="setFeaturedImage({{ image.id }})">
                        <img src="/assets/{{ image.filename }}" alt="{{ image.title or image.original_filename }}">
                        <div class="image-info">
                            <div class="image-title">{{ image.title or image.original_filename }}</div>
                            <div class="image-description">{{ image.description or 'No description' }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <script>
            // Update story
            document.getElementById('updateStoryForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const story = document.getElementById('storyText').value;
                
                try {
                    const response = await fetch('/api/admin/featured/story', {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ story: story })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Story updated successfully!');
                    } else {
                        alert('Failed to update story: ' + result.error);
                    }
                } catch (error) {
                    alert('Failed to update story: ' + error.message);
                }
            });
            
            // Set featured image
            async function setFeaturedImage(imageId) {
                try {
                    const response = await fetch('/api/admin/featured', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ image_id: imageId })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Featured image updated successfully!');
                        location.reload();
                    } else {
                        alert('Failed to set featured image: ' + result.error);
                    }
                } catch (error) {
                    alert('Failed to set featured image: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    ''', images=images, featured=featured)

@admin_bp.route('/admin/backgrounds')
def background_management():
    """Background image management"""
    images = PortfolioImage.query.all()
    background = BackgroundImage.query.first()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Background Image Management - Mind's Eye Photography</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .back-link {
                display: inline-block;
                margin-bottom: 2rem;
                color: #ff6b35;
                text-decoration: none;
                padding: 0.5rem 1rem;
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            .header h1 {
                color: #ff6b35;
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            
            .current-background {
                background: #2a2a2a;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .current-background h2 {
                color: #ff6b35;
                margin-bottom: 1rem;
            }
            
            .background-preview {
                width: 300px;
                height: 200px;
                border-radius: 10px;
                object-fit: cover;
            }
            
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
            }
            
            .image-card {
                background: #2a2a2a;
                border-radius: 10px;
                overflow: hidden;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            
            .image-card:hover {
                transform: translateY(-5px);
            }
            
            .image-card img {
                width: 100%;
                height: 200px;
                object-fit: cover;
            }
            
            .image-info {
                padding: 1rem;
            }
            
            .image-title {
                color: #ff6b35;
                font-size: 1.1rem;
                margin-bottom: 0.5rem;
            }
            
            .image-description {
                color: #ccc;
                font-size: 0.9rem;
            }
            
            .selected-image {
                border: 3px solid #ff6b35;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-link">← Back to Admin</a>
            
            <div class="header">
                <h1>Background Image Management</h1>
            </div>
            
            <!-- Current Background -->
            {% if background %}
            <div class="current-background">
                <h2>Current Background Image</h2>
                <img src="/assets/{{ background.filename }}" alt="{{ background.title }}" class="background-preview">
                <p style="color: #ccc; margin-top: 1rem;">{{ background.title }}</p>
            </div>
            {% endif %}
            
            <!-- Select Background Image -->
            <div style="background: #2a2a2a; padding: 2rem; border-radius: 10px;">
                <h2 style="color: #ff6b35; margin-bottom: 1rem;">Select Background Image</h2>
                <p style="color: #ccc; margin-bottom: 2rem;">Click on any image below to set it as the website background</p>
                
                <div class="image-grid">
                    {% for image in images %}
                    <div class="image-card {% if background and background.filename == image.filename %}selected-image{% endif %}" 
                         onclick="setBackgroundImage({{ image.id }})">
                        <img src="/assets/{{ image.filename }}" alt="{{ image.title or image.original_filename }}">
                        <div class="image-info">
                            <div class="image-title">{{ image.title or image.original_filename }}</div>
                            <div class="image-description">{{ image.description or 'No description' }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <script>
            async function setBackgroundImage(imageId) {
                try {
                    const response = await fetch('/api/admin/background', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ image_id: imageId })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Background image updated successfully!');
                        location.reload();
                    } else {
                        alert('Failed to set background image: ' + result.error);
                    }
                } catch (error) {
                    alert('Failed to set background image: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    ''', images=images, background=background)

@admin_bp.route('/admin/backup')
def backup_management():
    """Backup management"""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Backup Management - Mind's Eye Photography</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .back-link {
                display: inline-block;
                margin-bottom: 2rem;
                color: #ff6b35;
                text-decoration: none;
                padding: 0.5rem 1rem;
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            .header h1 {
                color: #ff6b35;
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            
            .backup-section {
                background: #2a2a2a;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .backup-section h2 {
                color: #ff6b35;
                margin-bottom: 1rem;
            }
            
            .btn {
                padding: 0.75rem 1.5rem;
                background: #ff6b35;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                transition: background 0.3s ease;
                margin-right: 1rem;
                margin-bottom: 1rem;
            }
            
            .btn:hover {
                background: #e55a2b;
            }
            
            .btn-success {
                background: #28a745;
            }
            
            .btn-success:hover {
                background: #218838;
            }
            
            .btn-danger {
                background: #dc3545;
            }
            
            .btn-danger:hover {
                background: #c82333;
            }
            
            .backup-status {
                background: #3a3a3a;
                padding: 1rem;
                border-radius: 5px;
                margin-top: 1rem;
                color: #ccc;
            }
            
            .feature-list {
                list-style: none;
                padding-left: 0;
            }
            
            .feature-list li {
                color: #ccc;
                margin-bottom: 0.5rem;
                padding-left: 1.5rem;
                position: relative;
            }
            
            .feature-list li:before {
                content: "•";
                color: #ff6b35;
                position: absolute;
                left: 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin" class="back-link">← Back to Admin</a>
            
            <div class="header">
                <h1>Backup Management</h1>
            </div>
            
            <!-- Local Backup -->
            <div class="backup-section">
                <h2>Local Backup</h2>
                <p style="color: #ccc; margin-bottom: 1rem;">Create an immediate backup to local disk before making changes</p>
                <button onclick="createLocalBackup()" class="btn">Create Local Backup</button>
                <div id="localBackupStatus" class="backup-status" style="display: none;"></div>
            </div>
            
            <!-- GitHub Auto-Backup -->
            <div class="backup-section">
                <h2>GitHub Auto-Backup</h2>
                <p style="color: #ccc; margin-bottom: 1rem;">Automatic set-and-forget backups to GitHub repository</p>
                <button onclick="setupAutoBackup()" class="btn btn-success">Setup Auto-Backup</button>
                <button onclick="checkBackupStatus()" class="btn">Check Status</button>
                
                <div style="margin-top: 1rem;">
                    <h4 style="color: #ff6b35;">Auto-backup features:</h4>
                    <ul class="feature-list">
                        <li>Daily automatic backups to GitHub</li>
                        <li>Version history and rollback capability</li>
                        <li>Secure cloud storage</li>
                        <li>No manual intervention required</li>
                    </ul>
                </div>
            </div>
            
            <!-- Emergency Restore -->
            <div class="backup-section">
                <h2>Emergency Restore</h2>
                <p style="color: #ccc; margin-bottom: 1rem;">Restore from a previous backup in case of issues</p>
                <button onclick="emergencyRestore()" class="btn btn-danger">Emergency Restore</button>
                
                <div style="margin-top: 1rem;">
                    <h4 style="color: #ff6b35;">Restore options:</h4>
                    <ul class="feature-list">
                        <li>Restore from local backup</li>
                        <li>Restore from GitHub backup</li>
                        <li>Selective restore (images only, data only, etc.)</li>
                    </ul>
                    <p style="color: #ff6b35; margin-top: 1rem;"><strong>Warning:</strong> This will overwrite current data</p>
                </div>
            </div>
        </div>
        
        <script>
            async function createLocalBackup() {
                const statusDiv = document.getElementById('localBackupStatus');
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = 'Creating backup...';
                
                try {
                    const response = await fetch('/api/admin/backup/local', {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        statusDiv.innerHTML = `Backup created successfully: ${result.filename}`;
                        statusDiv.style.color = '#28a745';
                    } else {
                        statusDiv.innerHTML = `Backup failed: ${result.error}`;
                        statusDiv.style.color = '#dc3545';
                    }
                } catch (error) {
                    statusDiv.innerHTML = `Backup failed: ${error.message}`;
                    statusDiv.style.color = '#dc3545';
                }
            }
            
            async function setupAutoBackup() {
                alert('Auto-backup setup would connect to GitHub API. This feature requires GitHub credentials.');
            }
            
            async function checkBackupStatus() {
                alert('Checking backup status...');
            }
            
            async function emergencyRestore() {
                if (!confirm('Are you sure you want to restore from backup? This will overwrite current data.')) {
                    return;
                }
                alert('Emergency restore functionality would be implemented here.');
            }
        </script>
    </body>
    </html>
    ''')

# API Routes
@admin_bp.route('/api/admin/bulk-update-categories', methods=['POST'])
def bulk_update_categories():
    """Update categories for multiple images"""
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        category_ids = data.get('category_ids', [])
        
        for image_id in image_ids:
            image = PortfolioImage.query.get(int(image_id))
            if image:
                # Clear existing categories
                image.categories.clear()
                
                # Add new categories
                for category_id in category_ids:
                    category = Category.query.get(int(category_id))
                    if category:
                        image.categories.append(category)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/image/<int:image_id>', methods=['PUT'])
def update_image(image_id):
    """Update image title and description"""
    try:
        data = request.get_json()
        image = PortfolioImage.query.get_or_404(image_id)
        
        image.title = data.get('title', image.title)
        image.description = data.get('description', image.description)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/image/<int:image_id>/categories', methods=['PUT'])
def update_image_categories(image_id):
    """Update categories for a single image"""
    try:
        data = request.get_json()
        category_ids = data.get('category_ids', [])
        
        image = PortfolioImage.query.get_or_404(image_id)
        
        # Clear existing categories
        image.categories.clear()
        
        # Add new categories
        for category_id in category_ids:
            category = Category.query.get(int(category_id))
            if category:
                image.categories.append(category)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/image/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete an image"""
    try:
        image = PortfolioImage.query.get_or_404(image_id)
        
        # Delete file
        file_path = os.path.join('src/static/assets', image.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database entry
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/categories', methods=['POST'])
def add_category():
    """Add new category"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'error': 'Category name is required'})
        
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/categories/<int:category_id>/set-default', methods=['POST'])
def set_default_category(category_id):
    """Set default category"""
    try:
        # Clear all default flags
        Category.query.update({'is_default': False})
        
        # Set new default
        category = Category.query.get_or_404(category_id)
        category.is_default = True
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete category"""
    try:
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/featured', methods=['POST'])
def set_featured_image():
    """Set featured image"""
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        
        # Get the portfolio image to get its title
        portfolio_image = PortfolioImage.query.get(image_id)
        if not portfolio_image:
            return jsonify({'success': False, 'error': 'Image not found'})
        
        # Remove existing featured image
        FeaturedImage.query.delete()
        
        # Set new featured image
        featured = FeaturedImage(
            portfolio_image_id=image_id,
            title=portfolio_image.title or portfolio_image.original_filename,
            is_active=True
        )
        db.session.add(featured)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/featured/story', methods=['PUT'])
def update_featured_story():
    """Update featured image story"""
    try:
        data = request.get_json()
        story = data.get('story')
        
        featured = FeaturedImage.query.first()
        if featured:
            featured.story = story
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'No featured image set'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/background', methods=['POST'])
def set_background_image():
    """Set background image"""
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        
        # Get the portfolio image to copy its data
        portfolio_image = PortfolioImage.query.get(image_id)
        if not portfolio_image:
            return jsonify({'success': False, 'error': 'Image not found'})
        
        # Remove existing background image
        BackgroundImage.query.delete()
        
        # Set new background image
        background = BackgroundImage(
            filename=portfolio_image.filename,
            original_filename=portfolio_image.original_filename,
            title=portfolio_image.title or portfolio_image.original_filename,
            is_active=True
        )
        db.session.add(background)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/admin/backup/local', methods=['POST'])
def create_local_backup():
    """Create local backup"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'
        
        # Create backup data
        backup_data = {
            'timestamp': timestamp,
            'images': [img.to_dict() for img in PortfolioImage.query.all()],
            'categories': [cat.to_dict() for cat in Category.query.all()],
            'featured': FeaturedImage.query.first().to_dict() if FeaturedImage.query.first() else None,
            'background': BackgroundImage.query.first().to_dict() if BackgroundImage.query.first() else None
        }
        
        # Save backup file
        backup_path = os.path.join('backups', filename)
        os.makedirs('backups', exist_ok=True)
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/admin/upload', methods=['POST'])
def upload_images():
    """Upload multiple images to portfolio"""
    try:
        if 'images' not in request.files:
            return jsonify({'success': False, 'error': 'No images selected'})
        
        files = request.files.getlist('images')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'No images selected'})
        
        title = request.form.get('title', 'Untitled')
        description = request.form.get('description', '')
        category_ids = request.form.getlist('categories')
        
        uploaded_count = 0
        errors = []
        
        # Create assets directory if it doesn't exist
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets')
        assets_dir = os.path.abspath(assets_dir)
        os.makedirs(assets_dir, exist_ok=True)
        
        for i, file in enumerate(files):
            if file and file.filename:
                try:
                    # Generate unique filename
                    import uuid
                    file_ext = os.path.splitext(file.filename)[1].lower()
                    unique_filename = f"{uuid.uuid4()}{file_ext}"
                    
                    # Save file
                    file_path = os.path.join(assets_dir, unique_filename)
                    file.save(file_path)
                    
                    # Generate title for multiple images
                    if len(files) > 1:
                        image_title = f"{title} {i + 1}"
                    else:
                        image_title = title
                    
                    # Extract EXIF data
                    exif_data = get_exif_data(file_path)
                    
                    # Create database entry
                    new_image = PortfolioImage(
                        filename=unique_filename,
                        original_filename=file.filename,
                        title=image_title,
                        description=description,
                        camera_make=exif_data.get('camera', 'Not Available'),
                        lens=exif_data.get('lens', 'Not Available'),
                        aperture='Not Available',
                        shutter_speed='Not Available',
                        iso='Not Available'
                    )
                    
                    db.session.add(new_image)
                    db.session.flush()  # Get the ID
                    
                    # Add categories
                    if category_ids:
                        categories = Category.query.filter(Category.id.in_(category_ids)).all()
                        new_image.categories = categories
                    
                    uploaded_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to upload {file.filename}: {str(e)}")
        
        db.session.commit()
        
        if uploaded_count > 0:
            message = f"Successfully uploaded {uploaded_count} image(s)"
            if errors:
                message += f" with {len(errors)} error(s)"
            return jsonify({'success': True, 'message': message, 'uploaded': uploaded_count, 'errors': errors})
        else:
            return jsonify({'success': False, 'error': 'No images were uploaded', 'errors': errors})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

