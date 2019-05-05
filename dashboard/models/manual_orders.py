from .. import db
from datetime import datetime

class ManualOrder(db.Model):
    __tablename__ = "manual_orders"

    id = db.Column(db.Integer, primary_key=True)
    exchange_account_id = db.Column(db.Integer, db.ForeignKey('exchange_account.id'), nullable=False)
    exchange = db.Column(db.String(64))
    symbol = db.Column(db.String(64))
    side = db.Column(db.String(64))
    price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    signal_id = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def serialize(self):
        return {
            'exchange': self.exchange,
            'exchange_account_id': self.exchange_account_id,
            'symbol': self.symbol,
            'side': self.side,
            'price': self.price,
            'quantity': self.quantity,
            'signal_id': self.signal_id,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"<Manual Order({self.id}, {self.exchange}, {self.symbol}, {self.side}, {self.price}, {self.quantity})"