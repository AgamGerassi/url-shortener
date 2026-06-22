from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Index
from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    original_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)

    # Composite index for potential future queries
    __table_args__ = (
        Index("ix_urls_created_at", "created_at"),
    )
