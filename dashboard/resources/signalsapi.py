from flask_restful import Resource, abort, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import Signal, ExchangeAccount
from .. import  user_datastore, db

parser = reqparse.RequestParser()
parser.add_argument("exchange")
parser.add_argument("signals", type=list, location='json')
parser.add_argument("account_signals_params", type=dict, location='json', action='append')
parser.add_argument("exchange_account")

class SignalsAPI(Resource):

    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account')
        if not user:
            abort(401, message=f"No user found for email {email}")
        if not exchange_account_id:
            return [signal.serialize() for signal in Signal.query.all()]
        print(f"Exchange account id is {exchange_account_id}")
        exchange_account = ExchangeAccount.query.get(exchange_account_id)
        signals = Signal.query.all()
        resp = [signal.serialize(exchange_account) for signal in signals]
        return resp

    @jwt_required
    def post(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account')
        signal_names = args.get('signals')
        signals = [Signal.query.filter_by(name=signal_name).first() for signal_name in signal_names]

        account_signals_params = args.get('account_signals_params', [])

        exchange_account = ExchangeAccount.query.get(exchange_account_id)
        if not exchange_account in user.exchange_accounts:
            abort(401, message=f"Oooops")
        if exchange_account:
            for signal in signals:
                if signal not in exchange_account.signals:
                    exchange_account.signals.append(signal)

            for signal in exchange_account.signals:
                if signal not in signals:
                    exchange_account.signals.remove(signal)

            db.session.commit()

            signals_assoc = exchange_account.signal_assoc
            print("*" * 50)
            print(account_signals_params)
            if not account_signals_params:
                account_signals_params = []
            for sig_params in account_signals_params:
                for signal_assoc in signals_assoc:
                    if sig_params['name'] == signal_assoc.signal.name:
                        if sig_params.get('percent_investment') != signal_assoc.percent_investment:
                            signal_assoc.percent_investment = sig_params.get('percent_investment')
                        if sig_params.get('profit_target') != signal_assoc.profit_target:
                            signal_assoc.profit_target = sig_params.get('profit_target')
            print(f"[+] Signals associations are {signals_assoc}")
            for sig_acc in signals_assoc:
                print(f"Signal {sig_acc.signal} account {sig_acc.exchange_account}")

            print(f"[+] Signals associations are {signals_assoc}")

            db.session.commit()

            signals = exchange_account.signals
            sig_names = [signal.name for signal in signals]
            signals_assocs = exchange_account.signal_assoc
            extra_params = []
            for signal_assoc in signals_assocs:
                sig_extra_params = {
                    'name': signal_assoc.signal.name,
                    'profit_target': signal_assoc.profit_target,
                    'percent_investment': signal_assoc.percent_investment
                }
                extra_params.append(sig_extra_params)
            return {'signal_names': sig_names, 'extra_params': extra_params}

class CheckedSignalsAPI(Resource):

    @jwt_required
    def get(self):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)

        args = parser.parse_args()
        exchange_account_id = args.get('exchange_account')
        if not user:
            abort(401, message=f"No user found for email {email}")

        exchange_account = ExchangeAccount.query.get(exchange_account_id)
        if not exchange_account in user.exchange_accounts:
            abort(401, message="Chai!")
        signals = exchange_account.signals
        sig_names = [signal.name for signal in signals]
        signals_assocs = exchange_account.signal_assoc
        extra_params = []
        for signal_assoc in signals_assocs:
            sig_extra_params = {
                'name' : signal_assoc.signal.name,
                'profit_target' : signal_assoc.profit_target,
                'percent_investment' : signal_assoc.percent_investment
            }
            extra_params.append(sig_extra_params)
        return {'signal_names': sig_names, 'extra_params': extra_params}
