from .. import db
from datetime import datetime

class ExchangeAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exchange = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(255), unique=True, nullable=False)
    api_secret = db.Column(db.String(255), nullable=False)
    profit_margin = db.Column(db.Float)
    stop_loss_trigger = db.Column(db.Float)
    order_cancel_seconds = db.Column(db.Integer)
    min_order_size = db.Column(db.Float)
    fixed_amount_per_order = db.Column(db.Float)
    use_fixed_amount_per_order = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_tg_id = db.Column(db.String(256))
    receive_notifications = db.Column(db.Boolean)
    signals = db.relationship('Signal', secondary='exchange_accounts_signals', backref='exchange_account')
    portfolio = db.relationship('Portfolio', backref='exchange_account', lazy=True)
    orders = db.relationship('Order', backref='exchange_account', lazy=True)
    trades = db.relationship('Trade', backref='exchange_account', lazy=True, order_by="desc(Trade.id)")
    manual_orders = db.relationship('ManualOrder', backref='exchange_account', lazy=True)
    assets = db.relationship('Asset', backref='exchange_account', lazy=True)
    valid_keys = db.Column(db.Boolean)
    max_drawdown = db.Column(db.Float)  # maximum coin to be used in trades per time. defaults to 50%
    max_orders_per_pair = db.Column(db.Integer)  # maximum orders to be placed per pair
    btc_volume_increase_order_above = db.Column(
        db.Float)  # if symbol daily volume is above this, order size will be increased by percent below
    percent_increase_of_order_size = db.Column(db.Float)
    sell_only_mode = db.Column(db.Boolean)
    max_age_of_trades_in_days = db.Column(db.String(64))

    use_different_targets_for_small_prices = db.Column(db.Boolean) #for smaller priced coins, you can increase the targets as price movements are higher
    small_price_value_in_satoshis = db.Column(db.Float) # 1 satoshi == 1/100,000,000 BTC
    small_price_take_profit = db.Column(db.Float)
    small_price_stop_loss = db.Column(db.Float)

    def serialize(self):
        return {
            'exchange': self.exchange,
            'exchange_account_id': self.id,
            'api_key': self.api_key,
            'api_secret': '*'*16,
            'profit_margin': self.profit_margin,
            'stop_loss_trigger': self.stop_loss_trigger,
            'order_cancel_seconds': self.order_cancel_seconds,
            'min_order_size': self.min_order_size,
            'timestamp': self.timestamp.isoformat(),
            'user_tg_id': self.user_tg_id,
            'receive_notifications': self.receive_notifications,
            'fixed_amount_per_order': self.fixed_amount_per_order,
            'use_fixed_amount_per_order': self.use_fixed_amount_per_order,
            'portfolio_uri': f'/api/portfolio?exchange_account_id={self.id}',
            'valid_keys': self.valid_keys,
            'max_drawdown': self.max_drawdown,
            'max_orders_per_pair': self.max_orders_per_pair,
            'sell_only_mode': self.sell_only_mode,
            'btc_volume_increase_order_above': self.btc_volume_increase_order_above,
            'percent_increase_of_order_size': self.percent_increase_of_order_size *100 if self.percent_increase_of_order_size else 0, #remember this, always.
            'max_age_of_trades_in_days' : self.max_age_of_trades_in_days,

            'use_different_targets_for_small_prices': self.use_different_targets_for_small_prices,
            'small_price_value_in_satoshis': self.small_price_value_in_satoshis,
            'small_price_take_profit': self.small_price_take_profit,
            'small_price_stop_loss': self.small_price_stop_loss
        }

    def __repr__(self):
        return f"<{self.exchange}-({self.id}, {self.profit_margin}, {self.stop_loss_trigger}, {self.order_cancel_seconds}, {self.min_order_size}, User{self.user_id})>"
