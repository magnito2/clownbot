import asyncio
import logging
import re
from datetime import datetime, timedelta

from models import create_session, Order, Asset, Trade, Portfolio, ExchangeAccount
from utils import run_in_executor

logger = logging.getLogger('clone.trader')

KEYS = {
    'binance': {
        'api_key': 'JeJMOBGQqGhFNmKp4szrgrTuHdETrtngq9EwxgV84TZiojhzcy3GW8QQc8YEXTE5',
        'secret_key': 'VV9p8cLqlUiw9bdql8OPDmoHMKVBjDs7YPvYIJs1FiocR5JHPceleF2a0g2vrzML'
    },
    'bittrex': {
        'api_key': '26d765d60cc7457695a0176a6bf3ff43',
        'secret_key': '2fdb68a632ef405cb560ea7862940877'
    }
}

class Trader:
    '''
    Manage 3 queues, updated from outside sources,
    1. Accounts_queue - get events about trades for every account
    2. Trades_queue - get the latest prices of symbols with open orders
    3. Orders_queue - Get signals to create new orders from telegram
    Create, update and destroy orders as necessary
    '''

    time_dict = {'S' : 1,'M' : 60,'H' : 60*60, 'D': 60*60*24, 'W': 60*60*24*7}
    time_re = '(\d+)([HMS]{1}$)'

    def __init__(self, **kwargs):
        self._exchange = '' #use this to separate binance from bittrex, create separate for each
        self.orders_queue = asyncio.Queue()
        self.percent_size = kwargs.get('percent_size') if kwargs.get('percent_size') < 1 else kwargs.get('percent_size') / 100
        self.profit_margin = kwargs.get('profit_margin') if kwargs.get('profit_margin') < 1 else kwargs.get('profit_margin') / 100
        self.order_timeout = kwargs.get('order_timeout')
        self.stop_loss_trigger = kwargs.get('stop_loss_trigger')
        self.streamer = None
        self.active_symbols = []
        self.open_orders = []
        self.active_symbol_prices = {}
        self.outgoing_message_queue = None
        self.user_tg_id = kwargs.get('user_tg_id')
        self.receive_notifications = kwargs.get('receive_notifications')
        self.subscribed_signals = kwargs.get('subscribed_signals')
        self.account_model_id = kwargs.get('exchange_account_model_id')
        self.last_portfolio_update_time = datetime.utcnow()
        self.portfolio_update_interval = kwargs.get('portfolio_update_interval', 300)
        self.keep_running = True

    async def run(self):
        '''
        The main loop, see if this can be removed
        :return:
        1. stream for account events, tell when a trade has occured
        '''
        if self.outgoing_message_queue and self.user_tg_id:
            logger.info(f"[+] Informing user on bot status")
            await self.outgoing_message_queue.put(
                {'id': self.user_tg_id, 'message': f'The bot has been started, you will be recieving updates now'})
        else:
            logger.error(f"[+] TG not set up properly")

        logger.info("[+] Warming up..")
        await self.warmup()
        logger.info(f"[+] Entering the main loop of {self._exchange}")
        while self.keep_running:
            logger.info(f"[+] {self._exchange} Awaiting the next order")
            try:
                _params = await asyncio.wait_for(self.orders_queue.get(), timeout=60)
                logger.info(f"{self._exchange} recieved {_params}")
                if _params and 'exchange' in _params:
                    order_params = _params
                    logger.debug(f'[+] Recieved new order parameters {order_params}')
                    if not type(order_params) is dict:
                        logger.error(f"Supported parameters should be dictionary, got {order_params} of type {type(order_params)}")
                        continue
                    if "signal_name" in order_params and order_params['signal_name'] not in self.subscribed_signals:
                        logger.debug(f"[*] {self._exchange} You have not subscribed to {order_params['signal_name']}")
                        continue
                    if order_params['exchange'] == self._exchange:
                        logger.debug(f'[+] __ New__Order__Being__Created')
                        resp = await self.create_order(**order_params)
                        if resp['error']:
                            logger.error(resp['message'])
                            await self.send_notification(f"Attempt to create an order failed because {resp['message']}")
                            continue
                        logger.info(resp)
                        result = resp['result']
                        self.streamer.add_trades(result['symbol'], self.process_symbol_stream)
                        await self.update_trade(**result)
                        await self.send_notification(f"New order created, {result} ")
                        continue #go to next loop
                    else:
                        logger.debug(f'[!] Order not understood, {order_params}')
                        continue

            except asyncio.TimeoutError:
                logger.info(f"[*] {self._exchange} Regular maintenance")
                await self.routine_check()
                if (datetime.utcnow() - self.last_portfolio_update_time).seconds > self.portfolio_update_interval:
                    self.last_portfolio_update_time = datetime.utcnow()
                    await self.update_portfolio()

            except asyncio.QueueEmpty as e:
                logger.error("The queue is empty")
            except Exception as e:
                logger.exception(e)

    async def warmup(self):
        pass

    async def create_order(self, params):
        pass

    async def update_order(self, id, params):
        pass

    async def cancel_order(self, symbol, id):
        pass

    async def query_order(self, symbol, id):
        pass

    async def get_buy_size(self, symbol, price):
        '''
        Sizing is critical to winning.
        :return:
        '''
        pass

    async def get_sell_size(self, symbol, price):
        '''
        Sizing is critical to winning.
        :return:
        '''
        pass

    async def process_user_socket_message(self, msg):
        pass

    async def process_symbol_stream(self, msg):
        pass

    async def synchronize_exchange(self):
        '''
        Called when warming up, or after lost connection, filled orders.

        :return:
        '''

    def parse_time(self, timestring):
        res = re.search(self.time_re, timestring)
        if res:
            val, interval = res.groups()
            return timedelta(seconds= int(val) * self.time_dict[interval])

    @run_in_executor
    def create_order_model(self, **kwargs):
        self._create_order_model(**kwargs)

    def _create_order_model(self, **kwargs):
        with create_session() as session:
            order = Order(**kwargs)
            session.add(order)
            session.commit()

    @run_in_executor
    def update_order_model(self, **kwargs):
        client_order_id = kwargs.get('client_order_id')
        with create_session() as session:
            order = session.query(Order).filter_by(exchange=self._exchange).filter_by(client_order_id=client_order_id).first()
            if order:
                session.query(Order).filter_by(exchange=self._exchange).filter_by(client_order_id=client_order_id).update(kwargs)
            else:
                order = Order(user_id=1,**kwargs)
                session.add(order)
            session.commit()


    @run_in_executor
    def get_order_model(self, client_order_id):
        with create_session() as session:
            order = session.query(Order).filter_by(exchange=self._exchange).filter_by(client_order_id=client_order_id).first()
            if order:
                return order

    @run_in_executor
    def get_order_models(self, status=None):
        with create_session() as session:
            if not status:
                orders = session.query(Order).filter_by(exchange=self._exchange).all()
            else:
                orders = session.query(Order).filter_by(exchange=self._exchange).filter_by(status=status).all()
            if orders:
                return orders
            else:
                return []

    @run_in_executor
    def get_trade_models(self):
        with create_session() as session:
            trades = session.query(Trade).filter_by(exchange=self._exchange).all()
            if trades:
                return trades
            else:
                return []

    @run_in_executor
    def get_asset_models(self, asset = None):
        with create_session() as session:
            if asset:
                asset_model = session.query(Asset).filter_by(exchange=self._exchange).filter_by(name=asset).first()
                return asset_model
            asset_models = session.query(Asset).filter_by(exchange=self._exchange).all()
            return asset_models

    @run_in_executor
    def update_asset_balance(self, msg):
        with create_session() as session:
            asset_name = msg['name']
            asset_model = session.query(Asset).filter_by(exchange=self._exchange).filter_by(name=asset_name).first()
            if asset_model:
                asset_model.name = asset_name
                asset_model.free = msg['free']
                asset_model.locked = msg['locked']
                asset_model.timestamp = datetime.utcnow()
            else:
                asset_model = Asset(exchange=self._exchange, name=msg['name'], free=msg['free'], locked=msg['locked'])
            session.add(asset_model)
            session.commit()

    @run_in_executor
    def update_asset_balances(self, assets):
        with create_session() as session:
            if not type(assets) == list:
                logger.error(f"assets must be a list")
                return
            for asset in assets:
                asset_name = asset['name']
                asset_model = session.query(Asset).filter_by(exchange=self._exchange).filter_by(name=asset_name).first()
                if asset_model:
                    asset_model.name = asset_name
                    asset_model.free = asset['free']
                    asset_model.locked = asset['locked']
                    asset_model.timestamp = datetime.utcnow()
                else:
                    asset_model = Asset(exchange=self._exchange, name=asset['name'], free=asset['free'], locked=asset['locked'])
                    session.add(asset_model)
            session.commit()

    @run_in_executor
    def update_portfolio_model(self, portfolio):
        with create_session() as session:
            print("="*150)
            print(f"{self._exchange} New portfolio is {portfolio}")
            print("=" * 150)
            portfolio_model = Portfolio(btc_value=portfolio)
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()
            account_model.portfolio.append(portfolio_model)
            session.add(account_model)
            session.commit()

    async def get_asset_balances(self):
        pass

    async def get_recent_orders(self, symbol):
        pass

    async def get_last_price(self, symbol):
        pass

    async def routine_check(self):
        """
        if the order is a buy order, check it has not expired.
        if the order is a sell order, check price for stop loss
        :param order:
        :return:
        """
        pass

    @run_in_executor
    def update_trade(self, **kwargs):
        client_order_id = kwargs.get('client_order_id')
        with create_session() as session:
            trade = session.query(Trade).filter_by(client_order_id=client_order_id).first()
            if trade:
                session.query(Trade).filter_by(client_order_id=client_order_id).update(kwargs)
            else:
                trade = Trade(**kwargs)
                session.add(trade)
            session.commit()

    async def send_notification(self, notification):
        if self.outgoing_message_queue and self.user_tg_id and self.receive_notifications:  # inform user about the new order
            await self.outgoing_message_queue.put({'id': self.user_tg_id, 'message': notification})

    async def update_portfolio(self):
        """
        Runs every set time to save current snapshot of the assets in BTC value
        :return:
        """
        try:
            logger.info(f"[+] {self._exchange} Updating portfolio")
            assets = await self.get_asset_models()
            portfolio = 0
            for asset in assets:
                if asset.name == "BTC":
                    portfolio += (float(asset.free) + float(asset.locked))
                else:
                    if self._exchange ==  "BITTREX":
                        symbol = f"BTC-{asset.name}"
                    elif self._exchange == "BINANCE":
                        symbol = f"{asset.name}BTC"
                    else:
                        logger.error(f"Unknown Exchange {self._exchange}")
                        continue
                    price_resp = await self.get_last_price(symbol)
                    if price_resp['error']:
                        logger.error(f"[!] Couldnt get price of {symbol}, reason: {price_resp['message']}")
                        continue
                    price = float(price_resp['result']['price'])
                    portfolio += (float(asset.free) + float(asset.locked)) * price
            logger.info(f"Total portfolio is {portfolio}")
            await self.update_portfolio_model(portfolio)
        except Exception as e:
            logger.exception(e)