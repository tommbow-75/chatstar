from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    preferences = Column(JSONB)
    user_api = Column(String(255))

    buddies = relationship("BuddyInfo", back_populates="user", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")
    user_topics = relationship("UserTopicLog", back_populates="user", cascade="all, delete-orphan")
    buddy_topics = relationship("BuddyTopicLog", back_populates="user", cascade="all, delete-orphan")

class BuddyInfo(Base):
    __tablename__ = "buddy_info"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    dmbuddy = Column(String(100), nullable=False)
    buddy_prefs = Column(JSONB)

    user = relationship("User", back_populates="buddies")

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    dmbuddy = Column(String(100), nullable=False)
    received_mess = Column(Text)
    generated_mess = Column(JSONB)
    selected_mess = Column(Text)
    date = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="chat_logs")

class UserTopicLog(Base):
    __tablename__ = "user_topics_log"
    # SQLAlchemy mapped class needs a primary key, so we use a composite primary key strategy
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    topic = Column(Text, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="user_topics")

class BuddyTopicLog(Base):
    __tablename__ = "buddy_topics_log"

    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    dmbuddy = Column(String(100), primary_key=True)
    topic = Column(Text, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="buddy_topics")

