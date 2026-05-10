from __future__ import annotations

import logging
from typing import Tuple

import bleach
from bleach.css_sanitizer import CSSSanitizer

# 允许的 HTML标签 (白名单)
ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "p",
    "br",
    "div",
    "span",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "img",
    "pre",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
]

# 允许的 HTML 属性 (白名单)
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    # 禁用通配符 style，避免全量开放导致样式注入
    # 仅在必要标签上允许 style，并配合 ALLOWED_STYLES 过滤
    "div": ["class", "id"],
    "span": ["class", "id"],
    "p": ["class", "id", "style"],
    "h1": ["class", "id"],
    "h2": ["class", "id"],
    "h3": ["class", "id"],
    "h4": ["class", "id"],
    "h5": ["class", "id"],
    "h6": ["class", "id"],
    "li": ["class", "id"],
    "ul": ["class", "id"],
    "ol": ["class", "id"],
    "strong": ["class"],
    "em": ["class"],
    "code": ["class"],
    "pre": ["class"],
    "blockquote": ["class"],
    "table": ["class"],
    "thead": ["class"],
    "tbody": ["class"],
    "tr": ["class"],
    "th": ["class"],
    "td": ["class"],
    "hr": ["class"],
}

# 允许的 CSS 样式 (如果允许 style 属性)
ALLOWED_STYLES = [
    "color",
    "background-color",
    "font-size",
    "font-weight",
    "text-align",
    "margin",
    "padding",
    "border",
    "width",
    "height",
]

logger = logging.getLogger(__name__)


def clean_html(content: str) -> str:
    """
    使用 bleach 清理 HTML 内容，移除危险的标签和属性（防止 XSS 攻击）

    Args:
        content: 原始 HTML 字符串

    Returns:
        str: 清理后的安全 HTML 字符串
    """
    if not content:
        return ""

    try:
        # 配置 CSS 净化器
        css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)

        cleaned_content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            css_sanitizer=css_sanitizer,
            strip=True,  # 剥离不安全的标签而不是转义
            strip_comments=True
        )
        # bleach.linkify 可以自动将 URL 转换为链接，但这里先不开启，避免意外破坏格式
        return cleaned_content
    except Exception as e:
        logger.error(f"HTML cleaning failed: {str(e)}")
        # 如果清理失败，为了安全起见，转义所有 HTML (退回到最安全模式) or 返回空字符串?
        # 这里选择转义，保证内容可见但安全
        return bleach.clean(content, tags=[], attributes={}, strip=True)


def check_post_content_with_sanitization(
        title: str, content: str) -> Tuple[bool, str, str, str]:
    """
    检查帖子内容并进行 XSS 清理

    Args:
        title: 帖子标题
        content: 帖子内容

    Returns:
        (passed, error_msg, cleaned_title, cleaned_content)
    """
    # 1. 基础内容检查 (长度等)
    # 这里可以复用 content_filter.py 中的逻辑，或者直接调用
    if not title or not title.strip():
        return False, "标题不能为空", "", ""
    if not content or not content.strip():
        return False, "内容不能为空", "", ""

    # 2. XSS 清理
    # 标题通常不允许 HTML，直接进行转义处理（或者也用 strict mode clean）
    # 这里假设标题纯文本，做转义
    clean_title = bleach.clean(title, tags=[], strip=True)

    # 内容允许富文本，使用白名单清理
    clean_content_html = clean_html(content)

    return True, "", clean_title, clean_content_html


def check_comment_content_with_sanitization(
        content: str) -> Tuple[bool, str, str]:
    """
    检查评论内容并进行 XSS 清理

    Args:
        content: 评论内容

    Returns:
        (passed, error_msg, cleaned_content)
    """
    if not content or not content.strip():
        return False, "内容不能为空", ""

    # XSS 清理
    clean_content_html = clean_html(content)

    return True, "", clean_content_html
