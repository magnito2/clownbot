from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base, create_session

class Trade(Base):

    __tablename__="trades"

    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey('exchange_account.id'), nullable=False)

    exchange = Column(String(64))
    buy_order_id = Column(String(255))
    sell_order_id = Column(String(255))
    symbol = Column(String(64))
    quote_asset = Column(String(64))
    base_asset = Column(String(64))
    buy_price = Column(Float, default=0)
    sell_price = Column(Float, default=0)
    buy_quantity = Column(Float, default=0)
    sell_quantity = Column(Float, default=0)
    buy_quantity_executed = Column(Float, default=0)
    sell_quantity_executed = Column(Float, default=0)
    buy_status = Column(String(64))
    sell_status = Column(String(64))
    buy_time = Column(DateTime)
    sell_time = Column(DateTime)
    trade_signal_id = Column(Integer, ForeignKey('trade_signals.id'), nullable=True)
    trade_signal = relationship('TradeSignal', back_populates='trades', lazy=True)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=True)
    signal = relationship('Signal', back_populates='trades', lazy=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    health = Column(String(64))
    reason = Column(String(255))

    def serialize(self):
        return {
            'exchange': self.exchange,
            'symbol': self.symbol,
            'buy_price' : self.buy_price,
            'sell_price': self.sell_price,
            'buy_order_id': self.buy_order_id,
            'sell_order_d': self.sell_order_id,
            'buy_quantity': self.buy_quantity,
            'sell_quantity': self.sell_quantity
        }

    def get_signal(self):
        with create_session() as session:
            return session.query(Trade).filter_by(id=self.id).first().signal

    def __repr__(self):
        return f"<Order({self.id}, BOID {self.buy_order_id}, SOID {self.sell_order_id}, BP {self.buy_price}, SP {self.sell_price}, BQ {self.buy_quantity})"