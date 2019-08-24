from flask_restful import Resource, abort, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import Trade, ExchangeAccount
from .. import  user_datastore
from sqlalchemy import desc

parser = reqparse.RequestParser()
parser.add_argument("exchange_account_id")

class AssetsApi(Resource):

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
                assets = exchange_account.assets
                assets_resp = [asset.serialize() for asset in assets]
                return assets_resp
        else:
            all_assets = {}
            for exchange_account in user.exchange_accounts:
                assets = exchange_account.assets
                assets_resp = [asset.serialize() for asset in assets]
                all_assets[exchange_account.exchange] = assets_resp
                print("the assets are ", all_assets)
            accounts = [{'exchange' : exchange_account.exchange, 'exchange_account_id' : exchange_account.id} for exchange_account in user.exchange_accounts]
            return {
                'assets': all_assets,
                'accounts': accounts
            }

