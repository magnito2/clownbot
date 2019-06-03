from trader.trader import Trader
import logging, json, uuid, asyncio, re,os, emoji
from binance import binance
from utils import run_in_executor
from datetime import datetime, timedelta
from models import create_session, BinanceSymbol

logger = logging.getLogger('clone.binance_trader')
binance.__log_enabled = True

class BinanceTrader(Trader):

    def __init__(self, **kwargs):
        try:
            Trader.__init__(self, **kwargs)
            self.account = binance.Account(kwargs.get('api_key'), kwargs.get('api_secret'))
            self._exchange = 'BINANCE'
            self.streamer = binance.Streamer()
            self.streamer.start_user(kwargs.get('api_key'), self.process_user_socket_message)

            self.exchange_info = binance.exchange_info()
            self.active_symbols = []

            self.fees = 0.001
        except Exception as e:
            logger.exception(e)

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
        quantity = kwargs.get('quantity')

        if not quantity:
            if side == "BUY":
                quantity_resp = self.quantity_and_price_roundoff(symbol=symbol, price=price, side='BUY')
            else:
                quantity_resp = self.quantity_and_price_roundoff(symbol=symbol, price=price, side='SELL')

            if quantity_resp['error']:
                logger.error(quantity_resp['message'])
                return {'error' : True, 'message' : quantity_resp['message']}
            quantity = quantity_resp['size']
            price = quantity_resp['price']

        else:
            quantity_resp = self.quantity_and_price_roundoff(symbol, price, quantity, side)
            if quantity_resp['error']:
                logger.error(quantity_resp['message'])
                return {'error': True, 'message': quantity_resp['message']}
            quantity = quantity_resp['size']
            price = quantity_resp['price']

        if side == "BUY":
            order_id = f"BUY_{str(uuid.uuid4())[:23]}"
        else:
            order_id = kwargs.get('order_id', f"SELL_{str(uuid.uuid4())[:23]}")

        if not quantity:
            return {'error': True, 'message': 'zero quantity'}
        if not symbol or not side or not quantity or not price:
            return {'error': True, 'message': f'fill all mandatory fields, symbol: {symbol}, side: {side}, price: {price}, quantity: {quantity}'}
        if not order_type:
            order_type = 'LIMIT'

        #orders = self.account.open_orders(symbol)
        #if orders:
        #    logger.debug(f"[+] Symbol {symbol} has open orders.")
        #    order_list = [order for order in orders if order['side'] == side]
        #    logger.info(f"[!] Cancelling orders {[order['orderId'] for order in order_list]}")
        #    for order in order_list:
        #       self.account.cancel_order(symbol, order_id=order['orderId'])

        print(f"{'+'*70}")
        print(f"New order, {symbol} {side} {order_type} {quantity} {price} {order_id}")
        resp = self.account.new_order(symbol= symbol, side=side, type=order_type,  quantity=quantity, price=f"{price:.8f}", new_client_order_id=order_id)

        symbol_info = self.get_symbol_info(symbol)

        print(f"{'+'*100}")
        print('response is')
        print(resp)
        print(f"{'-'*100}")
        if side == "BUY":
            params = {
                'exchange': self._exchange,
                'symbol': resp['symbol'],
                'buy_order_id': resp['clientOrderId'],
                'buy_time': resp['transactTime'],
                'quote_asset': symbol_info.quote_asset,
                'base_asset': symbol_info.base_asset,
                'buy_price': resp['price'],
                'buy_quantity': resp['origQty'],
                'buy_status': resp['status'],
                'side': 'BUY',
                'exchange_account_id': self.account_model_id
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
                'side': 'SELL',
                'buy_order_id': kwargs.get('buy_order_id')
            }
            return {'error': False, 'result': params}

    @run_in_executor
    def a_quantity_and_price_roundoff(self, symbol=None, price=None, quantity=None, side=None):
        return self.quantity_and_price_roundoff(symbol=symbol, price=price, quantity=quantity, side=side)

    def quantity_and_price_roundoff(self, symbol=None, price=None, quantity=None, side=None):
        logger.debug(f"[+] Rounding off price and quantity")
        symbol_info = self.get_symbol_info(symbol)

        if side == "BUY":
            _asset = symbol_info.quote_asset
        else:
            _asset = symbol_info.base_asset

        minQty = float(symbol_info.min_qty)
        stepSize = float(symbol_info.step_size)
        minNotional = float(symbol_info.min_notional)

        asset_model = self._get_asset_models(_asset)
        if not asset_model:
            return {'error': True, 'message': f'{side} {quantity} {symbol} @ {price} Zero account balance'}
        free_balance = float(asset_model.free)
        locked_balance = float(asset_model.locked)
        total_asset_balance = free_balance + locked_balance

        if not total_asset_balance:
            return {'error': True, 'message': f'{side} {quantity} {symbol} @ {price}Zero account balance'}

        if quantity:
            base_quantity = float(quantity)
        else:
            if side == 'BUY':
                if self.btc_per_order:
                    budget = self.btc_per_order
                else:
                    budget = total_asset_balance * self.percent_size
                base_quantity = budget / price
            else:
                base_quantity = free_balance

        if side == "BUY":
            if base_quantity * price > free_balance:
                return {'error': True, 'message': f' {side} {base_quantity} {symbol} @ {price} You have placed an order to {side} more than the account balance, acc bal {free_balance} '}
        elif side == "SELL":
            if base_quantity > free_balance:
                base_quantity = free_balance
                #return {'error': True, 'message': f'You have place an order to trade more than you own and trading fees, {side}ING {base_quantity} '}
            price = price - price % symbol_info.tick_size + symbol_info.tick_size

        notional = base_quantity * price
        if notional < minNotional:
            margin_of_safety = (1 + self.stop_loss_trigger * 1.005) #just margins of safety
            if side == 'BUY' and free_balance >= minNotional * margin_of_safety:
                base_quantity = (minNotional / price) * margin_of_safety
            elif side == 'SELL' and free_balance * price >= minNotional * margin_of_safety:
                base_quantity = (minNotional / price) * margin_of_safety
            else:
                if side == 'SELL':
                    lowest_price = minNotional/base_quantity
                    symbols_info = self.exchange_info['symbols']
                    xch_sym_info = [inf for inf in symbols_info if inf['symbol'] == symbol]
                    if xch_sym_info:
                        xch_sym_info = xch_sym_info[0]
                        xch_filters = xch_sym_info['filters']
                        percent_price_filter = [filter for filter in xch_filters if filter['filterType'] == 'PERCENT_PRICE']
                        if percent_price_filter:
                            percent_price_filter = percent_price_filter[0]
                            avg_market_price = binance.avgPrice(symbol)
                            if lowest_price > float(avg_market_price['price']) * float(percent_price_filter['multiplierUp']):
                                return {'error': True, 'message': f'{side} {base_quantity} {symbol} @ {price}\n Order will fail percent price filter \n{symbol} \nside{side} \norder price{lowest_price} \navg market price {avg_market_price["price"]} \nmultiplier-up {percent_price_filter["multiplierUp"]}'}

                    price = lowest_price - lowest_price % symbol_info.tick_size + symbol_info.tick_size
                else:
                    return {'error': True,
                        'message': f'Failed the minimum notional value, notional {notional}, minimum notional {minNotional}, symbol {symbol} side{side}'}
        if side == 'BUY':
            stepped_amount_to_trade = base_quantity - (base_quantity % stepSize) + stepSize
        else:
            stepped_amount_to_trade = base_quantity - (base_quantity % stepSize)

        if stepped_amount_to_trade < minQty:
            return {'error': True, 'message': f'{symbol}, trading qty {stepped_amount_to_trade}, min qty {minQty} Account balance is too low'}

        return {'error': False, 'size': f"{stepped_amount_to_trade:.6f}", 'price': price}

    async def warmup(self):
        '''
        check for balances of the account. match them to recently placed orders. sell everything else to BTC.
        :return:
        '''
        try:
            logger.info("[+] Warming up")
            balances_resp = await self.get_asset_balances()
            if balances_resp['error']:
                logger.error(f"[+] Error getting balances, {balances_resp['message']}")
                if 'code' in balances_resp and balances_resp['code'] == -2015:
                    await self.invalidate_keys()
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

        except binance.BinanceError as e:
            if e.code in [-2014, -2015]:
                await self.invalidate_keys()
                self.keep_running = False
                return
        except Exception as e:
            logger.exception(e)

    @run_in_executor
    def cancel_order(self, symbol, id):
        try:
            resp = self.account.cancel_order(symbol=symbol, order_id=id)
            client_order_id = resp['clientOrderId']
            _order_params = {
                    'exchange': self._exchange,
                    'client_order_id': client_order_id,
                    'symbol': resp['symbol'],
                    'price': resp['price'],
                    'quantity': resp['origQty'],
                    'type': resp['type'],
                    'side': resp['side'],
                    'order_time': datetime.fromtimestamp(int(resp["transactTime"])/1000),
                    'cummulative_filled_quantity': resp['executedQty'],
                    'cummulative_quote_asset_transacted': resp["cummulativeQuoteQty"],
                    'status': resp['status']
                }
            self._update_order_model(client_order_id=client_order_id, **_order_params)
        except binance.BinanceError as e:
            logger.error(f"[!] Error cancelling the order, {e} code {e.code}")
            return False
        except Exception as e:
            logger.error(f"[!] Error cancelling the order, {e}")
            return False
        return True

    @run_in_executor
    def query_order(self, symbol, id):
        resp = self.account.query_order(symbol=symbol, order_id=id)
        return resp

    async def process_user_socket_message(self, msg):
        # throw it in the database
        try:
            payload = msg
            if payload['e'] == "outboundAccountInfo":
                balances_all = payload['B']
                balances = [{'asset': bal['a'], 'free': bal['f'], 'locked': bal['l']} for bal in balances_all if
                            float(bal['f']) or float(bal['l'])]
                logger.debug(f"balances : {balances}")
                asset_balances_list = []
                for balance in balances:
                    balance_model = {
                        'name': balance['asset'],
                        'free': balance['free'],
                        'locked': balance['locked']
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
                    'quantity': payload.get('q'),
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
                    'exchange': self._exchange,
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
                        'exchange_account_id' : self.account_model_id,
                        'side': 'BUY'
                    }
                else:
                    trade_model_params = {
                        'exchange': self._exchange,
                        'symbol': trade_params['symbol'],
                        'sell_order_id': trade_params['client_order_id'],
                        'sell_status': trade_params['status'],
                        'sell_quantity_executed': trade_params['cummulative_filled_quantity'],
                        'side': 'SELL'
                    }

                await self.update_order_model(**order_model_params)
                await asyncio.sleep(3)
                await self.update_trade(**trade_model_params)

                await self.send_notification(f"{emoji.emojize(':dollar:', use_aliases=True)} {order_model_params['status']}: {order_model_params['side']}ING {order_model_params['quantity']} @ {order_model_params['price']}")

                if trade_params['type'] == "NEW":
                    self.active_symbols.append(order_model_params)

                if trade_params['type'] == "TRADE":
                    if trade_params['side'] == "BUY" and trade_params['status'] in ['FILLED', 'PARTIALLY_FILLED']: #we have bought something, lets put up a sell
                        avg_price = float(trade_params['cummulative_quote_asset_transacted']) / float(trade_params['cummulative_filled_quantity'])
                        sell_price = avg_price * (1 + self.profit_margin)
                        logger.info(f"[+] Trade event, we've bought {trade_params['cummulative_filled_quantity']} at {avg_price}")
                        logger.info(f"[+] Placing a sell for {trade_params['cummulative_filled_quantity']} at {sell_price}")
                        sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'], price=sell_price, side='SELL')
                        if sell_size_resp['error']:
                            logger.error(f"[!] {sell_size_resp['message']}")
                        order_id = f"SELL_{trade_params['client_order_id'].split('_')[1]}"
                        await self.orders_queue.put({
                            'symbol': trade_params['symbol'],
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_size_resp['price'],
                            'quantity': float(trade_params['cummulative_filled_quantity']),
                            'order_id': order_id,
                            'buy_order_id': trade_params['client_order_id']
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
                        sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=symbol, price=trade_params['price'], side='SELL')
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
            logger.exception(e)

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
        except binance.BinanceError as e:
            logger.exception(e)
            return {'error': True, 'message': f"{e}", 'code': e.code}
        except Exception as e:
            logger.exception(e)
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
            return {'error': False, 'result': resp['price']}
        except Exception as e:
            return {'error': True, 'message': str(e)}

    @run_in_executor
    def get_avg_price(self, symbol):
        try:
            resp = binance.avgPrice(symbol)
            return {'error': False, 'result': resp['price']}
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
            logger.info("[+] We have the following open orders")
            logger.info(open_order_models)
            for order in open_order_models:
                if order.side == 'BUY' and datetime.utcnow() - order.order_time > self.parse_time(self.order_timeout):
                    open_orders = await self.get_open_orders(order.symbol)
                    cur_order = [o for o in open_orders if o['orderId'] == order.order_id]
                    if cur_order:
                        await self.cancel_order(order.symbol, order.order_id)
                    else:
                        logger.info(f"[!] Order {order.client_order_id} has expired, cancelling")
                        await self.update_order_model(client_order_id=order.client_order_id, status='CANCELED')

                if order.side == "SELL":
                    logger.info(f"Checking if order {order} should be cancelled")
                    trade_model = await self.get_trade_model(sell_order_id=order.client_order_id)
                    if trade_model:
                        buy_price = trade_model.buy_price
                        market_price_resp = await self.get_avg_price(order.symbol)
                        if market_price_resp['error']:
                            logger.error(market_price_resp['message'])
                            continue
                        market_price = float(market_price_resp['result'])
                        print(f"Comparing buy {buy_price} and current {market_price} stop loss {self.stop_loss_trigger} stop loss price {buy_price * (1 - self.stop_loss_trigger)}")
                        if market_price < float(buy_price) * (1 - self.stop_loss_trigger):  # we've gone below our stop loss

                            if order.price < market_price * 1.005:
                                continue #no need to stop stop-losses
                            logger.warning(
                                f"[!] Market price for {order.symbol} has gone below stop loss trigger, placing stop loss sell")

                            sell_price = market_price * 0.995
                            await self.cancel_order(order.symbol, order.order_id)
                            order_id = f"SELL-LOSS_{order.client_order_id.split('_')[1]}"

                            await self.orders_queue.put({
                                'symbol': order.symbol,
                                'exchange': 'BINANCE',
                                'side': 'SELL',
                                'price': sell_price,
                                'order_id': order_id,
                                'buy_order_id': trade_model.buy_order_id
                            })
                    else:
                        logger.info('order does not have an accompanying buy order, cannot check for stop loss')
            for order_model in closed_order_models:
                if order_model.side == 'BUY':
                    trade_model = await self.get_trade_model(buy_order_id=order_model.client_order_id)
                    if trade_model and not trade_model.sell_status in ['NEW','FILLED','PARTIALLY_FILLED']:
                        logger.info(f'[+] BUY {trade_model.buy_quantity} {trade_model.symbol} @{trade_model.buy_price} Found an order with completed buy bt no sell')
                        buy_price = trade_model.buy_price
                        sell_price = buy_price * (1 + self.profit_margin)
                        sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_model.symbol,
                                                                                  price=sell_price, side='SELL')
                        if sell_size_resp['error']:
                            logger.error(f"[!] {sell_size_resp['message']}")
                        order_id = f"SELL_{trade_model.buy_order_id.split('_')[1]}"
                        await self.orders_queue.put({
                            'symbol': trade_model.symbol,
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_size_resp['price'],
                            'quantity': float(sell_size_resp['size']),
                            'order_id': order_id,
                            'buy_order_id': trade_model.buy_order_id
                        })

        except binance.BinanceError as e:
            logger.exception(e)
            if hasattr(e, 'code') and e.code in [-2014, -2015]:
                await self.invalidate_keys()

        except Exception as e:
            logger.exception(e)


    def get_symbol_info(self, symbol):
        if os.path.exists('last_binance_symbols_update'):
            last_update = datetime.fromtimestamp(os.path.getmtime('last_binance_symbols_update'))
        else:
            last_update = datetime.fromtimestamp(0)
        with create_session() as session:
            if datetime.now() - last_update > timedelta(days=1) or not session.query(BinanceSymbol).filter_by(name=symbol).first() :
                exchange_info = self.exchange_info
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


    @run_in_executor
    def validate_keys(self):
        try:
            balances_res = self.account.account_info()
            return {"error": False, "result": "keys are okay"}
        except Exception as e:
            return {'error': True, 'message': f"{e}"}

    @run_in_executor
    def get_open_orders(self, symbol):
        return self.account.open_orders(symbol)