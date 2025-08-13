// Enhanced Featured Image Component with EXIF Data
class EnhancedFeaturedImage {
    constructor() {
        this.featuredData = null;
        this.init();
    }

    async init() {
        await this.loadFeaturedData();
        this.renderEnhancedFeaturedSection();
    }

    async loadFeaturedData() {
        try {
            const response = await fetch('/api/featured');
            this.featuredData = await response.json();
        } catch (error) {
            console.error('Error loading featured image data:', error);
        }
    }

    renderEnhancedFeaturedSection() {
        const featuredSection = document.querySelector('#featured-image-section');
        if (!featuredSection || !this.featuredData) return;

        featuredSection.innerHTML = `
            <div class="enhanced-featured-container">
                <h2 class="featured-title">Featured Image</h2>
                
                <div class="featured-content">
                    <div class="featured-image-wrapper">
                        <img src="/photography-assets/${this.featuredData.image}" 
                             alt="${this.featuredData.title}"
                             class="featured-image-large"
                             onclick="this.parentElement.parentElement.classList.toggle('fullscreen')" />
                        <div class="image-overlay">
                            <h3>${this.featuredData.title}</h3>
                            <p>${this.featuredData.description}</p>
                        </div>
                    </div>
                    
                    <div class="exif-data-panel">
                        <h4>Technical Details</h4>
                        ${this.renderExifData()}
                    </div>
                </div>
            </div>
        `;

        this.addStyles();
    }

    renderExifData() {
        if (!this.featuredData.exif_data) {
            return '<p class="no-exif">No technical data available</p>';
        }

        const exif = this.featuredData.exif_data;
        const primaryData = [
            { label: 'Camera', value: exif.camera },
            { label: 'Lens', value: exif.lens },
            { label: 'Aperture', value: exif.aperture },
            { label: 'Shutter Speed', value: exif.shutter_speed },
            { label: 'ISO', value: exif.iso },
            { label: 'Focal Length', value: exif.focal_length }
        ];

        const additionalData = [
            { label: 'Date Taken', value: exif.date_taken },
            { label: 'Exposure Mode', value: exif.exposure_mode },
            { label: 'White Balance', value: exif.white_balance },
            { label: 'Flash', value: exif.flash },
            { label: 'Metering Mode', value: exif.metering_mode },
            { label: 'Image Size', value: `${exif.image_width} × ${exif.image_height}` },
            { label: 'Color Space', value: exif.color_space },
            { label: 'Software', value: exif.software },
            { label: 'Artist', value: exif.artist },
            { label: 'Copyright', value: exif.copyright }
        ];

        return `
            <div class="exif-primary">
                ${primaryData.map(item => 
                    item.value && item.value !== 'Unknown' ? 
                    `<div class="exif-item">
                        <span class="exif-label">${item.label}:</span>
                        <span class="exif-value">${item.value}</span>
                    </div>` : ''
                ).join('')}
            </div>
            
            <div class="exif-additional">
                <h5>Additional Information</h5>
                ${additionalData.map(item => 
                    item.value && item.value !== 'Unknown' ? 
                    `<div class="exif-item">
                        <span class="exif-label">${item.label}:</span>
                        <span class="exif-value">${item.value}</span>
                    </div>` : ''
                ).join('')}
            </div>
        `;
    }

    addStyles() {
        if (document.getElementById('enhanced-featured-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'enhanced-featured-styles';
        styles.textContent = `
            .enhanced-featured-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }

            .featured-title {
                font-size: 2.5rem;
                color: #ff6b35;
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }

            .featured-content {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 2rem;
                align-items: start;
            }

            .featured-image-wrapper {
                position: relative;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                cursor: pointer;
                transition: transform 0.3s ease;
            }

            .featured-image-wrapper:hover {
                transform: scale(1.02);
            }

            .featured-image-large {
                width: 100%;
                height: auto;
                display: block;
                transition: transform 0.3s ease;
            }

            .image-overlay {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
                color: white;
                padding: 2rem;
                transform: translateY(100%);
                transition: transform 0.3s ease;
            }

            .featured-image-wrapper:hover .image-overlay {
                transform: translateY(0);
            }

            .image-overlay h3 {
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
                color: #ff6b35;
            }

            .image-overlay p {
                font-size: 1rem;
                line-height: 1.4;
                opacity: 0.9;
            }

            .exif-data-panel {
                background: rgba(0, 0, 0, 0.6);
                border-radius: 8px;
                padding: 1.5rem;
                border: 1px solid #333;
            }

            .exif-data-panel h4 {
                color: #ff6b35;
                font-size: 1.3rem;
                margin-bottom: 1rem;
                border-bottom: 2px solid #ff6b35;
                padding-bottom: 0.5rem;
            }

            .exif-data-panel h5 {
                color: #ccc;
                font-size: 1.1rem;
                margin: 1.5rem 0 1rem 0;
                border-bottom: 1px solid #444;
                padding-bottom: 0.3rem;
            }

            .exif-primary {
                margin-bottom: 1.5rem;
            }

            .exif-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid #333;
            }

            .exif-item:last-child {
                border-bottom: none;
            }

            .exif-label {
                font-weight: 600;
                color: #ccc;
                font-size: 0.9rem;
            }

            .exif-value {
                color: #fff;
                font-weight: 500;
                text-align: right;
                font-size: 0.9rem;
            }

            .no-exif {
                color: #888;
                font-style: italic;
                text-align: center;
                padding: 2rem;
            }

            /* Fullscreen mode */
            .enhanced-featured-container.fullscreen {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 1000;
                max-width: none;
                margin: 0;
                border-radius: 0;
                background: rgba(0, 0, 0, 0.95);
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .enhanced-featured-container.fullscreen .featured-content {
                grid-template-columns: 1fr;
                max-width: 90vw;
                max-height: 90vh;
            }

            .enhanced-featured-container.fullscreen .featured-image-large {
                max-height: 80vh;
                object-fit: contain;
            }

            .enhanced-featured-container.fullscreen .exif-data-panel {
                display: none;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .featured-content {
                    grid-template-columns: 1fr;
                    gap: 1rem;
                }

                .enhanced-featured-container {
                    padding: 1rem;
                }

                .featured-title {
                    font-size: 2rem;
                }

                .exif-item {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 0.25rem;
                }

                .exif-value {
                    text-align: left;
                }
            }
        `;

        document.head.appendChild(styles);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EnhancedFeaturedImage();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedFeaturedImage;
}

