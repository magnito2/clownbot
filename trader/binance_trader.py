from trader.trader import Trader
import logging, json, uuid, asyncio, re,os, emoji
from binance import binance
from utils import run_in_executor
from datetime import datetime, timedelta
from models import create_session, BinanceSymbol
from utils.sync import async_to_sync, sync_to_async
import time

from trader.binance_portfolio import get_btc_price

logger = logging.getLogger('clone.binance_trader')
#logger.setLevel(logging.DEBUG)
binance.__log_enabled = True

class BinanceTrader(Trader):

    active_ticker_sockets = [] #a global list of tickers that need to be updated. have tickers running on a separate coroutine that checks price diff

    def __init__(self, **kwargs):
        try:
            Trader.__init__(self, **kwargs)
            self.account = binance.Account(kwargs.get('api_key'), kwargs.get('api_secret'))
            self._exchange = 'BINANCE'
            self.streamer = binance.Streamer()
            self.streamer.start_user(kwargs.get('api_key'), self.process_user_socket_message)

            self.exchange_info = binance.exchange_info() #used in multiple places, dont remove

            self.price_streamer = kwargs['price_streamer'] #class that streams in prices.

            self.scrapper_orders = {}
            logger.name = ""

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
        logger.info(f"{self.username} The symbol is {symbol}")
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
            #check that the signal has not maxed out on quantity to trade
            if not self.signal_can_buy(kwargs.get('signal_name'), symbol):
                logger.info(f"{self.username} Order has maxed out on limit")
                return {'error': True, 'message': f'Signal {kwargs.get("signal_name")} has maxed out on the limit set to it'}
            order_id = kwargs.get('order_id', f"BUY_{str(uuid.uuid4())[:23]}")
        else:
            if kwargs.get('order_id'):
                order_id = kwargs.get('order_id')
            elif kwargs.get('buy_order_id'):
                order_id = f"SELL_{kwargs.get('buy_order_id')}"
            else:
                order_id = f"SELL_{str(uuid.uuid4())[:23]}"

        if not quantity:
            return {'error': True, 'message': 'zero quantity'}
        if not symbol or not side or not quantity or not price:
            return {'error': True, 'message': f'fill all mandatory fields, symbol: {symbol}, side: {side}, price: {price}, quantity: {quantity}'}
        if not order_type:
            order_type = 'LIMIT'

        if side == "BUY": #dont have more that two open orders
            orders = self.sync_get_open_orders(symbol)
            if orders:
                logger.debug(f"[+] Symbol {symbol} has open orders.")

                if len(orders) > self.max_orders_per_symbol:
                    return {'error': True, 'message': f'There are already {self.max_orders_per_symbol} open orders for the symbol, cannot create a new one'}

        logger.info(f"{'+'*70}")
        logger.info(f"{self.username} New order, {symbol} {side} {order_type} {quantity} {price} {order_id}")
        if order_type == "LIMIT":
            resp = self.account.new_order(symbol= symbol, side=side, type=order_type,  quantity=quantity, price=f"{price:.8f}", new_client_order_id=order_id)
        elif order_type == "MARKET":
            resp = self.account.new_order(symbol=symbol, side=side, type=order_type, quantity=quantity, price=None, new_client_order_id=order_id, time_in_force=None)
        else:
            return {'error': True, 'message': 'Specify order type'}
        symbol_info = self.get_symbol_info(symbol)

        if side == "BUY":
            params = {
                'exchange': self._exchange,
                'symbol': resp['symbol'],
                'buy_order_id': resp['orderId'],
                'buy_time': datetime.utcfromtimestamp(int(resp['transactTime'])/1000),
                'quote_asset': symbol_info.quote_asset,
                'base_asset': symbol_info.base_asset,
                'buy_price': resp['price'],
                'buy_quantity': resp['origQty'],
                'buy_status': resp['status'],
                'side': 'BUY',
                'exchange_account_id': self.account_model_id,
                'trade_signal_id': kwargs.get('trade_signal_id')
            }
            return {'error': False, 'result': params, 'additional_info': {'signal': kwargs.get('trade_signal_name')}}

        if side == "SELL":
            params = {
                'exchange': self._exchange,
                'symbol': resp['symbol'],
                'sell_order_id': resp['orderId'],
                'sell_time': datetime.utcfromtimestamp(int(resp['transactTime'])/1000),
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
        if not free_balance:
            async_to_sync(self.http_update_asset_balances)()
            asset_model = self._get_asset_models(_asset)
            if not asset_model:
                return {'error': True, 'message': f'{side} {quantity} {symbol} @ {price} Zero account balance'}
            free_balance = float(asset_model.free)
            locked_balance = float(asset_model.locked)
            total_asset_balance = free_balance + locked_balance
            if not free_balance:
                return {'error': True, 'message': f'{side} {quantity} {symbol} @ {price}All your assets are locked in trades'}

        if quantity:
            base_quantity = float(quantity)
        else:
            if side == 'BUY':
                if self.btc_per_order:
                    budget = self.btc_per_order
                else:
                    budget = total_asset_balance * self.percent_size

                if self.btc_volume_increase_order_above: #we can increase the order size the X percent is daily volume is symbol is greater than Y
                    symbol_daily_volume = self.get_daily_volume_btc(symbol)
                    if not symbol_daily_volume['error']:
                        symbol_daily_volume = symbol_daily_volume['result']
                        if symbol_daily_volume > self.btc_volume_increase_order_above:
                            logger.info(f"[+] The daily volume of the symbol permits for an increase in order size, increasing the order size by {self.percent_increase_of_order_size} %")
                            if budget * (1 + self.percent_increase_of_order_size) < free_balance:
                                budget = budget * (1 + self.percent_increase_of_order_size)

                base_quantity = budget / price

            else:
                logger.warning("[!] Avoid placing sells without quantity, use buy quantity as quantity.")
                base_quantity = free_balance

        if side == "BUY":
            if base_quantity * price > free_balance:
                return {'error': True, 'message': f' {side} {base_quantity} {symbol} @ {price} You have placed an order to {side} more than the account balance, acc bal {free_balance} '}
        elif side == "SELL":
            if base_quantity > free_balance:
                if free_balance < base_quantity * 0.997:
                    logger.warning("Possible sync issue here")
                    async_to_sync(self.http_update_asset_balances)()

                    asset_model = self._get_asset_models(_asset)
                    if not asset_model:
                        return {'error': True, 'message': f'{side} {quantity} {symbol} @ {price} Zero account balance'}
                    free_balance = float(asset_model.free)

                base_quantity = free_balance

            price = price - price % symbol_info.tick_size + symbol_info.tick_size

        notional = base_quantity * price
        if notional < minNotional:
            margin_of_safety = (1 + self.stop_loss_trigger * 1.005) #just margins of safety
            if side == 'BUY' and free_balance >= minNotional * margin_of_safety:
                base_quantity = (minNotional / price) * margin_of_safety
            elif side == 'SELL' and free_balance * price >= minNotional:
                return {'error': True,
                        'message': f' {side} {base_quantity} {symbol} @ {price} You have placed an order to {side} more than the account balance, acc bal {free_balance} '}
            else:
                if side == 'SELL':
                    lowest_price = minNotional/base_quantity
                    avg_market_price = binance.avgPrice(symbol)
                    symbols_info = self.exchange_info['symbols']
                    xch_sym_info = [inf for inf in symbols_info if inf['symbol'] == symbol]
                    if lowest_price > float(avg_market_price['price']) * self.profit_margin *2:
                        return {"error":True, "message": f"{side} {base_quantity} {symbol} @ {price} Asset notional is too low. Consider salvaging"}
                    if xch_sym_info:
                        xch_sym_info = xch_sym_info[0]
                        xch_filters = xch_sym_info['filters']
                        percent_price_filter = [filter for filter in xch_filters if filter['filterType'] == 'PERCENT_PRICE']
                        if percent_price_filter:
                            percent_price_filter = percent_price_filter[0]
                            if lowest_price > float(avg_market_price['price']) * float(percent_price_filter['multiplierUp']):
                                return {'error': True, 'message': f'{side} {base_quantity} {symbol} @ {price}\n Order will fail percent price filter'}

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
        if stepped_amount_to_trade * price < minNotional:
            return {'error': True,'message': f'{symbol}, trading qty {stepped_amount_to_trade}, price {price} minNotional {minNotional} Fails minimum Notional'}

        return {'error': False, 'size': f"{stepped_amount_to_trade:.6f}", 'price': price}

    async def http_update_asset_balances(self):
        try:
            if hasattr(self, "last_assets_update"):
                last_update = self.last_assets_update
            else:
                last_update = datetime.fromtimestamp(0)
            if not datetime.now() - last_update > timedelta(minutes=1):
                return
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
            self.last_assets_update = datetime.now()

        except binance.BinanceError as e:
            if e.code in [-2014, -2015]:
                logger.error(f"{e}")
                await self.invalidate_keys()
                #self.keep_running = False
                return
        except Exception as e:
            logger.exception(e)

    async def warmup(self):
        '''
        check for balances of the account. match them to recently placed orders. sell everything else to BTC.
        :return:
        '''
        try:
            logger.info("[+] Warming up")

            await self.http_update_asset_balances()
            await self.warm_up_sync_trades_and_orders()  # to ensure trades and orders are at sync with server...

            trade_models = await self.get_trade_models()
            open_sell_trades = [trade for trade in trade_models if trade.buy_status == "FILLED" and not trade.sell_status == "FILLED" and not trade.health == "ERROR"]
            for trade in open_sell_trades:
                if trade.sell_status in ['NEW', 'PARTIALLY_FILLED']:
                    self.price_streamer.subscribe(trade.symbol, self, trade.buy_order_id, trade.buy_price * (1- self.stop_loss_trigger))

                    if float(trade.sell_quantity_executed) * 0.99 < float(trade.buy_quantity_executed):
                        logger.info(f"#{trade.id} - Trade has not placed all bought assets on sell")
                        cancel_order_resp = await self.cancel_order(trade.symbol, trade.sell_order_id)
                        if not cancel_order_resp['error']:

                            order_id = f"SELL_{trade.buy_order_id}_#2"
                            await self.orders_queue.put({
                                'symbol': trade.symbol,
                                'exchange': 'BINANCE',
                                'side': 'SELL',
                                'price': trade.sell_price,
                                'quantity': float(trade.buy_quantity_executed) - float(
                                    trade.sell_quantity_executed),
                                'order_id': order_id,
                                'buy_order_id': trade.buy_order_id
                            })

        except binance.BinanceError as e:
            if e.code in [-2014, -2015]:
                await self.invalidate_keys()
                self.keep_running = False
                return
        except Exception as e:
            logger.exception(e)

    @run_in_executor
    def cancel_order(self, symbol, order_id=None):
        logger.debug(f"[*] Attempting to cancel order oid {order_id}")
        if order_id == -1:
            logger.error(f"Order {symbol} has order_id is -1.")
            return {'error': True, 'message': 'Cannot cancel a rejected order'}
        if order_id == None:
            logger.error(f"Order {symbol} has no order_id.")
            return {'error': True, 'message': 'Specify order id'}
        try:
            resp = self.account.cancel_order(symbol=symbol, order_id=order_id)
            order_id = resp['orderId']
            _order_params = {
                    'order_id': order_id,
                    'exchange': self._exchange,
                    'client_order_id': resp['clientOrderId'],
                    'symbol': resp['symbol'],
                    'price': resp['price'],
                    'quantity': resp['origQty'],
                    'type': resp['type'],
                    'side': resp['side'],
                    #'order_time': datetime.utcfromtimestamp(int(resp["transactTime"])/1000),
                    'cummulative_filled_quantity': resp['executedQty'],
                    'cummulative_quote_asset_transacted': resp["cummulativeQuoteQty"],
                    'status': resp['status']
                }
            #self._update_order_model(order_id=order_id, **_order_params)
            return {"error": False, "result": _order_params}

        except binance.BinanceError as e:
            logger.error(f"[!] Error cancelling the order, {e} code {e.code} symbol {symbol} id {order_id}")
            return {'error': True, 'message': str(e), 'code': e.code }
        except Exception as e:
            logger.error(f"[!] Error cancelling the order, {e} symbol {symbol} id {order_id}")
            return {'error': True, 'message': str(e) }

    @run_in_executor
    def query_order(self, symbol, order_id):
        try:
            resp = self.account.query_order(symbol=symbol, order_id=order_id)
            return {'error': False, 'message': resp}
        except Exception as e:
            logger.error(f"[!] Error cancelling the order, {e} code {e.code} symbol {symbol} id {order_id}")
            return {'error': True, 'message': str(e), 'exception': e}

    async def warm_up_sync_trades_and_orders(self):
        trades = await self.get_trade_models()
        open_buys = [trade for trade in trades if trade.buy_status in ['NEW', 'PARTIALLY_FILLED'] and not trade.completed]
        open_sells = [trade for trade in trades if trade.sell_status in ['NEW', 'PARTIALLY_FILLED'] and not trade.completed]
        #closed_buys_empty_sells = [trade for trade in trades if trade.buy_status in ['FILLED'] and trade.sell_status == None]

        for trade in open_buys:
            logger.debug(f"[+] Syncing #{trade.id}")
            try:
                if trade.buy_order_id.isdigit():
                    _order_resp = await sync_to_async(self.account.query_order)(trade.symbol, order_id=trade.buy_order_id)
                else:
                    _order_resp = await sync_to_async(self.account.query_order)(trade.symbol, orig_client_order_id=trade.buy_order_id)

                _order = _order_resp

                order_model_params = {
                    'exchange': self._exchange,
                    'order_id': _order['orderId'],
                    'client_order_id': _order['clientOrderId'],
                    'price': _order['price'],
                    'quantity': _order['origQty'],
                    'cummulative_filled_quantity': _order['executedQty'],
                    'cummulative_quote_asset_transacted': _order['cummulativeQuoteQty'],
                    'status': _order['status']
                }

                if not float(order_model_params['cummulative_quote_asset_transacted']):
                    del order_model_params['cummulative_quote_asset_transacted']
                    executed_price = 0
                else:
                    try:
                        executed_price = float(order_model_params['cummulative_quote_asset_transacted']) / float(order_model_params['cummulative_filled_quantity'])
                    except Exception as e:
                        executed_price = 0

                await self.update_order_model(**order_model_params)


                trade_model_params = {
                    'exchange': self._exchange,
                    'buy_order_id': trade.buy_order_id,
                    'buy_status': _order['status'],
                    'buy_quantity_executed': _order['executedQty'],
                    'exchange_account_id': self.account_model_id,
                    #'executed_buy_price': executed_price, check down here
                    'side': 'BUY'
                }

                if executed_price:
                    trade_model_params['executed_buy_price'] = executed_price

                if trade_model_params['buy_status'] == "CANCELED":
                    trade_model_params['completed'] = True

                await self.update_trade(**trade_model_params)

            except binance.BinanceError as e:
                if e.code == -2013:
                    logger.error(f"trade #{trade.id} order #{trade.buy_order_id}, {e.message}")
                    await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                            buy_order_id=trade.buy_order_id, health="ERROR",
                                            reason=e.message)
                elif e.code == -1003:
                    logger.error(e.message)
                    asyncio.sleep(60)
            except Exception as e:
                logger.exception(e)

        for trade in open_sells:
            try:
                if trade.buy_order_id.isdigit():
                    _order_resp = await sync_to_async(self.account.query_order)(trade.symbol, order_id=trade.sell_order_id)
                else:
                    _order_resp = await sync_to_async(self.account.query_order)(trade.symbol, orig_client_order_id=trade.sell_order_id)

                _order = _order_resp

                order_model_params = {
                    'exchange': self._exchange,
                    'order_id': _order['orderId'],
                    'client_order_id': _order['clientOrderId'],
                    'price': _order['price'],
                    'quantity': _order['origQty'],
                    'cummulative_filled_quantity': _order['executedQty'],
                    'cummulative_quote_asset_transacted': _order['cummulativeQuoteQty'],
                    'status': _order['status']
                }

                if not float(order_model_params['cummulative_quote_asset_transacted']):
                    del order_model_params['cummulative_quote_asset_transacted']
                    executed_price = 0
                else:
                    try:
                        executed_price = float(order_model_params['cummulative_quote_asset_transacted']) / float(order_model_params['cummulative_filled_quantity'])
                    except Exception as e:
                        executed_price = 0

                await self.update_order_model(**order_model_params)

                trade_model_params = {
                    'exchange': self._exchange,
                    'buy_order_id': trade.buy_order_id,
                    'sell_status': _order['status'],
                    'sell_quantity_executed': _order['executedQty'],
                    'exchange_account_id': self.account_model_id,
                    #'executed_sell_price': executed_price check down here
                    'side': 'SELL'
                }

                if executed_price:
                    trade_model_params['executed_sell_price'] = executed_price

                await self.update_trade(**trade_model_params)
            except binance.BinanceError as e:
                logger.error(e.message)
                if e.code == -2013:
                    await self.update_trade(side='SELL', exchange_account_id=self.account_model_id,
                                            buy_order_id=trade.buy_order_id, health="ERROR",
                                            reason=e.message)
                elif e.code == -1003:
                    logger.error(e.message)
                    asyncio.sleep(60)


    async def process_user_socket_message(self, msg):
        # throw it in the database
        try:
            payload = msg
            if payload['e'] == "outboundAccountInfo":
                pass
                balances_all = payload['B']
                balances = [{'asset': bal['a'], 'free': bal['f'], 'locked': bal['l']} for bal in balances_all if
                            float(bal['f']) or float(bal['l'])]

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
                    'order_time': datetime.utcfromtimestamp(int(trade_params['time'])/1000),
                    'cummulative_filled_quantity': trade_params['cummulative_filled_quantity'],
                    'cummulative_quote_asset_transacted': trade_params['cummulative_quote_asset_transacted'],
                    'status': trade_params['status']
                }

                if trade_params['side'] == 'BUY':
                    trade_model_params = {
                        'exchange': self._exchange,
                        'symbol': trade_params['symbol'],
                        'buy_order_id': trade_params['orderId'],
                        'buy_status': trade_params['status'],
                        'buy_quantity_executed': trade_params['cummulative_filled_quantity'],
                        'exchange_account_id' : self.account_model_id,
                        'side': 'BUY',
                    }
                    if trade_params['cummulative_quote_asset_transacted'] and trade_params['cummulative_filled_quantity']:
                        trade_model_params['executed_buy_price'] =  float(trade_params['cummulative_quote_asset_transacted']) / float(trade_params['cummulative_filled_quantity'])
                    else:
                        print("*"*100)
                        print(f"Cannot find executed _buy_price, cumm_qoute_trans {trade_params['cummulative_quote_asset_transacted']}, cumm_filled_qty {trade_params['cummulative_filled_quantity']}")

                elif trade_params['side'] == "SELL":
                    trade_model_params = {
                        'exchange': self._exchange,
                        'symbol': trade_params['symbol'],
                        'sell_order_id': trade_params['orderId'],
                        'sell_status': trade_params['status'],
                        'sell_quantity_executed': trade_params['cummulative_filled_quantity'],
                        'side': 'SELL',
                    }
                    if trade_params['cummulative_quote_asset_transacted'] and trade_params['cummulative_filled_quantity']:
                        trade_model_params['executed_sell_price'] = float(trade_params['cummulative_quote_asset_transacted']) / float(trade_params['cummulative_filled_quantity'])
                    else:
                        print("*"*100)
                        print(f"Cannot find executed buy price, cumm_qt_trans {trade_params['cummulative_quote_asset_transacted']}, cumm_filled_qty {trade_params['cummulative_filled_quantity']}")

                else:
                    await self.send_admin_notification(f"Cant tell if it is buy or sell, {str(trade_params)}")
                    return

                message = ""

                if trade_params['side'] == 'BUY': #lets us check if we created this trade, if not, bail out.
                    if trade_params['status'] == "NEW" and "BUY_" in trade_params['client_order_id']:
                        if not order_model_params['status'] == "REJECTED":
                            await self.update_order_model(**order_model_params)
                        await self.update_trade(**trade_model_params)
                        await asyncio.sleep(3)
                    trade_model = await self.get_trade_model(buy_order_id=trade_model_params['buy_order_id'])
                elif trade_params['side'] == 'SELL': #websocket message arrives before http create_order is complete.. So lets update the trade here.
                    trade_model = await self.get_trade_model(sell_order_id=trade_model_params['sell_order_id'])
                    if not trade_model:
                        sell_cloid_split = order_model_params['client_order_id'].split("_", 1)
                        if len(sell_cloid_split) > 1 and sell_cloid_split[0] in ["SELL","SELL-LOSS"]:
                            buy_order_id = sell_cloid_split[1]
                            trade_model = await self.get_trade_model(buy_order_id=buy_order_id)
                            if trade_model:
                                trade_model_params['buy_order_id'] = buy_order_id
                else:
                    logger.error("We should not get here")
                    return

                if not trade_model and "BUY_" not in order_model_params['client_order_id'] and "SELL" not in order_model_params['client_order_id']:
                    message = f"{emoji.emojize(':x:', use_aliases=True)}Order: cloid {order_model_params['client_order_id']} {order_model_params['status']}: {order_model_params['side']}ING {float(order_model_params['quantity']):.8f} {order_model_params['symbol']}@ {float(order_model_params['price']):.8f}"
                    message += "\nThis order is not recognized by the bot. if this is a mistake, report to admin"
                    message += f"\nOrder id {trade_params['orderId']}"
                    logger.info(f"[!] This trade {message} is not from me, id {trade_params['orderId']}, client order id {trade_params['client_order_id']}")
                    await self.send_admin_notification(message)
                    return

                await self.update_order_model(**order_model_params)
                await self.update_trade(**trade_model_params)
                await asyncio.sleep(3)

                if trade_params['side'] == 'BUY': #dont delete, not a repetition, I was just checking if trade exists before updating.
                    trade_model = await self.get_trade_model(buy_order_id=trade_model_params['buy_order_id'])
                else:
                    trade_model = await self.get_trade_model(sell_order_id=trade_model_params['sell_order_id'])

                if trade_params['type'] == "TRADE":
                    if trade_params['side'] == "BUY" and trade_params['status'] in ['FILLED']: #we have bought something, lets put up a sell
                        avg_price = float(trade_params['cummulative_quote_asset_transacted']) / float(trade_params['cummulative_filled_quantity'])
                        signal = trade_model.get_signal()
                        if signal:
                            signal_assoc = await sync_to_async(self.get_account_signal_assoc)(signal_id=signal.id)
                            if signal_assoc and signal_assoc.profit_target:
                                sell_price = avg_price * (1 + signal_assoc.profit_target)
                            else:
                                sell_price = avg_price * (1 + self.profit_margin)
                        else:
                            sell_price = avg_price * (1 + self.profit_margin)

                        logger.info(f"[+]{self.username} Trade event, we've bought {trade_params['cummulative_filled_quantity']} at {avg_price}")
                        logger.info(f"[+] Placing a sell for {trade_params['cummulative_filled_quantity']} at {sell_price}")
                        sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'], price=sell_price, side='SELL')
                        if sell_size_resp['error']:
                            await asyncio.sleep(30)
                            sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'],
                                                                                      price=sell_price, side='SELL')
                            if sell_size_resp['error']:
                                await self.http_update_asset_balances()
                                sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'],
                                                                                          price=sell_price, side='SELL')
                                if sell_size_resp['error']:
                                    logger.error(f"[!] {sell_size_resp['message']}")
                                    return {'error': True, 'message': sell_size_resp['message']}

                        order_id = f"SELL_{trade_params['orderId']}"
                        await self.orders_queue.put({
                            'symbol': trade_params['symbol'],
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_size_resp['price'],
                            'quantity': float(trade_params['cummulative_filled_quantity']),
                            'order_id': order_id,
                            'buy_order_id': trade_params['orderId']
                        })

                        self.price_streamer.subscribe(order_model_params['symbol'], self, trade_params['orderId'], avg_price * (1 - self.stop_loss_trigger))
                        message = f"{emoji.emojize(':dollar:', use_aliases=True)} {order_model_params['status']}: {order_model_params['side']}ING {float(order_model_params['quantity']):.8f} {order_model_params['symbol']}@ {float(order_model_params['price']):.8f}"
                        message += f"\n Amount bought {float(trade_params['cummulative_filled_quantity']):.8f} at {avg_price} \n"
                        message += f"Target sell price {sell_price:.8f}"

                    if trade_params['side'] == "SELL" and trade_params['status'] == 'FILLED':
                        if trade_model:
                            message = f"{emoji.emojize(':id:', use_aliases=True)} #{trade_model.id}\n"
                            message += f"Symbol {trade_model.symbol}\n"

                            #AUDIT TIME !!
                            #did we all everything?
                            if not trade_model.sell_quantity_executed > trade_model.buy_quantity_executed * 0.99: #fee allowance
                                message += f"{emoji.emojize(':heavy_exclamation_mark:')}, We did not sell everything, Bought {trade_model.buy_quantity_executed}, Sold {trade_model.sell_quantity_executed}"
                                message += f"Attempting to sell the remaining {float(trade_model.buy_quantity_executed) - float(trade_model.sell_quantity_executed)}"

                                order_id = f"SELL_{trade_model.buy_order_id}_#2"
                                await self.orders_queue.put({
                                    'symbol': trade_params['symbol'],
                                    'exchange': 'BINANCE',
                                    'side': 'SELL',
                                    'price': trade_model.sell_price ,
                                    'quantity': float(trade_model.buy_quantity_executed) - float(trade_model.sell_quantity_executed),
                                    'order_id': order_id,
                                    'buy_order_id': trade_model.buy_order_id
                                })

                            buy_price = float(trade_model.executed_buy_price) if trade_model.executed_buy_price else trade_model.buy_price
                            sell_price = float(trade_model.executed_sell_price) if trade_model.executed_sell_price else trade_model.sell_price
                            profit = float(sell_price) * float(trade_model.sell_quantity_executed) - float(buy_price) * float(trade_model.buy_quantity_executed)

                            if profit > 0:
                                message += f"{emoji.emojize(':white_check_mark:', use_aliases=True)} {emoji.emojize(':dollar:', use_aliases=True)} Trade Closed at Profit"
                            else:
                                message += f"{emoji.emojize(':x:', use_aliases=True)} Trade Closed at Loss"

                            message += f"\n Bought {float(trade_model.buy_quantity_executed):.8f} {trade_model.symbol}@ {buy_price:.8f}"
                            message += f"\n Sold {float(trade_model.sell_quantity_executed):.8f} {trade_model.symbol}@ {sell_price:.8f}"
                            message += f"\n Profit {profit}, {(profit/(buy_price * float(trade_model.buy_quantity_executed))) * 100}%\n"

                            self.price_streamer.unsubscribe(trade_model.symbol, trade_model.buy_order_id)

                if trade_params['type'] == "CANCELED": #delete cancelled sells too
                    order = await self.get_order_model(order_id=trade_params['orderId'])
                    if trade_params['side'] == "SELL":
                        logger.warning(f"[!]{self.username} You just cancelled a a SELL!")

                    else: #deleted buy orders, cleanup.
                        if order:
                            #await self.delete_order_model(order.client_order_id)
                            pass
                        trade = await self.get_trade_model(buy_order_id=order.order_id)
                        if trade:
                            #await self.update_trade(buy_order_id=trade.buy_order_id)
                            pass
                if message:
                    await self.send_notification(message)

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

    @run_in_executor
    def get_asset_balances(self):
        try:
            balances_res = self.account.account_info()
            balances = balances_res['balances']
            asset_balances = [bal for bal in balances if float(bal['free']) > 0]
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
            sym_info = self.get_symbol_info(symbol)
            if not sym_info:
                return {'error': True, 'message': "Symbol not found"}
            if not sym_info.lastPrice or sym_info.lastPrice_timestamp and datetime.utcnow() - sym_info.lastPrice_timestamp > timedelta(minutes=1):
                self.update_symbol_model_prices()
                sym_info = self.get_symbol_info(symbol)
            return {'error': False, 'result': sym_info.lastPrice}
        except Exception as e:
            logger.exception(e)
            return {'error': True, 'message': str(e)}

    def update_symbol_model_prices(self):
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

    def get_daily_volume_btc(self, symbol):

        try:
            sym_info = self.get_symbol_info(symbol)
            if not sym_info:
                return {'error': True, 'message': "Symbol not found"}
            if not sym_info.dailyVolume or sym_info.dailyVolume_timestamp and datetime.utcnow() - sym_info.dailyVolume_timestamp > timedelta(minutes=5):
                self.update_symbol_model_volume(symbol)
                sym_info = self.get_symbol_info(symbol)
            return {'error': False, 'result': sym_info.dailyVolume}
        except Exception as e:
            logger.exception(e)
            return {'error': True, 'message': str(e)}

    def update_symbol_model_volume(self, symbol):
        symbol_24hr_ticker = binance.ticker_24hr(symbol)
        if not symbol_24hr_ticker:
            return
        with create_session() as session:
            symbol_model = session.query(BinanceSymbol).filter_by(name=symbol).first()
        if symbol_model:
            dailyVolume = float(symbol_24hr_ticker['volume']) * get_btc_price(symbol_model.base_asset)

            with create_session() as session:
                symbol_model = session.query(BinanceSymbol).filter_by(name=symbol).first()
                symbol_model.dailyVolume = dailyVolume
                symbol_model.dailyVolume_timestamp = datetime.utcnow()
                session.add(symbol_model)
                session.commit()

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
            trades_models = await self.get_trade_models()
            open_trades_models = [trade for trade in trades_models if trade.sell_status != "FILLED" and trade.health != "ERROR"]

            for trade_model in open_trades_models:
                symbol_info = self.get_symbol_info(trade_model.symbol)
                if trade_model.buy_status == "NEW" and trade_model.buy_time and datetime.utcnow() - trade_model.buy_time > self.parse_time(self.order_timeout):
                    resp = await self.cancel_order(symbol=trade_model.symbol, order_id=trade_model.buy_order_id)
                    if resp['error'] and 'code' in resp and resp['code'] == -2013:
                        logger.error(f"[!] {resp['message']}")
                        await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                buy_order_id=trade_model.buy_order_id, health="ERROR",
                                                sell_status='ERRORED',
                                                reason="Buy order not found in exchange")

                if trade_model.buy_status == "FILLED" and trade_model.sell_status in ["NEW", "PARTIALLY_FILLED"]:
                    market_price_resp = await self.get_avg_price(trade_model.symbol)
                    if market_price_resp['error']:
                        logger.error(market_price_resp['message'])
                        continue
                    market_price = float(market_price_resp['result'])

                    if market_price < float(trade_model.buy_price) * (1 - self.stop_loss_trigger):  # we've gone below our stop loss
                        if trade_model.sell_price < market_price * 1.005:
                            continue  # no need to stop stop-losses

                        logger.warning(
                            f"[!]{self.username} Market price for {trade_model.symbol} has gone below stop loss trigger, placing stop loss sell")

                        if trade_model.buy_quantity_executed * market_price < symbol_info.min_notional:
                            logger.info(f"[!]{self.username} The notional size for {trade_model.symbol} of the order is below minimum")
                            await self.update_trade(side='BUY', exchange_account_id=self.account_model_id, buy_order_id=trade_model.buy_order_id, health="ERRORED", reason="Notional value below minimum")
                            continue

                        sell_price = market_price * 0.995

                        resp = await self.cancel_order(trade_model.symbol, order_id=trade_model.sell_order_id)
                        if resp['error']:
                            logger.error(resp['message'])
                            if 'Unknown order sent' in resp['message']:
                                #await self.delete_order_model(trade_model.buy_order_id)
                                admin_message = f"{emoji.emojize(':x:', use_aliases=True)} Error cancelling sell Order\n"
                                admin_message += f"#{emoji.emojize(':id:', use_aliases=True)} {trade_model.id}\n"
                                admin_message += f"Order id {trade_model.sell_order_id}\n"
                                admin_message += f"Symbol {trade_model.symbol}, Buy {trade_model.buy_price}, Current Market Price {market_price}"
                                self.send_admin_notification(admin_message)

                        order_id = f"SELL-LOSS_{str(trade_model.buy_order_id)[:20]}"

                        await self.orders_queue.put({
                            'symbol': trade_model.symbol,
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_price,
                            'quantity': trade_model.buy_quantity_executed,
                            'order_id': order_id,
                            'buy_order_id': trade_model.buy_order_id
                        })

                    #audit, did we sell everything we bought?
                    elif float(trade_model.sell_quantity_executed) * 0.99 < float(trade_model.buy_quantity_executed):
                        logger.info(f"#{trade_model.id}, selling less than was bought, replacing order")
                        resp = await self.cancel_order(trade_model.symbol, order_id=trade_model.sell_order_id)

                        if not resp['error']:
                            order_id = f"SELL_{str(trade_model.buy_order_id)}_#2"
                            await self.orders_queue.put({
                                'symbol': trade_model.symbol,
                                'exchange': 'BINANCE',
                                'side': 'SELL',
                                'price': trade_model.sell_price,
                                'quantity': trade_model.buy_quantity_executed,
                                'order_id': order_id,
                                'buy_order_id': trade_model.buy_order_id
                            })

                if trade_model.buy_status == "FILLED" and not trade_model.sell_status in ['NEW', 'FILLED', 'PARTIALLY_FILLED','CANCELLED','ERRORED']:
                    if not trade_model.buy_price:
                        logger.error(f"[!] Order has no buy price, check if it was a market order")
                        continue

                    asset = await self.get_asset_models(asset=trade_model.base_asset)
                    if not asset or float(asset.free) < float(symbol_info.min_qty):
                        await self.http_update_asset_balances()
                        await asyncio.sleep(10)
                        asset = await self.get_asset_models(asset=trade_model.base_asset)
                        if not asset or float(asset.free) < float(symbol_info.min_qty):
                            await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                buy_order_id=trade_model.buy_order_id, health="ERROR",
                                                sell_status='ERRORED',
                                                reason="The base asset is missing or depleted")
                            continue

                    signal = trade_model.get_signal()
                    if signal:
                        signal_assoc = await sync_to_async(self.get_account_signal_assoc)(signal_id=signal.id)
                        if signal_assoc and signal_assoc.profit_target:
                            sell_price = trade_model.buy_price * (1 + signal_assoc.profit_target)
                        else:
                            sell_price = trade_model.buy_price * (1 + self.profit_margin)
                    else:
                        sell_price = trade_model.buy_price * (1 + self.profit_margin)

                    order_id = f"SELL_{str(trade_model.buy_order_id)[:20]}"

                    if not float(asset.free) + float(asset.locked) >= float(trade_model.buy_quantity_executed):
                        if not float(asset.free) * sell_price > symbol_info.min_notional:
                            await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                    buy_order_id=trade_model.buy_order_id, health="ERROR",
                                                    sell_status='ERRORED',
                                                    reason="The base asset is less than the amount bought")
                            continue
                    await self.orders_queue.put({
                        'symbol': trade_model.symbol,
                        'exchange': 'BINANCE',
                        'side': 'SELL',
                        'price': sell_price,
                        'quantity': trade_model.buy_quantity_executed,
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
            last_update = datetime.utcfromtimestamp(os.path.getmtime('last_binance_symbols_update'))
        else:
            last_update = datetime.utcfromtimestamp(0)
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

    def sync_get_open_orders(self, symbol):
        return self.account.open_orders(symbol)

    async def create_stop_loss_order(self, params):
        logger.info(f"{self.username} Stop loss attempted {params}")
        buy_order_id = params['buy_order_id']
        self.price_streamer.unsubscribe(params['symbol'], buy_order_id)
        trade_model = await self.get_trade_model(buy_order_id=buy_order_id)
        if not trade_model:
            logger.error(f"[!]{self.username} The trade model {buy_order_id} cannot be found")
            return
        if trade_model.health == "ERROR":
            logger.error(f"{self.username} Stop loss placed on a trade in error, #{trade_model}")
            return
        if trade_model.sell_status in ["NEW","PARTIALLY_FILLED"]:
            resp = await self.cancel_order(trade_model.symbol, order_id=trade_model.sell_order_id)

            if resp['error']:
                logger.error("!"*100)
                logger.error("Here is where the error comes in")
                logger.error(f"{self.username} {resp['message']}")
                if 'Unknown order sent' in resp['message']:
                    await self.send_notification(
                        f"{emoji.emojize(':x:', use_aliases=True)} Trade id {trade_model.id} Order Cloid {trade_model.sell_order_id} SELL {trade_model.sell_quantity} {trade_model.symbol} @ {trade_model.sell_price} cannot be cancelled. Order is unknown to the exchange")
                    #await self.delete_order_model(orderId=trade_model.sell_order_id)
                    await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                            buy_order_id=trade_model.buy_order_id, health="ERROR",
                                            reason="Sell order is not found in exchange, could have been cancelled externally")
            else:
                if trade_model.health == "ERROR":
                    logger.error(f"{self.username} Stop loss placed on a trade in error, #{trade_model}")
                    return
                sell_price = float(params['price']) * 0.995
                order_id = f"SELL-LOSS_{trade_model.buy_order_id[:20]}"
                logger.info(f"Adding stop loss {trade_model} into orders queue")
                await self.orders_queue.put({
                    'symbol': trade_model.symbol,
                    'exchange': 'BINANCE',
                    'side': 'SELL',
                    'price': sell_price,
                    'quantity': trade_model.buy_quantity_executed,
                    'order_id': order_id,
                    'buy_order_id': trade_model.buy_order_id
                })

    def get_binance_symbol_models(self):
        with create_session() as session:
            symbols = session.query(BinanceSymbol).all()
        return symbols

    async def scrap_assets(self):
        logger.info("[+] Scrapper initiated, tick tock tick tock")
        collectible_assets = ['BTC','ETH','BNB']
        asset_models = await self.get_asset_models()
        symbol_models = await sync_to_async(self.get_binance_symbol_models)()
        book_tickers = await sync_to_async(binance.ticker_order_books)()
        for asset in asset_models:
            name = asset.name
            if name in collectible_assets:
                continue
            asset_symbol_models = [symbol for symbol in symbol_models if symbol.base_asset == name]
            btc_symbol_model_l = [symbol for symbol in asset_symbol_models if symbol.quote_asset == "BTC"]
            if btc_symbol_model_l:
                btc_symbol_model = btc_symbol_model_l[0]
                ticker = book_tickers[btc_symbol_model.name]
                if float(asset.free) < float(btc_symbol_model.min_qty):
                    logger.info(f"[+] {asset.free} {asset.name}, dust.")
                    continue
                asset_notional = float(asset.free) * ticker['ask_price']
                if asset_notional > btc_symbol_model.min_notional:
                    logger.info(f"[+] {asset.name} - Asset can be sold without scrapping")
                    sell_order_params = {
                        'symbol': btc_symbol_model.name,
                        'exchange': 'BINANCE',
                        'side': 'SELL',
                        'type': 'MARKET',
                        'price': ticker['bid_price'],
                        'quantity': asset.free,
                        'order_id': f"SCRAPPER-{str(uuid.uuid4())[:23]}",
                        'buy_order_id': "SCRAPPER-NO-BUY"
                    }
                    resp = await self.create_order(**sell_order_params)
                    if not resp['error']:
                        logger.info(f"[+] Scrapping {asset.name} successful")
                    else:
                        logger.error(f"[!] Error Occured, {resp['message']}")

                if asset_notional < btc_symbol_model.min_notional * 0.05:
                    logger.info(f"[+] {asset.free} {asset.name}, too tiny a dust to collect")
                    continue
                btc_to_use = btc_symbol_model.min_notional * 1.01
                asset_after_buy = btc_to_use * ticker['ask_price'] + float(asset.free)
                btc_after_sell = asset_after_buy * ticker['bid_price']
                sell_notional = btc_after_sell - btc_to_use

                if sell_notional < btc_symbol_model.min_notional * 0.02:
                    logger.info(f"[+] {asset.free} {asset.name}, insignificant gain. {ticker['ask_price'] - ticker['bid_price']} too wide margin")
                    continue
                logger.info(f'[+] Salvaging {asset.name}')
                #issue buy for min_notional * 1.01
                #issue sell for max.
                buy_order_params = {
                    'symbol': btc_symbol_model.name,
                    'exchange': 'BINANCE',
                    'side': 'BUY',
                    'type': 'MARKET',
                    'price': ticker['ask_price'],
                    'quantity': btc_symbol_model.min_notional * 1.01,
                    'order_id': f"SCRAPPER-{str(uuid.uuid4())[:23]}"
                }
                logger.info(f"[+] Buying {buy_order_params}")
                resp = await self.create_order(**buy_order_params)
                if resp['error']:
                    logger.error(resp['message'])
                    continue
                buy_results = resp['result']
                print(buy_results)
                if buy_results['buy_status'] == "FILLED":
                    sell_quantity = float(buy_results['buy_quantity']) + float(asset.free)
                    sell_order_params = {
                        'symbol': btc_symbol_model.name,
                        'exchange': 'BINANCE',
                        'side': 'SELL',
                        'type': 'MARKET',
                        'price': ticker['bid_price'],
                        'quantity': sell_quantity,
                        'order_id': f"SCRAPPER-{str(uuid.uuid4())[:23]}",
                        'buy_order_id': buy_results['buy_order_id']
                    }
                    resp = await self.create_order(**sell_order_params)
                    if not resp['error']:
                        logger.info(f"[+] Scrapping {asset.name} successful")
                    else:
                        logger.error(f"[!] Error Occured, {resp['message']}")
                else:
                    self.scrapper_orders[buy_results['buy_order_id']] = buy_results

        max_loops = 100
        loop_count = 0
        while self.scrapper_orders and self.keep_running and loop_count < max_loops:
            logger.debug("[+] Scrapper order loop running")
            loop_count += 1
            for order_key in self.scrapper_orders:
                order = self.scrapper_orders[order_key]
                if order['side'] == "BUY":
                    if order['buy_status'] == "FILLED":
                        ticker = book_tickers[order['symbol']]
                        sell_order_params = {
                            'symbol': order['symbol'],
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'type': 'MARKET',
                            'price': ticker['bid_price'],
                            'order_id': f"SCRAPPER-{str(uuid.uuid4())[:23]}",
                            'buy_order_id': order['buy_order_id']
                        }
                        resp = await self.create_order(**sell_order_params)
                        if not resp['error']:
                            logger.info(f"[+] Scrapping {asset.name} successful")
                        else:
                            logger.error(f"[!] Error Occured, {resp['message']}")
                        del self.scrapper_orders[order_key]
                    if order['buy_status'] == "NEW" and datetime.utcnow() - order['order_time'] > timedelta(minutes=2):
                        resp = await self.cancel_order(order['symbol'], order_id=order['buy_order_id'])

    async def update_trade_status(self):
        '''
        Trades misbehave, from reporting error when they should not, to reporting filled when they should not
        :return:
        '''
        trades = await self.get_trade_models()
        for trade in trades:
            if not trade.sell_order_id:
                print(f"Trade #{trade.id} has not sold")
                continue
            #check trade sell status matches sell order status, or else update
            sell_order = await self.get_order_model(order_id=trade.sell_order_id)
            if not sell_order:
                print(f"Sell order {trade.sell_order_id} not found")
                continue
            if not trade.sell_order_id == None:
                if trade.sell_status == sell_order.status:
                    print(f"Trade {trade.id}, Thumbs up emoji")
                else:
                    print(f"Trade #{trade.id} error, sell status {sell_order.status}, model status {trade.sell_status}")
                    trade_model_params = {
                        'exchange': self._exchange,
                        'symbol': sell_order.symbol,
                        'sell_order_id': sell_order.order_id,
                        'sell_status': sell_order.status,
                        'sell_quantity_executed': sell_order.cummulative_filled_quantity,
                        'side': 'SELL',
                        'buy_order_id': trade.buy_order_id
                    }
                    await self.update_trade(**trade_model_params)

            else:
                logger.info(f"Trade #{trade.id} had not sold, buy status {trade.buy_status}")