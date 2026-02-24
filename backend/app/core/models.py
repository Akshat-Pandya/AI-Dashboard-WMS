# app/core/models.py
"""
SQLAlchemy ORM models.
Add this file — it does not affect any existing module.
Run the migration snippet in README to create the table.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.mysql import JSON

from app.core.database import Base          # reuse existing declarative Base


class SavedDashboard(Base):
    __tablename__ = "saved_dashboards"

    id         = Column(String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text,        nullable=False)
    intent_name= Column(String(100), nullable=True)
    params_json= Column(JSON,        nullable=True)   # stores extracted params for re-run
    label      = Column(String(255), nullable=True)   # optional user-supplied name
    user_id    = Column(String(100), nullable=True)   # null until auth is added
    created_at = Column(DateTime,    default=datetime.utcnow, nullable=False)