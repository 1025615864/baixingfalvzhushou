"""律所律师邀请表"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LawFirmInvitation(Base):
    """律所律师邀请表"""
    __tablename__ = "lawfirm_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawfirm_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    invited_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    firm_role: Mapped[str] = mapped_column(String(20), default="associate")
    message: Mapped[str] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    responded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_invitation_lawfirm", "lawfirm_id", "status"),
        Index("idx_invitation_lawyer", "lawyer_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<LawFirmInvitation(id={self.id}, lawfirm_id={self.lawfirm_id}, status={self.status})>"