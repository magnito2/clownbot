from sqlalchemy import Column, Integer, DateTime, String, Float
from datetime import datetime

from . import Base

class BinanceSymbol(Base):

    __tablename__="binance_symbols"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    base_asset = Column(String(32))
    quote_asset = Column(String(32))
    min_qty = Column(Float)
    step_size = Column(Float)
    min_notional = Column(Float)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    tick_size = Column(Float)

    def __repr__(self):
        return f"<Binance-Symbol({self.name}>"