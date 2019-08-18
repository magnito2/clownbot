from dashboard.models import Trade, Order
from dashboard import db
from flask_seeder import Seeder

class CorrectTradesTableReplaceClOidwithOid(Seeder):

    def run(self):
        trades = Trade.query.all()
        for trade in trades:
            if trade.buy_order_id:
                buy_order = Order.query.filter_by(client_order_id=trade.buy_order_id).first()
                if buy_order:
                    trade.buy_order_id = buy_order.order_id
            if trade.sell_order_id:
                sell_order = Order.query.filter_by(client_order_id=trade.sell_order_id).first()
                if sell_order:
                    trade.sell_order_id = sell_order.order_id
            print(trade)
            db.session.add(trade)
