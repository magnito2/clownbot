from .. import db
from datetime import datetime

class TradeSignal(db.Model):

    __tablename__="trade_signals"

    id = db.Column(db.Integer, primary_key=True)
    signal_id = db.Column(db.Integer, db.ForeignKey('signals.id'), nullable=False)
    signal_name = db.Column(db.String(64))
    exchange = db.Column(db.String(64))
    symbol = db.Column(db.String(64))
    side = db.Column(db.String(64))
    price = db.Column(db.Float)
    trades = db.relationship('Trade', backref='trade_signal')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def serialize(self):
        return {
            'signal_id': self.signal_id,
            'signal_name': self.signal_name,
            'exchange': self.exchange,
            'side': self.side,
            'price': self.price,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"<Trade Signal({self.signal_name})"