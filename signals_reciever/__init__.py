
#!/usr/bin/env python3
# countasync.py

import asyncio, logging, configparser
from aiohttp import web

logger = logging.getLogger('clone.http_handler')

class HttpSignalReciever:

    def __init__(self, binance_queues, bittrex_queues):
        self.binance_queues = binance_queues
        self.bittrex_queues = bittrex_queues
        config = configparser.ConfigParser()
        config.read('./config.ini')
        self.listening_port = config.getint('HTTP_SIGNAL_RECIEVER', 'PORT')

    async def handle_command(self, request):

        data = await request.json()
        '''
        {
            'signal_name' : channel name
            'symbol': signal_tup[0],
            'exchange': signal_tup[1],
            'side': signal_tup[2],
            'price': float(signal_tup[3]),
            'target_price': float(signal_tup[4]),
            'signal_id': signal_tup[5]
        }
        '''
        if 'signal' in data:
            signal = data

            if signal['exchange'] == "BINANCE":
                logger.info(f"********Putting {signal} into queues")
                for queue in self.binance_queues:
                    await queue.put(signal)
            elif signal['exchange'] == "BITTREX":
                logger.info(f"********Putting {signal} into queues")
                for queue in self.bittrex_queues:
                    await queue.put(signal)
        else:
            logger.info(f"[+] I recieved {data} which is not a signal")
        return web.json_response({'success':True})

    async def run(self):

        logger.info("HTTP Signal reciever is starting up")
        try:
            app = web.Application()
            app.add_routes([web.post('/signal', self.handle_command)])
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.listening_port)
            await site.start()
            #await web.run_app(app)
            while True:
                await asyncio.sleep(3000000000)
        except Exception as e:
            logger.exception(e)

    async def my_event_handler(self, event):
        try:
            pass
        except Exception as e:
            logger.exception(e)
