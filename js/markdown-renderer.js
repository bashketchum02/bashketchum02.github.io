/**
 * Markdown Renderer with LaTeX and Syntax Highlighting
 * Uses marked.js for markdown, highlight.js for code, and KaTeX for math
 */

class MarkdownRenderer {
    constructor(options = {}) {
        this.options = {
            enableMath: true,
            enableHighlight: true,
            enableSmartypants: true,
            ...options
        };

        this.initMarked();
    }

    initMarked() {
        // Configure marked with custom renderer
        const renderer = new marked.Renderer();

        // Custom heading renderer with IDs for TOC
        renderer.heading = (text, level) => {
            const slug = this.slugify(text);
            return `<h${level} id="${slug}">${text}</h${level}>`;
        };

        // Custom code block renderer
        renderer.code = (code, language) => {
            if (language === 'math' || language === 'latex') {
                return this.renderBlockMath(code);
            }

            const highlighted = this.options.enableHighlight && window.hljs
                ? hljs.highlight(code, { language: language || 'plaintext', ignoreIllegals: true }).value
                : this.escapeHtml(code);

            const langLabel = language ? `<div class="code-header"><span class="code-lang">${language}</span><button class="code-copy">Copy</button></div>` : '';

            return `${langLabel}<pre><code class="hljs ${language || ''}">${highlighted}</code></pre>`;
        };

        // Custom inline code - check for math
        renderer.codespan = (code) => {
            if (code.startsWith('$') && code.endsWith('$')) {
                return this.renderInlineMath(code.slice(1, -1));
            }
            return `<code>${this.escapeHtml(code)}</code>`;
        };

        // Custom image renderer with lazy loading and figures
        renderer.image = (href, title, text) => {
            const titleAttr = title ? ` title="${title}"` : '';
            const figcaption = text ? `<figcaption>${text}</figcaption>` : '';

            return `<figure>
                <img src="${href}" alt="${text || ''}"${titleAttr} loading="lazy">
                ${figcaption}
            </figure>`;
        };

        // Custom link renderer - external links open in new tab
        renderer.link = (href, title, text) => {
            const isExternal = href.startsWith('http') && !href.includes(window.location.hostname);
            const attrs = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
            const titleAttr = title ? ` title="${title}"` : '';
            return `<a href="${href}"${titleAttr}${attrs}>${text}</a>`;
        };

        // Custom blockquote for callouts
        renderer.blockquote = (quote) => {
            // Check for callout syntax: > [!NOTE], > [!WARNING], etc.
            const calloutMatch = quote.match(/^\s*<p>\[!(NOTE|WARNING|INFO|TIP)\]<\/p>/);
            if (calloutMatch) {
                const type = calloutMatch[1].toLowerCase();
                const content = quote.replace(calloutMatch[0], '');
                return `<div class="${type}">${content}</div>`;
            }
            return `<blockquote>${quote}</blockquote>`;
        };

        marked.setOptions({
            renderer,
            gfm: true,
            breaks: false,
            pedantic: false,
            smartypants: this.options.enableSmartypants
        });
    }

    /**
     * Render markdown to HTML
     */
    render(markdown) {
        // Pre-process math blocks before markdown parsing
        let processed = this.preprocessMath(markdown);

        // Parse markdown
        let html = marked.parse(processed);

        // Post-process to restore math
        html = this.postprocessMath(html);

        return html;
    }

    /**
     * Pre-process to protect math blocks from markdown parser
     */
    preprocessMath(text) {
        if (!this.options.enableMath) return text;

        this.mathBlocks = [];
        let counter = 0;

        // Protect display math: $$ ... $$
        text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, math) => {
            this.mathBlocks[counter] = { type: 'display', content: math.trim() };
            return `%%MATH_BLOCK_${counter++}%%`;
        });

        // Protect inline math: $ ... $ (not escaped)
        text = text.replace(/(?<![\\$])\$([^\$\n]+?)\$/g, (match, math) => {
            this.mathBlocks[counter] = { type: 'inline', content: math.trim() };
            return `%%MATH_BLOCK_${counter++}%%`;
        });

        return text;
    }

    /**
     * Post-process to render math blocks
     */
    postprocessMath(html) {
        if (!this.options.enableMath || !this.mathBlocks) return html;

        return html.replace(/%%MATH_BLOCK_(\d+)%%/g, (match, index) => {
            const block = this.mathBlocks[parseInt(index)];
            if (!block) return match;

            return block.type === 'display'
                ? this.renderBlockMath(block.content)
                : this.renderInlineMath(block.content);
        });
    }

    /**
     * Render display math using KaTeX
     */
    renderBlockMath(latex) {
        if (typeof katex === 'undefined') {
            return `<div class="math-block">${this.escapeHtml(latex)}</div>`;
        }

        try {
            const rendered = katex.renderToString(latex, {
                displayMode: true,
                throwOnError: false,
                trust: true
            });
            return `<div class="math-block">${rendered}</div>`;
        } catch (e) {
            console.error('KaTeX error:', e);
            return `<div class="math-block math-error">${this.escapeHtml(latex)}</div>`;
        }
    }

    /**
     * Render inline math using KaTeX
     */
    renderInlineMath(latex) {
        if (typeof katex === 'undefined') {
            return `<span class="math-inline">${this.escapeHtml(latex)}</span>`;
        }

        try {
            const rendered = katex.renderToString(latex, {
                displayMode: false,
                throwOnError: false,
                trust: true
            });
            return `<span class="math-inline">${rendered}</span>`;
        } catch (e) {
            console.error('KaTeX error:', e);
            return `<span class="math-inline math-error">${this.escapeHtml(latex)}</span>`;
        }
    }

    /**
     * Generate URL-friendly slug from text
     */
    slugify(text) {
        return text
            .toLowerCase()
            .replace(/<[^>]*>/g, '') // Remove HTML tags
            .replace(/[^\w\s-]/g, '') // Remove special chars
            .replace(/\s+/g, '-') // Replace spaces with hyphens
            .replace(/-+/g, '-') // Replace multiple hyphens
            .trim();
    }

    /**
     * Escape HTML entities
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * Generate Table of Contents from headings
     */
    generateTOC(container) {
        const headings = container.querySelectorAll('h2, h3');
        if (headings.length === 0) return null;

        const toc = document.createElement('nav');
        toc.className = 'toc';
        toc.innerHTML = '<h4 class="toc-title">Contents</h4>';

        const list = document.createElement('ul');
        list.className = 'toc-list';

        headings.forEach(heading => {
            const li = document.createElement('li');
            li.className = `toc-${heading.tagName.toLowerCase()}`;

            const a = document.createElement('a');
            a.href = `#${heading.id}`;
            a.textContent = heading.textContent;

            li.appendChild(a);
            list.appendChild(li);
        });

        toc.appendChild(list);
        return toc;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownRenderer;
}
