"""检索日志模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from datetime import datetime

from app.database import Base


class RetrievalLog(Base):
    """RAG检索日志表"""
    __tablename__ = "retrieval_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), index=True)
    query = Column(Text)
    intent = Column(String(50))
    retrieval_level = Column(String(50), index=True)
    docs_retrieved = Column(Integer, default=0)
    docs_used = Column(Integer, default=0)
    latency_ms = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    sources = Column(JSON)
    created_at = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<RetrievalLog(id={self.id}, query={self.query[:50]}, level={self.retrieval_level})>"
