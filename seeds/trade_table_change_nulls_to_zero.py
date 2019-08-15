from dashboard.models import Trade
from dashboard import db
from flask_seeder import Seeder

class CorrectTradesTableChangeNullsToZero(Seeder):

    def run(self):
        trades = Trade.query.all()
        for trade in trades:
            if trade.buy_price == None:
                trade.buy_price = 0
            if trade.sell_price == None:
                trade.sell_price = 0
            if trade.buy_quantity == None:
                trade.buy_quantity = 0
            if trade.sell_quantity == None:
                trade.sell_quantity = 0
            if trade.buy_quantity_executed == None:
                trade.buy_quantity_executed = 0
            if trade.sell_quantity_executed == None:
                trade.sell_quantity_executed = 0

            db.session.add(trade)
