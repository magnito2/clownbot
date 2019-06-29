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

    def subscribe(self, symbol, bot): #we will stick to 1m candles for now
        if not symbol in self.__subscription:
            self.__subscription[symbol] = []
            logger.info(f"Starting the socket for {symbol}")
            self.streamer.add_candlesticks(symbol, "1m", self.process_symbol_stream)
        if bot in self.__subscription[symbol]:
            logger.info(f"[+] Bot {bot} is already subscribed")
        else:
            self.__subscription[symbol].append(bot)
            logger.info(f"[+] Adding {bot} to {symbol}")

    def unsubscribe(self, symbol, bot):
        if symbol in self.__subscription:
            if bot in self.__subscription[symbol]:
                logger.info(f"[+] Removing {bot} from {symbol}")
                self.__subscription[symbol].remove(bot)
                if len(self.__subscription[symbol]) == 0:
                    del self.__subscription[symbol]
                    self.streamer.remove_candlesticks(symbol, "1m")
            else:
                logger.error(f"{bot} is not subscribed to {symbol}")
        else:
            logger.error(f"{bot} Unsubscribing from {symbol} which is not subscribed")

    async def process_symbol_stream(self, msg):
        kline = msg['k']
        if self.last_kline_price != float(kline['o']):
            params = {
                'symbol': msg['s'],
                'price': float(kline['o']) #use open price of period
            }
            self.last_kline_price = float(kline['o'])
            print(f"[+] {params['symbol']} - active")
            for bot in self.__subscription[params['symbol']]:
                try:
                    asyncio.create_task(bot.process_symbol_stream(params))
                except Exception as e:
                    logger.error(e)