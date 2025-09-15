from sqlalchemy import Column, Text, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    
    id           = Column(String(64), primary_key=True)   # sha256 hash of URL
    source_name  = Column(Text, nullable=False)
    url          = Column(Text, unique=True, nullable=False)
    title        = Column(Text, nullable=False)
    category     = Column(Text)  # New field for category
    published_at = Column(DateTime, nullable=False)
    fetched_at   = Column(DateTime, nullable=False)

class Video(Base):
    __tablename__ = "videos"
    video_id      = Column(String,   primary_key=True)    # YouTube ID
    channel_name  = Column(Text)
    url           = Column(Text)
    title         = Column(Text)
    description   = Column(Text)
    published_at  = Column(DateTime)