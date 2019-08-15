import os
print(os.path.dirname(os.path.realpath(__file__)))

from dashboard.models import Trade, TradeSignal, Signal
from dashboard import db
from flask_seeder import Seeder

class CorrectTradesTableSeedSignals(Seeder):

    def run(self):
        trade_signals = TradeSignal.query.all()
        for trade_signal in trade_signals:
            trades = trade_signal.trades
            signal = trade_signal.signal
            for trade in trades:
                trade.signal = signal
                db.session.add(trade)
