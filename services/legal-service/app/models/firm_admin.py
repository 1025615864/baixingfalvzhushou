"""律所管理员表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LawFirmAdmin(Base):
    """律所管理员表"""
    __tablename__ = "lawfirm_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawfirm_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_firmadmin_firm_user", "lawfirm_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<LawFirmAdmin(id={self.id}, lawfirm_id={self.lawfirm_id}, role={self.role})>"
