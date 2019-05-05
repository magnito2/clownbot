from sqlalchemy import Column, Integer, DateTime, String, Float
from datetime import datetime

from . import Base

class Trade(Base):

    __tablename__="trades"

    id = Column(Integer, primary_key=True)
    exchange = Column(String(64))
    client_order_id = Column(String(255))
    buy_order_id = Column(String(255))
    sell_order_id = Column(String(255))
    symbol = Column(String(64))
    quote_asset = Column(String(64))
    base_asset = Column(String(64))
    buy_price = Column(Float)
    sell_price = Column(Float)
    buy_quantity = Column(Float)
    sell_quantity = Column(Float)
    buy_quantity_executed = Column(Float)
    sell_quantity_executed = Column(Float)
    buy_status = Column(String(64))
    sell_status = Column(String(64))
    buy_time = Column(DateTime)
    sell_time = Column(DateTime)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)

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

    def __repr__(self):
        return f"<Order({self.id}, BOID {self.buy_order_id}, SOID {self.sell_order_id}, BP {self.buy_price}, SP {self.sell_price}, BQ {self.buy_quantity})"