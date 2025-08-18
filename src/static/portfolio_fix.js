// API Base URL
const API_BASE = '/api';

// Load featured image

// Load categories
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        const data = await response.json();
        
        const filtersContainer = document.getElementById('portfolio-filters');
        filtersContainer.innerHTML = '<button class="filter-btn active" data-category="all">All</button>';
        
        data.categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.setAttribute('data-category', category.name.toLowerCase());
            button.textContent = category.name;
            button.addEventListener('click', () => filterPortfolio(category.name.toLowerCase()));
            filtersContainer.appendChild(button);
        });
        
        // Add event listener for "All" button
        filtersContainer.querySelector('[data-category="all"]').addEventListener('click', () => filterPortfolio('all'));
        
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load portfolio
async function loadPortfolio(category = 'all') {
    try {
        const url = category === 'all' ? `${API_BASE}/portfolio` : `${API_BASE}/portfolio?category=${category}`;
        const response = await fetch(url);
        const data = await response.json();
        
        const portfolioGrid = document.getElementById('portfolio-grid');
        
        if (data.images && data.images.length > 0) {
            portfolioGrid.innerHTML = data.images.map(image => `
                <div class="portfolio-item" onclick="openImageLightbox('/assets/${image.filename}', '${image.title || image.original_filename}', '${image.description || ''}')">
                    <img src="/assets/${image.filename}" alt="${image.title || image.original_filename}">
                    <div class="portfolio-overlay">
                        <h4>${image.title || image.original_filename}</h4>
                        <p>${image.description || ''}</p>
                        <div class="portfolio-categories">
                            ${image.categories.map(cat => `<span class="category-tag">${cat.name}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            portfolioGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                    <h3>No images found</h3>
                    <p>Upload some images through the admin panel to get started!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading portfolio:', error);
        document.getElementById('portfolio-grid').innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                <h3>Unable to load portfolio</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// Filter portfolio
function filterPortfolio(category) {
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-category="${category}"]`).classList.add('active');
    
    // Load portfolio with filter
    loadPortfolio(category);
}

// Load background image
async function loadBackgroundImage() {
    try {
        const response = await fetch(`${API_BASE}/background`);
        const data = await response.json();
        
        if (data.background) {
            const heroSection = document.querySelector('.hero');
            if (heroSection) {
                heroSection.style.backgroundImage = `url('/assets/${data.background.filename}')`;
                heroSection.style.backgroundSize = 'cover';
                heroSection.style.backgroundPosition = 'center';
                heroSection.style.backgroundRepeat = 'no-repeat';
                
                // Add overlay for better text readability (35% transparency as preferred)
                const overlay = heroSection.querySelector('.hero-overlay');
                if (!overlay) {
                    const overlayDiv = document.createElement('div');
                    overlayDiv.className = 'hero-overlay';
                    overlayDiv.style.cssText = `
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: rgba(0, 0, 0, 0.35);
                        z-index: 1;
                    `;
                    heroSection.appendChild(overlayDiv);
                }
                
                // Add background shape behind logo to make it pop
                const logoContainer = heroSection.querySelector('.logo-container');
                if (logoContainer) {
                    const logoBackground = logoContainer.querySelector('.logo-background');
                    if (!logoBackground) {
                        const logoBackgroundDiv = document.createElement('div');
                        logoBackgroundDiv.className = 'logo-background';
                        logoBackgroundDiv.style.cssText = `
                            position: absolute;
                            top: -10px;
                            left: -15px;
                            right: -15px;
                            bottom: -10px;
                            background: rgba(0, 0, 0, 0.45);
                            border-radius: 15px;
                            backdrop-filter: blur(10px);
                            z-index: -1;
                        `;
                        logoContainer.style.position = 'relative';
                        logoContainer.appendChild(logoBackgroundDiv);
                    }
                }
                
                // Ensure hero content is above overlay
                const heroContent = heroSection.querySelector('.hero-content');
                if (heroContent) {
                    heroContent.style.position = 'relative';
                    heroContent.style.zIndex = '2';
                }
            }
        }
    } catch (error) {
        console.error('Error loading background image:', error);
    }
}

// Open image in lightbox overlay
function openImageLightbox(imagePath, title, description) {
    // Create lightbox overlay
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox-overlay';
    lightbox.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        cursor: pointer;
    `;
    
    // Create lightbox content
    const lightboxContent = document.createElement('div');
    lightboxContent.style.cssText = `
        position: relative;
        max-width: 90%;
        max-height: 90%;
        display: flex;
        flex-direction: column;
        align-items: center;
        cursor: default;
    `;
    
    // Create image
    const img = document.createElement('img');
    img.src = imagePath;
    img.alt = title;
    img.style.cssText = `
        max-width: 100%;
        max-height: 80vh;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1);
    `;
    
    // Create info section
    const info = document.createElement('div');
    info.style.cssText = `
        color: white;
        text-align: center;
        margin-top: 20px;
        max-width: 600px;
    `;
    
    const titleElement = document.createElement('h3');
    titleElement.textContent = title;
    titleElement.style.cssText = `
        margin: 0 0 10px 0;
        font-size: 1.5rem;
        color: #ff6b35;
    `;
    
    const descElement = document.createElement('p');
    descElement.textContent = description;
    descElement.style.cssText = `
        margin: 0;
        font-size: 1rem;
        line-height: 1.4;
        color: #ccc;
    `;
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: -40px;
        right: -40px;
        background: #ff6b35;
        border: none;
        color: white;
        font-size: 30px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
    `;
    
    // Assemble lightbox
    info.appendChild(titleElement);
    if (description) info.appendChild(descElement);
    lightboxContent.appendChild(img);
    lightboxContent.appendChild(info);
    lightboxContent.appendChild(closeBtn);
    lightbox.appendChild(lightboxContent);
    
    // Add event listeners
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            document.body.removeChild(lightbox);
        }
    });
    
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(lightbox);
    });
    
    // Prevent content clicks from closing lightbox
    lightboxContent.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Add to page
    document.body.appendChild(lightbox);
    
    // Add keyboard support
    const handleKeydown = (e) => {
        if (e.key === 'Escape') {
            document.body.removeChild(lightbox);
            document.removeEventListener('keydown', handleKeydown);
        }
    };
    document.addEventListener('keydown', handleKeydown);
}

// Open featured image modal with EXIF data

// Open high resolution image in new window
function openHighResImage(imagePath, title) {
    const newWindow = window.open('', '_blank');
    newWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>${title} - High Resolution</title>
            <style>
                body {
                    margin: 0;
                    padding: 20px;
                    background: #000;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    font-family: Arial, sans-serif;
                }
                img {
                    max-width: 100%;
                    max-height: 100vh;
                    object-fit: contain;
                    box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1);
                }
                .title {
                    position: absolute;
                    top: 20px;
                    left: 20px;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="title">${title}</div>
            <img src="${imagePath}" alt="${title}" />
        </body>
        </html>
    `);
    newWindow.document.close();
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadPortfolio();
    loadBackgroundImage();
});

