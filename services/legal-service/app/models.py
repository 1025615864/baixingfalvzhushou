"""法律服务数据模型"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Consultation(Base):
    """咨询表"""
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, answered, closed
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=True)
    final_answer: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_consult_user", "user_id", "created_at"),
        Index("idx_consult_lawyer", "lawyer_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Consultation(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, lawyer
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role})>"


class Lawyer(Base):
    """律师表"""
    __tablename__ = "lawyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    lawfirm_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    specialties: Mapped[list] = mapped_column(JSON, default=list)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(default=5.0)
    consultation_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, verified, rejected
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Lawyer(id={self.id}, name={self.name}, status={self.status})>"


class LawFirm(Base):
    """律所表"""
    __tablename__ = "lawfirms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_no: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)
    province: Mapped[str] = mapped_column(String(50), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LawFirm(id={self.id}, name={self.name})>"


class LawyerConsultation(Base):
    """律师咨询预约表"""
    __tablename__ = "lawyer_consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # text, phone, video
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, rejected, completed
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    price: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LawyerConsultation(id={self.id}, type={self.type}, status={self.status})>"
