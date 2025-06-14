from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Feed(Base):
    __tablename__ = "feeds"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    description = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow)
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    category = relationship("Category", back_populates="feeds")
    entries = relationship("Entry", back_populates="feed", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    feeds = relationship("Feed", back_populates="category")

class Entry(Base):
    __tablename__ = "entries"
    
    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"))
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    published = Column(DateTime)
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    feed = relationship("Feed", back_populates="entries")