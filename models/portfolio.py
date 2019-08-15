from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey('exchange_account.id'), nullable=False)
    exchange_account = relationship("ExchangeAccount", back_populates="portfolio")
    btc_value = Column(Float)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)


    def __repr__(self):
        return f"<Portfolio {self.timestamp} {self.btc_value}"