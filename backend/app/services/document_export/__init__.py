"""文档导出服务模块"""

# 延迟导入，避免在weasyprint不可用时影响Word功能
try:
    from .pdf_generator import generate_contract_pdf, PDFGenerationError
    _PDF_AVAILABLE = True
except (ImportError, OSError):
    _PDF_AVAILABLE = False
    generate_contract_pdf = None
    PDFGenerationError = None

from .word_generator import generate_contract_word, WordGenerationError

if _PDF_AVAILABLE:
    __all__ = [
        "generate_contract_pdf",
        "generate_contract_word",
        "PDFGenerationError",
        "WordGenerationError",
    ]
else:
    __all__ = [
        "generate_contract_word",
        "WordGenerationError",
    ]