from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="analyst")
    created_at = Column(DateTime, default=datetime.utcnow)

    histories = relationship("QueryHistory", back_populates="user")
    logs = relationship("AuditLog", back_populates="user")


class ThreatIntel(Base):
    __tablename__ = "threat_intel"

    id = Column(Integer, primary_key=True, index=True)
    indicator = Column(String(255), index=True, nullable=False)
    indicator_type = Column(String(50), nullable=False)
    source_name = Column(String(100), nullable=False)
    severity = Column(String(20), default="unknown")
    summary = Column(Text)
    raw_json = Column(LONGTEXT)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class SourceConfig(Base):
    __tablename__ = "source_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    source_type = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    base_url = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    extra_config = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_text = Column(String(255), nullable=False)
    query_type = Column(String(50), nullable=False)
    result_count = Column(Integer, default=0)
    queried_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="histories")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")