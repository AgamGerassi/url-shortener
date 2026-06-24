from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Index
from app.database import Base


class URL(Base):
    """URL mapping model."""
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    original_url = Column(String(2048), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
