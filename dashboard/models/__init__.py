from .. import db
from flask_security import RoleMixin, UserMixin

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    exchange_accounts = db.relationship('ExchangeAccount', backref='user', lazy=True)
    username = db.Column(db.String(255))
    avatar = db.Column(db.String(255))
    tg_address = db.Column(db.String(255))

    def serialize(self):
        return {
            'email' : self.email,
            'username' : self.username,
            'avatar' : self.avatar,
            'tg_address' : self.tg_address,
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

from .trades import Trade
from .orders import Order
from .exchange_accounts import ExchangeAccount
from .revokedtokens import RevokedTokenModel
from .signals import exchange_accounts_signals, Signal
from .portfolio import Portfolio
from .assets import Asset
from .startups import StartUp
from .manual_orders import ManualOrder
from .binance_symbols import BinanceSymbol