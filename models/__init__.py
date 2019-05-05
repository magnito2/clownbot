import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
import threading, logging
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

engine = sqlalchemy.create_engine('mysql://root:@localhost/clown_bot')
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