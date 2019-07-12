from .. import db
from datetime import datetime

# Define models
exchange_accounts_signals = db.Table('exchange_accounts_signals',
        db.Column('id', db.Integer, primary_key=True),
        db.Column('exchange_account_id', db.Integer(), db.ForeignKey('exchange_account.id')),
        db.Column('signal_id', db.Integer(), db.ForeignKey('signals.id')))


class Signal(db.Model):
    __tablename__ = "signals"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(255))
    short_name = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    exchange_accounts = db.relationship('ExchangeAccount', secondary=exchange_accounts_signals, backref='ex_signals')

    def serialize(self, acc=None):
        resp =  {
            'name': self.name,
            'description': self.description,
            'short_name': self.short_name
        }
        if acc:
            resp['subscribed'] = True if self in acc.signals else False

        return resp