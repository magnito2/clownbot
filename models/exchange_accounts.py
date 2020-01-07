from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.associationproxy import association_proxy

from . import Base


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
    signals = relationship('Signal', secondary='exchange_accounts_signals', backref='exchange_account')
    portfolio = relationship('Portfolio', back_populates='exchange_account', lazy=True)
    orders = relationship('Order', backref='exchange_account', lazy=True)
    trades = relationship('Trade', backref='exchange_account', lazy=True)
    manual_orders = relationship('ManualOrder', backref='exchange_account', lazy=True)
    valid_keys = Column(Boolean)
    assets = relationship('Asset', backref='exchange_account', lazy=True)
    max_drawdown = Column(Float) #maximum coin to be used in trades per time. defaults to 50%
    max_orders_per_pair = Column(Integer) #maximum orders to be placed per pair
    btc_volume_increase_order_above = Column(Float) #if symbol daily volume is above this, order size will be increased by percent below
    percent_increase_of_order_size = Column(Float)
    sell_only_mode = Column(Boolean)
    max_age_of_trades_in_days = Column(String(64))

    use_different_targets_for_small_prices = Column(Boolean)  # for smaller priced coins, you can increase the targets as price movements are higher
    small_price_value_in_satoshis = Column(Float)  # 1 satoshi == 1/100,000,000 BTC
    small_price_take_profit = Column(Float)
    small_price_stop_loss = Column(Float)

    signal_percent_size = None
    profit_target = None