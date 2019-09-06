from models import BinanceSymbol, Asset, ExchangeAccount, create_session
from datetime import datetime, timedelta
from binance import binance
import os

exchange_info = binance.exchange_info()

def update_symbol_model_prices():
    all_tickers = binance.ticker_prices()

    if not all_tickers:
        return
    with create_session() as session:
        for ticker_sym in all_tickers:
            ticker = {"symbol": ticker_sym, "price": float(all_tickers[ticker_sym])}
            symbol_model = session.query(BinanceSymbol).filter_by(name= ticker['symbol']).first()
            if symbol_model:
                symbol_model.lastPrice = ticker['price']
                symbol_model.lastPrice_timestamp = datetime.utcnow()
                session.add(symbol_model)
        session.commit()

def get_last_price(symbol):
    try:
        sym_info = get_symbol_info(symbol)
        if not sym_info:
            return {'error': True, 'message': "Symbol not found"}
        if not sym_info.lastPrice or sym_info.lastPrice_timestamp and datetime.utcnow() - sym_info.lastPrice_timestamp > timedelta(minutes=1):
            update_symbol_model_prices()
            sym_info = get_symbol_info(symbol)
        return {'error': False, 'result': sym_info.lastPrice}
    except Exception as e:
        return {'error': True, 'message': str(e)}

def get_symbol_info(symbol):
    if os.path.exists('last_binance_symbols_update'):
        last_update = datetime.utcfromtimestamp(os.path.getmtime('last_binance_symbols_update'))
    else:
        last_update = datetime.utcfromtimestamp(0)
    with create_session() as session:
        if datetime.now() - last_update > timedelta(days=1) or not session.query(BinanceSymbol).filter_by(name=symbol).first() :
            for symbol_data in exchange_info['symbols']:
                filters =  symbol_data['filters']
                _params = {
                    'name': symbol_data['symbol'],
                    'base_asset': symbol_data['baseAsset'],
                    'quote_asset': symbol_data['quoteAsset'],
                }
                for filter in filters:
                    if filter['filterType'] == 'LOT_SIZE':
                        _params['min_qty'] = filter['minQty']
                        _params['step_size'] = filter['stepSize']
                    elif filter['filterType'] == 'MIN_NOTIONAL':
                        _params['min_notional'] = filter['minNotional']
                    elif filter['filterType'] == 'PRICE_FILTER':
                        _params['tick_size'] = filter['tickSize']
                    elif filter['filterType'] == 'PERCENT_PRICE' :
                        _params['multiplierUp'] = filter['multiplierUp']
                        _params['multiplierDown'] = filter['multiplierDown']
                if session.query(BinanceSymbol).filter_by(name=_params['name']).first():
                    session.query(BinanceSymbol).filter_by(name=_params['name']).update(_params)
                else:
                    bin_sym = BinanceSymbol(**_params)
                    session.add(bin_sym)
            session.commit()
            with open('last_binance_symbols_update','w+') as f:
                f.write(str(datetime.now()))
        symbol_model = session.query(BinanceSymbol).filter_by(name=symbol).first()
        return symbol_model

def get_btc_price(asset_name):
    if asset_name == "BTC":
        return 1
    if asset_name in ["123","456","VTHO"]:
        return None
    with create_session() as session:
        base_symbols = session.query(BinanceSymbol).filter_by(base_asset=asset_name).all()
        quote_symbols = session.query(BinanceSymbol).filter_by(quote_asset=asset_name).all()
    if base_symbols:
        for symbol in base_symbols:
            if symbol.quote_asset == "BTC":
                return float(symbol.lastPrice)
    if quote_symbols:
        for symbol in quote_symbols:
            if symbol.base_asset == "BTC":
                return 1/float(symbol.lastPrice)
    #print("Attempting 2 stage conversion")
    if base_symbols:
        for symbol in base_symbols:
            with create_session() as session:
                inter_quote_symbols = session.query(BinanceSymbol).filter_by(quote_asset=symbol.quote_asset).all()
            for inter_symbol in inter_quote_symbols:
                if inter_symbol.base_asset == "BTC":
                    return float(symbol.lastPrice) * 1/float(inter_symbol.lastPrice)
    if quote_symbols:
        for symbol in quote_symbols:
            with create_session() as session:
                inter_base_symbols = session.query(BinanceSymbol).filter_by(base_asset=symbol.base_asset).all()
            for inter_symbol in inter_base_symbols:
                if inter_symbol.quote_asset == "BTC":
                    return 1/float(symbol.lastPrice) * float(inter_symbol.lastPrice)