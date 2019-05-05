'''
the brain.
'''

import asyncio, logging, configparser

from telegram_api import MyTelegramClient, MagnitoCrypto, CQSScalpingFree

from signals_reciever import HttpSignalReciever

from trader import BinanceTrader, BittrexTrader

from models import create_session, StartUp, ExchangeAccount

logger = logging.getLogger('clone.celebro')

logging.getLogger().setLevel(level=logging.ERROR)
logging.getLogger('clone').setLevel(level=logging.DEBUG)

class Celebro:

    def __init__(self, config):

        logger.debug('celebro is booting up')

        self.exchange_traders = []
        with create_session() as session:
            exchange_account_models = session.query(ExchangeAccount).all()
            if not exchange_account_models:
                logger.error("No single account has been added, please add accounts")
            for account in exchange_account_models:
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
                        'exchange_account_model_id': account.id
                    }
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
                        'exchange_account_model_id': account.id
                    }
                    kwargs['subscribed_signals'].append('ManualOrder')
                    bittrex_trader = BittrexTrader(**kwargs)
                    self.exchange_traders.append(bittrex_trader)

            startup = StartUp()
            session.add(startup)
            session.commit()

    async def run(self):
        '''
        Main loop.
        :return:
        '''


        binance_trader_queues = [trader.orders_queue for trader in self.exchange_traders if trader._exchange == "BINANCE"]
        bittrex_traders_queues = [trader.orders_queue for trader in self.exchange_traders if trader._exchange == "BITTREX"]
        tg_client = MyTelegramClient(binance_trader_queues, bittrex_traders_queues, [MagnitoCrypto, CQSScalpingFree])
        producers = [asyncio.create_task(tg_client.run())]

        for trader in self.exchange_traders: #pass tg_client message queue to every traderxc
            trader.outgoing_message_queue = tg_client.outgoing_messages_queue

        print("[+] Starting the traders")

        consumers = [asyncio.create_task(trader.run()) for trader in self.exchange_traders]
        asyncio.create_task(tg_client.send_message_loop()) #task to process message loop. part of consumers, so should be implicitly awaited
        print("[+] Adding Http signal reciever")
        http_signal_handler = HttpSignalReciever(binance_trader_queues, bittrex_traders_queues)
        http_signal_handler_task = asyncio.create_task(http_signal_handler.run())
        producers.append(http_signal_handler_task)

        await asyncio.gather(*producers)
        #await self.binance_orders_queue.join()  # Implicitly awaits consumers, too
        #await self.bittrex_orders_queue.join()  # Implicitly awaits consumers, too
        logger.error("And we found our way to our the program, crash")
        for c in consumers:
            c.cancel()
