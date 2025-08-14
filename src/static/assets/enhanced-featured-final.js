// Enhanced Featured Image Component - Final Version with EXIF Badge Styling
// Professional Photography Showcase with Orange Badge EXIF Data
class EnhancedFeaturedImage {
    constructor() {
        this.featuredData = null;
        this.currentImageIndex = 0;
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.init();
    }

    async init() {
        console.log('🎯 Enhanced Featured Image Component initializing...');
        try {
            await this.loadFeaturedData();
            this.injectEnhancedSection();
            this.addEventListeners();
            console.log('✅ Enhanced featured section created successfully');
        } catch (error) {
            console.error('❌ Failed to initialize enhanced featured section:', error);
            this.createFallbackSection();
        }
    }

    async loadFeaturedData() {
        try {
            const response = await fetch('/api/featured-image');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.featuredData = await response.json();
            console.log('📸 Featured data loaded:', this.featuredData);
        } catch (error) {
            console.error('Failed to load featured data:', error);
            throw error;
        }
    }

    findInsertionPoint() {
        // Try multiple strategies to find a good insertion point
        const strategies = [
            // Look for about section to insert before it
            () => {
                const aboutSection = document.querySelector('#about, [class*="about"], section:has(h2:contains("About"))');
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
                console.log('Strategy failed, trying next');
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
        } else if (insertionPoint && insertionPoint.nextSibling) {
            // Legacy element-based insertion
            insertionPoint.parentNode.insertBefore(enhancedContainer, insertionPoint.nextSibling);
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
                    <p>📸 No featured image currently set</p>
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
                    <h2 class="featured-title">Weekly Featured Image</h2>
                    <div class="featured-content">
                        <div class="featured-image-wrapper" onclick="this.classList.toggle('fullscreen')">
                            <img src="${imageUrl}" 
                                 alt="${this.featuredData.title}"
                                 class="featured-image-large"
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
                        </div>
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
                        
                        <div class="image-overlay">
                            <h3>${this.featuredData.title}</h3>
                            <p>${this.featuredData.description || 'Professional photography showcase'}</p>
                        </div>
                    </div>
                    
                    <div class="exif-data-panel">
                        <h4>
                            <span class="exif-icon">📷</span>
                            Technical Details
                        </h4>
                        ${this.generateExifBadges()}
                        ${this.generateStorySection()}
                    </div>
                </div>
            </div>
        `;
    }

    // NEW: Generate EXIF data as orange badges instead of plain text
    generateExifBadges() {
        if (!this.featuredData || !this.featuredData.exif) {
            return `
                <div class="exif-badges-container">
                    <div class="exif-badge camera">
                        <span class="exif-badge-icon">📷</span>
                        Camera: Professional DSLR
                    </div>
                    <div class="exif-badge lens">
                        <span class="exif-badge-icon">🔍</span>
                        Lens: Professional Grade
                    </div>
                    <div class="exif-badge settings">
                        <span class="exif-badge-icon">⚙️</span>
                        Settings: Optimized
                    </div>
                </div>
            `;
        }

        const exif = this.featuredData.exif;
        let badgesHTML = '<div class="exif-badges-container">';

        // Camera badge
        if (exif.camera) {
            badgesHTML += `
                <div class="exif-badge camera">
                    <span class="exif-badge-icon">📷</span>
                    ${exif.camera}
                </div>
            `;
        }

        // Lens badge
        if (exif.lens) {
            badgesHTML += `
                <div class="exif-badge lens">
                    <span class="exif-badge-icon">🔍</span>
                    ${exif.lens}
                </div>
            `;
        }

        // Settings badges
        if (exif.aperture) {
            badgesHTML += `
                <div class="exif-badge settings">
                    <span class="exif-badge-icon">🔆</span>
                    f/${exif.aperture}
                </div>
            `;
        }

        if (exif.shutter_speed) {
            badgesHTML += `
                <div class="exif-badge settings">
                    <span class="exif-badge-icon">⏱️</span>
                    ${exif.shutter_speed}
                </div>
            `;
        }

        if (exif.iso) {
            badgesHTML += `
                <div class="exif-badge settings">
                    <span class="exif-badge-icon">🎯</span>
                    ISO ${exif.iso}
                </div>
            `;
        }

        if (exif.focal_length) {
            badgesHTML += `
                <div class="exif-badge settings">
                    <span class="exif-badge-icon">📏</span>
                    ${exif.focal_length}mm
                </div>
            `;
        }

        // Location badge
        if (exif.location) {
            badgesHTML += `
                <div class="exif-badge location">
                    <span class="exif-badge-icon">📍</span>
                    ${exif.location}
                </div>
            `;
        }

        badgesHTML += '</div>';
        return badgesHTML;
    }

    generateStorySection() {
        if (!this.featuredData || !this.featuredData.story) {
            return '';
        }

        return `
            <div class="story-section">
                <h5>📖 Story Behind the Shot</h5>
                <p>${this.featuredData.story}</p>
            </div>
        `;
    }

    injectEnhancedSection() {
        // Find insertion point after portfolio section
        const insertionPoint = this.findInsertionPoint();
        
        if (insertionPoint) {
            console.log('Found insertion point, creating enhanced section...', insertionPoint);
            this.createEnhancedSection(insertionPoint);
        } else {
            console.log('No insertion point found, appending to body...');
            this.createEnhancedSection(document.body);
        }
    }

    addEventListeners() {
        console.log('Enhanced featured section created successfully');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new EnhancedFeaturedImage();
    });
} else {
    new EnhancedFeaturedImage();
}

