from sqlalchemy import Column, ForeignKey, Integer, String, Text
from database.db import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    session_id = Column(String, nullable=False)  # used instead of user_email

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    from_email = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    summary = Column(Text, nullable=True)
    raw = Column(Text, nullable=True)
    user_email = Column(String, nullable=False)
    gmail_id = Column(String, nullable=False)