import requests

def get_binance_symbols():
    try:
        exc_info = requests.get("https://api.binance.com/api/v1/exchangeInfo")
        symbols_info = exc_info.json()['symbols']
        symbol_names = [symbol['symbol'] for symbol in symbols_info]
        return {'error': False, 'result': symbol_names}
    except Exception as e:
        return {'error': True, 'message': str(e)}

def get_bittrex_symbols():
    try:
        markets_resp = requests.get('https://api.bittrex.com/api/v1.1/public/getmarkets')
        markets_resp_json = markets_resp.json()
        if markets_resp_json['success'] == False:
            return {'error': True, 'message': markets_resp_json['message']}
        markets = markets_resp_json['result']
        symbols = [market['MarketName'] for market in markets]
        return {'error': False, 'result': symbols}
    except Exception as e:
        return {'error': True, 'message': str(e)}