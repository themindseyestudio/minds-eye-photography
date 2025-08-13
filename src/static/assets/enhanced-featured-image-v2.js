// Enhanced Featured Image Component with EXIF Data - Version 2
// Improved React integration and DOM manipulation

class EnhancedFeaturedImage {
    constructor() {
        this.featuredData = null;
        this.isInitialized = false;
        this.retryCount = 0;
        this.maxRetries = 10;
        this.init();
    }

    async init() {
        // Wait for React to fully render
        this.waitForReactAndInject();
    }

    waitForReactAndInject() {
        // Check if React has rendered the page
        const checkReactReady = () => {
            const rootElement = document.getElementById('root');
            const hasContent = rootElement && rootElement.children.length > 0;
            
            if (hasContent && !this.isInitialized) {
                this.loadAndRender();
            } else if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                setTimeout(checkReactReady, 500);
            }
        };

        checkReactReady();
    }

    async loadAndRender() {
        try {
            await this.loadFeaturedData();
            this.injectEnhancedSection();
            this.isInitialized = true;
        } catch (error) {
            console.error('Error initializing enhanced featured image:', error);
        }
    }

    async loadFeaturedData() {
        try {
            const response = await fetch('/api/featured');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.featuredData = await response.json();
            console.log('Loaded featured data:', this.featuredData);
        } catch (error) {
            console.error('Error loading featured image data:', error);
            // Use fallback data if API fails
            this.featuredData = {
                title: 'Featured Image',
                description: 'Loading...',
                image: '',
                exif_data: {}
            };
        }
    }

    injectEnhancedSection() {
        // Find and replace the existing featured image section
        const existingSection = this.findFeaturedImageSection();
        
        if (existingSection) {
            console.log('Found existing featured section, replacing...');
            this.replaceExistingSection(existingSection);
        } else {
            console.log('No existing featured section found, creating new one...');
            this.createNewSection();
        }
    }

    findFeaturedImageSection() {
        // Look for elements containing "Featured Image" text
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes('Featured Image')) {
                // Find the parent container
                let container = node.parentElement;
                while (container && container !== document.body) {
                    if (container.tagName === 'SECTION' || 
                        container.tagName === 'DIV' && container.className.includes('section')) {
                        return container;
                    }
                    container = container.parentElement;
                }
            }
        }

        // Alternative: look for specific class patterns
        const selectors = [
            '[class*="featured"]',
            '[id*="featured"]',
            'section:nth-of-type(3)', // Often the third section
            'div[class*="container"]:has(h2)'
        ];

        for (const selector of selectors) {
            try {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element.textContent.toLowerCase().includes('featured')) {
                        return element;
                    }
                }
            } catch (e) {
                // Selector not supported
            }
        }

        return null;
    }

    replaceExistingSection(existingSection) {
        const enhancedContainer = document.createElement('section');
        enhancedContainer.id = 'enhanced-featured-section';
        enhancedContainer.className = 'enhanced-featured-section';
        enhancedContainer.innerHTML = this.generateEnhancedHTML();
        
        existingSection.parentNode.replaceChild(enhancedContainer, existingSection);
        this.addEventListeners();
    }

    createNewSection() {
        // Find a good insertion point (after portfolio section)
        const portfolioSection = document.querySelector('section:has(h2:contains("Portfolio")), div:has(h2:contains("Portfolio"))');
        const aboutSection = document.querySelector('section:has(h2:contains("About")), div:has(h2:contains("About"))');
        
        const insertionPoint = portfolioSection || aboutSection || document.querySelector('main') || document.body;
        
        const enhancedContainer = document.createElement('section');
        enhancedContainer.id = 'enhanced-featured-section';
        enhancedContainer.className = 'enhanced-featured-section';
        enhancedContainer.innerHTML = this.generateEnhancedHTML();
        
        if (portfolioSection) {
            portfolioSection.parentNode.insertBefore(enhancedContainer, portfolioSection.nextSibling);
        } else {
            insertionPoint.appendChild(enhancedContainer);
        }
        
        this.addEventListeners();
    }

    generateEnhancedHTML() {
        if (!this.featuredData) return '<div>Loading featured image...</div>';

        return `
            <div class="enhanced-featured-container">
                <h2 class="featured-title">Featured Image</h2>
                
                <div class="featured-content">
                    <div class="featured-image-wrapper" onclick="this.classList.toggle('fullscreen')">
                        <img src="/photography-assets/${this.featuredData.image}" 
                             alt="${this.featuredData.title}"
                             class="featured-image-large"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
                        <div class="image-error" style="display: none;">
                            <p>Image not available</p>
                        </div>
                        <div class="image-overlay">
                            <h3>${this.featuredData.title}</h3>
                            <p>${this.featuredData.description}</p>
                        </div>
                    </div>
                    
                    <div class="exif-data-panel">
                        <h4>📷 Technical Details</h4>
                        ${this.renderExifData()}
                    </div>
                </div>
                
                <div class="featured-actions">
                    <button onclick="window.open('/photography-assets/${this.featuredData.image}', '_blank')" 
                            class="action-btn view-full-btn">
                        🔍 View Full Resolution
                    </button>
                    <button onclick="navigator.share ? navigator.share({title: '${this.featuredData.title}', url: window.location.href}) : alert('Sharing not supported')" 
                            class="action-btn share-btn">
                        📱 Share
                    </button>
                </div>
            </div>
        `;
    }

    renderExifData() {
        if (!this.featuredData.exif_data || Object.keys(this.featuredData.exif_data).length === 0) {
            return '<p class="no-exif">📊 No technical data available for this image</p>';
        }

        const exif = this.featuredData.exif_data;
        
        // Primary camera settings
        const primaryData = [
            { label: '📷 Camera', value: exif.camera, icon: '📷' },
            { label: '🔍 Lens', value: exif.lens, icon: '🔍' },
            { label: '⚪ Aperture', value: exif.aperture, icon: '⚪' },
            { label: '⏱️ Shutter Speed', value: exif.shutter_speed, icon: '⏱️' },
            { label: '🎞️ ISO', value: exif.iso, icon: '🎞️' },
            { label: '📏 Focal Length', value: exif.focal_length, icon: '📏' }
        ];

        // Additional technical data
        const additionalData = [
            { label: '📅 Date Taken', value: exif.date_taken, icon: '📅' },
            { label: '💡 Exposure Mode', value: exif.exposure_mode, icon: '💡' },
            { label: '🌡️ White Balance', value: exif.white_balance, icon: '🌡️' },
            { label: '⚡ Flash', value: exif.flash, icon: '⚡' },
            { label: '📐 Metering Mode', value: exif.metering_mode, icon: '📐' },
            { label: '📏 Image Size', value: `${exif.image_width} × ${exif.image_height}`, icon: '📏' },
            { label: '🎨 Color Space', value: exif.color_space, icon: '🎨' },
            { label: '💻 Software', value: exif.software, icon: '💻' },
            { label: '👤 Artist', value: exif.artist, icon: '👤' },
            { label: '©️ Copyright', value: exif.copyright, icon: '©️' }
        ];

        const renderDataGroup = (data, title) => {
            const validItems = data.filter(item => item.value && item.value !== 'Unknown' && item.value !== 'ISO Unknown');
            if (validItems.length === 0) return '';

            return `
                <div class="exif-group">
                    ${title ? `<h5>${title}</h5>` : ''}
                    ${validItems.map(item => `
                        <div class="exif-item">
                            <span class="exif-label">${item.label}</span>
                            <span class="exif-value">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        };

        return `
            ${renderDataGroup(primaryData, '📸 Camera Settings')}
            ${renderDataGroup(additionalData, '📋 Additional Information')}
        `;
    }

    addEventListeners() {
        // Add escape key listener for fullscreen mode
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const fullscreenElement = document.querySelector('.featured-image-wrapper.fullscreen');
                if (fullscreenElement) {
                    fullscreenElement.classList.remove('fullscreen');
                }
            }
        });

        // Add click outside to close fullscreen
        document.addEventListener('click', (e) => {
            const fullscreenWrapper = document.querySelector('.featured-image-wrapper.fullscreen');
            if (fullscreenWrapper && !fullscreenWrapper.contains(e.target)) {
                fullscreenWrapper.classList.remove('fullscreen');
            }
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => new EnhancedFeaturedImage(), 1500);
    });
} else {
    setTimeout(() => new EnhancedFeaturedImage(), 1500);
}

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedFeaturedImage;
}

