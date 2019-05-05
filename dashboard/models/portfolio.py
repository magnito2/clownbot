from .. import db
from datetime import datetime


class Portfolio(db.Model):
    __tablename__ = "portfolios"
    id = db.Column(db.Integer, primary_key=True)
    exchange_account_id = db.Column(db.Integer, db.ForeignKey('exchange_account.id'), nullable=False)
    btc_value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def serialize(self, acc=None):
        return {
            'timestamp': self.timestamp.isoformat(),
            'btc_value': self.btc_value,
        }