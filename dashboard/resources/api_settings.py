from flask_restful import Resource, reqparse, abort
from flask_jwt_extended import get_jwt_identity, jwt_required
from .. import db, user_datastore, app
from dashboard.models import ExchangeAccount
import requests, re

parser = reqparse.RequestParser()
parser.add_argument('exchange')
parser.add_argument('api_key')
parser.add_argument('api_secret')
parser.add_argument('profit_margin')
parser.add_argument('stop_loss_trigger')
parser.add_argument('order_cancel_seconds')
parser.add_argument('min_order_size')
parser.add_argument('user_tg_id')
parser.add_argument('receive_notifications')
parser.add_argument('fixed_amount_per_order')
parser.add_argument('use_fixed_amount_per_order')

class ExchangeSettings(Resource):

    @jwt_required
    def get(self):
        email = get_jwt_identity()
        current_user = user_datastore.get_user(email)
        if current_user:
            exchange_accounts = [exchange.serialize() for exchange in current_user.exchange_accounts]
            return exchange_accounts
        return 401

    @jwt_required
    def post(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange = args.get('exchange')
        api_key = args.get('api_key')
        api_secret = args.get('api_secret')
        profit_margin = args.get('profit_margin')
        stop_loss_trigger = args.get('stop_loss_trigger')
        cancel_order_seconds = args.get('order_cancel_seconds')
        min_order_percentage = args.get('min_order_size')
        user_tg_id = args.get('user_tg_id')
        receive_notifications = args.get('receive_notifications')
        fixed_amount_per_order = args.get('fixed_amount_per_order')
        use_fixed_amount_per_order = args.get('use_fixed_amount_per_order')

        has_error = False
        response = ''

        exchange_accounts = [account for account in user.exchange_accounts if account.exchange == exchange]
        if exchange_accounts:
            exchange_account = exchange_accounts[0]

            if api_key and not exchange_account.api_key == api_key:
                exchange_account.api_key = api_key
            if api_secret:
                if not re.search("^\*+\*$",api_secret) and not exchange_account.api_secret == api_secret:
                    exchange_account.api_secret = api_secret
            if profit_margin:
                exchange_account.profit_margin = profit_margin
            if stop_loss_trigger:
                exchange_account.stop_loss_trigger = stop_loss_trigger
            if cancel_order_seconds:
                exchange_account.order_cancel_seconds = cancel_order_seconds
            if min_order_percentage:
                exchange_account.min_order_size = min_order_percentage
            if user_tg_id:
                exchange_account.user_tg_id = user_tg_id
            if receive_notifications in ['True', 'False']:
                exchange_account.receive_notifications = True if receive_notifications == "True" else False
            if use_fixed_amount_per_order in ['True', 'False']:
                exchange_account.use_fixed_amount_per_order = True if use_fixed_amount_per_order == "True" else False
            if fixed_amount_per_order:
                exchange_account.fixed_amount_per_order = fixed_amount_per_order

            db.session.commit()

            response = {"action": "starting-bot", "message": "Your trading bot will be started"}

            params = {
                'signal_name': 'AddAccount',
                'command': True,
                'account_id': exchange_account.id
            }
            try:
                resp = requests.post(app.config['BOT_ADDRESS'], json=params)
                if not resp.status_code == 200:
                    response = {'message': "Ooops, we developed a problem handling the command"}
                    has_error = True
                else:
                    result = resp.json()
                    if not result['success']:
                        response = {'message': 'something went wrong somewhere..'}
                        has_error = True
            except requests.exceptions.ConnectionError:
                response = {'message': "The auto trader is currently inaccessible, will start your trades as soon as we make contact"}
                has_error = True
        else:

            exchange_account = ExchangeAccount(exchange=exchange, api_key=api_key, api_secret=api_secret)
            user.exchange_accounts.append(exchange_account)
            db.session.commit()
            response = {"action": "get-settings", "message": "Now set up some options you want to use"}

        if has_error:
            abort(401, message=response.get('message'))
        return response