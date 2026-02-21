# Blog

A minimal, research-focused blog for ML/MLOps content. Designed to appeal to both academic and industry audiences.

## Features

- **Modern, minimalist design** with a clean aesthetic
- **Markdown support** for writing posts
- **LaTeX equations** via KaTeX
- **Syntax highlighting** via highlight.js
- **Dark mode** support (automatic based on system preference)
- **RSS feed** for subscribers
- **GitHub Pages compatible** - fully static

## Structure

```
blog/
├── index.html          # Homepage with recent posts
├── about.html          # About page
├── research.html       # Publications and research
├── archive.html        # All posts archive
├── feed.xml            # RSS feed
├── build.py            # Markdown to HTML converter
├── css/
│   ├── style.css       # Main styles
│   ├── post.css        # Post-specific styles
│   └── syntax.css      # Code syntax highlighting
├── js/
│   ├── main.js         # Site interactions
│   └── markdown-renderer.js  # Client-side markdown (optional)
├── posts/
│   ├── template.md     # Post template
│   ├── example-post.md # Example markdown post
│   └── *.html          # Rendered posts
└── images/
    └── *.svg           # Post images
```

## Writing Posts

### Option 1: Write in HTML directly

Create a new `.html` file in `posts/` using an existing post as a template.

### Option 2: Write in Markdown

1. Create a new `.md` file in `posts/`
2. Add YAML front matter:

```yaml
---
title: Your Post Title
date: 2026-02-08
category: MLOps
tags: [feature-engineering, infrastructure]
excerpt: A brief description of your post.
---
```

3. Write your content in markdown
4. Run the build script:

```bash
python build.py
```

### Markdown Features

**Code blocks** with syntax highlighting:

~~~markdown
```python
def train_model(X, y):
    return model.fit(X, y)
```
~~~

**LaTeX equations**:

- Inline: `$f(x) = x^2$`
- Display: `$$\nabla_\theta J(\theta)$$`

**Images**:

```markdown
![Caption text](../images/your-image.png)
```

**Callouts**:

```markdown
> [!NOTE]
> This is a note callout.

> [!WARNING]
> This is a warning callout.
```

## Local Development

Start a local server:

```bash
python build.py --serve
```

Or use any static file server:

```bash
python -m http.server 8000
```

Visit `http://localhost:8000`

## Deploying to GitHub Pages

1. Create a repository (e.g., `username.github.io` or `blog`)
2. Push the contents of this folder
3. Enable GitHub Pages in repository settings
4. (Optional) Configure custom domain

The site is fully static and requires no build step on GitHub - just push and serve.

## Customization

### Colors & Theme

Edit CSS variables in `css/style.css`:

```css
:root {
    --accent: #C45D3A;           /* Primary accent color */
    --accent-secondary: #2D5A4A; /* Secondary accent */
    --bg-primary: #FDFBF7;       /* Background */
    --text-primary: #1A1A1A;     /* Text color */
}
```

### Fonts

The site uses:
- **Cormorant Garamond** - Display/headings
- **Source Sans 3** - Body text
- **JetBrains Mono** - Code and technical text

Change fonts by updating the Google Fonts import in HTML files.

### Adding Pages

Copy an existing page template and modify. Update navigation links in all pages.

## Dependencies

External CDN resources (no npm required):
- KaTeX for LaTeX rendering
- highlight.js for code syntax highlighting
- Google Fonts for typography

All dependencies are loaded from CDNs - no build process needed.

## License

MIT
