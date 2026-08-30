#!/usr/bin/env python3
"""
Blog Build Script

A simple static site generator that converts markdown posts to HTML
and automatically updates the content-first index and RSS feed.

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


FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700'
    '&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">'
)


POST_HEAD_EXTRAS = (
    '\n    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">'
    '\n    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/default.min.css">'
)

# Loaded at the end of post pages; definition order guarantees our CSS/JS still win.
POST_SCRIPTS = '''
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
    <script type="module">
        import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
        mermaid.initialize({ startOnLoad: true, theme: "dark" });
    </script>
    <script>
        document.querySelectorAll("code.language-mermaid").forEach(function(el) {
            var pre = el.parentElement;
            var div = document.createElement("pre");
            div.className = "mermaid";
            div.textContent = el.textContent;
            pre.parentNode.replaceChild(div, pre);
        });
        hljs.highlightAll();
        document.addEventListener("DOMContentLoaded", function() {
            renderMathInElement(document.body, {
                delimiters: [
                    {left: "$$", right: "$$", display: true},
                    {left: "$", right: "$", display: false}
                ],
                throwOnError: false
            });
        });
    </script>
    <script>
        (function() {
            window.addEventListener("message", function(event) {
                if (!event.data || event.data.type !== "app:height") return;
                var frames = document.querySelectorAll("iframe.app-frame");
                for (var i = 0; i < frames.length; i++) {
                    if (frames[i].contentWindow === event.source) {
                        var h = parseInt(event.data.height, 10);
                        if (h > 40 && h < 20000) frames[i].style.height = h + "px";
                        return;
                    }
                }
            });
        })();
    </script>'''


class BlogBuilder:
    def __init__(self, source_dir: str = "posts", output_dir: str = "posts"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.posts = []
        self.site_name = "bashketchum02"
        self.site_url = "https://bashketchum02.github.io"
        self.site_description = "bashketchum02 builds ML infrastructure and likes social sciences."

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

    def reading_time(self, text: str) -> int:
        """Estimate reading time in minutes from body text."""
        text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
        text = re.sub(r'\$\$.+?\$\$', ' ', text, flags=re.DOTALL)
        words = len(text.split())
        return max(1, round(words / 225))

    # --- Interactive app embedding -----------------------------------------
    # Markdown directives:
    #   <!-- app: name height=460 caption="Simulator" -->   -> apps/<name>/index.html
    #   <!-- embed: https://... height=520 -->              -> external iframe
    # These pass through python-markdown untouched and are replaced post-render.

    APP_DIRECTIVE_RE = re.compile(r'<!--\s*app:\s*([A-Za-z0-9_-]+)\s*(.*?)-->', re.DOTALL)
    EMBED_DIRECTIVE_RE = re.compile(r'<!--\s*embed:\s*(\S+)\s*(.*?)-->', re.DOTALL)
    ATTR_RE = re.compile(r'(\w+)\s*=\s*("([^"]*)"|\'([^\']*)\'|(\S+))')

    @staticmethod
    def _parse_attrs(text: str) -> dict:
        attrs = {}
        for m in BlogBuilder.ATTR_RE.finditer(text or ''):
            key = m.group(1).lower()
            val = next(g for g in (m.group(3), m.group(4), m.group(5)) if g is not None)
            attrs[key] = val
        return attrs

    @staticmethod
    def _safe_height(attrs: dict, default: int = 420) -> int:
        raw = str(attrs.get('height', ''))
        return int(raw) if re.fullmatch(r'\d{2,5}', raw) else default

    def _embed_figure(self, src: str, attrs: dict) -> str:
        height = self._safe_height(attrs)
        caption = attrs.get('caption', '').strip()
        title = self.escape_html(caption or 'interactive app')
        cap_html = f'\n    <figcaption>{self.escape_html(caption)}</figcaption>' if caption else ''
        return (f'<figure class="app-embed">\n'
                f'    <iframe class="app-frame" src="{self.escape_html(src)}" '
                f'style="height:{height}px" loading="lazy" title="{title}"></iframe>'
                f'{cap_html}\n</figure>')

    def embed_apps(self, html: str) -> str:
        """Replace app/embed directives with iframe figures."""
        def app_repl(m):
            name = m.group(1)
            if not (Path('apps') / name / 'index.html').exists():
                print(f"  Warning: app '{name}' not found (apps/{name}/index.html)")
                return (f'<div class="app-embed app-missing">'
                        f'app not found: {self.escape_html(name)}</div>')
            return self._embed_figure(f'../apps/{name}/', self._parse_attrs(m.group(2)))

        def embed_repl(m):
            url = m.group(1)
            if not re.match(r'^https?://', url):
                print(f"  Warning: embed url not http(s): {url}")
                return (f'<div class="app-embed app-missing">'
                        f'invalid embed url: {self.escape_html(url)}</div>')
            return self._embed_figure(url, self._parse_attrs(m.group(2)))

        html = self.APP_DIRECTIVE_RE.sub(app_repl, html)
        html = self.EMBED_DIRECTIVE_RE.sub(embed_repl, html)
        return html

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
            return date.strftime('%b %d, %Y')
        elif isinstance(date, str):
            try:
                return datetime.strptime(date, '%Y-%m-%d').strftime('%b %d, %Y')
            except ValueError:
                return date
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

    def page_head(self, title: str, prefix: str, description: str = "", head_extras: str = "") -> str:
        """Shared HTML head for generated pages."""
        desc = f'    <meta name="description" content="{self.escape_html(description)}">\n' if description else ''
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
{desc}    <link rel="icon" type="image/svg+xml" href="{prefix}images/intro.svg">
    <link rel="stylesheet" href="{prefix}css/style.css">
    <link rel="stylesheet" href="{prefix}css/post.css">
    <link rel="stylesheet" href="{prefix}css/syntax.css">

    {FONTS_LINK}{head_extras}
</head>
<body>
'''

    def render_header(self, prefix: str, active: str) -> str:
        """Shared site header + open main. active in {'writing','about'}."""
        writing_active = ' class="nav-link active"' if active == 'writing' else ' class="nav-link"'
        about_active = ' class="nav-link active"' if active == 'about' else ' class="nav-link"'
        return f'''    <header class="site-header">
        <nav class="nav-container">
            <a href="{prefix}index.html" class="logo">bashketchum02</a>
            <div class="nav-links">
                <a href="{prefix}index.html"{writing_active}>Writing</a>
                <a href="{prefix}about.html"{about_active}>About</a>
            </div>
        </nav>
    </header>

    <main class="main-content">
'''

    def render_footer(self, prefix: str) -> str:
        """Close main + shared footer + scripts."""
        return f'''    </main>

    <footer class="site-footer">
        <div class="footer-content">
            <div class="footer-left">
                <p class="footer-copyright">&copy; {datetime.now().year} {self.site_name}</p>
                <p class="footer-note">ml infrastructure &middot; social sciences</p>
            </div>
            <div class="footer-links">
                <a href="https://github.com/bashketchum02" class="footer-link">GitHub</a>
                <a href="https://x.com/bashketchum02" class="footer-link">X</a>
                <a href="{prefix}feed.xml" class="footer-link">RSS</a>
            </div>
        </div>
    </footer>

    <script src="{prefix}js/main.js"></script>
</body>
</html>'''

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

        # Replace app/embed directives with iframe embeds
        html_content = self.embed_apps(html_content)

        # Generate TOC
        toc_html = self.generate_toc(html_content)

        # Reading time from raw body
        front_matter['read_min'] = self.reading_time(body)

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
            'read_min': front_matter.get('read_min', 1),
            'slug': md_path.stem,
            'path': f'posts/{output_filename}',
        }

    def build_post_page(self, meta: dict, content: str, toc: str) -> str:
        """Build complete HTML page for a post."""
        title = meta.get('title', 'Untitled')
        date = self.format_date(meta.get('date', datetime.now().strftime('%Y-%m-%d')))
        category = meta.get('category', 'General')
        excerpt = meta.get('excerpt', '')
        read_min = meta.get('read_min', 1)

        html = f'''{self.page_head(f"{self.escape_html(title)} | {self.site_name}", "../", excerpt, POST_HEAD_EXTRAS)}
{self.render_header("../", "writing")}        <article>
            <header class="post-header">
                <div class="post-meta">
                    <time class="post-date">{date}</time>
                    <span class="post-category">{category}</span>
                    <span class="post-read">{read_min} min read</span>
                </div>
                <h1 class="post-title">{self.escape_html(title)}</h1>
                <p class="post-excerpt">{self.escape_html(excerpt)}</p>
            </header>

            <div class="post-layout">
                <div class="post-content">
                    {content}
                </div>

                {toc}
            </div>
        </article>
{self.render_footer("../")}'''

        # Inject post-only scripts before </body>
        html = html.replace(
            '<script src="../js/main.js"></script>',
            '<script src="../js/main.js"></script>' + POST_SCRIPTS,
        )
        return html

    def build_all(self):
        """Build all markdown posts."""
        print("Building posts...")
        md_files = list(self.source_dir.glob('*.md'))

        if not md_files:
            print("No markdown files found in posts/")
            return

        for md_file in md_files:
            if md_file.name == 'template.md' or md_file.name.startswith('_'):
                continue
            post = self.render_post(md_file)
            if post:
                self.posts.append(post)

        # Sort posts by date (newest first)
        self.posts.sort(key=lambda x: str(x.get('date', '')), reverse=True)

        print(f"\nBuilt {len(self.posts)} posts")

    def generate_index(self):
        """Generate the index.html content-first directory of all posts."""
        if not self.posts:
            print("No posts to include in index")
            return

        print("Generating index.html...")

        items = ''
        for post in self.posts:
            items += f'''
            <a href="{post['path']}" class="post-row">
                <span class="post-row-meta"><time>{post['date_display']}</time> &middot; {self.escape_html(post['category'])}</span>
                <span class="post-row-title">{self.escape_html(post['title'])}</span>
                <span class="post-row-read">{post['read_min']}m</span>
            </a>'''

        if not items:
            items = '\n            <p class="directory-empty">Nothing published yet.</p>\n'

        index_html = f'''{self.page_head(self.site_name, "", self.site_description)}
{self.render_header("", "writing")}        <section class="home-hero">
            <img src="images/intro.svg" alt="">
        </section>

        <section class="posts-section">
            <div class="post-list">
                {items}
            </div>
        </section>
{self.render_footer("")}'''

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("  Generated: index.html")

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
        """Full build: posts, index, RSS."""
        print(f"\n{'='*50}")
        print(f"Building blog: {self.site_name}")
        print(f"{'='*50}\n")

        self.build_all()

        if self.posts:
            self.generate_index()
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
