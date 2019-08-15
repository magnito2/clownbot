from sqlalchemy import Column, Integer, DateTime, String, Table, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from datetime import datetime

from . import Base

'''exchange_accounts_signals = Table('exchange_accounts_signals', Base.metadata,
    Column('signal_id', Integer, ForeignKey('signals.id')),
    Column('exchange_account_id', Integer, ForeignKey('exchange_account.id')))'''

class Signal(Base):

    __tablename__="signals"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    short_name = Column(String(64))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    exchange_accounts = relationship('ExchangeAccount', secondary='exchange_accounts_signals', backref='acc_signals')
    trade_signals = relationship('TradeSignal', back_populates='signal', lazy=True)
    trades = relationship('Trade', back_populates='signal', lazy=True)

    def __repr__(self):
        return f"<Signal({self.id}, {self.short_name} {self.timestamp})"
