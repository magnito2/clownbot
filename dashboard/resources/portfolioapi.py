from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import ExchangeAccount, Portfolio
from .. import  user_datastore, db

parser = reqparse.RequestParser()

class PortfolioAPI(Resource):


    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)
        if not user:
            abort(401, message=f"No user found for email {email}")

        exchange_accounts = user.exchange_accounts
        if not exchange_accounts:
            abort(401, message="You need to create an account")
        resp = {}
        labels = Portfolio.create_labels(user)
        for account in exchange_accounts:
            resp[account.exchange] = Portfolio.serialize_with_labels(labels, account.portfolio)

        return {
            'portfolios': resp,
            'labels': [label.isoformat() for label in labels]
        }

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
                    'timestamp': account.portfolio[-1].timestamp.isoformat(),
                    'is_active': account.valid_keys
                }
                portfolios.append(btc_values)
        return portfolios