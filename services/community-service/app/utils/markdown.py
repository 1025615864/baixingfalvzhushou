"""Markdown 工具"""
import re
from typing import List, Tuple, Optional


MENTION_PATTERN = re.compile(r"@(\w+)")
URL_PATTERN = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")

SAFE_TAGS = {"p", "br", "strong", "em", "b", "i", "u", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "code", "pre"}


def extract_mentions(content: str) -> List[str]:
    return MENTION_PATTERN.findall(content)


def extract_urls(content: str) -> List[Tuple[str, str]]:
    return URL_PATTERN.findall(content)


def render_markdown(content: str) -> str:
    html = content
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html)
    html = re.sub(r"_(.+?)_", r"<em>\1</em>", html)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    html = re.sub(r"```(\w+)?\n([\s\S]+?)```", r"<pre><code>\2</code></pre>", html)
    html = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', html)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    paragraphs = re.split(r"\n\n+", html)
    html = "\n".join(f"<p>{p}</p>" if not p.startswith("<") and not p.endswith(">") else p for p in paragraphs)
    html = html.replace("\n", "<br>")
    return html


def get_content_preview(content: str, max_length: int = 200) -> str:
    content = re.sub(r"\s+", " ", content)
    content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)
    content = re.sub(r"[*_`#>-]", "", content)
    if len(content) > max_length:
        return content[:max_length] + "..."
    return content


def sanitize_html(html: str) -> str:
    allowed_tags = {"p", "br", "strong", "em", "b", "i", "u", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "code", "pre", "a", "span"}
    for tag in allowed_tags:
        html = re.sub(f"<{tag}(?!s)[^>]*>", f"<{tag}>", html)
        html = re.sub(f"</{tag}>", f"</{tag}>", html)
    dangerous_tags = re.findall(r"<(script|style|iframe|object|embed|form|input)[^>]*>.*?</\1>", html, re.DOTALL | re.IGNORECASE)
    for tag in dangerous_tags:
        html = html.replace(tag, "")
    return html
