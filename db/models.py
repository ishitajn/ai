from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class MatchMemoryDB(Base):
    __tablename__ = "match_memories"
    match_id = Column(String, primary_key=True, index=True)
    memory_data = Column(JSON)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())