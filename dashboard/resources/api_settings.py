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
parser.add_argument('btc_volume_increase_order_above')
parser.add_argument('percent_increase_of_order_size')
parser.add_argument('sell_only_mode')

parser.add_argument('use_different_targets_for_small_prices')
parser.add_argument('small_price_value_in_satoshis')
parser.add_argument('small_price_take_profit')
parser.add_argument('small_price_stop_loss')

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
        btc_volume_increase_order_above = args.get('btc_volume_increase_order_above')
        percent_increase_of_order_size = args.get('percent_increase_of_order_size')
        sell_only_mode = args.get('sell_only_mode')

        use_different_targets_for_small_prices = args.get('use_different_targets_for_small_prices')
        small_price_value_in_satoshis = args.get('small_price_value_in_satoshis')
        small_price_take_profit = args.get('small_price_take_profit')
        small_price_stop_loss = args.get('small_price_stop_loss')

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
            if btc_volume_increase_order_above and percent_increase_of_order_size and float(btc_volume_increase_order_above):
                exchange_account.btc_volume_increase_order_above = btc_volume_increase_order_above
                exchange_account.percent_increase_of_order_size = float(percent_increase_of_order_size) / 100
            else:
                if exchange_account.btc_volume_increase_order_above or exchange_account.percent_increase_of_order_size:
                    exchange_account.btc_volume_increase_order_above = 0
                    exchange_account.percent_increase_of_order_size = 0
            if sell_only_mode in ['True', 'False']:
                exchange_account.sell_only_mode = True if sell_only_mode == "True" else False

            if use_different_targets_for_small_prices in ['True', 'False']:
                exchange_account.use_different_targets_for_small_prices = True if use_different_targets_for_small_prices == "True" else False
            if small_price_value_in_satoshis:
                exchange_account.small_price_value_in_satoshis = small_price_value_in_satoshis
            if small_price_take_profit:
                exchange_account.small_price_take_profit = small_price_take_profit
            if small_price_stop_loss:
                exchange_account.small_price_stop_loss = small_price_stop_loss

            db.session.add(exchange_account)
            db.session.commit()

            response = {"action": "starting-bot", "message": "Your trading bot will be started"}

            params = {
                'signal_name': 'AddAccount',
                'command': True,
                'account_id': exchange_account.id
            }
            try:
                resp = requests.post(app.config['BOT_ADDRESS'], json=params, timeout=15)
                if not resp.status_code == 200:
                    print(resp.raw())
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
            except requests.Timeout:
                response = {'message': "The auto trader is currently inaccessible, will start your trades as soon as we make contact"}
                has_error = True

            except Exception as e:
                response = {'message': str(e)}
                has_error = True
        else:

            exchange_account = ExchangeAccount(exchange=exchange, api_key=api_key, api_secret=api_secret)
            user.exchange_accounts.append(exchange_account)
            db.session.commit()
            response = {"action": "get-settings", "message": "Now set up some options you want to use"}

        if has_error:
            abort(401, message=response.get('message'))
        return response