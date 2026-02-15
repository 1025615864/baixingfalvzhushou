"""PDF生成服务"""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from fastapi import Response


@dataclass
class DocumentPdfConfig:
    """PDF生成配置"""
    right_margin_mm: int = 18
    left_margin_mm: int = 18
    top_margin_mm: int = 18
    bottom_margin_mm: int = 18
    title_font_size: int = 18
    body_font_size: int = 11
    meta_font_size: int = 9


def _escape_pdf_paragraph(text: str) -> str:
    """转义PDF特殊字符"""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def generate_document_pdf(
    *,
    title: str,
    content: str,
    config: DocumentPdfConfig | None = None,
) -> bytes:
    """生成法律文书PDF

    Args:
        title: 文书标题
        content: 文书内容
        config: PDF配置

    Returns:
        PDF文件字节流

    Raises:
        RuntimeError: PDF依赖未安装
    """
    if config is None:
        config = DocumentPdfConfig()

    try:
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as e:
        raise RuntimeError("PDF_DEPENDENCY_MISSING") from e

    class _PdfMetrics(Protocol):
        def registerFont(self, font: object) -> None: ...

    class _DocBuilder(Protocol):
        def build(self, flowables: list[object]) -> None: ...

    cast(
        _PdfMetrics,
        cast(
            object,
            pdfmetrics)).registerFont(
        UnicodeCIDFont("STSong-Light"))

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=config.title_font_size,
        leading=24,
        alignment=1,
        spaceAfter=14,
    )
    meta_style = ParagraphStyle(
        name="DocMeta",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=config.meta_font_size,
        leading=14,
        textColor=colors.grey,
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        name="DocBody",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=config.body_font_size,
        leading=18,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=config.right_margin_mm * mm,
        leftMargin=config.left_margin_mm * mm,
        topMargin=config.top_margin_mm * mm,
        bottomMargin=config.bottom_margin_mm * mm,
    )

    safe_title = str(title or "法律文书").strip() or "法律文书"
    safe_content = str(content or "").strip()

    story: list[object] = []
    story.append(Paragraph(_escape_pdf_paragraph(safe_title), title_style))
    story.append(
        Paragraph(
            _escape_pdf_paragraph(
                datetime.now().strftime("%Y年%m月%d日")),
            meta_style)
    )
    if safe_content:
        story.append(
            Paragraph(
                _escape_pdf_paragraph(safe_content),
                body_style))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            _escape_pdf_paragraph(
                "免责声明：本文书由系统生成，仅供参考。正式使用前，请务必咨询专业律师进行审核和修改。"
            ),
            meta_style,
        )
    )

    cast(_DocBuilder, cast(object, doc)).build(story)
    _ = buf.seek(0)
    return buf.getvalue()


def create_pdf_response(
    *,
    title: str,
    content: str,
    filename: str | None = None,
    config: DocumentPdfConfig | None = None,
) -> Response:
    """创建PDF响应

    Args:
        title: 文书标题
        content: 文书内容
        filename: 文件名（不含扩展名）
        config: PDF配置

    Returns:
        FastAPI Response对象
    """
    try:
        pdf_bytes = generate_document_pdf(
            title=title, content=content, config=config)
    except RuntimeError as e:
        if str(e) == "PDF_DEPENDENCY_MISSING":
            from fastapi import HTTPException

            raise HTTPException(status_code=501, detail="PDF 生成依赖未安装")
        raise

    ascii_filename = "document.pdf"
    utf8_filename = f"{str(filename or title).strip() or '法律文书'}.pdf"
    quoted_utf8 = urllib.parse.quote(utf8_filename, safe="")
    content_disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8''{quoted_utf8}'

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": content_disposition,
        },
    )
