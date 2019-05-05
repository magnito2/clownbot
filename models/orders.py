from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey
from datetime import datetime

from . import Base, User

class Order(Base):

    __tablename__="orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    exchange = Column(String(64))
    order_id = Column(String(128))
    client_order_id = Column(String(255))
    symbol = Column(String(64))
    quote_asset = Column(String(64))
    base_asset = Column(String(64))
    price = Column(Float)
    quantity = Column(Float)
    type = Column(String(64))
    side = Column(String(64))
    stop_price = Column(Float)
    commission = Column(Float)
    commission_asset = Column(String(64))
    order_time = Column(DateTime)
    cummulative_filled_quantity = Column(Float)
    cummulative_quote_asset_transacted = Column(Float)
    status = Column(String(64))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)


    def __repr__(self):
        return f"<Order({self.id}, {self.order_id}, {self.symbol}, {self.side}, {self.price}, {self.quantity})"