from sqlalchemy import Column, Text, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    
    id           = Column(String(64), primary_key=True)   # sha256 hash of URL
    source_name  = Column(Text, nullable=False)
    url          = Column(Text, unique=True, nullable=False)
    title        = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    fetched_at   = Column(DateTime, nullable=False)
