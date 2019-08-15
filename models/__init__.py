import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
import threading, logging, configparser
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

config = configparser.ConfigParser()
config.read('config.ini')
database_uri = config.get('SQLALCHEMY', 'DATABASE_URI')

engine = sqlalchemy.create_engine(database_uri)
Session = sessionmaker(bind=engine)
Base = declarative_base()

db_lock = threading.Lock()
logger = logging.getLogger('clone.database')

@contextmanager
def create_session():
    session = None
    try:
        #generate database schema
        Base.metadata.create_all(engine)
        #create a new session
        session = Session()
        with db_lock:
            yield session
    except SQLAlchemyError as e:
        logger.exception(e)
        #raise e
    finally:
        if session:
            session.close()

from .startups import StartUp
from .assets import Asset
from .trades import Trade
from .exchange_accounts import ExchangeAccount
from .user import User
from .orders import Order
from .signals import Signal
from .portfolio import Portfolio
from .manual_orders import ManualOrder
from .binance_symbols import BinanceSymbol
from .trade_signals import TradeSignal


from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
class ExchangeAccountSignal(Base):
    __tablename__="exchange_accounts_signals"

    signal_id = Column(Integer, ForeignKey('signals.id'), primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey('exchange_account.id'), primary_key=True)
    percent_investment = Column(Float) #set the lot size for each signal individually
    profit_target = Column(Float) #set the profit target for each signal individually
    exchange_account = relationship(ExchangeAccount, backref=backref('signal_assoc'))
    signal = relationship(Signal, backref=backref('exchange_account_assoc'))