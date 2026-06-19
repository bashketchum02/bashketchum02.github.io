#!/usr/bin/env python3
"""
Blog Build Script

A simple static site generator that converts markdown posts to HTML
and automatically updates the index, archive, and RSS feed.

Usage:
    python build.py              # Build all posts
    python build.py --watch      # Watch for changes and rebuild
    python build.py --serve      # Build and start local server
    python build.py --serve --watch  # Serve with live reload
"""

import os
import re
import yaml
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from html import escape

# Try to import markdown library
try:
    import markdown
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.toc import TocExtension
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    print("Note: Install python-markdown for better rendering: pip install markdown")


class BlogBuilder:
    def __init__(self, source_dir: str = "posts", output_dir: str = "posts"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.posts = []
        self.site_name = "Bala"
        self.site_url = "https://bashketchum02.github.io"
        self.site_description = "Bala's notes on engineering, economics, policy, and complex systems."

    def parse_front_matter(self, content: str) -> tuple[dict, str]:
        """Extract YAML front matter from markdown content."""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    front_matter = yaml.safe_load(parts[1])
                    return front_matter or {}, parts[2].strip()
                except yaml.YAMLError:
                    pass
        return {}, content

    def process_latex(self, content: str) -> str:
        """Protect LaTeX from markdown processing."""
        # Protect display math
        content = re.sub(
            r'\$\$(.*?)\$\$',
            lambda m: f'<div class="math-block">$${m.group(1)}$$</div>',
            content,
            flags=re.DOTALL
        )
        # Protect inline math
        content = re.sub(
            r'(?<![\\$])\$([^\$\n]+?)\$',
            lambda m: f'<span class="math-inline">${m.group(1)}$</span>',
            content
        )
        return content

    def render_markdown(self, content: str) -> str:
        """Convert markdown to HTML."""
        if HAS_MARKDOWN:
            md = markdown.Markdown(extensions=[
                'fenced_code',
                'tables',
                'toc',
                'smarty',
                'attr_list',
            ])
            return md.convert(content)
        else:
            return self.basic_markdown(content)

    def basic_markdown(self, content: str) -> str:
        """Basic markdown processing for when library is unavailable."""
        lines = content.split('\n')
        html_lines = []
        in_code_block = False
        code_lang = ''
        code_content = []
        in_list = False

        for line in lines:
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    code = '\n'.join(code_content)
                    lang_class = f'language-{code_lang}' if code_lang else ''
                    header = f'<div class="code-header"><span class="code-lang">{code_lang}</span><button class="code-copy">Copy</button></div>' if code_lang else ''
                    html_lines.append(f'{header}<pre><code class="hljs {lang_class}">{self.escape_html(code)}</code></pre>')
                    in_code_block = False
                    code_content = []
                else:
                    in_code_block = True
                    code_lang = line[3:].strip()
                continue

            if in_code_block:
                code_content.append(line)
                continue

            # Headings
            if line.startswith('#### '):
                slug = self.slugify(line[5:])
                html_lines.append(f'<h4 id="{slug}">{line[5:]}</h4>')
            elif line.startswith('### '):
                slug = self.slugify(line[4:])
                html_lines.append(f'<h3 id="{slug}">{line[4:]}</h3>')
            elif line.startswith('## '):
                slug = self.slugify(line[3:])
                html_lines.append(f'<h2 id="{slug}">{line[3:]}</h2>')
            elif line.startswith('# '):
                slug = self.slugify(line[2:])
                html_lines.append(f'<h1 id="{slug}">{line[2:]}</h1>')
            # Horizontal rule
            elif line.strip() == '---' or line.strip() == '***':
                html_lines.append('<hr>')
            # Blockquotes / Callouts
            elif line.startswith('> '):
                quote_content = line[2:]
                if quote_content.startswith('[!NOTE]'):
                    html_lines.append(f'<div class="note">{quote_content[7:]}</div>')
                elif quote_content.startswith('[!WARNING]'):
                    html_lines.append(f'<div class="warning">{quote_content[10:]}</div>')
                elif quote_content.startswith('[!INFO]'):
                    html_lines.append(f'<div class="info">{quote_content[7:]}</div>')
                else:
                    html_lines.append(f'<blockquote><p>{self.process_inline(quote_content)}</p></blockquote>')
            # Lists
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{self.process_inline(line[2:])}</li>')
            elif re.match(r'^\d+\. ', line):
                if not in_list:
                    html_lines.append('<ol>')
                    in_list = True
                html_lines.append(f'<li>{self.process_inline(re.sub(r"^\d+\. ", "", line))}</li>')
            elif line.strip() == '':
                if in_list:
                    html_lines.append('</ul>' if html_lines[-1].startswith('<li>') else '</ol>')
                    in_list = False
                html_lines.append('')
            # Regular paragraph
            elif line.strip():
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{self.process_inline(line)}</p>')

        if in_list:
            html_lines.append('</ul>')

        return '\n'.join(html_lines)

    def process_inline(self, text: str) -> str:
        """Process inline markdown elements."""
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Code
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        # Links
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        # Images
        text = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<figure><img src="\2" alt="\1"><figcaption>\1</figcaption></figure>', text)
        return text

    def escape_html(self, text: str) -> str:
        """Escape HTML entities."""
        return escape(text)

    def slugify(self, text: str) -> str:
        """Generate URL-friendly slug."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', '-', text)
        return text.strip('-')

    def generate_toc(self, content: str) -> str:
        """Generate table of contents HTML."""
        headings = re.findall(r'<h([1234])[^>]*id="([^"]+)"[^>]*>(.+?)</h\1>', content)
        if not headings:
            return ''

        min_level = min(int(h[0]) for h in headings)
        toc_html = '<aside class="toc"><h4 class="toc-title">Contents</h4><ul class="toc-list">'
        for level, slug, text in headings:
            depth = int(level) - min_level
            class_name = f'toc-sub' if depth > 0 else ''
            toc_html += f'<li class="{class_name}"><a href="#{slug}">{text}</a></li>'
        toc_html += '</ul></aside>'
        return toc_html

    def format_date(self, date) -> str:
        """Format date for display."""
        if hasattr(date, 'strftime'):  # datetime or date object
            return date.strftime('%Y.%m.%d')
        elif isinstance(date, str):
            return date.replace('-', '.')
        return str(date)

    def format_date_rss(self, date) -> str:
        """Format date for RSS feed."""
        if isinstance(date, datetime):
            return date.strftime('%a, %d %b %Y 00:00:00 +0000')
        elif isinstance(date, str):
            try:
                dt = datetime.strptime(date, '%Y-%m-%d')
                return dt.strftime('%a, %d %b %Y 00:00:00 +0000')
            except:
                return date
        return str(date)

    def render_post(self, md_path: Path) -> Optional[dict]:
        """Render a single markdown post to HTML."""
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        front_matter, body = self.parse_front_matter(content)

        if not front_matter.get('title'):
            print(f"Skipping {md_path}: No title in front matter")
            return None

        # Process LaTeX before markdown
        body = self.process_latex(body)

        # Render markdown
        html_content = self.render_markdown(body)

        # Generate TOC
        toc_html = self.generate_toc(html_content)

        # Build the full HTML page
        post_html = self.build_post_page(front_matter, html_content, toc_html)

        # Write output
        output_filename = md_path.stem + '.html'
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(post_html)

        print(f"  Built: {output_path}")

        return {
            'title': front_matter.get('title'),
            'date': front_matter.get('date'),
            'date_display': self.format_date(front_matter.get('date', '')),
            'category': front_matter.get('category', 'General'),
            'tags': front_matter.get('tags', []),
            'excerpt': front_matter.get('excerpt', ''),
            'slug': md_path.stem,
            'path': f'posts/{output_filename}',
        }

    def build_post_page(self, meta: dict, content: str, toc: str) -> str:
        """Build complete HTML page for a post."""
        title = meta.get('title', 'Untitled')
        date = self.format_date(meta.get('date', datetime.now().strftime('%Y-%m-%d')))
        category = meta.get('category', 'General')
        excerpt = meta.get('excerpt', '')
        tags = meta.get('tags', [])

        tags_html = ''.join(f'<span class="tag">{tag}</span>' for tag in tags)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.escape_html(title)} | {self.site_name}</title>
    <meta name="description" content="{self.escape_html(excerpt)}">

    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../css/post.css">
    <link rel="stylesheet" href="../css/syntax.css">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,520;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/default.min.css">
    <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
</head>
<body>
    <div class="grain-overlay"></div>

    <header class="site-header">
        <nav class="nav-container">
            <a href="../index.html" class="logo">
                <span class="logo-symbol">λ</span>
                <span class="logo-text">bala</span>
            </a>
            <div class="nav-links">
                <a href="../index.html" class="nav-link active">Writing</a>
                <a href="../about.html" class="nav-link">About</a>
            </div>
        </nav>
    </header>

    <main class="main-content">
        <article>
            <header class="post-header">
                <div class="post-meta">
                    <time class="post-date">{date}</time>
                    <span class="post-category">{category}</span>
                </div>
                <h1 class="post-title">{self.escape_html(title)}</h1>
                <p class="post-excerpt">{self.escape_html(excerpt)}</p>
            </header>

            <div class="post-layout">
                <div class="post-content">
                    {content}

                    <div class="post-tags">
                        {tags_html}
                    </div>
                </div>

                {toc}
            </div>
        </article>
    </main>

    <footer class="site-footer">
        <div class="footer-content">
            <div class="footer-left">
                <p class="footer-copyright">© {datetime.now().year} {self.site_name}</p>
                <p class="footer-note">Engineering, platforms, economics, and policy.</p>
            </div>
            <div class="footer-links">
                <a href="https://github.com/bashketchum02" class="footer-link">GitHub</a>
                <a href="https://x.com/bashketchum02" class="footer-link">X</a>
                <a href="../feed.xml" class="footer-link">RSS</a>
            </div>
        </div>
    </footer>

    <script src="../js/main.js"></script>
    <script>
        document.querySelectorAll('code.language-mermaid').forEach(function(el) {{
            var pre = el.parentElement;
            var div = document.createElement('pre');
            div.className = 'mermaid';
            div.textContent = el.textContent;
            pre.parentNode.replaceChild(div, pre);
        }});
        hljs.highlightAll();
        document.addEventListener("DOMContentLoaded", function() {{
            renderMathInElement(document.body, {{
                delimiters: [
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ],
                throwOnError: false
            }});
        }});
    </script>
</body>
</html>'''

    def build_all(self):
        """Build all markdown posts."""
        print("Building posts...")
        md_files = list(self.source_dir.glob('*.md'))

        if not md_files:
            print("No markdown files found in posts/")
            return

        for md_file in md_files:
            if md_file.name == 'template.md':
                continue
            post = self.render_post(md_file)
            if post:
                self.posts.append(post)

        # Sort posts by date (newest first)
        self.posts.sort(key=lambda x: str(x.get('date', '')), reverse=True)

        print(f"\nBuilt {len(self.posts)} posts")

    def generate_index(self):
        """Generate the index.html with recent posts."""
        if not self.posts:
            print("No posts to include in index")
            return

        print("Generating index.html...")

        # Featured post (most recent)
        featured = self.posts[0] if self.posts else None

        # Other recent posts (next 4)
        recent = self.posts[1:5] if len(self.posts) > 1 else []

        featured_html = ''
        if featured:
            tags_html = ''.join(f'<span class="tag">{tag}</span>' for tag in featured.get('tags', []))
            featured_html = f'''
            <article class="post-card featured">
                <div class="post-meta">
                    <time class="post-date">{featured['date_display']}</time>
                    <span class="post-category">{featured['category']}</span>
                </div>
                <h3 class="post-title">
                    <a href="{featured['path']}">{self.escape_html(featured['title'])}</a>
                </h3>
                <p class="post-excerpt">{self.escape_html(featured['excerpt'])}</p>
                <div class="post-tags">{tags_html}</div>
            </article>'''

        recent_html = ''
        for post in recent:
            recent_html += f'''
                <article class="post-card">
                    <div class="post-meta">
                        <time class="post-date">{post['date_display']}</time>
                        <span class="post-category">{post['category']}</span>
                    </div>
                    <h3 class="post-title">
                        <a href="{post['path']}">{self.escape_html(post['title'])}</a>
                    </h3>
                    <p class="post-excerpt">{self.escape_html(post['excerpt'])}</p>
                </article>'''

        index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.site_name}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,520;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="grain-overlay"></div>

    <header class="site-header">
        <nav class="nav-container">
            <a href="index.html" class="logo">
                <span class="logo-symbol">λ</span>
                <span class="logo-text">bala</span>
            </a>
            <div class="nav-links">
                <a href="index.html" class="nav-link active">Writing</a>
                <a href="about.html" class="nav-link">About</a>
            </div>
        </nav>
    </header>

    <main class="main-content">
        <section class="hero">
            <div class="hero-content">
                <p class="hero-tagline">Hi, I am Bala.</p>
                <h1 class="hero-title">I like engineering, economics, policy, and complex systems.</h1>
            </div>
            <div class="hero-aside">
                <p class="aside-kicker">Now</p>
                <ul class="topic-list">
                    <li>building ML infrastructure at <a href="https://www.grab.com/" target="_blank" rel="noopener">Grab</a></li>
                    <li>thinking about social sciences, especially economics and policy</li>
                    <li>previously: wizard wearing many hats</li>
                </ul>
            </div>
        </section>

        <section class="posts-section">
            <div class="section-header">
                <h2 class="section-title">Writing</h2>
                <div class="section-line"></div>
            </div>

            {featured_html}

            <div class="posts-grid">
                {recent_html}
            </div>

            <a href="archive.html" class="view-all">
                Browse the archive
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </a>
        </section>
    </main>

    <footer class="site-footer">
        <div class="footer-content">
            <div class="footer-left">
                <p class="footer-copyright">© {datetime.now().year} {self.site_name}</p>
                <p class="footer-note">Engineering, platforms, economics, and policy.</p>
            </div>
            <div class="footer-links">
                <a href="https://github.com/bashketchum02" class="footer-link" target="_blank" rel="noopener">GitHub</a>
                <a href="https://x.com/bashketchum02" class="footer-link" target="_blank" rel="noopener">X</a>
                <a href="feed.xml" class="footer-link">RSS</a>
            </div>
        </div>
    </footer>

    <script src="js/main.js"></script>
</body>
</html>'''

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("  Generated: index.html")

    def generate_archive(self):
        """Generate the archive.html with all posts by year."""
        if not self.posts:
            return

        print("Generating archive.html...")

        # Group posts by year
        posts_by_year = {}
        for post in self.posts:
            date = post.get('date', '')
            if hasattr(date, 'year'):  # datetime or date object
                year = date.year
            elif isinstance(date, str) and len(date) >= 4:
                year = date[:4]
            else:
                year = 'Unknown'

            if year not in posts_by_year:
                posts_by_year[year] = []
            posts_by_year[year].append(post)

        # Build archive HTML
        years_html = ''
        for year in sorted(posts_by_year.keys(), reverse=True):
            posts = posts_by_year[year]
            items_html = ''
            for post in posts:
                date_short = post['date_display'][5:] if len(post['date_display']) > 5 else post['date_display']
                items_html += f'''
                    <li class="archive-item">
                        <time class="archive-date">{date_short}</time>
                        <a href="{post['path']}" class="archive-title">{self.escape_html(post['title'])}</a>
                        <span class="archive-category">{post['category']}</span>
                    </li>'''

            years_html += f'''
            <div class="archive-year">
                <h2 class="year-heading">{year}</h2>
                <ul class="archive-list">{items_html}
                </ul>
            </div>'''

        archive_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive | {self.site_name}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,520;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="grain-overlay"></div>

    <header class="site-header">
        <nav class="nav-container">
            <a href="index.html" class="logo">
                <span class="logo-symbol">λ</span>
                <span class="logo-text">bala</span>
            </a>
            <div class="nav-links">
                <a href="index.html" class="nav-link active">Writing</a>
                <a href="about.html" class="nav-link">About</a>
            </div>
        </nav>
    </header>

    <main class="main-content">
        <section class="archive-section">
            <header class="page-header">
                <h1 class="page-title">Archive</h1>
                <p class="page-description">Everything published here, newest first.</p>
            </header>
            {years_html}
        </section>
    </main>

    <footer class="site-footer">
        <div class="footer-content">
            <div class="footer-left">
                <p class="footer-copyright">© {datetime.now().year} {self.site_name}</p>
                <p class="footer-note">Engineering, platforms, economics, and policy.</p>
            </div>
            <div class="footer-links">
                <a href="https://github.com/bashketchum02" class="footer-link" target="_blank" rel="noopener">GitHub</a>
                <a href="https://x.com/bashketchum02" class="footer-link" target="_blank" rel="noopener">X</a>
                <a href="feed.xml" class="footer-link">RSS</a>
            </div>
        </div>
    </footer>

    <script src="js/main.js"></script>
</body>
</html>'''

        with open('archive.html', 'w', encoding='utf-8') as f:
            f.write(archive_html)
        print("  Generated: archive.html")

    def generate_rss(self):
        """Generate RSS feed."""
        if not self.posts:
            return

        print("Generating feed.xml...")

        items = ''
        for post in self.posts[:10]:
            items += f'''
        <item>
            <title>{self.escape_html(post['title'])}</title>
            <link>{self.site_url}/{post['path']}</link>
            <description>{self.escape_html(post['excerpt'])}</description>
            <pubDate>{self.format_date_rss(post['date'])}</pubDate>
            <guid>{self.site_url}/{post['path']}</guid>
        </item>'''

        rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{self.site_name}</title>
        <link>{self.site_url}</link>
        <description>{self.site_description}</description>
        <atom:link href="{self.site_url}/feed.xml" rel="self" type="application/rss+xml"/>
        <language>en-us</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        {items}
    </channel>
</rss>'''

        with open('feed.xml', 'w', encoding='utf-8') as f:
            f.write(rss)
        print("  Generated: feed.xml")

    def build(self):
        """Full build: posts, index, archive, RSS."""
        print(f"\n{'='*50}")
        print(f"Building blog: {self.site_name}")
        print(f"{'='*50}\n")

        self.build_all()

        if self.posts:
            self.generate_index()
            self.generate_archive()
            self.generate_rss()

        print(f"\n{'='*50}")
        print(f"Build complete! {len(self.posts)} posts processed.")
        print(f"{'='*50}\n")

    def watch(self):
        """Watch for changes and rebuild."""
        print("Watching for changes... (Ctrl+C to stop)")
        last_build = 0

        while True:
            try:
                # Check for modified files
                md_files = list(self.source_dir.glob('*.md'))
                latest_mod = max((f.stat().st_mtime for f in md_files), default=0)

                if latest_mod > last_build:
                    self.posts = []  # Reset
                    self.build()
                    last_build = time.time()

                time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopped watching.")
                break


def main():
    parser = argparse.ArgumentParser(description='Build blog from markdown')
    parser.add_argument('--watch', action='store_true', help='Watch for changes')
    parser.add_argument('--serve', action='store_true', help='Start local server')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    args = parser.parse_args()

    builder = BlogBuilder()

    if args.watch and args.serve:
        # Start server in background, then watch
        import threading
        import http.server
        import socketserver

        def serve():
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", args.port), handler) as httpd:
                print(f"Serving at http://localhost:{args.port}")
                httpd.serve_forever()

        builder.build()
        server_thread = threading.Thread(target=serve, daemon=True)
        server_thread.start()
        builder.watch()

    elif args.serve:
        builder.build()
        import http.server
        import socketserver

        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", args.port), handler) as httpd:
            print(f"\nServing at http://localhost:{args.port}")
            httpd.serve_forever()

    elif args.watch:
        builder.build()
        builder.watch()

    else:
        builder.build()


if __name__ == '__main__':
    main()
