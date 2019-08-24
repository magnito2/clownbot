from flask_restful import Resource, abort, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import Trade, ExchangeAccount
from .. import  user_datastore
from sqlalchemy import desc

parser = reqparse.RequestParser()
parser.add_argument("start_id")
parser.add_argument("end_id")
parser.add_argument("start_date", help="This field cannot be empty")
parser.add_argument("end_date", help="This field cannot be empty")
parser.add_argument("exchange_account_id")

class TradesAPI(Resource):

    trades_fields = {
        "id" : fields.Integer(),
        "start_id": fields.Integer(),
        "end_id": fields.Integer(),
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
            if exchange_account and exchange_account in user.exchange_accounts:
                trades = exchange_account.trades
                trades_resp = [trade.serialize() for trade in trades if trade.buy_status != 'CANCELED']
                return trades_resp
        else:
            all_trades = []
            for exchange_account in user.exchange_accounts:
                trades = exchange_account.trades
                trades_resp = [trade.serialize() for trade in trades if trade.buy_status != 'CANCELED']
                all_trades += trades_resp
                print("the trades are ", all_trades)
            return all_trades