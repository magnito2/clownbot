'''
Zignally Clone.

Get buy signals from telegram groups, channels, whatever. #only two exchanges supported, binance and bittrex. more on the way

@todo #for future expansion: seperate telegram parsers into classes, so that user can add a class, with a regex and spit out a buy signal.

puts the signals in a queue, then processes the queue buying.
when a buy happens, places a sell at a target price (1.5% above buy price)
monitors the market price, if market price goes stop_loss trigger price below, place a sell at stop loss price.
if a sell happens, celebrate buy slaughtering a goat. ;)
logs everything (almost) in a db for analytics.
'''

import logging, configparser, time
import logging.handlers
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger('clone')

fh = logging.handlers.RotatingFileHandler("logs/bot.log", maxBytes=100000, backupCount=5, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s  - %(name)s - %(levelname)s - %(message)s')
formatter.converter = time.gmtime
fh.setFormatter(formatter)
logger.addHandler(fh)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

from celebro import Celebro
import asyncio


async def main():
    with open('logo.txt','r') as logo:
        logo_text = logo.read()
        print(logo_text)

    logger.info('[+] Getting it started')
    config = configparser.ConfigParser()
    config.read('config.ini')
    logger.setLevel(config.getint('DEFAULT','LOG_LEVEL'))
    celebro_instance = Celebro(config)
    await celebro_instance.run()

if __name__ == "__main__":
    asyncio.run(main())