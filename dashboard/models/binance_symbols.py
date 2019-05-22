from .. import db
from datetime import datetime

class BinanceSymbol(db.Model):

    __tablename__="binance_symbols"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    base_asset = db.Column(db.String(32))
    quote_asset = db.Column(db.String(32))
    min_qty = db.Column(db.Float)
    step_size = db.Column(db.Float)
    min_notional = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    tick_size = db.Column(db.Float)

    def serialize(self):
        return {
            'name': self.name,
            'base_asset' : self.base_asset,
            'quote_asset' : self.quote_asset,
            'lot_size' : self.lot_size,
            'min_qty' : self.min_qty,
            'step_size' : self.step_size,
            'min_notational' : self.min_notional
        }

    def __repr__(self):
        return f"<Binance-Symbol({self.name}>"