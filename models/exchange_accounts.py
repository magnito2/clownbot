from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base
from .signals import exchange_accounts_signals

class ExchangeAccount(Base):

    __tablename__ = "exchange_account"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    exchange = Column(String(64))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    profit_margin = Column(Float)
    stop_loss_trigger = Column(Float)
    order_cancel_seconds = Column(Integer)
    min_order_size = Column(Float)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    user_tg_id = Column(String(256))
    receive_notifications = Column(Boolean)
    use_fixed_amount_per_order = Column(Boolean)
    fixed_amount_per_order = Column(Float)
    signals = relationship('Signal', secondary=exchange_accounts_signals, backref='exchange_account')
    portfolio = relationship('Portfolio', backref='exchange_account', lazy=True)
    orders = relationship('Order', backref='exchange_account', lazy=True)
    trades = relationship('Trade', backref='exchange_account', lazy=True)
    manual_orders = relationship('ManualOrder', backref='exchange_account', lazy=True)
    valid_keys = Column(Boolean)
    assets = relationship('Asset', backref='exchange_account', lazy=True)