from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import ExchangeAccount, Portfolio
from .. import  user_datastore, db

parser = reqparse.RequestParser()
parser.add_argument("exchange_account_id")

class PortfolioAPI(Resource):


    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account_id')
        if not user:
            abort(401, message=f"No user found for email {email}")
        if not exchange_account_id:
            abort(401, message=f"No exchange account found for {exchange_account_id}")
        exchange_account = ExchangeAccount.query.get(exchange_account_id)
        portfolios = exchange_account.portfolio
        if portfolios:
            return [portfolio.serialize() for portfolio in portfolios]

class BTCValuesAPI(Resource):

    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)
        if not user:
            abort(401, message=f"No user found for email {email}")
        portfolios = []
        for account in user.exchange_accounts:
            if account.portfolio:
                btc_values = {
                    'exchange': account.exchange,
                    'btc_value': account.portfolio[-1].btc_value,
                    'timestamp': account.portfolio[-1].timestamp.isoformat()
                }
                portfolios.append(btc_values)
        return portfolios