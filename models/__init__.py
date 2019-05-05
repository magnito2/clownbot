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