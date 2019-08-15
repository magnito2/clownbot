from trader.trader import Trader
import logging, json, uuid, asyncio, re,os, emoji
from utils import run_in_executor
from datetime import datetime, timedelta
from models import create_session, BinanceSymbol
from utils.sync import async_to_sync, sync_to_async

logger = logging.getLogger('clone.paper_trader')
logger.setLevel(logging.INFO)

class PaperTrader(Trader):
    pass