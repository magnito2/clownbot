from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base

class TradeSignal(Base):
    __tablename__ = "trade_signals"

    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=False)
    signal_name = Column(String(64))
    exchange = Column(String(64))
    symbol = Column(String(64))
    side = Column(String(64))
    price = Column(Float)
    trades = relationship('Trade', backref='trade_signal')
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f"<Trade Signal({self.id}, {self.exchange}, {self.symbol}, {self.side}, {self.price}, {self.quantity})"