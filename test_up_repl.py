#use this to have repl initialize
#use anaconda ipython

import configparser, time
import logging

import logging.handlers
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
logging.getLogger().setLevel(level=logging.ERROR)

logger = logging.getLogger('clone')

fh = logging.handlers.RotatingFileHandler("logs/bot.log", maxBytes=100000, backupCount=5, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s  - %(name)s - %(levelname)s - %(message)s')
formatter.converter = time.gmtime
fh.setFormatter(formatter)
logger.addHandler(fh)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

from celebro import Celebro

config = configparser.ConfigParser()
config.read('config.ini')
logger.setLevel(config.getint('DEFAULT','LOG_LEVEL'))
celebro_instance = Celebro(config)