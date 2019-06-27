from trader.binance_socker_manager import BinanceSocketManager
import asyncio

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('clone')
logger.setLevel(logging.ERROR)
#sh = logging.StreamHandler()
#logger.addHandler(sh)

class DummyBot:

    def __init__(self, name):
        self._name = name

    async def process_symbol_stream(self, msg):
        logger.info(f"{self._name} has recieved a new message, {msg}")

    def __repr__(self):
        return f"<Dummy {self._name}>"

sm = BinanceSocketManager()

async def unsubscribe():
    await asyncio.sleep(15)
    sm.unsubscribe("ETHBTC",me)
    sm.unsubscribe("LTCBTC",you)
    await asyncio.sleep(15)
    sm.unsubscribe("LTCBTC",me)
    await asyncio.sleep(30)
    sm.unsubscribe("BTCUSDT",me)
    await asyncio.sleep(15)
    asyncio.get_event_loop().stop()

me = DummyBot("magnito")
you = DummyBot("otwimy")

sm.subscribe("ETHBTC", me)
sm.subscribe("BTCUSDT",me)
sm.subscribe("LTCBTC",me)
sm.subscribe("LTCBTC",you)

asyncio.Task(unsubscribe())

asyncio.get_event_loop().run_forever()
