"""Legal Document and Template models"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, JSON, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LegalDocument(Base):
    """法律文书表"""
    __tablename__ = "legal_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)

    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="draft")

    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_prompt: Mapped[str] = mapped_column(Text, nullable=True)

    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_document_consultation", "consultation_id", "created_at"),
        Index("idx_document_lawyer", "lawyer_id", "status"),
        Index("idx_document_type_status", "document_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<LegalDocument(id={self.id}, type={self.document_type}, status={self.status})>"


class DocumentTemplate(Base):
    """文书模板表"""
    __tablename__ = "document_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    template_content: Mapped[str] = mapped_column(Text, nullable=False)

    required_fields: Mapped[list] = mapped_column(JSON, default=list)
    optional_fields: Mapped[list] = mapped_column(JSON, default=list)

    description: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DocumentTemplate(id={self.id}, name={self.name})>"