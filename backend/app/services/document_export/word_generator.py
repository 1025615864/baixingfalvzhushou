"""Word生成服务模块

使用python-docx生成Word格式的合同审查报告
"""

from io import BytesIO
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from sqlalchemy.ext.asyncio import AsyncSession

from ..contracts.history_service import ContractHistoryService

# 性能优化：模块级别导入，避免重复导入
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    Document = None


class WordGenerationError(Exception):
    """Word生成异常"""
    pass

# 性能优化：预定义常量
_CHINESE_FONT_NAME = "宋体"
_CHINESE_FONT_BOLD_NAME = "黑体"
_CHINESE_FONT_SIZE = 10.5
_SECTION_HEADING_SIZE = 14
_TITLE_SIZE = 18


async def generate_contract_word(
    db: AsyncSession,
    review_id: str,
    options: dict[str, Any] | None = None,
) -> bytes:
    """
    生成合同审查报告Word文档
    
    Args:
        db: 数据库会话
        review_id: 审查记录ID
        options: 导出选项
            - includeDetailedRisks: 包含详细风险分析
            - includeRecommendedEdits: 包含建议修改稿
            - includeMissingClauses: 包含缺失条款
    
    Returns:
        bytes: Word文档内容
    
    Raises:
        WordGenerationError: Word生成失败
    """
    options = options or {}
    
    # 获取审查记录
    review = await ContractHistoryService.get_review_detail(db=db, review_id=review_id)
    if not review:
        raise WordGenerationError(f"未找到审查记录: {review_id}")
    
    # 创建Word文档
    if not DOCX_AVAILABLE:
        raise WordGenerationError("缺少python-docx依赖，请安装: pip install python-docx")
    
    try:
        doc = _create_word_document(
            review=review,
            options=options,
        )
        
        # 保存到BytesIO
        word_buffer = BytesIO()
        doc.save(word_buffer)
        
        # 返回Word内容
        word_buffer.seek(0)
        return word_buffer.getvalue()
    except Exception as e:
        raise WordGenerationError(f"Word生成失败: {str(e)}") from e


def _create_word_document(
    review: Any,
    options: dict[str, Any],
) -> Document:
    """
    创建Word文档
    
    Args:
        review: 审查记录
        options: 导出选项
    
    Returns:
        Document: Word文档对象
    """
    # 创建文档
    doc = Document()
    
    # 设置默认字体（中文字体）
    _set_document_font(doc)
    
    # 标题（使用预定义常量）
    title = doc.add_heading("合同审查报告", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_paragraph_font(title, "SimHei", _TITLE_SIZE, bold=True)
    
    # 基本信息
    doc.add_heading("基本信息", level=1)
    _set_section_heading_font(doc.paragraphs[-1])
    
    _add_info_row(doc, "文件名称", review.filename or "未知")
    _add_info_row(doc, "审查时间", review.created_at.strftime("%Y年%m月%d日 %H:%M:%S") if review.created_at else "未知")
    _add_info_row(doc, "请求ID", review.request_id or "-")
    
    doc.add_paragraph()  # 空行
    
    # 风险评级
    if review.report_json:
        risk_level = review.report_json.get("risk_level")
        risk_count = review.report_json.get("risk_count", 0)
        if risk_level:
            # 使用预定义的映射避免重复创建
            level_map = _get_risk_level_map()
            doc.add_heading("风险评级", level=1)
            _set_section_heading_font(doc.paragraphs[-1])
            
            _add_info_row(doc, "风险等级", level_map.get(risk_level, risk_level))
            _add_info_row(doc, "风险点数量", str(risk_count))
            
            doc.add_paragraph()  # 空行
    
    # 详细风险分析
    if options.get("includeDetailedRisks", True):
        doc.add_heading("风险分析", level=1)
        _set_section_heading_font(doc.paragraphs[-1])
        
        if review.report_json and "risk_items" in review.report_json:
            risk_items = review.report_json["risk_items"]
            if risk_items:
                for i, item in enumerate(risk_items, 1):
                    # 风险标题
                    risk_title = doc.add_heading(f"{i}. {item.get('title', '未知风险')}", level=2)
                    
                    # 风险详情
                    _add_detail_row(doc, "类型", item.get("type", "未知"))
                    _add_detail_row(doc, "严重程度", item.get("severity", "未知"))
                    _add_detail_row(doc, "位置", item.get("location", "未知"))
                    
                    # 问题描述（使用预定义常量）
                    doc.add_heading("问题描述", level=3)
                    desc_para = doc.add_paragraph(item.get("description", "无描述"))
                    _set_paragraph_font(desc_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    # 法律依据
                    if item.get("legal_basis"):
                        doc.add_heading("法律依据", level=3)
                        legal_para = doc.add_paragraph(item["legal_basis"])
                        _set_paragraph_font(legal_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    # 建议
                    if item.get("suggestion"):
                        doc.add_heading("建议", level=3)
                        suggest_para = doc.add_paragraph(item["suggestion"])
                        _set_paragraph_font(suggest_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    doc.add_paragraph()  # 空行
            else:
                para = doc.add_paragraph("暂无详细风险分析")
                _set_paragraph_font(para, "SimSun", _CHINESE_FONT_SIZE)
        else:
            para = doc.add_paragraph("暂无详细风险分析")
            _set_paragraph_font(para, "SimSun", _CHINESE_FONT_SIZE)
        
        doc.add_paragraph()  # 空行
    
    # 建议修改稿
    if options.get("includeRecommendedEdits", True):
        doc.add_heading("建议修改稿", level=1)
        _set_section_heading_font(doc.paragraphs[-1])
        
        if review.report_json and "recommended_edits" in review.report_json:
            edits = review.report_json["recommended_edits"]
            if edits:
                for i, edit in enumerate(edits, 1):
                    doc.add_heading(f"修改 {i}", level=2)
                    _add_detail_row(doc, "位置", edit.get("location", "未知"))
                    
                    # 原文
                    doc.add_heading("原文", level=3)
                    original_para = doc.add_paragraph(edit.get("original", "无"))
                    _set_paragraph_font(original_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    # 修改建议
                    doc.add_heading("修改建议", level=3)
                    suggested_para = doc.add_paragraph(edit.get("suggested", "无"))
                    _set_paragraph_font(suggested_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    doc.add_paragraph()  # 空行
            else:
                para = doc.add_paragraph("暂无建议修改")
                _set_paragraph_font(para, "SimSun", _CHINESE_FONT_SIZE)
        else:
            para = doc.add_paragraph("暂无建议修改")
            _set_paragraph_font(para, "SimSun", _CHINESE_FONT_SIZE)
        
        doc.add_paragraph()  # 空行
    
    # 缺失条款
    if options.get("includeMissingClauses", True):
        doc.add_heading("缺失条款建议", level=1)
        _set_section_heading_font(doc.paragraphs[-1])
        
        if review.report_json and "missing_clauses" in review.report_json:
            missing = review.report_json["missing_clauses"]
            if missing:
                for i, clause in enumerate(missing, 1):
                    doc.add_heading(f"{i}. {clause.get('type', '未知类型')}", level=2)
                    
                    desc_para = doc.add_paragraph(clause.get("description", "无描述"))
                    _set_paragraph_font(desc_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    if clause.get("suggested_text"):
                        doc.add_heading("建议文本", level=3)
                        suggest_para = doc.add_paragraph(clause["suggested_text"])
                        _set_paragraph_font(suggest_para, "SimSun", _CHINESE_FONT_SIZE)
                    
                    doc.add_paragraph()  # 空行
            else:
                para = doc.add_paragraph("未发现缺失条款")
                _set_paragraph_font(para, "SimSun", _CHINESE_FONT_SIZE)
        else:
            para = doc.add_paragraph("未发现缺失条款")
            _set_paragraph_font(para, "SimSun", _CHINESE_FONT_SIZE)
        
        doc.add_paragraph()  # 空行
    
    # 添加分隔线
    doc.add_paragraph("_" * 80)
    
    # 免责声明
    doc.add_heading("免责声明", level=1)
    _set_section_heading_font(doc.paragraphs[-1])
    
    disclaimer_para = doc.add_paragraph(
        "本报告由AI系统生成，仅供参考，不构成正式法律意见。具体案件请结合证据材料并咨询专业律师。\n\n"
        f"生成时间: {review.created_at.strftime('%Y年%m月%d日 %H:%M') if review.created_at else '未知'}"
    )
    _set_paragraph_font(disclaimer_para, "SimSun", _CHINESE_FONT_SIZE)
    
    return doc


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

def _set_document_font(doc: Document) -> None:
    """
    设置文档默认字体（性能优化版）
    
    Args:
        doc: Word文档对象
    """
    # 设置默认样式（使用预定义常量）
    style = doc.styles["Normal"]
    font = style.font
    font.name = _CHINESE_FONT_NAME
    font.size = Pt(_CHINESE_FONT_SIZE)
    
    # 设置中文字体
    font.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")


def _set_paragraph_font(
    paragraph: Any,
    font_name: str,
    font_size: float,
    bold: bool = False,
    color: RGBColor | None = None,
) -> None:
    """
    设置段落字体
    
    Args:
        paragraph: 段落对象
        font_name: 字体名称
        font_size: 字体大小
        bold: 是否加粗
        color: 字体颜色
    """
    for run in paragraph.runs:
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = color
        run.element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def _set_section_heading_font(paragraph: Any) -> None:
    """
    设置章节标题字体（使用预定义常量）
    
    Args:
        paragraph: 段落对象
    """
    _set_paragraph_font(
        paragraph,
        _CHINESE_FONT_BOLD_NAME,
        _SECTION_HEADING_SIZE,
        bold=True,
        color=RGBColor(30, 64, 175)
    )


def _add_info_row(doc: Document, label: str, value: str) -> None:
    """
    添加信息行（使用预定义常量）
    
    Args:
        doc: Word文档对象
        label: 标签
        value: 值
    """
    para = doc.add_paragraph()
    run = para.add_run(f"**{label}**: {value}")
    run.bold = True
    _set_paragraph_font(para, _CHINESE_FONT_NAME, _CHINESE_FONT_SIZE)


def _add_detail_row(doc: Document, label: str, value: str) -> None:
    """
    添加详情行（使用预定义常量）
    
    Args:
        doc: Word文档对象
        label: 标签
        value: 值
    """
    para = doc.add_paragraph()
    para.add_run(f"{label}: ")
    run = para.add_run(value)
    run.bold = True
    _set_paragraph_font(para, _CHINESE_FONT_NAME, _CHINESE_FONT_SIZE)