from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from db import Base

class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    venue = Column(String, nullable=False)
    start_at = Column(DateTime, default=datetime.utcnow)
    end_at = Column(DateTime, default=datetime.utcnow)
    capacity = Column(Integer, nullable=False)
    status = Column(String, default="published")