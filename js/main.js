/**
 * Main JavaScript for the blog
 * Handles markdown rendering, syntax highlighting, LaTeX, and interactions
 */

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initCodeCopy();
    initTOC();
});

/**
 * Theme toggle functionality (Light / Dark)
 */
function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle');
    if (!toggleBtn) return;

    function getStoredTheme() {
        try {
            const t = localStorage.getItem('theme');
            if (t === 'dark' || t === 'light') return t;
        } catch (e) {}
        try {
            const m = document.cookie.match(/(?:^|;\s*)theme=([^;]*)/);
            if (m && (m[1] === 'dark' || m[1] === 'light')) return m[1];
        } catch (e) {}
        return 'light'; // Default to light mode
    }

    function setStoredTheme(theme) {
        try {
            localStorage.setItem('theme', theme);
        } catch (e) {}
        try {
            document.cookie = "theme=" + encodeURIComponent(theme) + ";path=/;max-age=31536000;SameSite=Lax";
        } catch (e) {}
    }

    // Ensure state is set on DOM ready
    const initialTheme = getStoredTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);

    toggleBtn.addEventListener('click', () => {
        const active = document.documentElement.getAttribute('data-theme') || getStoredTheme();
        const nextTheme = active === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', nextTheme);
        setStoredTheme(nextTheme);
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
