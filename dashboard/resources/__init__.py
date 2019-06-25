from .. import api
from .auth import UserLogin,UserRegistration, UserLogoutAccess, UserLogoutRefresh, TokenRefresh, SecretResource
from .ordersapi import OrdersAPI
from .api_settings import ExchangeSettings
from .signalsapi import SignalsAPI, CheckedSignalsAPI
from .portfolioapi import PortfolioAPI, BTCValuesAPI
from .manual_orders_api import ManualOrdersAPI, ExchangeSymbolsAPI
from .tradesapi import TradesAPI

api.add_resource(UserRegistration, '/api/registration')
api.add_resource(UserLogin, '/api/login')
api.add_resource(UserLogoutAccess, '/api/logout/access')
api.add_resource(UserLogoutRefresh, '/api/logout/refresh')
api.add_resource(TokenRefresh, '/api/token/refresh')
api.add_resource(SecretResource, '/api/secret')

api.add_resource(ExchangeSettings, '/api/exchange/settings')

api.add_resource(OrdersAPI, '/api/orders/')
api.add_resource(SignalsAPI, '/api/signals')
api.add_resource(CheckedSignalsAPI, '/api/checked-signals')

api.add_resource(PortfolioAPI, '/api/portfolios')
api.add_resource(BTCValuesAPI, '/api/portfolios/btc-values')
api.add_resource(ManualOrdersAPI, '/api/manualorders')
api.add_resource(ExchangeSymbolsAPI, '/api/exchangesymbols')

api.add_resource(TradesAPI, '/api/trades/')