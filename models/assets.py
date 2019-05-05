from sqlalchemy import Column, Integer, DateTime, String, Float
from datetime import datetime

from . import Base

class Asset(Base):

    __tablename__="assets"

    id = Column(Integer, primary_key=True)
    exchange = Column(String(64))
    name = Column(String(64))
    free = Column(String(128))
    locked = Column(String(128))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)

    def serialize(self):
        return {
            'name': self.name,
            'free' : self.free,
            'locked': self.locked
        }

    def __repr__(self):
        return f"<Asset({self.id}, {self.name}, free {self.free}, locked {self.locked})>"