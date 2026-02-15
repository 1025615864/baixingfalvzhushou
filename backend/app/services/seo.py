"""SEO 基础建设服务

提供站点地图、Meta 标签、结构化数据等 SEO 功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SitemapGenerator:
    """站点地图生成器"""

    def __init__(self):
        self._pages: list[dict[str, Any]] = []
        self._base_url = "https://baixing-law.com"

    def add_page(
        self,
        path: str,
        changefreq: str = "weekly",
        priority: float | str = 0.5,
        lastmod: str | None = None,
    ) -> None:
        """添加页面到站点地图

        Args:
            path: 页面路径
            changefreq: 更新频率
            priority: 优先级
            lastmod: 最后修改时间
        """
        if lastmod is None:
            lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        self._pages.append({
            "loc": f"{self._base_url}{path}",
            "changefreq": changefreq,
            "priority": priority,
            "lastmod": lastmod,
        })

        logger.info(f"Added sitemap page: {path}")

    def generate_sitemap_xml(self) -> str:
        """生成站点地图 XML

        Returns:
            XML 内容
        """
        urls: list[str] = []
        for page in self._pages:
            url = f"""<url>
    <loc>{page['loc']}</loc>
    <changefreq>{page['changefreq']}</changefreq>
    <priority>{page['priority']}</priority>
    <lastmod>{page['lastmod']}</lastmod>
</url>"""
            urls.append(url)

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""

        return xml

    def generate_sitemap_index(self, sitemaps: list[str]) -> str:
        """生成站点地图索引

        Args:
            sitemaps: 子站点地图列表

        Returns:
            XML 内容
        """
        urls: list[str] = []
        for sitemap in sitemaps:
            url = f"""<sitemap>
    <loc>{sitemap}</loc>
    <lastmod>{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</lastmod>
</sitemap>"""
            urls.append(url)

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</sitemapindex>"""

        return xml

    def get_page_list(self) -> list[dict[str, Any]]:
        """获取页面列表

        Returns:
            页面列表
        """
        return self._pages.copy()


class MetaTagGenerator:
    """Meta 标签生成器"""

    def __init__(self):
        self._templates: dict[str, dict[str, Any]] = {}

    def set_template(
        self,
        page_type: str,
        title: str,
        description: str,
        keywords: list[str] | None = None,
        og_image: str | None = None,
    ) -> None:
        """设置页面模板

        Args:
            page_type: 页面类型
            title: 标题
            description: 描述
            keywords: 关键词
            og_image: Open Graph 图片
        """
        self._templates[page_type] = {
            "title": title,
            "description": description,
            "keywords": keywords or [],
            "og_image": og_image,
        }

    def generate_meta_tags(
        self,
        page_type: str,
        custom_title: str | None = None,
        custom_description: str | None = None,
        additional_params: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """生成 Meta 标签

        Args:
            page_type: 页面类型
            custom_title: 自定义标题
            custom_description: 自定义描述
            additional_params: 额外参数

        Returns:
            Meta 标签字典
        """
        template = self._templates.get(page_type, {})

        title = custom_title or template.get("title", "")
        description = custom_description or template.get("description", "")
        keywords = template.get("keywords", [])
        og_image = template.get("og_image", "")

        if additional_params:
            if "title_suffix" in additional_params:
                title = f"{title} | {additional_params['title_suffix']}"
            if "user_name" in additional_params:
                title = f"{title} - {additional_params['user_name']}"

        return {
            "title": title,
            "description": description,
            "keywords": ", ".join(keywords),
            "og:title": title,
            "og:description": description,
            "og:image": og_image,
            "twitter:card": "summary_large_image",
            "twitter:title": title,
            "twitter:description": description,
        }

    def get_template(self, page_type: str) -> dict[str, Any] | None:
        """获取模板

        Args:
            page_type: 页面类型

        Returns:
            模板信息
        """
        return self._templates.get(page_type)


class StructuredDataGenerator:
    """结构化数据生成器"""

    def __init__(self):
        self._schemas: dict[str, dict[str, Any]] = {}

    def generate_organization(self) -> dict[str, Any]:
        """生成组织结构化数据

        Returns:
            JSON-LD 数据
        """
        return {
            "@context": "https://schema.org",
            "@type": "LegalService",
            "name": "百姓法律助手",
            "url": "https://baixing-law.com",
            "logo": "https://baixing-law.com/logo.png",
            "description": "专业的法律咨询服务平台",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "CN",
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "400-123-4567",
                "contactType": "customer service",
            },
        }

    def generate_article(
        self,
        title: str,
        description: str,
        url: str,
        published_time: str,
        author_name: str,
        image: str | None = None,
    ) -> dict[str, Any]:
        """生成文章结构化数据

        Args:
            title: 标题
            description: 描述
            url: 链接
            published_time: 发布时间
            author_name: 作者名
            image: 图片

        Returns:
            JSON-LD 数据
        """
        data: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "datePublished": published_time,
            "author": {
                "@type": "Person",
                "name": author_name,
            },
        }

        if image:
            data["image"] = [image]

        return data

    def generate_faq(self, items: list[dict[str, str]]) -> dict[str, Any]:
        """生成 FAQ 结构化数据

        Args:
            items: FAQ 项目列表

        Returns:
            JSON-LD 数据
        """
        faq_elements: list[dict[str, Any]] = []
        for item in items:
            faq_elements.append({
                "@type": "Question",
                "name": item.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("answer", ""),
                },
            })

        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_elements,
        }

    def generate_breadcrumb(
            self, items: list[dict[str, str]]) -> dict[str, Any]:
        """生成面包屑结构化数据

        Args:
            items: 面包屑项目列表

        Returns:
            JSON-LD 数据
        """
        breadcrumb_list: list[dict[str, Any]] = []
        for i, item in enumerate(items):
            breadcrumb_list.append({
                "@type": "ListItem",
                "position": i + 1,
                "name": item.get("name", ""),
                "item": item.get("url", ""),
            })

        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumb_list,
        }

    def generate_jsonld(self, data: dict[str, Any]) -> str:
        """生成 JSON-LD 字符串

        Args:
            data: 结构化数据

        Returns:
            JSON-LD 字符串
        """
        import json
        json_text = json.dumps(data, ensure_ascii=False)
        return (
            f'<script type="application/ld+json">{json_text}</script>'
        )


class SEOAnalyzer:
    """SEO 分析器"""

    def __init__(self):
        self._scores: dict[str, dict[str, Any]] = {}

    async def analyze_page(
        self,
        url: str,
        title: str,
        description: str,
        content: str,
        h1_count: int = 0,
        image_count: int = 0,
        link_count: int = 0,
    ) -> dict[str, Any]:
        """分析页面 SEO

        Args:
            url: 页面 URL
            title: 标题
            description: 描述
            content: 内容
            h1_count: H1 标签数量
            image_count: 图片数量
            link_count: 链接数量

        Returns:
            分析结果
        """
        score = 0
        issues: list[str] = []
        suggestions: list[str] = []

        if len(title) >= 30 and len(title) <= 60:
            score += 20
        elif len(title) > 60:
            issues.append("标题过长，可能被截断")
            suggestions.append("将标题控制在 60 个字符以内")
        else:
            issues.append("标题过短")
            suggestions.append("增加标题长度，至少 30 个字符")
            score += 10

        if len(description) >= 120 and len(description) <= 160:
            score += 20
        elif len(description) > 160:
            issues.append("描述过长，可能被截断")
            suggestions.append("将描述控制在 160 个字符以内")
        else:
            issues.append("描述过短")
            suggestions.append("增加描述长度，至少 120 个字符")
            score += 10

        if h1_count == 1:
            score += 15
        elif h1_count > 1:
            issues.append("存在多个 H1 标签")
            suggestions.append("确保页面只有一个 H1 标签")
        else:
            issues.append("缺少 H1 标签")
            suggestions.append("添加一个 H1 标签")
            score += 5

        if image_count > 0:
            score += 10
        else:
            issues.append("缺少图片")
            suggestions.append("添加相关图片以增强内容")
            score += 5

        if link_count > 0:
            score += 10
        else:
            suggestions.append("添加内部或外部链接以丰富内容")
            score += 5

        word_count = len(content.split())
        if word_count >= 300:
            score += 25
        elif word_count >= 150:
            score += 15
        else:
            issues.append("内容过短")
            suggestions.append("增加内容，至少 300 个单词")
            score += 5

        grade = "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D"

        result: dict[str, Any] = {
            "url": url,
            "score": score,
            "grade": grade,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "title_length": len(title),
                "description_length": len(description),
                "h1_count": h1_count,
                "image_count": image_count,
                "link_count": link_count,
                "word_count": word_count,
            },
        }

        self._scores[url] = result

        return result

    def get_score_history(
            self, url: str | None = None) -> list[dict[str, Any]]:
        """获取评分历史

        Args:
            url: 页面 URL

        Returns:
            评分历史
        """
        if url:
            return [self._scores[url]] if url in self._scores else []
        return list(self._scores.values())


# 单例实例
sitemap_generator = SitemapGenerator()
meta_generator = MetaTagGenerator()
structured_data_generator = StructuredDataGenerator()
seo_analyzer = SEOAnalyzer()


def generate_sitemap() -> str:
    """便捷函数：生成站点地图

    Returns:
        XML 内容
    """
    sitemap_generator.add_page("/", "daily", 1.0)
    sitemap_generator.add_page("/consultation", "weekly", 0.8)
    sitemap_generator.add_page("/lawyers", "weekly", 0.8)
    sitemap_generator.add_page("/articles", "daily", 0.7)
    sitemap_generator.add_page("/about", "monthly", 0.5)

    return sitemap_generator.generate_sitemap_xml()


def generate_meta_tags(
    page_type: str,
    title: str | None = None,
    description: str | None = None,
) -> dict[str, str]:
    """便捷函数：生成 Meta 标签

    Args:
        page_type: 页面类型
        title: 自定义标题
        description: 自定义描述

    Returns:
        Meta 标签字典
    """
    return meta_generator.generate_meta_tags(
        page_type=page_type,
        custom_title=title,
        custom_description=description,
    )


def generate_organization_jsonld() -> str:
    """便捷函数：生成组织 JSON-LD

    Returns:
        JSON-LD 字符串
    """
    data = structured_data_generator.generate_organization()
    return structured_data_generator.generate_jsonld(data)


async def analyze_seo(
    url: str,
    title: str,
    description: str,
    content: str,
) -> dict[str, Any]:
    """便捷函数：分析页面 SEO

    Args:
        url: 页面 URL
        title: 标题
        description: 描述
        content: 内容

    Returns:
        分析结果
    """
    return await seo_analyzer.analyze_page(
        url=url,
        title=title,
        description=description,
        content=content,
    )
