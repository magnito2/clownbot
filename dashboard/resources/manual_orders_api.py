from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import ExchangeAccount, ManualOrder
from .. import  user_datastore, db, app
import requests
from ..myutils import get_binance_symbols, get_bittrex_symbols

import logging

logger = logging.getLogger(__name__)

parser = reqparse.RequestParser()
parser.add_argument("exchange")
parser.add_argument("exchange_account_id")
parser.add_argument('symbol')
parser.add_argument('side')
parser.add_argument('price')
parser.add_argument('quantity')

class ManualOrdersAPI(Resource):
    '''
            {
                'signal_name' : channel name
                'symbol': signal_tup[0],
                'exchange': signal_tup[1],
                'side': signal_tup[2],
                'price': float(signal_tup[3]),
                'quantity' : float
                'target_price': float(signal_tup[4]),
                'signal_id': signal_tup[5]
            }
    '''

    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account_id')
        if not user:
            abort(401, message=f"No user found for email {email}")
        if not exchange_account_id:
            abort(404, message=f"No orders found")

        exchange_account = ExchangeAccount.query.get(exchange_account_id)
        manual_orders = exchange_account.manual_orders
        resp = [order.serialize() for order in manual_orders]
        return resp

    @jwt_required
    def post(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account_id')
        exchange = args.get('exchange')
        symbol = args.get('symbol')
        side = args.get('side')
        price = args.get('price')
        quantity = args.get('quantity')
        if not user:
            abort(401, message=f"No user found for email {email}")
        if not exchange_account_id:
            abort(404, message=f"No orders found")

        if not exchange_account_id  and not exchange and not symbol and not side and not price and not quantity:
            abort(401, message=f"Provide all required details")

        order_params = {
            'signal_name': 'ManualOrder',
            'exchange': exchange,
            'symbol': symbol,
            'side': side,
            'price': price,
            'quantity': quantity,
            'signal_id': None,
            'signal': True
        }
        exchange_account = ExchangeAccount.query.get(exchange_account_id)

        try:
            resp = requests.post(app.config['BOT_ADDRESS'], json=order_params)
            if not resp.status_code == 200:
                print(resp.raw)
                abort(500, message="Ooops, we developed a problem handling the command")
            result = resp.json()
            if not result['success']:
                abort(500, message="something went wrong somewhere..")
            new_order = ManualOrder(exchange = exchange, symbol=symbol, side=side, price=price, quantity=quantity, signal_id=None)
            exchange_account.manual_orders.append(new_order)
            db.session.commit()

        except Exception as e:
            logger.exception(e)
            abort(401, message="failed to create new order")

        if not exchange_account:
            abort(404, message=f"No account found")

class ExchangeSymbolsAPI(Resource):


    def get(self):

        args = parser.parse_args()
        exchange = args.get('exchange')
        if exchange == "BINANCE":
            resp = get_binance_symbols()
            if resp['error']:
                abort(500, message=resp['message'])
            return {'exchange': 'BINANCE', 'symbols': resp['result']}

        if exchange == "BITTREX":
            resp = get_bittrex_symbols()
            if resp['error']:
                abort(500, message=resp['message'])
            return {'exchange': 'BITTREX', 'symbols': resp['result']}