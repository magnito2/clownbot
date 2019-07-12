from .. import db
from datetime import datetime
from .signals import exchange_accounts_signals

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
    signals = db.relationship('Signal', secondary=exchange_accounts_signals, backref='exchange_account')
    portfolio = db.relationship('Portfolio', backref='exchange_account', lazy=True)
    orders = db.relationship('Order', backref='exchange_account', lazy=True)
    trades = db.relationship('Trade', backref='exchange_account', lazy=True)
    manual_orders = db.relationship('ManualOrder', backref='exchange_account', lazy=True)
    assets = db.relationship('Asset', backref='exchange_account', lazy=True)
    valid_keys = db.Column(db.Boolean)
    max_drawdown = db.Column(db.Float)  # maximum coin to be used in trades per time. defaults to 50%
    max_orders_per_pair = db.Column(db.Integer)  # maximum orders to be placed per pair

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
            'max_orders_per_pair': self.max_orders_per_pair
        }

    def __repr__(self):
        return f"<{self.exchange}-({self.id}, {self.profit_margin}, {self.stop_loss_trigger}, {self.order_cancel_seconds}, {self.min_order_size}, User{self.user_id})>"
