// Enhanced Featured Image Component - Final Version
// Fixed selectors and robust implementation

class EnhancedFeaturedImage {
    constructor() {
        this.featuredData = null;
        this.isInitialized = false;
        this.retryCount = 0;
        this.maxRetries = 15;
        this.init();
    }

    async init() {
        console.log('Enhanced Featured Image: Initializing...');
        this.waitForReactAndInject();
    }

    waitForReactAndInject() {
        const checkReactReady = () => {
            const rootElement = document.getElementById('root');
            const hasContent = rootElement && rootElement.children.length > 0;
            const portfolioExists = document.querySelector('#portfolio, [id*="portfolio"], section');
            
            if (hasContent && portfolioExists && !this.isInitialized) {
                console.log('React ready, loading featured image...');
                this.loadAndRender();
            } else if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Waiting for React... attempt ${this.retryCount}/${this.maxRetries}`);
                setTimeout(checkReactReady, 1000);
            } else {
                console.log('Max retries reached, creating section anyway...');
                this.loadAndRender();
            }
        };

        checkReactReady();
    }

    async loadAndRender() {
        try {
            await this.loadFeaturedData();
            this.injectEnhancedSection();
            this.isInitialized = true;
            console.log('Enhanced Featured Image: Successfully initialized');
        } catch (error) {
            console.error('Error initializing enhanced featured image:', error);
            this.createFallbackSection();
        }
    }

    async loadFeaturedData() {
        try {
            const response = await fetch('/api/featured');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.featuredData = data;
            console.log('Loaded featured data:', this.featuredData);
        } catch (error) {
            console.error('Error loading featured image data:', error);
            // Use fallback data if API fails
            this.featuredData = {
                title: 'Featured Image',
                description: 'No featured image currently set',
                image: '',
                exif_data: {},
                categories: []
            };
        }
    }

    injectEnhancedSection() {
        // Find insertion point after portfolio section
        const insertionPoint = this.findInsertionPoint();
        
        if (insertionPoint) {
            console.log('Found insertion point, creating enhanced section...');
            this.createEnhancedSection(insertionPoint);
        } else {
            console.log('No insertion point found, appending to body...');
            this.createEnhancedSection(document.body);
        }
    }

    findInsertionPoint() {
        // Try multiple strategies to find a good insertion point
        const strategies = [
            // Look for about section to insert before it
            () => {
                const aboutSection = document.querySelector('#about, [class*="about"], section:has(h2:contains("About")), section:has(h1:contains("About"))');
                if (aboutSection) {
                    console.log('Found about section, will insert before it:', aboutSection);
                    return { element: aboutSection, insertBefore: true };
                }
                return null;
            },
            // Look for portfolio section to insert after it
            () => {
                const portfolioSection = document.querySelector('#portfolio, [class*="portfolio"]');
                if (portfolioSection) {
                    console.log('Found portfolio section, will insert after it:', portfolioSection);
                    return { element: portfolioSection, insertBefore: false };
                }
                return null;
            },
            // Look for any section
            () => {
                const sections = document.querySelectorAll('section');
                if (sections.length >= 2) {
                    console.log('Found sections, will insert after second section:', sections[1]);
                    return { element: sections[1], insertBefore: false };
                }
                return null;
            },
            // Fallback to main content area
            () => {
                const main = document.querySelector('main, #root');
                if (main) {
                    console.log('Fallback to main content area:', main);
                    return { element: main, insertBefore: false };
                }
                return null;
            }
        ];

        for (const strategy of strategies) {
            try {
                const result = strategy();
                if (result) {
                    return result;
                }
            } catch (e) {
                // Strategy failed, try next
            }
        }

        return null;
    }

    createEnhancedSection(insertionPoint) {
        // Remove any existing enhanced section
        const existing = document.getElementById('enhanced-featured-section');
        if (existing) {
            existing.remove();
        }

        // Remove redundant "Featured Image" section (old version)
        const redundantSections = document.querySelectorAll('section, div');
        redundantSections.forEach(section => {
            const heading = section.querySelector('h2, h3, h4');
            if (heading && heading.textContent.trim() === 'Featured Image') {
                console.log('Removing redundant Featured Image section:', section);
                section.remove();
            }
        });

        const enhancedContainer = document.createElement('section');
        enhancedContainer.id = 'enhanced-featured-section';
        enhancedContainer.className = 'enhanced-featured-section';
        enhancedContainer.innerHTML = this.generateEnhancedHTML();
        
        // Handle insertion based on insertionPoint type
        if (insertionPoint && typeof insertionPoint === 'object' && insertionPoint.element) {
            // New object-based insertion
            if (insertionPoint.insertBefore) {
                insertionPoint.element.parentNode.insertBefore(enhancedContainer, insertionPoint.element);
            } else {
                if (insertionPoint.element.nextSibling) {
                    insertionPoint.element.parentNode.insertBefore(enhancedContainer, insertionPoint.element.nextSibling);
                } else {
                    insertionPoint.element.parentNode.appendChild(enhancedContainer);
                }
            }
        } else if (insertionPoint) {
            // Legacy element-based insertion
            if (insertionPoint.nextSibling) {
                insertionPoint.parentNode.insertBefore(enhancedContainer, insertionPoint.nextSibling);
            } else {
                insertionPoint.parentNode.appendChild(enhancedContainer);
            }
        } else {
            // Fallback to body
            document.body.appendChild(enhancedContainer);
        }
        
        this.addEventListeners();
        console.log('Enhanced featured section created successfully');
    }

    createFallbackSection() {
        console.log('Creating fallback section...');
        const fallbackContainer = document.createElement('section');
        fallbackContainer.id = 'enhanced-featured-section';
        fallbackContainer.className = 'enhanced-featured-section';
        fallbackContainer.innerHTML = `
            <div class="enhanced-featured-container">
                <h2 class="featured-title">Featured Image</h2>
                <div class="no-exif">
                    <p>📸 Featured image system is loading...</p>
                    <p>Please refresh the page if this message persists.</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(fallbackContainer);
    }

    generateEnhancedHTML() {
        if (!this.featuredData || !this.featuredData.image) {
            return `
                <div class="enhanced-featured-container">
                    <h2 class="featured-title">Featured Image</h2>
                    <div class="no-exif">
                        <p>📸 No featured image currently set</p>
                        <p>Visit the admin panel to select a featured image from your portfolio.</p>
                    </div>
                </div>
            `;
        }

        const imageUrl = `/photography-assets/${this.featuredData.image}`;
        
        return `
            <div class="enhanced-featured-container">
                <h2 class="featured-title">Weekly Featured Image</h2>
                
                <div class="featured-content">
                    <div class="featured-image-wrapper" onclick="this.classList.toggle('fullscreen')">
                        <img src="${imageUrl}" 
                             alt="${this.featuredData.title}"
                             class="featured-image-large"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
                        <div class="image-error" style="display: none;">
                            <p>📷 Image not available</p>
                            <p>Please check the image file or contact the administrator.</p>
                        </div>
                        <div class="image-overlay">
                            <h3>${this.featuredData.title}</h3>
                            <p>${this.featuredData.description}</p>
                            ${this.featuredData.categories && this.featuredData.categories.length > 0 ? 
                                `<div class="image-categories">
                                    ${this.featuredData.categories.map(cat => `<span class="category-tag">${cat}</span>`).join('')}
                                </div>` : ''
                            }
                        </div>
                    </div>
                    
                    <div class="exif-data-panel">
                        <h4>📷 Technical Details</h4>
                        ${this.renderExifData()}
                    </div>
                </div>
                
                <div class="featured-actions">
                    <button onclick="window.open('${imageUrl}', '_blank')" 
                            class="action-btn view-full-btn">
                        🔍 Full Resolution in New Window
                    </button>
                </div>
            </div>
        `;
    }

    renderExifData() {
        if (!this.featuredData.exif_data || Object.keys(this.featuredData.exif_data).length === 0) {
            return `
                <div class="exif-group">
                    <h5>📸 Camera Settings</h5>
                    <p class="no-exif">📊 EXIF data extraction is being enhanced. Technical details will be available soon!</p>
                </div>
            `;
        }

        const exif = this.featuredData.exif_data;
        
        // Primary camera settings
        const primaryData = [
            { label: '📷 Camera', value: exif.camera || exif.make },
            { label: '🔍 Lens', value: exif.lens || exif.lens_model },
            { label: '⚪ Aperture', value: exif.aperture || exif.f_number },
            { label: '⏱️ Shutter Speed', value: exif.shutter_speed || exif.exposure_time },
            { label: '🎞️ ISO', value: exif.iso || exif.iso_speed },
            { label: '📏 Focal Length', value: exif.focal_length }
        ];

        // Additional technical data
        const additionalData = [
            { label: '📅 Date Taken', value: exif.date_taken || exif.datetime },
            { label: '💡 Exposure Mode', value: exif.exposure_mode },
            { label: '🌡️ White Balance', value: exif.white_balance },
            { label: '⚡ Flash', value: exif.flash },
            { label: '📐 Metering Mode', value: exif.metering_mode },
            { label: '📏 Image Size', value: exif.image_width && exif.image_height ? `${exif.image_width} × ${exif.image_height}` : null },
            { label: '🎨 Color Space', value: exif.color_space },
            { label: '💻 Software', value: exif.software },
            { label: '👤 Artist', value: exif.artist },
            { label: '©️ Copyright', value: exif.copyright }
        ];

        const renderDataGroup = (data, title) => {
            const validItems = data.filter(item => item.value && item.value !== 'Unknown' && item.value !== 'ISO Unknown');
            if (validItems.length === 0) return '';

            return `
                <div class="exif-group">
                    <h5>${title}</h5>
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

    renderImageInfo() {
        return `
            <div class="exif-group">
                <h5>ℹ️ Image Information</h5>
                <div class="exif-item">
                    <span class="exif-label">📂 Filename</span>
                    <span class="exif-value">${this.featuredData.image}</span>
                </div>
                <div class="exif-item">
                    <span class="exif-label">📅 Featured Since</span>
                    <span class="exif-value">${this.featuredData.set_date || 'Recently'}</span>
                </div>
                ${this.featuredData.categories && this.featuredData.categories.length > 0 ? `
                <div class="exif-item">
                    <span class="exif-label">🏷️ Categories</span>
                    <span class="exif-value">${this.featuredData.categories.join(', ')}</span>
                </div>
                ` : ''}
            </div>
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

        // Add share functionality with better error handling
        window.shareImage = () => {
            console.log('📱 Share Image button clicked');
            
            const shareUrl = `${window.location.origin}/website/featured-image`;
            const shareData = {
                title: `${this.featuredData.title} - Mind's Eye Photography`,
                text: this.featuredData.description,
                url: shareUrl
            };
            
            console.log('📤 Attempting to share:', shareData);
            
            // Try native Web Share API first
            if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
                navigator.share(shareData)
                    .then(() => {
                        console.log('✅ Successfully shared via Web Share API');
                    })
                    .catch((error) => {
                        console.log('❌ Web Share API failed:', error);
                        this.fallbackShare(shareUrl);
                    });
            } else {
                console.log('📋 Web Share API not available, using fallback');
                this.fallbackShare(shareUrl);
            }
        };
        
        // Fallback share method
        this.fallbackShare = (shareUrl) => {
            // Try clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(shareUrl)
                    .then(() => {
                        console.log('✅ URL copied to clipboard');
                        this.showShareSuccess('Featured image link copied to clipboard!');
                    })
                    .catch((error) => {
                        console.log('❌ Clipboard API failed:', error);
                        this.showShareFallback(shareUrl);
                    });
            } else {
                console.log('📋 Clipboard API not available');
                this.showShareFallback(shareUrl);
            }
        };
        
        // Show success message
        this.showShareSuccess = (message) => {
            // Create a temporary notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ff6b35;
                color: white;
                padding: 1rem 2rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000;
                font-weight: 600;
                animation: slideIn 0.3s ease-out;
            `;
            notification.textContent = message;
            
            // Add animation keyframes
            if (!document.getElementById('share-notification-styles')) {
                const style = document.createElement('style');
                style.id = 'share-notification-styles';
                style.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(notification);
            
            // Remove after 3 seconds
            setTimeout(() => {
                notification.remove();
            }, 3000);
        };
        
        // Show fallback dialog
        this.showShareFallback = (shareUrl) => {
            const message = `Share this featured image:\n\n${shareUrl}`;
            alert(message);
            console.log('📢 Showed fallback share dialog');
        };
    }
}

// Initialize when DOM is ready with multiple fallbacks
function initializeEnhancedFeaturedImage() {
    console.log('Initializing Enhanced Featured Image...');
    new EnhancedFeaturedImage();
}

// Multiple initialization strategies
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(initializeEnhancedFeaturedImage, 2000);
    });
} else {
    setTimeout(initializeEnhancedFeaturedImage, 2000);
}

// Also try after window load
window.addEventListener('load', () => {
    setTimeout(() => {
        if (!document.getElementById('enhanced-featured-section')) {
            console.log('Fallback initialization...');
            initializeEnhancedFeaturedImage();
        }
    }, 3000);
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedFeaturedImage;
}

