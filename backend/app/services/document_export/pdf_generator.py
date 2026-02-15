"""PDF生成服务模块

使用weasyprint生成PDF格式的合同审查报告
"""

from io import BytesIO
from typing import Any

import markdown2
from sqlalchemy.ext.asyncio import AsyncSession

from ..contracts.history_service import ContractHistoryService

# 性能优化：模块级别导入，避免重复导入
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    # 捕获ImportError和OSError（Windows上缺少GTK3库）
    WEASYPRINT_AVAILABLE = False
    HTML = None


class PDFGenerationError(Exception):
    """PDF生成异常"""
    pass


async def generate_contract_pdf(
    db: AsyncSession,
    review_id: str,
    options: dict[str, Any] | None = None,
) -> bytes:
    """
    生成合同审查报告PDF
    
    Args:
        db: 数据库会话
        review_id: 审查记录ID
        options: 导出选项
            - includeDetailedRisks: 包含详细风险分析
            - includeRecommendedEdits: 包含建议修改稿
            - includeMissingClauses: 包含缺失条款
    
    Returns:
        bytes: PDF文件内容
    
    Raises:
        PDFGenerationError: PDF生成失败
    """
    options = options or {}
    
    # 获取审查记录
    review = await ContractHistoryService.get_review_detail(db=db, review_id=review_id)
    if not review:
        raise PDFGenerationError(f"未找到审查记录: {review_id}")
    
    # 构建Markdown内容
    markdown_content = _build_markdown_report(
        review=review,
        options=options,
    )
    
    # 转换为HTML
    html_content = _markdown_to_html(markdown_content)
    
    # 生成PDF
    if not WEASYPRINT_AVAILABLE:
        raise PDFGenerationError("缺少weasyprint依赖，请安装: pip install weasyprint")
    
    try:
        # 创建HTML对象
        html_obj = HTML(string=html_content)
        
        # 生成PDF到BytesIO（使用缓存的CSS）
        pdf_buffer = BytesIO()
        html_obj.write_pdf(pdf_buffer, stylesheets=[_get_cached_pdf_css()])
        
        # 返回PDF内容
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    except Exception as e:
        raise PDFGenerationError(f"PDF生成失败: {str(e)}") from e


def _build_markdown_report(
    review: Any,
    options: dict[str, Any],
) -> str:
    """
    构建Markdown格式的报告（性能优化版）
    
    Args:
        review: 审查记录
        options: 导出选项
    
    Returns:
        str: Markdown内容
    """
    # 性能优化：使用列表拼接一次，而不是多次append
    report_lines = [
        "# 合同审查报告",
        "",
        "## 基本信息",
        f"- **文件名称**: {review.filename or '未知'}",
        f"- **审查时间**: {review.created_at.strftime('%Y年%m月%d日 %H:%M:%S') if review.created_at else '未知'}",
        f"- **请求ID**: {review.request_id or '-'}",
        "",
    ]
    
    # 标题
    report_lines.append("# 合同审查报告")
    report_lines.append("")
    
    # 基本信息
    report_lines.append("## 基本信息")
    report_lines.append(f"- **文件名称**: {review.filename or '未知'}")
    report_lines.append(f"- **审查时间**: {review.created_at.strftime('%Y年%m月%d日 %H:%M:%S') if review.created_at else '未知'}")
    report_lines.append(f"- **请求ID**: {review.request_id or '-'}")
    report_lines.append("")
    
    # 风险评级（性能优化：缓存常用映射）
    if review.report_json:
        risk_level = review.report_json.get("risk_level")
        risk_count = review.report_json.get("risk_count", 0)
        if risk_level:
            # 使用预定义的映射避免重复创建
            level_map = _get_risk_level_map()
            report_lines.extend([
                "## 风险评级",
                f"- **风险等级**: {level_map.get(risk_level, risk_level)}",
                f"- **风险点数量**: {risk_count}",
                "",
            ])
    
    # 详细风险分析
    if options.get("includeDetailedRisks", True):
        report_lines.append("## 风险分析")
        
        if review.report_json and "risk_items" in review.report_json:
            risk_items = review.report_json["risk_items"]
            for i, item in enumerate(risk_items, 1):
                report_lines.append(f"### {i}. {item.get('title', '未知风险')}")
                report_lines.append(f"- **类型**: {item.get('type', '未知')}")
                report_lines.append(f"- **严重程度**: {item.get('severity', '未知')}")
                report_lines.append(f"- **位置**: {item.get('location', '未知')}")
                report_lines.append("")
                report_lines.append("**问题描述**:")
                report_lines.append(item.get("description", "无描述"))
                report_lines.append("")
                
                if item.get("legal_basis"):
                    report_lines.append("**法律依据**:")
                    report_lines.append(item["legal_basis"])
                    report_lines.append("")
                
                if item.get("suggestion"):
                    report_lines.append("**建议**:")
                    report_lines.append(item["suggestion"])
                    report_lines.append("")
        else:
            report_lines.append("暂无详细风险分析")
            report_lines.append("")
    
    # 建议修改稿
    if options.get("includeRecommendedEdits", True):
        report_lines.append("## 建议修改稿")
        
        if review.report_json and "recommended_edits" in review.report_json:
            edits = review.report_json["recommended_edits"]
            if edits:
                for i, edit in enumerate(edits, 1):
                    report_lines.append(f"### 修改 {i}")
                    report_lines.append(f"- **位置**: {edit.get('location', '未知')}")
                    report_lines.append("")
                    report_lines.append("**原文**:")
                    report_lines.append(edit.get("original", "无"))
                    report_lines.append("")
                    report_lines.append("**修改建议**:")
                    report_lines.append(edit.get("suggested", "无"))
                    report_lines.append("")
            else:
                report_lines.append("暂无建议修改")
                report_lines.append("")
        else:
            report_lines.append("暂无建议修改")
            report_lines.append("")
    
    # 缺失条款
    if options.get("includeMissingClauses", True):
        report_lines.append("## 缺失条款建议")
        
        if review.report_json and "missing_clauses" in review.report_json:
            missing = review.report_json["missing_clauses"]
            if missing:
                for i, clause in enumerate(missing, 1):
                    report_lines.append(f"### {i}. {clause.get('type', '未知类型')}")
                    report_lines.append(clause.get("description", "无描述"))
                    report_lines.append(clause.get("suggested_text", ""))
                    report_lines.append("")
            else:
                report_lines.append("未发现缺失条款")
                report_lines.append("")
        else:
            report_lines.append("未发现缺失条款")
            report_lines.append("")
    
    # 免责声明
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 免责声明")
    report_lines.append("")
    report_lines.append("本报告由AI系统生成，仅供参考，不构成正式法律意见。具体案件请结合证据材料并咨询专业律师。")
    report_lines.append("")
    report_lines.append(f"生成时间: {review.created_at.strftime('%Y年%m月%d日 %H:%M') if review.created_at else '未知'}")
    
    return "\n".join(report_lines)


# 性能优化：预定义的extras列表
_MARKDOWN_EXTRAS = [
    "tables",
    "fenced-code-blocks",
    "break-on-newline",
    "cuddled-lists",
    "footnotes",
    "header-ids",
]

def _get_risk_level_map() -> dict[str, str]:
    """
    获取风险等级映射（缓存优化）
    
    Returns:
        dict: 风险等级映射
    """
    return {
        "low": "低风险",
        "medium": "中风险",
        "high": "高风险",
    }

def _markdown_to_html(markdown: str) -> str:
    """
    将Markdown转换为HTML（性能优化版）
    
    Args:
        markdown: Markdown内容
    
    Returns:
        str: HTML内容
    """
    # 使用markdown2转换为HTML（使用预定义的extras）
    html = markdown2.markdown(markdown, extras=_MARKDOWN_EXTRAS)
    
    # 添加HTML包装
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>合同审查报告</title>
</head>
<body>
    <div class="document">
        {html}
    </div>
</body>
</html>
"""


# 性能优化：缓存CSS以避免重复生成
_pdf_css_cache = None

def _get_cached_pdf_css() -> str:
    """
    获取缓存的PDF样式CSS
    
    Returns:
        str: CSS样式内容
    """
    global _pdf_css_cache
    if _pdf_css_cache is None:
        _pdf_css_cache = _get_pdf_css()
    return _pdf_css_cache


def _get_pdf_css() -> str:
    """
    获取PDF样式CSS（内部实现）
    
    Returns:
        str: CSS样式内容
    """
    return """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

@page {
    size: A4;
    margin: 2cm;
    
    @top-center {
        content: "合同审查报告";
        font-size: 10pt;
        color: #666;
    }
    
    @bottom-center {
        content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
        font-size: 9pt;
        color: #999;
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: "Noto Sans SC", "SimSun", "Microsoft YaHei", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 0;
}

.document {
    max-width: 100%;
}

h1 {
    font-size: 24pt;
    font-weight: 700;
    color: #1a56db;
    text-align: center;
    margin: 20pt 0 15pt 0;
    page-break-after: avoid;
}

h2 {
    font-size: 16pt;
    font-weight: 600;
    color: #1e40af;
    margin: 18pt 0 10pt 0;
    page-break-after: avoid;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 5pt;
}

h3 {
    font-size: 13pt;
    font-weight: 600;
    color: #374151;
    margin: 14pt 0 8pt 0;
    page-break-after: avoid;
}

h4 {
    font-size: 11pt;
    font-weight: 600;
    color: #4b5563;
    margin: 12pt 0 6pt 0;
}

p {
    margin: 6pt 0;
    text-align: justify;
}

ul, ol {
    margin: 6pt 0;
    padding-left: 24pt;
}

li {
    margin: 3pt 0;
}

strong {
    font-weight: 600;
    color: #1f2937;
}

em {
    font-style: italic;
    color: #4b5563;
}

code {
    font-family: "Consolas", "Monaco", monospace;
    font-size: 10pt;
    background: #f3f4f6;
    padding: 2pt 4pt;
    border-radius: 3px;
}

pre {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    padding: 12pt;
    margin: 10pt 0;
    overflow: hidden;
}

pre code {
    background: none;
    padding: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
    page-break-inside: avoid;
}

th {
    background: #f3f4f6;
    font-weight: 600;
    padding: 8pt 10pt;
    text-align: left;
    border: 1px solid #e5e7eb;
}

td {
    padding: 8pt 10pt;
    border: 1px solid #e5e7eb;
    vertical-align: top;
}

blockquote {
    margin: 10pt 0;
    padding: 10pt 15pt;
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    color: #92400e;
}

hr {
    border: none;
    border-top: 2px solid #e5e7eb;
    margin: 20pt 0;
}

a {
    color: #2563eb;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* 打印优化 */
@media print {
    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    
    h1, h2, h3, h4 {
        page-break-after: avoid;
    }
    
    table {
        page-break-inside: auto;
    }
    
    tr {
        page-break-inside: avoid;
    }
}
"""