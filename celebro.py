'''
the brain.
'''

import asyncio, logging, configparser

from telegram_api import MyTelegramClient, MagnitoCrypto, CQSScalpingFree, QualitySignalsChannel, CryptoPingMikeBot, CryptoPingXrayBot

from signals_reciever import HttpSignalReciever

from trader import BinanceTrader, BittrexTrader, BinanceSocketManager

from models import create_session, StartUp, ExchangeAccount

from monitor import Monitor

from datetime import datetime

import os,sys,psutil

logger = logging.getLogger('clone.celebro')

class Celebro:

    def __init__(self, config):

        logger.info('***** clown bot celebro starting *****')
        self.tg_kwargs = {}
        self.tg_kwargs['API_ID'] = config.get('DEFAULT','Telegram_API_ID')
        self.tg_kwargs['API_HASH'] = config.get('DEFAULT','Telegram_API_HASH')
        self.exchange_traders = []

        self.last_bot_restart = datetime.utcnow()
        self.bot_restart_interval = 60 * 60 * 3

        self.binance_price_streamer = BinanceSocketManager() #pushes prices in real time to subscribed bots.

        with create_session() as session:
            exchange_account_models = session.query(ExchangeAccount).filter_by(valid_keys=True).all()
            if not exchange_account_models:
                logger.error("No single account has been added, please add accounts")
            for account in exchange_account_models:
                logger.info(f"[+] Adding {account.user.username}- {account.exchange}")
                if account.exchange == "BINANCE":
                    kwargs = {
                        'api_key': account.api_key,
                        'api_secret': account.api_secret,
                        'percent_size': account.min_order_size,
                        'profit_margin': account.profit_margin,
                        'order_timeout': account.order_cancel_seconds,
                        'stop_loss_trigger': account.stop_loss_trigger,
                        'user_id': account.user_id,
                        'user_tg_id': account.user_tg_id,
                        'receive_notifications': account.receive_notifications,
                        'subscribed_signals': [signal.name for signal in account.signals],
                        'use_fixed_amount_per_order': account.use_fixed_amount_per_order,
                        'fixed_amount_per_order': account.fixed_amount_per_order,
                        'exchange_account_model_id': account.id,
                        'price_streamer': self.binance_price_streamer,
                        'username': account.user.username,
                        'max_orders_per_symbol': account.max_orders_per_pair,
                        'max_drawdown': account.max_drawdown,
                        'sell_only_mode': account.sell_only_mode,
                        'btc_volume_increase_order_above': float(
                            account.btc_volume_increase_order_above) if account.btc_volume_increase_order_above else 0,
                        'percent_increase_of_order_size': float(
                            account.percent_increase_of_order_size) if account.percent_increase_of_order_size else 0,
                        'max_age_of_trades_in_days': account.max_age_of_trades_in_days,

                        'use_different_targets_for_small_prices': account.use_different_targets_for_small_prices,
                        'small_price_value_in_satoshis': account.small_price_value_in_satoshis,
                        'small_price_take_profit': account.small_price_take_profit,
                        'small_price_stop_loss': account.small_price_stop_loss,
                    }
                    valid = self.validate_account_model_params(kwargs)
                    if not valid:
                        logger.error(f'[!] Account {account.id} is invalid. cannot trade')
                        continue
                    kwargs['subscribed_signals'].append('ManualOrder')
                    binance_trader = BinanceTrader(**kwargs)
                    self.exchange_traders.append(binance_trader)

                elif account.exchange == "BITTREX":

                    kwargs = {
                        'api_key': account.api_key,
                        'api_secret': account.api_secret,
                        'percent_size': account.min_order_size,
                        'profit_margin': account.profit_margin,
                        'order_timeout': account.order_cancel_seconds,
                        'stop_loss_trigger': account.stop_loss_trigger,
                        'user_id': account.user_id,
                        'user_tg_id': account.user_tg_id,
                        'receive_notifications': account.receive_notifications,
                        'subscribed_signals': [signal.name for signal in account.signals],
                        'use_fixed_amount_per_order': account.use_fixed_amount_per_order,
                        'fixed_amount_per_order': account.fixed_amount_per_order,
                        'exchange_account_model_id': account.id,
                        'username': account.user.username,
                        'max_orders_per_symbol': account.max_orders_per_pair,
                        'max_drawdown': account.max_drawdown,
                        'sell_only_mode': account.sell_only_mode,
                        'btc_volume_increase_order_above': float(
                            account.btc_volume_increase_order_above) if account.btc_volume_increase_order_above else 0,
                        'percent_increase_of_order_size': float(
                            account.percent_increase_of_order_size) if account.percent_increase_of_order_size else 0,
                        'max_age_of_trades_in_days': account.max_age_of_trades_in_days,

                        'use_different_targets_for_small_prices': account.use_different_targets_for_small_prices,
                        'small_price_value_in_satoshis': account.small_price_value_in_satoshis,
                        'small_price_take_profit': account.small_price_take_profit,
                        'small_price_stop_loss': account.small_price_stop_loss,
                    }

                    valid = self.validate_account_model_params(kwargs)
                    if not valid:
                        logger.error(f'[!] Account {account.id} is invalid. cannot trade')
                        continue
                    kwargs['subscribed_signals'].append('ManualOrder')
                    bittrex_trader = BittrexTrader(**kwargs)
                    self.exchange_traders.append(bittrex_trader)
                    continue

            startup = StartUp()
            session.add(startup)
            session.commit()

        self.monitor = Monitor(self)

    def validate_account_model_params(self, kwargs):
        for key in ['api_key', 'api_secret', 'profit_margin', 'stop_loss_trigger', 'order_timeout']:
            if kwargs[key] == None:
                return False
        if kwargs['percent_size'] == None:
            if not kwargs['use_fixed_amount_per_order'] and kwargs['fixed_amount_per_order']:
                return False
        return True

    async def run(self):
        '''
        Main loop.
        :return:
        '''

        binance_trader_queues = [trader.orders_queue for trader in self.exchange_traders if trader._exchange == "BINANCE"]
        bittrex_traders_queues = [trader.orders_queue for trader in self.exchange_traders if trader._exchange == "BITTREX"]

        magcrypt = MagnitoCrypto(QualitySignalsChannel)
        self.tg_client = MyTelegramClient(binance_trader_queues, bittrex_traders_queues, [magcrypt, CQSScalpingFree, QualitySignalsChannel, CryptoPingMikeBot, CryptoPingXrayBot], self.tg_kwargs)
        producers = [asyncio.create_task(self.tg_client.run())]

        for trader in self.exchange_traders: #pass tg_client message queue to every traderxc
            trader.outgoing_message_queue = self.tg_client.outgoing_messages_queue

        consumers = [asyncio.create_task(trader.run()) for trader in self.exchange_traders]
        asyncio.create_task(self.tg_client.send_message_loop()) #task to process message loop. part of consumers, so should be implicitly awaited

        self.http_signal_handler = HttpSignalReciever(binance_trader_queues, bittrex_traders_queues)
        self.http_signal_handler_task = asyncio.create_task(self.http_signal_handler.run())

        self.http_signal_handler.celebro_instance = self

        producers.append(self.http_signal_handler_task)

        self.monitor_handler = asyncio.create_task(self.monitor.run()) #M&E
        producers.append(self.monitor_handler)

        await asyncio.gather(*producers)
        #await self.binance_orders_queue.join()  # Implicitly awaits consumers, too
        #await self.bittrex_orders_queue.join()  # Implicitly awaits consumers, too
        logger.error("And we found our way to our the program, crash")
        for c in consumers:
            c.cancel()

    async def add_account(self, account_id):
        trader_l = [trader for trader in self.exchange_traders if trader.account_model_id == account_id]
        if trader_l:
            logger.info("[+] Account with the same id alread exists")
            return

        with create_session() as session:
            account = session.query(ExchangeAccount).filter_by(id=account_id).first()
            if not account:
                logger.error(f"The account with id {account_id} was not found.")

            trader = None

            if account.exchange == "BINANCE":
                kwargs = {
                        'api_key': account.api_key,
                        'api_secret': account.api_secret,
                        'percent_size': account.min_order_size,
                        'profit_margin': account.profit_margin,
                        'order_timeout': account.order_cancel_seconds,
                        'stop_loss_trigger': account.stop_loss_trigger,
                        'user_id': account.user_id,
                        'user_tg_id': account.user_tg_id,
                        'receive_notifications': account.receive_notifications,
                        'subscribed_signals': [signal.name for signal in account.signals],
                        'use_fixed_amount_per_order': account.use_fixed_amount_per_order,
                        'fixed_amount_per_order': account.fixed_amount_per_order,
                        'exchange_account_model_id': account.id,
                        'price_streamer': self.binance_price_streamer,
                        'username': account.user.username,
                        'max_orders_per_symbol': account.max_orders_per_pair,
                        'max_drawdown': account.max_drawdown,
                        'sell_only_mode': account.sell_only_mode,
                        'btc_volume_increase_order_above': float(
                            account.btc_volume_increase_order_above) if account.btc_volume_increase_order_above else 0,
                        'percent_increase_of_order_size': float(
                            account.percent_increase_of_order_size) if account.percent_increase_of_order_size else 0,
                        'max_age_of_trades_in_days': account.max_age_of_trades_in_days
                    }

                kwargs['subscribed_signals'].append('ManualOrder')
                binance_trader = BinanceTrader(**kwargs)
                self.exchange_traders.append(binance_trader)
                self.tg_client.binance_queues.append(binance_trader.orders_queue)
                self.http_signal_handler.binance_queues.append(binance_trader.orders_queue)
                trader = binance_trader

            elif account.exchange == "BITTREX":
                kwargs = {
                        'api_key': account.api_key,
                        'api_secret': account.api_secret,
                        'percent_size': account.min_order_size,
                        'profit_margin': account.profit_margin,
                        'order_timeout': account.order_cancel_seconds,
                        'stop_loss_trigger': account.stop_loss_trigger,
                        'user_id': account.user_id,
                        'user_tg_id': account.user_tg_id,
                        'receive_notifications': account.receive_notifications,
                        'subscribed_signals': [signal.name for signal in account.signals],
                        'use_fixed_amount_per_order': account.use_fixed_amount_per_order,
                        'fixed_amount_per_order': account.fixed_amount_per_order,
                        'exchange_account_model_id': account.id,
                        'username': account.user.username,
                        'max_orders_per_symbol': account.max_orders_per_pair,
                        'max_drawdown': account.max_drawdown,
                        'sell_only_mode': account.sell_only_mode,
                        'btc_volume_increase_order_above': float(
                            account.btc_volume_increase_order_above) if account.btc_volume_increase_order_above else 0,
                        'percent_increase_of_order_size': float(
                            account.percent_increase_of_order_size) if account.percent_increase_of_order_size else 0,
                        'max_age_of_trades_in_days': account.max_age_of_trades_in_days
                    }

                kwargs['subscribed_signals'].append('ManualOrder')
                bittrex_trader = BittrexTrader(**kwargs)
                self.exchange_traders.append(bittrex_trader)
                self.tg_client.bittrex_queues.append(bittrex_trader.orders_queue)
                self.http_signal_handler.bittrex_queues.append(bittrex_trader.orders_queue)
                trader = bittrex_trader

            trader.outgoing_message_queue = self.tg_client.outgoing_messages_queue
            asyncio.create_task(trader.run())

    async def remove_account(self, account_id):
        for trader in self.exchange_traders:
            if trader.account_model_id == account_id:
                trader.keep_running = False
                if trader._exchange == "BINANCE":
                    self.tg_client.binance_queues.remove(trader.orders_queue)
                    #self.http_signal_handler.binance_queues.remove(trader.orders_queue)
                elif trader._exchange == "BITTREX":
                    self.tg_client.bittrex_queues.remove(trader.orders_queue)
                    #self.http_signal_handler.bittrex_queues.remove(trader.orders_queue)
                self.exchange_traders.remove(trader)


    async def reload_account(self, account_id):
        try:
            await self.remove_account(account_id)
        except Exception as e:
            logger.exception(e)
        await asyncio.sleep(30)
        try:
            await self.add_account(account_id)
        except Exception as e:
            logger.exception(e)

    async def subscribe_signal(self, signal):
        pass

    def restart_bot(self):
        """Restarts the current program, with file objects and descriptors
              cleanup
           """
        logger.info("[!] Restarting the bot")
        try:
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            logger.error(e)
        python = sys.executable
        os.execl(python, python, *sys.argv)