"""Document export service."""
from __future__ import annotations
from typing import Optional
from app.services.document_export.pdf_generator import PDFGenerator
from app.services.document_export.word_generator import WordGenerator


class DocumentExportService:
    def __init__(self):
        self._pdf_generator = PDFGenerator()
        self._word_generator = WordGenerator()

    async def export_pdf(self, title: str, content: str, output_path: Optional[str] = None, **kwargs) -> dict:
        return await self._pdf_generator.generate(title=title, content=content, output_path=output_path, **kwargs)

    async def export_word(self, title: str, content: str, output_path: Optional[str] = None, **kwargs) -> dict:
        return await self._word_generator.generate(title=title, content=content, output_path=output_path, **kwargs)


document_export_service = DocumentExportService()
