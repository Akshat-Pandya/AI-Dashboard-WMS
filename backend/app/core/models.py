# app/core/models.py
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON

from app.core.database import Base


class SavedDashboard(Base):
    __tablename__ = "saved_dashboards"

    id                    = Column(String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text            = Column(Text,         nullable=False)
    query_text_normalized = Column(String(500),  nullable=False)   # lowercase+stripped for dedup
    intent_name           = Column(String(100),  nullable=True)
    params_json           = Column(JSON,         nullable=True)
    label                 = Column(String(255),  nullable=True)
    user_id               = Column(String(100),  nullable=True)
    created_at            = Column(DateTime,     default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("query_text_normalized", name="uq_query_normalized"),
    )