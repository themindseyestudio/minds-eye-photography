// Navigation Fix Script - Updates Featured Photo menu link to point to Weekly Featured Image section

class NavigationFixer {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.fixNavigation());
        } else {
            this.fixNavigation();
        }
    }

    fixNavigation() {
        console.log('🔧 Navigation Fixer: Starting navigation link fixes...');
        
        // Try multiple times to catch dynamically loaded navigation
        this.attemptFix();
        setTimeout(() => this.attemptFix(), 1000);
        setTimeout(() => this.attemptFix(), 3000);
        setTimeout(() => this.attemptFix(), 5000);
    }

    attemptFix() {
        // Find all navigation links that might be "Featured Photo"
        const navLinks = document.querySelectorAll('a, button, [role="button"]');
        let fixed = false;

        navLinks.forEach(link => {
            const text = link.textContent?.trim();
            if (text === 'Featured Photo' || text === 'Featured Image') {
                console.log('🎯 Found Featured Photo link:', link);
                
                // Update the link to scroll to enhanced featured section
                link.onclick = (e) => {
                    e.preventDefault();
                    this.scrollToFeaturedSection();
                };
                
                // Also update href if it exists
                if (link.href) {
                    link.href = '#enhanced-featured-section';
                }
                
                fixed = true;
                console.log('✅ Fixed Featured Photo navigation link');
            }
        });

        if (!fixed) {
            console.log('⚠️ Featured Photo navigation link not found yet, will retry...');
        }
    }

    scrollToFeaturedSection() {
        console.log('📍 Scrolling to Weekly Featured Image section...');
        
        // Try to find the enhanced featured section
        const enhancedSection = document.getElementById('enhanced-featured-section');
        if (enhancedSection) {
            enhancedSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
            console.log('✅ Scrolled to enhanced featured section');
            return;
        }

        // Fallback: look for any section with "Weekly Featured Image" text
        const sections = document.querySelectorAll('section, div');
        for (const section of sections) {
            const heading = section.querySelector('h1, h2, h3, h4');
            if (heading && heading.textContent.includes('Weekly Featured Image')) {
                section.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
                console.log('✅ Scrolled to Weekly Featured Image section (fallback)');
                return;
            }
        }

        console.log('⚠️ Could not find Weekly Featured Image section to scroll to');
    }
}

// Initialize the navigation fixer
new NavigationFixer();

