from flask_restful import Resource, abort, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import Signal, ExchangeAccount
from .. import  user_datastore, db

parser = reqparse.RequestParser()
parser.add_argument("exchange")
parser.add_argument("signals", type=list, location='json')
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


        exchange_account = ExchangeAccount.query.get(exchange_account_id)
        if exchange_account:
            for signal in signals:
                if signal not in exchange_account.signals:
                    exchange_account.signals.append(signal)

            for signal in exchange_account.signals:
                if signal not in signals:
                    exchange_account.signals.remove(signal)

            db.session.commit()

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
        if not exchange_account:
            abort(401, message="You have not created an account")
        signals = exchange_account.signals
        resp = [signal.name for signal in signals]
        print(f"[+] Signals are {resp}")
        return resp
