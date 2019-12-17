from binance.binance import Streamer
import asyncio

import logging

logger = logging.getLogger('clone.binance_ws')
logger.setLevel(logging.DEBUG)

class BinanceSocketManager:
    '''
    Handles public sockets, i.e prices. Used to determine stop loss triggers.
    '''

    def __init__(self):
        '''
            Holds the subscribed traders entities in the format
            'BTCUSDT' : [bot1, bot2, bot3].
            the subscribed bots should implement method process_socket_message.
        '''
        self.__subscription = {}
        self.streamer = Streamer()
        self.last_kline_price = 0

    def subscribe(self, symbol, bot, buy_order_id, stop_price): #we will stick to 1m candles for now
        if not symbol in self.__subscription:
            self.__subscription[symbol] = []
            logger.info(f"Starting the socket for {symbol}")
            self.streamer.add_candlesticks(symbol, "1m", self.check_stop_loss)
        ids = [x['buy_order_id'] for x in self.__subscription[symbol]]
        if buy_order_id in ids:
            logger.debug(f"[+] Bot {bot} is already subscribed")
        else:
            params = {
                'bot' : bot,
                'buy_order_id': buy_order_id,
                'stop_price': stop_price
            }
            self.__subscription[symbol].append(params)
            logger.debug(f"[+] Adding {bot.username} to {symbol}")

    def unsubscribe(self, symbol, buy_order_id):
        if symbol in self.__subscription:
            for bot in self.__subscription[symbol]:
                if bot['buy_order_id'] == buy_order_id:
                    logger.debug(f"[+] Removing {bot} from {symbol}")
                    self.__subscription[symbol].remove(bot)
                    if len(self.__subscription[symbol]) == 0:
                        del self.__subscription[symbol]
                        self.streamer.remove_candlesticks(symbol, "1m")


    async def check_stop_loss(self, msg):
        kline = msg['k']
        symbol = msg['s']
        close_price = float(kline['c'])
        kline_closed = kline['x']
        if not kline_closed:
            return
        if not symbol in self.__subscription:
            #self.streamer.remove_candlesticks(symbol, "1m")
            return
        for sub in self.__subscription[symbol]:
            if close_price <= sub['stop_price']:
                logger.info(f"[!] Stop loss hit, {symbol}, stop_price {sub['stop_price']}, current price {close_price}")
                try:
                    params = {
                        'symbol': msg['s'],
                        'price': float(kline['c']),  # use open price of period,
                        'buy_order_id' : sub['buy_order_id']
                    }
                    asyncio.create_task(sub['bot'].create_stop_loss_order(params))
                    self.unsubscribe(symbol, sub['buy_order_id'])
                except Exception as e:
                    logger.error(e)