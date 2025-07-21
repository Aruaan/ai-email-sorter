from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from database.db import Base
import uuid
from sqlalchemy.orm import relationship

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {'extend_existing': True}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    session_id = Column(String, nullable=False)  # used instead of user_email

class Email(Base):
    __tablename__ = "emails"
    __table_args__ = {'extend_existing': True}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject = Column(String, nullable=False)
    from_email = Column(String, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    summary = Column(Text, nullable=True)
    raw = Column(Text, nullable=True)
    user_email = Column(String, nullable=False)
    gmail_id = Column(String, nullable=False)
    headers = Column(Text, nullable=True)  # Store headers as JSON string for SQLite compatibility

class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = {'extend_existing': True}
    id = Column(String, primary_key=True, index=True)  # session_id (UUID)
    primary_account = Column(String, nullable=False)
    accounts = relationship("database.models.SessionAccount", back_populates="session", cascade="all, delete-orphan")

class SessionAccount(Base):
    __tablename__ = "session_accounts"
    __table_args__ = {'extend_existing': True}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    email = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    history_id = Column(String, nullable=True)
    session = relationship("database.models.Session", back_populates="accounts")