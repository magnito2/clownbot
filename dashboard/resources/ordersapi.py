from flask_restful import Resource, abort, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import Order, ExchangeAccount
from .. import  user_datastore

parser = reqparse.RequestParser()
parser.add_argument("start_id")
parser.add_argument("end_id")
parser.add_argument("side")
parser.add_argument("start_date", help="This field cannot be empty")
parser.add_argument("end_date", help="This field cannot be empty")
parser.add_argument("exchange_account_id")

class OrdersAPI(Resource):

    orders_fields = {
        "id" : fields.Integer(),
        "start_id": fields.Integer(),
        "end_id": fields.Integer(),
        "side": fields.String(),
        "start_date": fields.DateTime(),
        "end_date": fields.DateTime(),
    }
    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account_id')
        if not user:
            abort(401, message=f"No user found for email {email}")
        if exchange_account_id:
            exchange_account = ExchangeAccount.query.get(exchange_account_id)
            if exchange_account:
                orders = exchange_account.orders
                orders_resp = [order.serialize() for order in orders if order.status != 'CANCELED']
                return orders_resp
        else:
            all_orders = []
            for exchange_account in user.exchange_accounts:
                orders = exchange_account.orders
                orders_resp = [order.serialize() for order in orders if order.status != 'CANCELED']
                all_orders += orders_resp
        return all_orders