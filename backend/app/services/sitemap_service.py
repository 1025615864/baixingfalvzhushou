from __future__ import annotations


def _normalize_base_url(raw: str) -> str:
    base = str(raw or "").strip()
    if base.endswith("/"):
        base = base[:-1]
    return base


def generate_robots_txt(base_url: str) -> str:
    base = _normalize_base_url(base_url)
    sitemap_url = f"{base}/sitemap.xml" if base else "/sitemap.xml"
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    return content


def generate_sitemap_xml(base_url: str) -> str:
    base = _normalize_base_url(base_url)

    paths = [
        "/",
        "/chat",
        "/chat/history",
        "/lawfirm",
        "/calculator",
        "/limitations",
        "/documents",
        "/contracts",
        "/faq",
        "/vip",
        "/terms",
        "/privacy",
        "/ai-disclaimer",
    ]

    uniq_paths: list[str] = []
    seen: set[str] = set()
    for p in paths:
        if not isinstance(p, str):
            continue
        if p in seen:
            continue
        seen.add(p)
        uniq_paths.append(p)
    paths = uniq_paths

    def _loc(p: str) -> str:
        if not p.startswith("/"):
            p = "/" + p
        return f"{base}{p}" if base else p

    urls_xml: str = "\n".join(
        f"  <url>\n    <loc>{_loc(p)}</loc>\n  </url>" for p in paths
    )

    xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"{urls_xml}\n"
        "</urlset>\n"
    )
    return xml
