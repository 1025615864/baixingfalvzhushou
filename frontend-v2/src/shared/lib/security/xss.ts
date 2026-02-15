/**
 * XSS 防护工具函数
 * 提供 HTML 内容净化功能，防止 XSS 攻击
 */

import DOMPurify from 'dompurify';

/**
 * 净化 HTML 内容，防止 XSS 攻击
 * @param html 原始 HTML 字符串
 * @returns 净化后的 HTML 字符串
 */
export function sanitizeHtml(html: string): string {
  if (!html) return '';
  
  return DOMPurify.sanitize(html, {
    // 允许的标签
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li',
      'blockquote', 'code', 'pre',
      'a', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'div', 'span'
    ],
    // 允许的属性
    ALLOWED_ATTR: [
      'href', 'title', 'target', 'rel',
      'src', 'alt', 'width', 'height',
      'class', 'id', 'style'
    ],
    // 强制所有链接在新窗口打开
    FORCE_BODY: true,
    // 添加安全属性到链接
    ADD_ATTR: ['target="_blank"', 'rel="noopener noreferrer"']
  });
}

/**
 * 净化 SVG 内容
 * @param svg SVG 字符串
 * @returns 净化后的 SVG 字符串
 */
export function sanitizeSvg(svg: string): string {
  if (!svg) return '';
  
  return DOMPurify.sanitize(svg, {
    ALLOWED_TAGS: ['svg', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'text', 'g', 'defs', 'use', 'symbol', 'linearGradient', 'radialGradient', 'stop'],
    ALLOWED_ATTR: ['viewBox', 'width', 'height', 'xmlns', 'fill', 'stroke', 'stroke-width', 'd', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'points', 'transform', 'class', 'id', 'href', 'xlink:href'],
    USE_PROFILES: { svg: true }
  });
}

/**
 * 纯文本净化（移除所有 HTML 标签）
 * @param text 原始文本
 * @returns 纯文本字符串
 */
export function stripHtml(text: string): string {
  if (!text) return '';
  
  return DOMPurify.sanitize(text, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  });
}

/**
 * 创建安全的 dangerouslySetInnerHTML 对象
 * @param html 原始 HTML
 * @returns 净化后的对象
 */
export function createSafeHtml(html: string): { __html: string } {
  return {
    __html: sanitizeHtml(html)
  };
}

/**
 * 创建安全的 SVG innerHTML 对象
 * @param svg 原始 SVG
 * @returns 净化后的对象
 */
export function createSafeSvg(svg: string): { __html: string } {
  return {
    __html: sanitizeSvg(svg)
  };
}
