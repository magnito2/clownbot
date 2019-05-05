from sqlalchemy import Column, Integer, DateTime, String, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base

class User(Base):

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    tg_address = Column(String(255))
    orders = relationship('Order', backref='user', lazy=True)