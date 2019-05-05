from .. import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exchange = db.Column(db.String(64))
    order_id = db.Column(db.String(128))
    client_order_id = db.Column(db.String(255))
    symbol = db.Column(db.String(64))
    quote_asset = db.Column(db.String(64))
    base_asset = db.Column(db.String(64))
    price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    type = db.Column(db.String(64))
    side = db.Column(db.String(64))
    stop_price = db.Column(db.Float)
    commission = db.Column(db.Float)
    commission_asset = db.Column(db.String(64))
    order_time = db.Column(db.DateTime)
    cummulative_filled_quantity = db.Column(db.Float)
    cummulative_quote_asset_transacted = db.Column(db.Float)
    status = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def serialize(self):
        return {
            'exchange': self.exchange,
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'symbol': self.symbol,
            'quote_asset': self.quote_asset,
            'base_asset': self.base_asset,
            'price': self.price,
            'quantity': self.quantity,
            'type': self.type,
            'side': self.side,
            'stop_price': self.stop_price,
            'commission': self.commission,
            'commission_asset': self.commission_asset,
            'order_time': self.order_time.isoformat(),
            'cummulative_filled_quantity': self.cummulative_filled_quantity,
            'cummulative_quote_asset_transacted': self.cummulative_quote_asset_transacted,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"<Order({self.id}, {self.order_id}, {self.symbol}, {self.side}, {self.price}, {self.quantity})"