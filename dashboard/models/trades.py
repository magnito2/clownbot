from .. import db
from datetime import datetime
from .trade_signals import TradeSignal

class Trade(db.Model):

    __tablename__="trades"

    id = db.Column(db.Integer, primary_key=True)
    exchange_account_id = db.Column(db.Integer, db.ForeignKey('exchange_account.id'), nullable=False)
    exchange = db.Column(db.String(64))
    buy_order_id = db.Column(db.String(255))
    sell_order_id = db.Column(db.String(255))
    symbol = db.Column(db.String(64))
    quote_asset = db.Column(db.String(64))
    base_asset = db.Column(db.String(64))
    buy_price = db.Column(db.Float)
    sell_price = db.Column(db.Float)
    buy_quantity = db.Column(db.Float)
    sell_quantity = db.Column(db.Float)
    buy_quantity_executed = db.Column(db.Float)
    sell_quantity_executed = db.Column(db.Float)
    buy_status = db.Column(db.String(64))
    sell_status = db.Column(db.String(64))
    buy_time = db.Column(db.DateTime)
    sell_time = db.Column(db.DateTime)
    trade_signal_id = db.Column(db.Integer, db.ForeignKey('trade_signals.id'), nullable=True)
    trade_signal = db.relationship('TradeSignal', back_populates='trades', lazy=True)
    signal_id = db.Column(db.Integer, db.ForeignKey('signals.id'), nullable=True)
    signal = db.relationship('Signal', back_populates='trades', lazy=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    health = db.Column(db.String(64))
    reason = db.Column(db.String(255))
    executed_buy_price = db.Column(db.Float) #for binance, cumm_quote_asset/cumm_base_asset
    executed_sell_price = db.Column(db.Float)
    completed = db.Column(db.Boolean) #final mark the no further action shall be taken on this trade. trade marked ready for deletion

    def serialize(self):

        return {
            'id': self.id,
            'exchange': self.exchange,
            'symbol': self.symbol,
            'buy_price' : self.buy_price,
            'sell_price': self.sell_price,
            'buy_order_id': self.buy_order_id,
            'sell_order_d': self.sell_order_id,
            'buy_quantity': self.buy_quantity,
            'sell_quantity': self.sell_quantity,
            'signal': self.trade_signal.signal_name if self.trade_signal else "",
            'PNL': 0 if self.sell_price is None or self.sell_quantity is None or self.buy_price is None or self.buy_price is None else round(self.sell_price * self.sell_quantity - self.buy_price * self.buy_quantity, 6),
            'sell_status': self.sell_status,
            'timestamp': self.timestamp.isoformat(),
            'executed_price_price': self.executed_buy_price,
            'executed_sell_price': self.executed_sell_price,
            'completed': self.completed
        }

    def __repr__(self):
        return f"<Trade({self.id}, BOID {self.buy_order_id}, SOID {self.sell_order_id}, BP {self.buy_price}, SP {self.sell_price}, BQ {self.buy_quantity})>"