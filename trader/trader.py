import asyncio
import logging
import re
from datetime import datetime, timedelta

from models import create_session, Order, Asset, Trade, Portfolio, ExchangeAccount
from utils import run_in_executor
from utils.sync import async_to_sync, sync_to_async
import emoji

from trader.binance_portfolio import get_btc_price

logger = logging.getLogger('clone.trader')
#logger.setLevel(logging.)

class Trader:
    '''
    Manage 3 queues, updated from outside sources,
    1. Accounts_queue - get events about trades for every account
    2. Trades_queue - get the latest prices of symbols with open orders
    3. Orders_queue - Get signals to create new orders from telegram
    Create, update and destroy orders as necessary
    '''

    time_dict = {'S' : 1,'M' : 60,'H' : 60*60, 'D': 60*60*24, 'W': 60*60*24*7}
    time_re = '(\d+)([WDHMS]{1}$)'

    def __init__(self, **kwargs):
        self._exchange = '' #use this to separate binance from bittrex, create separate for each
        self.orders_queue = asyncio.Queue(maxsize=10)
        self.percent_size = None
        self.btc_per_order = None
        self.profit_margin = kwargs.get('profit_margin') / 100
        self.order_timeout = kwargs.get('order_timeout')
        self.stop_loss_trigger = kwargs.get('stop_loss_trigger') / 100
        self.active_symbols = []
        self.open_orders = []
        self.active_symbol_prices = {}
        self.outgoing_message_queue = None
        self.user_tg_id = kwargs.get('user_tg_id')
        self.receive_notifications = kwargs.get('receive_notifications')
        self.subscribed_signals = kwargs.get('subscribed_signals')
        self.account_model_id = kwargs.get('exchange_account_model_id')
        self.last_portfolio_update_time = datetime.utcnow()
        self.portfolio_update_interval = kwargs.get('portfolio_update_interval', 60*60*2)
        self.keep_running = True
        self.api_key = kwargs.get('api_key')

        self.routine_check_interval = 60*5

        if kwargs.get('use_fixed_amount_per_order') and kwargs.get('fixed_amount_per_order'):
            self.btc_per_order = float(kwargs.get('fixed_amount_per_order'))
        if kwargs.get('percent_size'):
            self.percent_size = float(kwargs.get('percent_size')) / 100

        self.username = kwargs.get('username')
        self.max_orders_per_symbol = kwargs.get('max_orders_per_symbol') if kwargs.get('max_orders_per_symbol') else 2

        self.btc_volume_increase_order_above = kwargs.get('btc_volume_increase_order_above') if kwargs.get('btc_volume_increase_order_above') else 0
        self.percent_increase_of_order_size = kwargs.get('percent_increase_of_order_size') if kwargs.get('percent_increase_of_order_size') else 0

        self.sell_only_mode = kwargs.get('sell_only_mode', False)

        self.last_assets_update = datetime.fromtimestamp(0)
        self.max_age_of_portfolio_in_days = 100
        self.max_age_of_trades_in_days = kwargs.get('max_age_of_trades_in_days') if kwargs.get('max_age_of_trades_in_days') else "7D"

    async def run(self):
        '''
        The main loop, see if this can be removed
        :return:
        1. stream for account events, tell when a trade has occured
        '''

        is_valid = await self._validate_keys()
        if not is_valid:
            await self.send_notification(f"{emoji.emojize(':bangbang:', use_aliases=True)} The API key and Secret for {self._exchange} is INVALID. Please provide valid keys.")
            logging.error(f"[!] Invalid Keys provide for account {self._exchange} - {self.api_key}")
            return

        await self.warmup()

        logger.info(f"[+] Entering the main loop")
        while self.keep_running:
            logger.info(f"[+] {self.username}-{self._exchange} Awaiting the next order")
            try:
                _params = await asyncio.wait_for(self.orders_queue.get(), timeout=self.routine_check_interval)
                logger.info(f"{self.username}-{self._exchange} recieved {_params}")
                if _params and 'exchange' in _params:
                    order_params = _params
                    logger.info(f'[+] {self.username} Recieved new order parameters')
                    if not type(order_params) is dict:
                        logger.error(f"Supported parameters should be dictionary, got {order_params} of type {type(order_params)}")
                        continue
                    if "signal_name" in order_params and order_params['signal_name'] not in self.subscribed_signals:
                        logger.info(f"[*]{self.username} {self._exchange} You have not subscribed to {order_params['signal_name']}")
                        continue
                    if order_params['exchange'] == self._exchange:
                        if order_params['side'] == 'BUY' and self.sell_only_mode:
                            logger.info(f"{self.username} Bot is in sell only model, not placing order {order_params}")
                            continue

                        logger.info(f'[+] {self.username}__ New__Order__Being__Created')

                        '''
                        Allow for overiding default params with user specified params for signal
                        '''

                        resp = await self.create_order(**order_params)
                        if resp['error']:
                            logger.error(f"{self.username} {resp['message']}")
                            if self._exchange == "BINANCE" and order_params['side'] == "SELL":
                                trade_model = await self.get_trade_model(buy_order_id=order_params['buy_order_id'])
                                if not trade_model:
                                    self.price_streamer.unsubscribe(order_params['symbol'], order_params['buy_order_id'])
                                if "SELL" in order_params['order_id'] :
                                    await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                            buy_order_id=trade_model.buy_order_id, health="ERROR",
                                                            reason=resp['message'])
                            continue
                        logger.info(resp)
                        result = resp['result']

                        signal_id = result.get('signal_id')


                        await self.update_trade(**result)
                        await asyncio.sleep(3)
                        trade_model = await self.get_trade_model(buy_order_id=result['buy_order_id'])
                        if not trade_model:
                            logger.error(f"[+] Could not find trade model of id {result['buy_order_id']}")
                            continue
                        logger.info("*"*100)
                        logger.info(result)
                        if result['side'] == "BUY":
                            signal = trade_model.get_signal()
                            if signal:
                                signal_assoc = await sync_to_async(self.get_account_signal_assoc)(signal_id=signal.id)
                                if signal_assoc and signal_assoc.profit_target:
                                    sell_price = trade_model.buy_price * (1 + float(signal_assoc.profit_target)/100)
                                else:
                                    sell_price = trade_model.buy_price * (1 + self.profit_margin)
                            else:
                                sell_price = trade_model.buy_price * (1 + self.profit_margin)

                            await self.send_notification(f"{emoji.emojize(':new:', use_aliases=True)} Trade Initiated\n{emoji.emojize(':id:', use_aliases=True)}: #{trade_model.id}\n"
                                                     f"Symbol: {result['symbol']}\nQuantity: {float(result['buy_quantity']):.8f} \nEntry price: {float(result['buy_price']):.8f}\n"
                                                     f"Target price: {sell_price:.8f}\n"
                                                     f"Stop loss trigger price: {float(result['buy_price']) * (1 - self.stop_loss_trigger):.8f}\n"
                                                     f"Signal: {resp['additional_info']['signal']}")
                        elif result['side'] == "SELL":
                            if trade_model.executed_buy_price and float(trade_model.sell_price) > float(trade_model.executed_buy_price): #if executed buy price is available, use it
                                await self.send_notification(
                                    f"{emoji.emojize(':white_check_mark:', use_aliases=True)}Now Selling\n {emoji.emojize(':id:', use_aliases=True)}: #{trade_model.id}\n"
                                    f"Symbol: {trade_model.symbol}\n Buy price: {float(trade_model.executed_buy_price):.8f}\n Sell price: {float(trade_model.sell_price):.8f}\n"
                                    f"Quantity Bought: {float(trade_model.buy_quantity):.8f}\n"
                                    f"Quantity Selling: {float(trade_model.sell_quantity):.8f}")
                            elif float(trade_model.sell_price) > float(trade_model.buy_price):
                                await self.send_notification(
                                    f"{emoji.emojize(':white_check_mark:', use_aliases=True)}Now Selling\n {emoji.emojize(':id:', use_aliases=True)}: #{trade_model.id}\n"
                                    f"Symbol: {trade_model.symbol}\n Buy price: {float(trade_model.buy_price):.8f}\n Sell price: {float(trade_model.sell_price):.8f}\n"
                                    f"Quantity Bought: {float(trade_model.buy_quantity):.8f}\n"
                                    f"Quantity Selling: {float(trade_model.sell_quantity):.8f}")
                            else:
                                await self.send_notification(
                                    f"{emoji.emojize(':red_circle:', use_aliases=True)}Stop loss, Selling\n {emoji.emojize(':id:', use_aliases=True)}: #{trade_model.id}\n"
                                    f"Symbol: {trade_model.symbol}\n Buy price: {float(trade_model.buy_price):.8f}\n Sell price: {float(trade_model.sell_price):.8f}\n"
                                    f"Quantity: {float(trade_model.sell_quantity):.8f}")
                        continue #go to next loop
                    else:
                        logger.info(f'[!]{self.username} Order not understood, {order_params}')
                        continue

                elif 'alive_check' in _params:
                    logger.info(f"[+] {self.username} Bot is alive")
                    monitor = _params['monitor']
                    await monitor.confirm_alive(self.api_key)

            except asyncio.TimeoutError:
                logger.info(f"[*] {self._exchange} Regular maintenance")

                if (datetime.utcnow() - self.last_portfolio_update_time).seconds > self.portfolio_update_interval:
                    self.last_portfolio_update_time = datetime.utcnow()
                    await self.update_portfolio()

                await self.routine_check()

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
        if type(timestring) == str:
            res = re.search(self.time_re, timestring)
            if res:
                val, interval = res.groups()
                return timedelta(seconds= int(val) * self.time_dict[interval])
        else:
            return timedelta(seconds=timestring)

    @run_in_executor
    def create_order_model(self, **kwargs):
        self._create_order_model(**kwargs)

    def _create_order_model(self, **kwargs):
        with create_session() as session:
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()
            order = Order(**kwargs)
            account_model.orders.append(order)
            session.commit()

    @run_in_executor
    def update_order_model(self, **kwargs):
        return self._update_order_model(**kwargs)

    def _update_order_model(self, **kwargs):

        order_id = kwargs.get('order_id')
        if not order_id:
            return False
        with create_session() as session:
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()

            order = session.query(Order).filter_by(exchange=self._exchange).filter_by(order_id=order_id).first()
            if order:
                session.query(Order).filter_by(exchange=self._exchange).filter_by(order_id=order_id).update(kwargs)
            else:
                order = Order(**kwargs)
                account_model.orders.append(order)
            session.commit()

    @run_in_executor
    def get_order_model(self, client_order_id=None, order_id=None):
        return self.sync_get_order_model(client_order_id, order_id)

    def sync_get_order_model(self, client_order_id=None, order_id=None):
        with create_session() as session:
            if client_order_id:
                order = session.query(Order).filter_by(exchange=self._exchange).filter_by(client_order_id=client_order_id).first()
            elif order_id:
                order = session.query(Order).filter_by(exchange=self._exchange).filter_by(order_id=order_id).first()
            else:
                return None
            if order:
                return order

    @run_in_executor
    def get_order_models(self, status=None):
        with create_session() as session:
            if not status:
                orders = session.query(Order).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).all()
            else:
                orders = session.query(Order).filter_by(exchange=self._exchange).filter_by(status=status).filter_by(exchange_account_id=self.account_model_id).all()
            if orders:
                return orders
            else:
                return []

    @run_in_executor
    def delete_order_model(self, order_id):
        with create_session() as session:
            order = session.query(Order).filter_by(exchange=self._exchange).filter_by(order_id=order_id).first()
            if order:
                session.delete(order)
                session.commit()
                return True

    @run_in_executor
    def get_trade_models(self):
        with create_session() as session:
            trades = session.query(Trade).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).all()
            if trades:
                return trades
            else:
                return []

    @run_in_executor
    def get_trade_model(self, buy_order_id=None, sell_order_id=None):
        with create_session() as session:
            trade = None
            if buy_order_id:
                trade = session.query(Trade).filter_by(buy_order_id=buy_order_id).first()
            elif sell_order_id:
                trade = session.query(Trade).filter_by(sell_order_id=sell_order_id).first()
            return trade

    @run_in_executor
    def delete_trade_model(self, buy_order_id):
        with create_session() as session:
            trade = session.query(Trade).filter_by(buy_order_id=buy_order_id).first()
            session.delete(trade)
            session.commit()
        return True

    @run_in_executor
    def get_asset_models(self, asset = None):
        return self._get_asset_models(asset)

    def _get_asset_models(self, asset=None):
        with create_session() as session:
            if asset:
                asset_model = session.query(Asset).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).filter_by(name=asset).first()
                return asset_model
            asset_models = session.query(Asset).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).all()
            return asset_models

    @run_in_executor
    def update_asset_balance(self, msg):
        with create_session() as session:
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()
            asset_name = msg['name']
            asset_model = session.query(Asset).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).filter_by(name=asset_name).first()
            if asset_model:
                asset_model.name = asset_name
                asset_model.free = msg['free']
                asset_model.locked = msg['locked']
                asset_model.timestamp = datetime.utcnow()
            else:
                asset_model = Asset(exchange=self._exchange, name=msg['name'], free=msg['free'], locked=msg['locked'])
                account_model.assets.append(asset_model)
            session.commit()

    @run_in_executor
    def update_asset_balances(self, assets):
        with create_session() as session:
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()
            if not type(assets) == list:
                logger.error(f"assets must be a list")
                return
            for asset in assets:
                asset_name = asset['name']
                asset_model = session.query(Asset).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).filter_by(name=asset_name).first()
                if asset_model:
                    asset_model.name = asset_name
                    asset_model.free = asset['free']
                    asset_model.locked = asset['locked']
                    asset_model.timestamp = datetime.utcnow()
                else:
                    asset_model = Asset(exchange=self._exchange, name=asset['name'], free=asset['free'], locked=asset['locked'])
                    account_model.assets.append(asset_model)
            asset_names = [asset['name'] for asset in assets]
            for asset in account_model.assets:
                if asset.name not in asset_names:
                    logger.info(f'Removing {asset.name}')
                    session.delete(asset)
            session.commit()

    @run_in_executor
    def update_portfolio_model(self, portfolio):
        with create_session() as session:
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
        with create_session() as session:
            side = kwargs.get('side')
            exchange_account_id = kwargs.get('exchange_account_id')
            buy_order_id = kwargs.get('buy_order_id')
            if not side:
                logger.error('Must provide a side')
                return
            del kwargs['side']

            if side == 'BUY':
                if not buy_order_id:
                    logger.error('[!] Include buy order id')
                    return
                trade = session.query(Trade).filter_by(buy_order_id=str(buy_order_id)).first()
                if trade:
                    session.query(Trade).filter_by(buy_order_id=str(buy_order_id)).update(kwargs)
                else:
                    if not exchange_account_id:
                        logger.error('[!] Include buy order id')
                        return
                    trade = Trade(**kwargs)
                    session.add(trade)

            elif side == 'SELL':
                if buy_order_id:
                    trade = session.query(Trade).filter_by(buy_order_id=str(buy_order_id)).first()
                    if trade:
                        session.query(Trade).filter_by(buy_order_id=str(buy_order_id)).update(kwargs)
                    else:
                        logger.error(f'Buy order of id {buy_order_id} not found')
                else:
                    sell_order_id = kwargs.get('sell_order_id')
                    if not sell_order_id:
                        logger.error('Must include sell order id')
                        return
                    trade = session.query(Trade).filter_by(sell_order_id=str(sell_order_id)).first()
                    if trade:
                        session.query(Trade).filter_by(sell_order_id=str(sell_order_id)).update(kwargs)
                    else:
                        logger.error('If sell is new, include buy order id to link it to a buy, else, include sell order it.\n '
                                     'The provided sell order id was not found')
            session.commit()

    async def send_notification(self, notification):
        if self.outgoing_message_queue and self.user_tg_id and self.receive_notifications:  # inform user about the new order
            await self.outgoing_message_queue.put({'id': self.user_tg_id, 'message': notification, 'sender': self._exchange, 'username': self.username})

    async def send_admin_notification(self, notification):
        if self.outgoing_message_queue:  # inform admin about the new order
            await self.outgoing_message_queue.put({'id': 'me', 'message': notification, 'sender': self._exchange, 'username': self.username})

    def get_symbol_info(self, symbol):
        #exchange specific, check binance_trader for implementation
        pass

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
                    if self._exchange ==  "BITTREX":
                        pass
                    elif self._exchange == "BINANCE":
                        price = get_btc_price(asset.name)
                        if not price:
                            logger.error(f"Could not get price of {asset.name}")
                            continue
                        portfolio += (float(asset.free) + float(asset.locked)) * price

            logger.info(f"Total portfolio is {portfolio}")
            await self.update_portfolio_model(portfolio)

            await sync_to_async(self.delete_old_portfolio_models)()

        except Exception as e:
            logger.exception(e)

    def delete_old_portfolio_models(self):
        """
        delete the old models, portfolio adds a big overhead on server database
        :return:
        """
        time_before = datetime.utcnow() - timedelta(days=self.max_age_of_portfolio_in_days)
        with create_session() as session:
            old_portfolios = session.query(Portfolio).filter_by(exchange_account_id=self.account_model_id).filter(Portfolio.timestamp < time_before).all()
            for old_portfolio in old_portfolios:
                session.delete(old_portfolio)
            session.commit()
            return True

    def delete_old_trades(self):
        """
        delete the old trades that have been marked completed
        :return:
        """
        time_before = datetime.utcnow() - timedelta(days=self.max_age_of_trades_in_days)
        with create_session() as session:
            old_trades = session.query(Trade).filter_by(exchange_account_id=self.account_model_id).filter_by(completed=True).filter(Trade.timestamp < time_before).all()
            for trade in old_trades:
                session.delete(trade)
            session.commit()
            return True

    def delete_old_orders(self):
        """
        delete the old orders that have been filled more than 2 weeks ago
        :return:
        """
        time_before = datetime.utcnow() - timedelta(days=self.max_age_of_trades_in_days)
        with create_session() as session:
            old_orders = session.query(Order).filter_by(exchange_account_id=self.account_model_id).filter_by(status="FILLED").filter(Order.timestamp < time_before).all()
            for order in old_orders:
                session.delete(order)
            session.commit()
            return True

    async def _validate_keys(self):
        resp = await self.validate_keys()
        is_valid = True
        if resp['error']:
            is_valid = False
        await self.update_validate_keys_model(is_valid)
        return is_valid

    async def validate_keys(self):
        pass

    async def invalidate_keys(self):
        await self.update_validate_keys_model(False)
        if self.keep_running:
            self.keep_running = False

    @run_in_executor
    def update_validate_keys_model(self, is_valid):
        with create_session() as session:
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()
            account_model.valid_keys = is_valid
            session.commit()


    def get_account_signal_assoc(self, signal_name=None, signal_id=None):
        """
        returns the relationship model between exchange account and the telegram signal
        from the exchange_account_signal pivot table.
        :param signal_name:
        :return:
        """
        if not signal_name and not signal_id:
            return None

        with create_session() as session:
            account_model = session.query(ExchangeAccount).filter_by(id=self.account_model_id).first()
            sig_assocs = account_model.signal_assoc

            if signal_name:
                wanted_assocs = [assoc for assoc in sig_assocs if assoc.signal.name == signal_name]
            else:
                wanted_assocs = [assoc for assoc in sig_assocs if assoc.signal.id == signal_id]
            wanted_assoc = wanted_assocs[0] if len(wanted_assocs) else None
            return wanted_assoc

    def signal_can_buy(self, signal_name, symbol):
        logger.info(f"{self.username} Check {signal_name} can buy {symbol}")
        signal_assoc = self.get_account_signal_assoc(signal_name)
        if not signal_assoc or not signal_assoc.percent_investment:
            return True

        symbol_info = self.get_symbol_info(symbol)
        asset = async_to_sync(self.get_asset_models)(asset=symbol_info.quote_asset)
        if not asset:
            logger.error("Quote asset not found")
            return False
        logger.info(f"Asset is {asset.name}, free {asset.free}, locked {asset.locked}")


        with create_session() as session:
            trades_models = session.query(Trade).filter_by(exchange=self._exchange).filter_by(exchange_account_id=self.account_model_id).all()
            open_trades_models = [trade for trade in trades_models if trade.sell_status != "FILLED" and trade.health != "ERROR"]
            quote_trades_models = [trade_model for trade_model in open_trades_models if trade_model.quote_asset == symbol_info.quote_asset]
            signal_trade_models = [trade_model for trade_model in  quote_trades_models if trade_model.signal and trade_model.signal.name == signal_name]
            held_portfolio = 0
            total_portfolio = 0
            for trade in signal_trade_models:
                buy_quote = trade.buy_price * trade.buy_quantity
                sell_quote = trade.sell_price * trade.sell_quantity
                held_portfolio += buy_quote - sell_quote

            for trade in quote_trades_models:
                buy_quote = trade.buy_price * trade.buy_quantity
                sell_quote = trade.sell_price * trade.sell_quantity
                total_portfolio += buy_quote - sell_quote
                total_portfolio += float(asset.free) + float(asset.locked)

            if not total_portfolio:
                return True

            if signal_assoc.percent_investment and held_portfolio/total_portfolio > signal_assoc.percent_investment:
                logger.info(f"{self.username}, {signal_name} cannot buy {symbol}")
                return False
            else:
                logger.info(f"{self.username}Percent investment: {signal_assoc.percent_investment}")
                logger.info(f"Held portfolio: {held_portfolio}")
                logger.info(f"total portfolio: {total_portfolio}")
                logger.info(f"{self.username}, {signal_name} can buy {symbol}")
                return True