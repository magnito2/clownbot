from sqlalchemy import Column, Integer, DateTime, String, Float
from datetime import datetime

from . import Base

class StartUp(Base):

    __tablename__="startups"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f"<Startup({self.id}, {self.timestamp})"