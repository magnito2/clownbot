from sqlalchemy import Column, Integer, DateTime, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base

exchange_accounts_signals = Table('exchange_accounts_signals', Base.metadata,
    Column('signal_id', Integer, ForeignKey('signals.id')),
    Column('exchange_account_id', Integer, ForeignKey('exchange_account.id')))

class Signal(Base):

    __tablename__="signals"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    exchange_accounts = relationship('ExchangeAccount', secondary=exchange_accounts_signals, backref='acc_signals')
    trade_signals = relationship('TradeSignal', backref='signal', lazy=True)

    def __repr__(self):
        return f"<Signal({self.id}, {self.timestamp})"