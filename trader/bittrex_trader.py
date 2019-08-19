from bittrex.bittrex import *
from bittrex_websocket.websocket_client import BittrexSocket, BittrexMethods
from trader.trader import Trader
import logging, time
from utils import run_in_executor
from datetime import datetime

logger = logging.getLogger('clone.bittrex_trader')
logger.setLevel(logging.ERROR)

class HandleSocket(BittrexSocket):


    async def on_public(self, msg):
        '''
        Only provides updates, hence not all symbols are captured everytime.
        :param msg:
        :return:
        '''
        if msg['invoke_type'] == BittrexMethods.SUBSCRIBE_TO_SUMMARY_LITE_DELTAS:
            deltas = msg['D']
            for symbol in self.trader.active_symbols:
                res = [delta for delta in deltas if delta['M'] == symbol]
                if res:
                    delta = res[0]
                    self.trader.active_symbol_prices[symbol] = delta['l']
            #logger.info(f"[+] New symbol prices, {self.trader.active_symbol_prices}")

    async def on_private(self, msg):
        logger.info(f"[+] Recieved a private message, {msg}")
        if msg.get('o'):
            order_types = ['OPEN', 'PARTIAL', 'FILL', 'CANCEL']
            order_res = msg.get('o')
            order_delta = {
                'delta': 'ORDER',
                'exchange': 'Bittrex',
                'order_id': order_res.get('I'),
                'client_order_id': order_res.get('OU'),
                'symbol': order_res.get('E'),
                'price': order_res.get('X'),
                'quantity': order_res.get('Q'),
                'type':order_types[int(msg.get('TY'))],
                'side': order_res.get('OT').split('_')[1],
                'stop_price':'',
                'commission': order_res.get('n'),
                'commission_asset':'',
                'order_time':order_res.get('Y'),
                'cummulative_filled_quantity': float(order_res.get('Q')) - float(order_res.get('q')),
                'cummulative_quote_asset_transacted':'',
                'status': order_types[int(msg.get('TY'))]
            }

            order_params = {
                "Uuid": order_res.get('U'),
                "OrderUuid": order_res.get('OU'),
                "Exchange": order_res.get('E'),
                'type': order_types[int(msg.get('TY'))],
                "OrderType": order_res.get('OT'),
                "Quantity": order_res.get('Q'),
                "QuantityRemaining": order_res.get('q'),
                "Limit": order_res.get('X'),
                "CommissionPaid": order_res.get('n'),
                "Price": order_res.get('P'),
                "PricePerUnit": order_res.get('PU'),
                "Opened": order_res.get('Y'),
                "Closed": order_res.get('C'),
                "CancelInitiated": order_res.get('CI'),
                "ImmediateOrCancel": order_res.get('K'),
                "IsConditional": order_res.get('k')
            }

            present_order = [order for order in self.trader.open_orders if order['OrderUuid'] == order_params['OrderUuid']]
            if present_order:
                present_order = present_order[0]
                logger.info(f"[+] Updating the order {present_order['OrderUuid']}")
                if order_types[int(msg.get('TY'))] in ["OPEN", "PARTIAL"]:
                    present_order = order_params
                elif order_types[int(msg.get('TY'))] in ["FILL", "CANCEL"]:
                    logger.info(f"[-] Removing {present_order['OrderUuid']} from open orders")
                    self.trader.open_orders.remove(present_order)
                    if order_types[int(msg.get('TY'))] in ["FILL"]:
                        self.trader.closed_orders.append(present_order)
            else:
                logger.info(f"[+] Creating new order {order_params['OrderUuid']}")
                self.trader.open_orders.append(order_params)

            logger.info(f"[+] New order delta, {order_delta}")
            await self.trader.process_user_socket_message(order_delta)


        elif msg.get('d'):
            delta_res = msg.get('d')
            balance_delta = {
                'DELTA': 'BALANCE',
                'Uuid': delta_res['U'],
                "AccountId": delta_res['W'],
                "Currency": delta_res['c'],
                "Balance": delta_res['b'],
                "Available": delta_res['a'],
                "Pending": delta_res['z'],
                "CryptoAddress": delta_res['p'],
                "Requested": delta_res['r'],
                "Updated": delta_res['u'],
                "AutoSell": delta_res['h']
            }

            logger.info(f"[+] New balance delta, {balance_delta}")
            await self.trader.process_user_socket_message(balance_delta)

    def add_trades(self, symbol, callback):
        '''Need to get initial market price for symbols as stream only updates.'''
        invoke_l = [invoke for invoke in self.invokes if invoke['invoke'] == BittrexMethods.SUBSCRIBE_TO_SUMMARY_LITE_DELTAS]
        if not invoke_l:
            logger.info(f"[+] {'*'*50}Subscribing to Prices Stream {'*'*50}")
            self.subscribe_to_summary_lite_deltas()
        if symbol not in self.trader.active_symbols:
            self.trader.active_symbols.append(symbol)
        last_price_resp = self.trader.account.get_ticker(symbol)
        if last_price_resp['success']:
            self.trader.active_symbol_prices[symbol] = last_price_resp['result']['Last']
        else:
            logger.error(f"[!] Failed to get the last ticker price for {symbol}")


class BittrexTrader(Trader):

    def __init__(self, **kwargs):
        try:
            Trader.__init__(self, **kwargs)
            self.account = Bittrex(kwargs.get('api_key'), kwargs.get('api_secret'))
            self._exchange = 'BITTREX'
            self.streamer = HandleSocket()
            self.streamer.authenticate(kwargs.get('api_key'), kwargs.get('api_secret'))
            self.active_symbols = [] #list of symbols that are currently trading {'symbol': 'BTC-USDT', 'buy_price':xxx, 'order_id': xxx, 'latest_price': xxx}
            logger.info('Bittrex trader successfully booted')
            self.streamer.trader = self
        except Exception as e:
            logger.exception(e)

    @run_in_executor
    def create_order(self, **kwargs):

        if kwargs.get('signal_id'):
            parts = kwargs.get('symbol').split("_")
            if not len(parts) == 2:
                return {'error': True, 'message': 'Invalid Symbol'}
            symbol = f"{parts[0]}-{parts[1]}"
        else:
            symbol = kwargs.get('symbol')

        print(f"The symbol is {symbol}")
        side = kwargs.get('side')
        type = kwargs.get('type')
        price = float(kwargs.get('price'))

        if side == "BUY":
            quantity_resp = self.get_buy_size(symbol, price)
        elif side == "SELL":
            quantity_resp = self.get_sell_size(symbol, price)
        else:
            return {'error': True, 'message': f'Side not understood, side was {side}, should be either BUY or SELL'}
        if quantity_resp['error']:
            logger.error(quantity_resp['message'])
            return quantity_resp
        quantity = quantity_resp['size']
        if not quantity:
            return {'error': True, 'message': 'zero quantity'}
        if not symbol or not side or not quantity or not price:
            return {'error': True,
                    'message': f'fill all mandatory fields, symbol: {symbol}, side: {side}, price: {price}, quantity: {quantity}'}
        if not type:
            type = 'LIMIT'

        orders_resp =  self._get_open_orders(symbol)
        if not orders_resp['error']:
            orders = orders_resp['result']
            if orders:
                logger.debug(f"[+] Symbol {symbol} has open orders.")
                order_list = [order for order in orders if order['OrderType'] == f"LIMIT_{side}"]
                logger.info(f"[!] Cancelling orders {[order['OrderUuid'] for order in order_list]}")
                #for order in order_list:
                #    self.cancel_order(symbol, order['OrderUuid'])
                if len(order_list) > self.max_orders_per_symbol:
                    logger.info(f"[!] Symbol {symbol} has {len(order_list)} {side} orders open. Not placing another")
                    return {'error': True, 'message': f"Symbol {symbol} has {len(order_list)} {side} orders open. Not placing another"}

        if side == "BUY":
            resp = self.account.buy_limit(market=symbol, quantity=quantity, rate=f"{price:.8f}")
        elif side == "SELL":
            resp = self.account.sell_limit(market=symbol, quantity=quantity, rate=f"{price:.8f}")
        else:
            return {'error': True, 'message': f'Side {side} is not a BUY or SELL'}
        if resp['success']:
            order_uuid = resp['result']['uuid']

            if side == "BUY":
                params = {
                    'exchange': self._exchange,
                    'symbol': symbol,
                    'buy_order_id': order_uuid,
                    'buy_time': None,
                    'quote_asset': quantity_resp['quote'],
                    'base_asset': quantity_resp['base'],
                    'buy_price': price,
                    'buy_quantity': quantity,
                    'buy_status': 'NEW',
                    'side': 'BUY',
                    'exchange_account_id': self.account_model_id,
                    'trade_signal_id': kwargs.get('trade_signal_id'),
                }
                return {'error': False, 'result': params, 'additional_info': {'signal': kwargs.get('trade_signal_name')}}

            if side == "SELL":
                params = {
                    'exchange': self._exchange,
                    'symbol': symbol,
                    'sell_order_id': order_uuid,
                    'sell_time': None,
                    'sell_price': price,
                    'sell_quantity': quantity,
                    'sell_status': 'NEW',
                    'side': 'SELL',
                    'buy_order_id': kwargs.get('buy_order_id')
                }
                return {'error': False, 'result': params}

        return {'error': True, 'message': resp['message']}

    async def warmup(self):
        try:
            logger.info("[+] Warming Up")
            balances_resp = await self.get_asset_balances()
            if balances_resp['error']:
                logger.error(f"[!] {balances_resp['message']}")
                if balances_resp['message'] == 'APIKEY_INVALID':
                    await self.invalidate_keys()
                    self.keep_running = False
                    return
            balances = balances_resp['result']

            asset_bals = []
            for asset in balances:
                balance_model_msg = {
                    'name': asset['Currency'],
                    'balance': asset['Balance'],
                    'free': asset['Available'],
                    'locked': float(asset['Balance']) - float(asset['Available'])
                }
                asset_bals.append(balance_model_msg)
            await self.update_asset_balances(asset_bals)

            open_orders_resp = await self.get_open_orders()
            if open_orders_resp['error']:
                logger.error(f"[!] {open_orders_resp['message']}")
            open_orders = open_orders_resp.get('result')
            for order in open_orders:
                logger.info(f"[+] Adding {order['Exchange']} to active symbols")
                self.streamer.add_trades(order['Exchange'], self.process_symbol_stream)
                _params = {
                    'exchange': self._exchange,
                    'order_id': order['OrderUuid'],
                    'client_order_id': order['OrderUuid'],
                    'symbol': order['Exchange'],
                    'price': order['Limit'],
                    'quantity': order['Quantity'],
                    'type': order['OrderType'],
                    'side': order['OrderType'],
                    'order_time': order['Opened'],
                    'cummulative_filled_quantity': float(order['Quantity']) - float(order['QuantityRemaining']),
                    'status': 'FILLED' if order['Closed'] else 'NEW',
                    'timestamp': order.get('Opened')
                }
                await self.update_order_model(**_params)

            order_history_resp = await self.get_recent_orders()
            if order_history_resp['error']:
                logger.error(f"[!] {order_history_resp['message']}")

        except Exception as e:
            logger.exception(e)

    def get_buy_size(self, symbol, price):

        logger.info(f"[+] Getting the buy size for {symbol} with price {price}")
        markets = self.account.get_markets()
        symbol_info = [market for market in markets['result'] if market['MarketName'] == symbol]
        if not symbol_info:
            return {'error': True, 'message': 'Could not get the specified symbol in market'}
        symbol_info = symbol_info[0]
        base_asset = symbol_info['BaseCurrency']
        base_asset_bal_res = self.account.get_balance(base_asset)
        if not base_asset_bal_res['success']:
            return {'error': True, 'message': base_asset_bal_res['message']}
        base_asset_bal_raw = base_asset_bal_res['result']['Balance']
        if not base_asset_bal_raw:
            return {'error': True, 'message': 'Zero Balance'}
        base_asset_bal = float(base_asset_bal_raw)
        logger.debug(f"[+] The bal of {base_asset} is {base_asset_bal}")

        if self.btc_per_order:
            budget = self.btc_per_order
        else:
            budget = base_asset_bal * self.percent_size #check on deminishing account as more orders are placed

        if budget < 0.001:
            logger.warning(f"[+] Order size is below minimum trade size of 0.0005BTC. order size is {budget}, adjusting to 0.0005BTC")
            budget = 0.001
        if budget > float(base_asset_bal_res['result']['Available']):
            logger.error("[+] Budget is greater than available account balance")
            if float(base_asset_bal_res['result']['Available']) * 0.9975 > 0.001:
                budget = float(base_asset_bal_res['result']['Available']) * 0.9975
            else:
                return {'error': True, 'message': f'account balance not sufficient to place order, account balance {base_asset_bal_res["result"]["Available"]}, minimum order size 0.0005'}
        amount_to_buy = budget / price
        return {'error': False, 'size': f"{amount_to_buy:.6f}", 'quote':base_asset, 'base': symbol_info['MarketCurrency']}

    def get_sell_size(self, symbol, price):
        markets = self.account.get_markets()
        symbol_info = [market for market in markets['result'] if market['MarketName'] == symbol]
        if not symbol_info:
            return {'error': True, 'message': 'Could not get the specified symbol in market'}
        symbol_info = symbol_info[0]
        quote_asset = symbol_info['MarketCurrency']
        quote_asset_bal_res = self.account.get_balance(quote_asset)
        if not quote_asset_bal_res['success']:
            return {'error': True, 'message': quote_asset_bal_res['message']}
        quote_asset_bal = quote_asset_bal_res['result']['Available']
        logger.debug(f"[+] The bal of {quote_asset} is {quote_asset_bal}")
        return {'error': False, 'size': quote_asset_bal, 'base': quote_asset}

    #@run_in_executor
    def cancel_order(self, symbol, id):
        resp = self.account.cancel(id)
        if resp['success']:
            return {'error': False, 'result': resp['result']}
        return {'error': True, 'message': resp['message']}

    @run_in_executor
    def query_order(self, symbol, id):
        resp = self.account.get_order(id)
        if resp['success']:
            return {'error': False, 'result': resp['result']}
        return {'error': True, 'message': resp['message']}

    async def process_symbol_stream(self, msg):
        pass

    async def process_user_socket_message(self, msg):
        delta = msg.get('delta')
        if delta == "ORDER":
            del msg['delta']
            await self.update_order_model(**msg)

            if msg['side'] == 'BUY' and msg['type'] in ['PARTIAL', 'FILL']:
                buy_price = msg['price']
                symbol = msg['symbol']
                logger.info(f"[+] Creating a sell order for {msg['symbol']}")
                order_params = {
                    'price': float(buy_price) * (1 + self.profit_margin),
                    'symbol': symbol,
                    'exchange': self._exchange,
                    'side': 'SELL',
                    'buy_order_id': msg['client_order_id']
                }
                await self.orders_queue.put(order_params)

            if msg['side'] == 'BUY':
                trade_params = {
                    'exchange': self._exchange,
                    'buy_order_id': msg['client_order_id'],
                    'symbol':msg['symbol'],
                    'buy_quantity_executed': msg['cummulative_filled_quantity'],
                    'buy_status': msg['status']
                }
            elif msg['side'] == 'SELL':
                trade_params = {
                    'exchange': self._exchange,
                    'sell_order_id': msg['client_order_id'],
                    'symbol': msg['symbol'],
                    'sell_quantity_executed': msg['cummulative_filled_quantity'],
                    'sell_status': msg['status']
                }
            else:
                logger.error(f"[!] Side {msg['side']} is not known")
                return
            await self.update_trade(**trade_params)

        elif delta == "BALANCE":
            asset = msg
            #put a sell right here, Do not remove this message unless you've fucking put up the fucking sell, lazy
            logger.info(msg)

            balance_model_msg = {
                    'name': asset['Currency'],
                    'balance': asset['Balance'],
                    'free': asset['Available'],
                    'locked': float(asset['Balance']) - float(asset['Available'])
                }
            await self.update_asset_balance(balance_model_msg)

    @run_in_executor
    def get_asset_balances(self):
        balances_resp = self.account.get_balances()
        if balances_resp['success']:
            return {'error': False, 'result': balances_resp['result']}
        return {'error': True, 'message': balances_resp['message']}

    @run_in_executor
    def get_recent_orders(self, symbol=None):
        recent_orders_resp = self.account.get_order_history(market=symbol)
        if recent_orders_resp['success']:
            return {'error': False, 'result': recent_orders_resp['result']}
        return {'error': True, 'message': recent_orders_resp['message']}

    @run_in_executor
    def get_open_orders(self, symbol=None, cached=True):
        return self._get_open_orders(symbol=symbol, cached=cached)

    def _get_open_orders(self, symbol=None, cached=True):
        '''
        Cached orders are added by the streamer class on_private method to the self.open_orders.
        prefer fetching this
        :param symbol:
        :param cached:
        :return:
        '''
        if not cached or not self.open_orders:
            open_orders_resp = self.account.get_open_orders(market=symbol)
            if open_orders_resp['success']:
                new_open_orders = open_orders_resp['result']
                for new_order in new_open_orders:
                    old_order = [order for order in self.open_orders if order['OrderUuid'] == new_order['OrderUuid']]
                    if old_order:
                        old_order = old_order[0]
                        logger.info(f"[+] Replacing order {old_order['OrderUuid']}")
                        old_order = new_order
                    else:
                        self.open_orders.append(new_order)
                return {'error': False, 'result': open_orders_resp['result']}
            return {'error': True, 'message': open_orders_resp['message']}

        #Using cached result
        if symbol:
            symbol_orders = [order for order in self.open_orders if order['Exchange'] == symbol]
            return {'error': False, 'result': symbol_orders}
        return {'error': False, 'result': self.open_orders}

    @run_in_executor
    def get_last_price(self, symbol):
        last_price = self.account.get_ticker(symbol)
        if last_price['success']:
            return {'error': False, 'result': last_price['result']['Last']}
        return {'error': True, 'message': last_price['message']}

    async def routine_check(self):
        #order get open orders every 5 minutes, else open orders should be updated via websockets trade event.
        try:
            orders_res = await self.get_open_orders()
            if orders_res['error']:
                logger.error(orders_res['message'])
                return
            orders = orders_res['result']
            #await self.print_open_orders(orders)
            logger.info("[+] Checking for expired orders and stop lossed orders")

            recent_orders_resp = await self.get_recent_orders()
            if recent_orders_resp['error']:
                logger.error(f"[!] {recent_orders_resp['message']}")
                return
            closed_orders = recent_orders_resp['result']

            for order in orders:

                #check for timed out orders, applies to buy orders only
                if order['OrderType'] == 'LIMIT_BUY' and datetime.utcnow() - datetime.fromtimestamp(float(order['Opened'])/1000) > self.parse_time(self.order_timeout):
                    logger.info(f"[!] Order {order['OrderUuid']} has expired, cancelling")
                    await self.cancel_order(order['Exchange'], order['OrderUuid'])

                #check for stop loss condition, applies to sell orders only.
                if order['OrderType'] == "LIMIT_SELL":
                    symbol = order['Exchange']
                    order_id = order['OrderUuid']
                    trade_model = await self.get_trade_model(sell_order_id=order_id)
                    if not trade_model:
                        continue
                    buy_price = trade_model.buy_price
                    symbol_market_price = self.active_symbol_prices.get(symbol)
                    if not symbol_market_price:
                        symbol_market_price = await self.get_last_price(symbol)
                        if symbol_market_price['error']:
                            logger.error(f"[!] {symbol_market_price['message']}")
                            continue
                        symbol_market_price = float(symbol_market_price['result']['price'])
                    if symbol_market_price < buy_price - self.stop_loss_trigger:  # we've gone below our stop loss
                        logger.info(
                            f"[!] {symbol} Price has gone below stop loss, placing a stop loss sell. buy price {buy_price}, market price {symbol_market_price}")
                        order_params = {
                            'price': symbol_market_price * 0.99,
                            'symbol': symbol,
                            'exchange': self._exchange,
                            'side': 'SELL',
                            'buy_order_id': trade_model.buy_order_id
                        }
                        await self.orders_queue.put(order_params)

        except Exception as e:
            logger.exception(e)

    @run_in_executor
    def validate_keys(self):
        balances_resp = self.account.get_balances()
        if not balances_resp['success'] and balances_resp['message'] == 'APIKEY_INVALID':
            return {'error': True, 'message': balances_resp['message']}
        return {'error': False, 'message': 'API Key is valid'}