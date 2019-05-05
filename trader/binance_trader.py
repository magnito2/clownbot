from trader.trader import Trader
import logging, json, uuid, asyncio, re
from binance import binance
from utils import run_in_executor
from datetime import datetime

logger = logging.getLogger('clone.binance_trader')
binance.__log_enabled = True

class BinanceTrader(Trader):

    def __init__(self, **kwargs):
        Trader.__init__(self, **kwargs)
        self.account = binance.Account(kwargs.get('api_key'), kwargs.get('api_secret'))
        self._exchange = 'BINANCE'
        self.streamer = binance.Streamer()
        self.streamer.start_user(kwargs.get('api_key'), self.process_user_socket_message)

        self.exchange_info = binance.exchange_info()

        self.active_symbols = [] #list of symbols that are currently trading {'symbol': 'BTCUSDT', 'buy_price':xxx, 'order_id': xxx, 'latest_price': xxx}
        logger.info('Binance trader successfully booted')

    @run_in_executor
    def create_order(self, **kwargs):
        if kwargs.get('signal_id'):
            parts = kwargs.get('symbol').split("_")
            if not len(parts) == 2:
                return {'error': True, 'message': 'Invalid Symbol'}
            symbol = parts[1] + parts[0]
        else:
            symbol = kwargs.get('symbol')
        logger.info(f"The symbol is {symbol}")
        side = kwargs.get('side')
        order_type = kwargs.get('type')
        price = kwargs.get('price')
        logger.debug(f"[+] Trade params, side {side}, type {order_type}, price {price}")
        logger.debug("[+] Getting the quantity")
        if side == "BUY":
            quantity_resp = self.get_buy_size(symbol, price)
            order_id = f"BUY_{uuid.uuid4()}"
        elif side == "SELL":
            quantity_resp = self._get_sell_size(symbol, price)
            order_id = kwargs.get('order_id', f"SELL_{uuid.uuid4()}")
        else:
            return {'error': True, 'message': f'Side not understood, side was {side}, should be either BUY or SELL'}
        logger.debug(f"[+] The quantity response is {quantity_resp}")
        if quantity_resp['error']:
            logger.error(quantity_resp['message'])
            return quantity_resp
        quantity = quantity_resp['size']
        if quantity_resp.get('price'):
            price = quantity_resp['price']
        if not quantity:
            return {'error': True, 'message': 'zero quantity'}
        if not symbol or not side or not quantity or not price:
            return {'error': True, 'message': f'fill all mandatory fields, symbol: {symbol}, side: {side}, price: {price}, quantity: {quantity}'}
        if not order_type:
            order_type = 'LIMIT'
        orders = self.account.open_orders(symbol)
        if orders:
            logger.debug(f"[+] Symbol {symbol} has open orders.")
            order_list = [order for order in orders if order['side'] == side]
            logger.info(f"[!] Cancelling orders {[order['orderId'] for order in order_list]}")
            for order in order_list:
                self.account.cancel_order(symbol, order_id=order['orderId'])

        resp = self.account.new_order(symbol= symbol, side=side, type=order_type,  quantity=quantity, price=f"{price:.8f}", new_client_order_id=order_id)

        assets_res = self._assets_from_symbol(symbol)
        if assets_res['error']:
            base, quote = re.search("([A-Z]+)(BTC|ETH|BNB|USDT)",symbol).groups()
        else:
            base, quote = assets_res['result']['base_asset'], assets_res['result']['quote_asset']
        if side == "BUY":
            params = {
                'exchange': self._exchange,
                'symbol': resp['symbol'],
                'buy_order_id': resp['clientOrderId'],
                'buy_time': resp['transactTime'],
                'quote_asset': quote,
                'base_asset': base,
                'buy_price': resp['price'],
                'buy_quantity': resp['origQty'],
                'buy_status': resp['status'],
                'side': 'BUY'
            }
            return {'error': False, 'result': params}

        if side == "SELL":
            params = {
                'exchange': self._exchange,
                'symbol': resp['symbol'],
                'sell_order_id': resp['clientOrderId'],
                'sell_time': resp['transactTime'],
                'sell_price': resp['price'],
                'sell_quantity': resp['origQty'],
                'sell_status': resp['status'],
                'side': 'SELL'
            }
            return {'error': False, 'result': params}

    async def warmup(self):
        '''
        check for balances of the account. match them to recently placed orders. sell everything else to BTC.
        :return:
        '''
        try:
            logger.info("[+] Starting to warm up")
            balances_resp = await self.get_asset_balances()
            if balances_resp['error']:
                logger.error(f"[+] Error getting balances, {balances_resp['message']}")
                return
            balances = balances_resp['result']
            bal_list = []
            for balance in balances:
                bal_list.append({
                    'name': balance['asset'],
                    'free': balance['free'],
                    'locked': balance['locked']
                })
            await self.update_asset_balances(bal_list)

            for asset in balances:
                if asset['asset'] == "BTC":
                    continue
                asset_name = asset['asset']

                last_saved_orders = await self.get_order_models()
                symbol = f"{asset_name}BTC"
                for quote in ['BTC','ETH','BNB','USDT']:
                    sym = f"{asset_name}{quote}"
                    last_order_l = [order for order in last_saved_orders if order.symbol == sym and order.side == "BUY"]
                    if last_order_l:
                        symbol = sym
                        break

                if last_order_l:
                    logger.info(f"[+] Orders found for symbol {symbol}, {last_order_l}")
                    last_order = max(last_order_l, key=lambda x: x.timestamp.timestamp())
                    buy_price = last_order.price
                    order_id = last_order.client_order_id.split("_")
                    if len(order_id) == 2:
                        order_id = f"SELL_{order_id[1]}"
                    else:
                        order_id = f"SELL_{order_id[0]}"
                else:
                    logger.info(f"[!] Did not find a saved order matching the symbol {symbol}")
                    exchange_recent_orders_resp = await self.get_recent_orders(symbol)
                    if exchange_recent_orders_resp['error']:
                        logger.error(f"[!] Ran into an error fetching recent orders for {symbol}, {exchange_recent_orders_resp['message']}")
                        continue
                    exchange_recent_orders = exchange_recent_orders_resp['result']

                    for order in exchange_recent_orders:
                        order_model_params = {
                            'order_id': order['orderId'],
                            'client_order_id': order['clientOrderId'],
                            'symbol': order['symbol'],
                            'price': order['price'],
                            'quantity': order['origQty'],
                            'type': order['type'],
                            'side': order['side'],
                            'order_time': datetime.fromtimestamp(int(order['time'])/1000),
                            'status': order['status'],
                            'cummulative_filled_quantity': order['executedQty'],
                            'cummulative_quote_asset_transacted': order['cummulativeQuoteQty']
                        }
                        await self.update_order_model(**order_model_params)

                    recent_buys = [order for order in exchange_recent_orders if order['side'] == 'BUY']
                    if recent_buys:
                        last_exchange_order = max(recent_buys, key=lambda x: int(x['time']))
                        buy_price = last_exchange_order['price']
                        logger.info(f"[+] Last price for {symbol} is {buy_price}")

                        order_id = last_exchange_order['clientOrderId'].split("_")
                        if len(order_id) == 2:
                            order_id = f"SELL_{order_id[1]}"
                        else:
                            order_id = f"SELL_{order_id[0]}"

                    else: #we cannot trace this symbol anywhere, lets use market price to convert it to BTC.
                        logger.info(f"[!] No recent order information available on {symbol}, defaults to using market price")
                        buy_price_resp = await self.get_last_price(symbol)
                        if buy_price_resp['error']:
                            logger.error(f"[!] Error occured getting last price for {symbol}, {buy_price_resp['message']}")
                        buy_price = buy_price_resp['result']['price']
                        order_id = f"SELL_{uuid.uuid4()}"

                sell_size_resp = await self.get_sell_size(symbol, float(buy_price) * (1 + self.profit_margin))
                if sell_size_resp['error']:
                    logger.error(f"{sell_size_resp['message']}")
                    continue
                sell_size = sell_size_resp['size']
                order_params = {
                        'symbol': symbol,
                        'exchange': self._exchange,
                        'side': 'SELL',
                        'price': float(buy_price) * (1+ self.profit_margin),
                        'quantity': sell_size,
                        'order_id': order_id
                    }
                await self.orders_queue.put(order_params)
        except Exception as e:
            logger.exception(e)

    @run_in_executor
    def cancel_order(self, symbol, id):
        resp = self.account.cancel_order(symbol=symbol, order_id=id)
        client_order_id = resp['clientOrderId']
        self.update_order_model(client_order_id=client_order_id, **resp)
        return True

    @run_in_executor
    def query_order(self, symbol, id):
        resp = self.account.query_order(symbol=symbol, order_id=id)
        return resp

    def _get_symbol_info(self, symbol):
        exchange_info = self.exchange_info
        symbol_info_list = [data for data in exchange_info['symbols'] if data['symbol'] == symbol]
        if not symbol_info_list:
            return {'error': True, 'message': 'Symbol was not found in exchange'}
        return {'error': False, 'result': symbol_info_list[0]}


    #@run_in_executor
    def get_buy_size(self, symbol, price):
        logger.debug(f"[+] Getting buy size for {symbol} at {price}")
        symbol_info_res = self._get_symbol_info(symbol)
        if symbol_info_res['error']:
            return symbol_info_res
        symbol_info = symbol_info_res['result']
        symbol_filters = symbol_info['filters']
        quote_asset = symbol_info['quoteAsset']
        logger.debug(f"[+] Quote Asset is {quote_asset}")
        lot_filter_list = [sym_filter for sym_filter in symbol_filters if sym_filter['filterType'] == "LOT_SIZE"]
        if not lot_filter_list:
            return {'error': True, 'message': 'Symbol has no Lot Size Filter'}
        lot_filter = lot_filter_list[0]
        minQty = float(lot_filter['minQty'])
        stepSize = float(lot_filter['stepSize'])
        logger.debug(f"[+] minQty {minQty} and stepSize {stepSize}")

        min_notional_filter_list = [sym_filter for sym_filter in symbol_filters if sym_filter['filterType'] == "MIN_NOTIONAL"]
        if not min_notional_filter_list:
            return {'error': True, 'message': 'Symbol has no Min Notional Filter'}
        min_notional_filter = min_notional_filter_list[0]
        minNotional = float(min_notional_filter['minNotional'])

        print(f"minQty: {minQty}, stepSize: {stepSize}, minNotational {minNotional}")
        #get account balance
        account_info = self.account.account_info()
        print("[+] Got the account info")
        balances = account_info['balances']
        asset_balance_list = [bal for bal in balances if bal['asset'] == quote_asset]
        if not asset_balance_list:
            return {'error': True, 'message': 'Asset if not found in account_info, weird'}
        asset_balance = float(asset_balance_list[0]['free']) + float(asset_balance_list[0]['locked'])
        logger.info(f"[+] Checking asset {quote_asset} for balance, {asset_balance}")
        if not asset_balance:
            return {'error': True, 'message': 'Zero account balance'}
        budget = asset_balance * self.percent_size
        amount_to_buy = budget/price

        if amount_to_buy < minQty:
            return {'error': True, 'message': 'Account balance is too low, consider increasing the percent_size'}
        notional = amount_to_buy * price
        if notional < minNotional:
            free_balance = float(asset_balance_list[0]['free'])
            if free_balance/price >= minNotional:
                amount_to_buy = minNotional/price
            else:
                return {'error': True, 'message': f'Failed the minimum notional value, notional {notional}, minimum notional {minNotional}'}
        stepped_amount_to_buy = amount_to_buy - (amount_to_buy % stepSize) + stepSize
        logger.debug(f"[+] The calculated quantity is {stepped_amount_to_buy}, min notation is {minNotional} and notation is {stepped_amount_to_buy * price}")
        return {'error': False, 'size': f"{stepped_amount_to_buy:.6f}"}

    @run_in_executor
    def get_sell_size(self, symbol, price):
        return self._get_sell_size(symbol, price)

    def _get_sell_size(self, symbol, price):
        price = float(price)
        symbol_info_res = self._get_symbol_info(symbol)
        if symbol_info_res['error']:
            return symbol_info_res
        symbol_info = symbol_info_res['result']

        symbol_filters = symbol_info['filters']
        base_asset = symbol_info['baseAsset']

        lot_filter_list = [sym_filter for sym_filter in symbol_filters if sym_filter['filterType'] == "LOT_SIZE"]
        if not lot_filter_list:
            return {'error': True, 'message': 'Symbol has no Lot Size Filter'}
        lot_filter = lot_filter_list[0]
        minQty = float(lot_filter['minQty'])
        stepSize = float(lot_filter['stepSize'])
        logger.debug(f"[+] minQty {minQty} and stepSize {stepSize}")

        min_notional_filter_list = [sym_filter for sym_filter in symbol_filters if
                                    sym_filter['filterType'] == "MIN_NOTIONAL"]
        if not min_notional_filter_list:
            return {'error': True, 'message': 'Symbol has no Min Notional Filter'}
        min_notional_filter = min_notional_filter_list[0]
        minNotional = float(min_notional_filter['minNotional'])

        price_filter_list = [sym_filter for sym_filter in symbol_filters if
                                    sym_filter['filterType'] == "PRICE_FILTER"]
        if not price_filter_list:
            return {'error': True, 'message': 'Symbol has no Price Filter'}
        price_filter = price_filter_list[0]
        minPrice = float(price_filter['minPrice'])
        tickSize = float(price_filter['tickSize'])
        if price < minPrice:
            logger.error(f"[!] The price of {price} is less than min price {minPrice}, changing to minPrice")
            price = minPrice
        if not price % tickSize == 0:
            new_price = price - (price % tickSize) + tickSize
            logger.error(f"[!] Round of price from {price} to  {new_price}")
            price = new_price

        # get account balance
        account_info = self.account.account_info()
        logger.debug("[+] Got the account info")
        balances = account_info['balances']
        asset_balance_list = [bal for bal in balances if bal['asset'] == base_asset]
        if not asset_balance_list:
            return {'error': True, 'message': 'Asset if not found in account_info, weird'}
        asset_balance = float(asset_balance_list[0]['free'])
        if not asset_balance:
            return {'error': True, 'message': 'Zero account balance'}
        notional = asset_balance * price
        if notional < minNotional:
            return {'error': True, 'message': f'Failed on minimum Notional, notional {notional}, min notional {minNotional}'}
        if asset_balance < minQty:
            return {'error': True,'message': f'Failed on minimum Quantity, quantity {asset_balance}, min quantity {minQty}'}
        taxed_asset_balance = asset_balance * 0.9975
        asset_balance = taxed_asset_balance - (taxed_asset_balance % stepSize)
        return {'error': False, 'size': asset_balance, 'price': price}

    async def process_user_socket_message(self, msg):
        # throw it in the database
        try:
            payload = msg
            if payload['e'] == "outboundAccountInfo":
                balances_all = payload['B']
                logger.info(f"{self._exchange} received a balance event, {balances_all}")
                balances = [{'asset': bal['a'], 'free': bal['f'], 'locked': bal['l']} for bal in balances_all if
                            float(bal['f']) or float(bal['l'])]
                logger.debug(f"balances : {balances}")
                asset_balances_list = []
                for balance in balances:
                    balance_model = {
                        'name': balance['a'],
                        'free': balance['f'],
                        'locked': balance['l']
                    }
                    asset_balances_list.append(balance_model)
                await self.update_asset_balances(asset_balances_list)

            elif payload['e'] == "executionReport":
                logger.info(f"{self._exchange} received a trading event")
                trade_params = {
                    'trade_id': payload.get('t'),
                    'orderId': payload.get('i'),
                    'client_order_id': payload.get('c'),
                    'symbol': payload.get('s'),
                    'price': payload.get('p'),
                    'quantity': payload.get('l'),
                    'commission': payload.get('n'),
                    'commissionAsset': payload.get('N'),
                    'time': payload.get('T'),
                    'isBuyer': not bool(payload.get('m')),
                    'isMaker': payload.get('m'),
                    'isBestMatch': None,
                    'type': payload.get('x'),
                    'status': payload.get('X'),
                    'side': payload.get('S'),
                    'cummulative_filled_quantity': payload['z'],
                    'cummulative_quote_asset_transacted': payload['Z'],
                    'stop_price' : payload.get('P')
                }

                order_model_params = {
                    'order_id': trade_params['orderId'],
                    'client_order_id': trade_params['client_order_id'],
                    'symbol': trade_params['symbol'],
                    'price': trade_params['price'],
                    'quantity': trade_params['quantity'],
                    'type': trade_params['type'],
                    'side': trade_params['side'],
                    'stop_price': trade_params['stop_price'],
                    'commission': trade_params['commission'],
                    'commission_asset': trade_params['commissionAsset'],
                    'order_time': datetime.fromtimestamp(int(trade_params['time'])/1000),
                    'cummulative_filled_quantity': trade_params['cummulative_filled_quantity'],
                    'cummulative_quote_asset_transacted': trade_params['cummulative_quote_asset_transacted'],
                    'status': trade_params['status']
                }

                if trade_params['side'] == 'BUY':
                    trade_model_params = {
                        'exchange': self._exchange,
                        'symbol': trade_params['symbol'],
                        'buy_order_id': trade_params['client_order_id'],
                        'buy_status': trade_params['status'],
                        'buy_quantity_executed': trade_params['cummulative_filled_quantity'],
                    }
                else:
                    trade_model_params = {
                        'exchange': self._exchange,
                        'symbol': trade_params['symbol'],
                        'sell_order_id': trade_params['client_order_id'],
                        'sell_status': trade_params['status'],
                        'sell_quantity_executed': trade_params['cummulative_filled_quantity'],
                    }

                logger.info(f"[+] Saving order to database {order_model_params}")
                await self.update_order_model(**order_model_params)
                asyncio.sleep(3)
                await self.update_trade(**trade_model_params)

                if trade_params['type'] == "NEW":
                    self.active_symbols.append(order_model_params)

                if trade_params['type'] == "TRADE":
                    if trade_params['side'] == "BUY" and trade_params['status'] in ['FILLED', 'PARTIALLY_FILLED']: #we have bought something, lets put up a sell
                        avg_price = float(trade_params['cummulative_quote_asset_transacted']) / float(trade_params['cummulative_filled_quantity'])
                        sell_price = avg_price * (1 + self.profit_margin)
                        logger.info(f"[+] Trade event, we've bought {trade_params['cummulative_filled_quantity']} at {avg_price}")
                        logger.info(f"[+] Placing a sell for {trade_params['cummulative_filled_quantity']} at {sell_price}")
                        sell_size_resp = await self.get_sell_size(trade_params['symbol'], sell_price)
                        if sell_size_resp['error']:
                            logger.error(f"[!] {sell_size_resp['message']}")
                        order_id = f"SELL_{trade_params['client_order_id'].split('_')[1]}"
                        await self.orders_queue.put({
                            'symbol': trade_params['symbol'],
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_size_resp['price'],
                            'quantity': float(trade_params['cummulative_filled_quantity']),
                            'order_id': order_id
                        })
                        if trade_params['status'] == "FILLED":
                            ol = [o for o in self.active_symbols if o['client_order_id'] == trade_params['client_order_id']]
                            if ol:
                                o = ol[0]
                                self.active_symbols.remove(o)

                if trade_params['type'] == "CANCELED":
                    if trade_params['side'] == "SELL":
                        logger.warning("[!] You just cancelled a a SELL! You dont cancel a sell. Sleeping for 30s to avoid conflicts")
                        await asyncio.sleep(30)
                        symbol = trade_params['symbol']
                        sell_size_resp = await self.get_sell_size(symbol, trade_params['price'])
                        if not sell_size_resp['error']:
                            _order_params = {
                                'symbol': symbol,
                                'exchange': self._exchange,
                                'side' : 'SELL',
                                'quantity': sell_size_resp['size'],
                                'price': sell_size_resp['price']
                            }
                            await self.orders_queue.put(_order_params)
                    ol = [o for o in self.active_symbols if o['client_order_id'] == trade_params['client_order_id']]
                    if ol:
                        o = ol[0]
                        self.active_symbols.remove(o)

            elif payload['e'] == 'error':
                error = payload['m']
                logger.error(f"A network connection error occured, {error}")

            elif payload['e'] == 'connection_lost':
                #update last_update_time
                message = payload['m']
                logger.error(f"{message}")

            elif payload['e'] == 'connection_started':
                #update connection established
                message = payload['m']
                logger.info(f"{message}")
            else:
                logger.error(f"unknown event, {msg}")
        except json.JSONDecodeError as e:
            logger.error(f"error occured, {e}")

        except Exception as e:
            logger.error(f"unknown error occurred, {e}")

    async def process_symbol_stream(self, msg):
        payload = msg
        _params = {
            'type': payload['e'],
            'time' : payload['T'],
            'symbol': payload['s'],
            'price': payload['p'],
            'quantity': payload['q'],
        }
        symbol_params_l = [symbol_params for symbol_params in self.active_symbols if symbol_params['symbol'] == _params['symbol']]
        if not symbol_params_l: #maybe symbol is no longer active, stop stream.
            active_orders = await self.get_order_models()
            order_l = [order for order in active_orders if order.symbol == _params['symbol'] and order.status is not 'CANCELLED']
            if not order_l:
                logger.info(f"[+] Did not find an active trade for {_params['symbol']}, closing stream now")
                self.streamer.remove_trades(_params['symbol'])
                return
            order = order_l[0]
            order_dict = order.serialize()
            order_dict['current_price'] = _params['price']
            self.active_symbols.append(order_dict)
            logger.info(f"[+] Added {order_dict} to active symbols, {self.active_symbols}")
            return
        symbol_params = symbol_params_l[0]
        symbol_params['current_price'] = _params['price']

    @run_in_executor
    def get_asset_balances(self):
        try:
            balances_res = self.account.account_info()
            balances = balances_res['balances']
            asset_balances = [bal for bal in balances if float(bal['free']) > 0]
            logger.info("[+] Current account balances")
            logger.info(asset_balances)
            return {"error": False, "result": asset_balances}
        except Exception as e:
            return {'error': True, 'message': f"{e}"}

    @run_in_executor
    def get_recent_orders(self, symbol):
        try:
            orders_resp = self.account.all_orders(symbol)
            return {'error': False, 'result': orders_resp}
        except Exception as e:
            return {'error': True, 'message': str(e)}

    @run_in_executor
    def get_last_price(self, symbol):
        try:
            resp = binance.ticker_price(symbol)
            return {'error': False, 'result': resp}
        except Exception as e:
            return {'error': True, 'message': str(e)}

    async def routine_check(self):
        '''
        check order has not expired
        check order has not been stop lossed
        run every minute
        :return:
        '''
        try:
            order_models = await self.get_order_models()
            open_order_models = [order_model for order_model in order_models if order_model.status == "NEW"]
            closed_order_models = [order_model for order_model in order_models if order_model.status in ['FILLED', 'PARTIALLY_FILLED']]
            for order in open_order_models:
                if order.side == 'BUY' and datetime.utcnow() - order.order_time > self.parse_time(self.order_timeout):
                    logger.info(f"[!] Order {order.client_order_id} has expired, cancelling")
                    await self.cancel_order(order.symbol, order.order_id)

                if order.side == "SELL":
                    complementary_buy_orders = [order_model for order_model in closed_order_models if order_model.symbol == order.symbol and order_model.side == "BUY"]
                    last_buy_order = max(complementary_buy_orders, key=lambda x: int(x['order_time']))
                    buy_price = last_buy_order.price
                    market_price_resp = await self.get_last_price(order.symbol)
                    if market_price_resp['error']:
                        logger.error(market_price_resp['message'])
                        continue
                    market_price = market_price_resp['result']
                    if float(market_price) < float(buy_price) - self.stop_loss_trigger: #we've gone below our stop loss
                        logger.warning(f"[!] Market price for {order.symbol} has gone below stop loss trigger, placing stop loss sell")
                        order_id = f"SELL_{order.order_id.split('_')[1]}"
                        await self.orders_queue.put({
                            'symbol': order.symbol,
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': market_price * 0.995,
                            'order_id': order_id
                        })
        except Exception as e:
            logger.exception(e)

    async def assets_from_symbol(self, symbol):
        return self._assets_from_symbol(symbol)

    def _assets_from_symbol(self, symbol):
        symbol_info_resp = self._get_symbol_info(symbol)
        if symbol_info_resp['error']:
            logger.error(f"[!] {symbol_info_resp['message']}")
            return {'error': True, 'message': symbol_info_resp['message']}
        symbol_info = symbol_info_resp['result']
        return {'error': False, 'result': {'quote_asset': symbol_info['quoteAsset'], 'base_asset': symbol_info['baseAsset']}}