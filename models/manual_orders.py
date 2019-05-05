from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey
from datetime import datetime

from . import Base

class ManualOrder(Base):
    __tablename__ = "manual_orders"

    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey('exchange_account.id'), nullable=False)
    exchange = Column(String(64))
    symbol = Column(String(64))
    side = Column(String(64))
    price = Column(Float)
    quantity = Column(Float)
    signal_id = Column(String(64))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f"<Manual Order({self.id}, {self.exchange}, {self.symbol}, {self.side}, {self.price}, {self.quantity})"