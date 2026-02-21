/**
 * Main JavaScript for the blog
 * Handles markdown rendering, syntax highlighting, LaTeX, and interactions
 */

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initAnimations();
    initCodeCopy();
    initTOC();
});

/**
 * Intersection Observer for scroll animations
 */
function initAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements with animation classes
    document.querySelectorAll('.post-card, .topic-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
}

/**
 * Code block copy functionality
 */
function initCodeCopy() {
    document.querySelectorAll('.code-copy').forEach(button => {
        button.addEventListener('click', async () => {
            const codeBlock = button.closest('.code-header').nextElementSibling;
            const code = codeBlock.querySelector('code').textContent;

            try {
                await navigator.clipboard.writeText(code);
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });
}

/**
 * Table of Contents active state
 */
function initTOC() {
    const toc = document.querySelector('.toc');
    if (!toc) return;

    const headings = document.querySelectorAll('.post-content h2, .post-content h3');
    const tocLinks = toc.querySelectorAll('a');

    const observerOptions = {
        root: null,
        rootMargin: '-80px 0px -80% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                tocLinks.forEach(link => link.classList.remove('active'));
                const activeLink = toc.querySelector(`a[href="#${entry.target.id}"]`);
                if (activeLink) activeLink.classList.add('active');
            }
        });
    }, observerOptions);

    headings.forEach(heading => observer.observe(heading));
}

/**
 * Smooth scroll for anchor links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: fadeInUp 0.5s ease forwards;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);
