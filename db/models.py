from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .base import Base


class BaseModel(Base):
    """基础模型类"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
