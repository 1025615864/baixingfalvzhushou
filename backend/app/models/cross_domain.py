"""Cross-Domain 域名管理模型"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..database import Base


class Domain(Base):
    """域名验证表"""
    __tablename__: str = "cross_domain_domains"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    domain: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # pending/verified/failed
    verification_code: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Domain(id={self.id}, domain={self.domain}, status={self.status})>"