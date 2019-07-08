from trader.trader import Trader
import logging, json, uuid, asyncio, re,os, emoji
from binance import binance
from utils import run_in_executor
from datetime import datetime, timedelta
from models import create_session, BinanceSymbol

logger = logging.getLogger('clone.binance_trader')
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

            self.exchange_info = binance.exchange_info()

            self.price_streamer = kwargs['price_streamer'] #class that streams in prices.

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

        if side == "BUY": #dont have more that two open orders
            orders = self.sync_get_open_orders(symbol)
            if orders:
                logger.debug(f"[+] Symbol {symbol} has open orders.")
                if len(orders) > 2:
                    return {'error': True, 'message': f'There are already two open orders for the symbol, cannot create a new one'}

        print(f"{'+'*70}")
        print(f"New order, {symbol} {side} {order_type} {quantity} {price} {order_id}")
        resp = self.account.new_order(symbol= symbol, side=side, type=order_type,  quantity=quantity, price=f"{price:.8f}", new_client_order_id=order_id)

        symbol_info = self.get_symbol_info(symbol)

        if side == "BUY":
            params = {
                'exchange': self._exchange,
                'symbol': resp['symbol'],
                'buy_order_id': resp['clientOrderId'],
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
                'sell_order_id': resp['clientOrderId'],
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
            return {'error': True, 'message': f'{side} {quantity} {symbol} @ {price}All your assets are locked in trades'}

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
                logger.warning("[!] Avoid placing sells without quantity, use buy quantity as quantity.")
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

            trade_models = await self.get_trade_models()
            open_sell_trades = [trade for trade in trade_models if trade.buy_status == "FILLED" and not trade.sell_status == "FILLED" and not trade.health == "ERROR"]
            for trade in open_sell_trades:
                self.price_streamer.subscribe(trade.symbol, self)

        except binance.BinanceError as e:
            if e.code in [-2014, -2015]:
                await self.invalidate_keys()
                self.keep_running = False
                return
        except Exception as e:
            logger.exception(e)

    @run_in_executor
    def cancel_order(self, symbol, order_id=None, client_order_id=None):
        logger.debug(f"[*] Attempting to cancel order cloid  {client_order_id} oid {order_id}")
        try:
            resp = self.account.cancel_order(symbol=symbol, order_id=order_id, orig_client_order_id=client_order_id)
            client_order_id = resp['clientOrderId']
            _order_params = {
                    'exchange': self._exchange,
                    'client_order_id': client_order_id,
                    'symbol': resp['symbol'],
                    'price': resp['price'],
                    'quantity': resp['origQty'],
                    'type': resp['type'],
                    'side': resp['side'],
                    'order_time': datetime.utcfromtimestamp(int(resp["transactTime"])/1000),
                    'cummulative_filled_quantity': resp['executedQty'],
                    'cummulative_quote_asset_transacted': resp["cummulativeQuoteQty"],
                    'status': resp['status']
                }
            self._update_order_model(client_order_id=client_order_id, **_order_params)
        except binance.BinanceError as e:
            logger.error(f"[!] Error cancelling the order, {e} code {e.code} symbol {symbol} id {order_id}")
            return {'error' : True, 'message': str(e)}
        except Exception as e:
            logger.error(f"[!] Error cancelling the order, {e}")
            return {'error': True, 'message': str(e)}
        return {'error': False}

    @run_in_executor
    def query_order(self, symbol, order_id):
        resp = self.account.query_order(symbol=symbol, order_id=order_id)
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
                    'order_time': datetime.utcfromtimestamp(int(trade_params['time'])/1000),
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

                message = ""

                if trade_params['side'] == 'BUY': #lets us check if we created this trade, if not, bail out.
                    if trade_params['status'] == "NEW" and "BUY_" in trade_params['client_order_id']:
                        if not order_model_params['status'] == "REJECTED":
                            await self.update_order_model(**order_model_params)
                        await self.update_trade(**trade_model_params)
                        await asyncio.sleep(3)
                    trade_model = await self.get_trade_model(buy_order_id=trade_model_params['buy_order_id'])
                else:
                    trade_model = await self.get_trade_model(sell_order_id=trade_model_params['sell_order_id'])

                if not trade_model:
                    message = f"{emoji.emojize(':x:', use_aliases=True)}Order: cloid{order_model_params['client_order_id']}{order_model_params['status']}: {order_model_params['side']}ING {float(order_model_params['quantity']):.8f} {order_model_params['symbol']}@ {float(order_model_params['price']):.8f}"
                    message += "This order is not recognized by the bot. if this is a mistake, report to admin"
                    logger.info(f"[!] This trade {message} is not from me, id {trade_params['orderId']}, client order id {trade_params['client_order_id']}")
                    self.send_notification(message)
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
                        sell_price = avg_price * (1 + self.profit_margin)
                        logger.info(f"[+] Trade event, we've bought {trade_params['cummulative_filled_quantity']} at {avg_price}")
                        logger.info(f"[+] Placing a sell for {trade_params['cummulative_filled_quantity']} at {sell_price}")
                        sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'], price=sell_price, side='SELL')
                        if sell_size_resp['error']:
                            await asyncio.sleep(30)
                            sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'],
                                                                                      price=sell_price, side='SELL')
                            if sell_size_resp['error']:
                                await self.warmup()
                                sell_size_resp = await self.a_quantity_and_price_roundoff(symbol=trade_params['symbol'],
                                                                                          price=sell_price, side='SELL')
                                if sell_size_resp['error']:
                                    logger.error(f"[!] {sell_size_resp['message']}")
                                    return {'error': True, 'message': sell_size_resp['message']}
                        order_id = f"SELL_{trade_params['client_order_id'].split('_')[1]}" if len(trade_params['client_order_id'].split('_')) > 1 else f"SELL_{trade_params['client_order_id'][:30]}"
                        await self.orders_queue.put({
                            'symbol': trade_params['symbol'],
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_size_resp['price'],
                            'quantity': float(trade_params['cummulative_filled_quantity']),
                            'order_id': order_id,
                            'buy_order_id': trade_params['client_order_id']
                        })

                        message = f"{emoji.emojize(':dollar:', use_aliases=True)} {order_model_params['status']}: {order_model_params['side']}ING {float(order_model_params['quantity']):.8f} {order_model_params['symbol']}@ {float(order_model_params['price']):.8f}"
                        message += f"\n Amount bought {float(trade_params['cummulative_filled_quantity']):.8f} at {avg_price} \n"
                        message += f"Target sell price {sell_price:.8f}"

                    if trade_params['side'] == "SELL" and trade_params['status'] == 'FILLED':
                        if trade_model:
                            if float(trade_model.sell_price) * float(trade_model.sell_quantity_executed) - float(trade_model.buy_price) * float(trade_model.buy_quantity_executed) > 0:
                                message = f"{emoji.emojize(':white_check_mark:', use_aliases=True)} {emoji.emojize(':dollar:', use_aliases=True)} Trade Closed at Profit"
                                message += f"\n Bought {float(trade_model.buy_quantity_executed):.8f} @ {float(trade_model.buy_price):.8f}"
                                message += f"\n Sold {float(trade_model.sell_quantity_executed):.8f} @ {float(trade_model.sell_price):.8f}"
                                message += f"\n Profit {float(trade_model.sell_price) * float(trade_model.sell_quantity_executed) - float(trade_model.buy_price) * float(trade_model.buy_quantity_executed):.8f}\n"
                            else:
                                message = f"{emoji.emojize(':x:', use_aliases=True)} Trade Closed at Loss"
                                message += f"\n Bought {float(trade_model.buy_quantity_executed):.8f} @ {float(trade_model.buy_price):.8f}"
                                message += f"\n Sold {float(trade_model.sell_quantity_executed):.8f} @ {float(trade_model.sell_price):.8f}"
                                message += f"\n Profit {float(trade_model.sell_price) * float(trade_model.sell_quantity_executed) - float(trade_model.buy_price) * float(trade_model.buy_quantity_executed):.8f}\n"

                            self.price_streamer.unsubscribe(trade_model.symbol, self)

                if trade_params['type'] == "CANCELED": #delete cancelled sells too
                    order = self.get_order_model(client_order_id=trade_params['client_order_id'])
                    if trade_params['side'] == "SELL":
                        logger.warning("[!] You just cancelled a a SELL!")

                    else: #deleted buy orders, cleanup.
                        if order:
                            #await self.delete_order_model(order.client_order_id)
                            pass
                        trade = self.get_trade_model(buy_order_id=order.client_order_id)
                        if trade:
                            #await self.delete_trade_model(trade.buy_order_id)
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

    async def process_symbol_stream(self, msg):
        params =  msg
        trade_models = await self.get_trade_models()
        sym_open_trades = [trade for trade in trade_models if trade.symbol == params['symbol'] and trade.buy_status == "FILLED" and not trade.sell_status == "FILLED"]
        symbol_info = self.get_symbol_info(params['symbol'])
        if not sym_open_trades:
            self.price_streamer.unsubscribe(params['symbol'], self)
        for trade in sym_open_trades:

            if not trade.buy_price:
                # check if buy price is greater than zero, not necessary but external bots sometimes sell at market price.
                if not "BUY_" in trade.buy_order_id:
                    logger.info("[!] Externally initiated order, deleting")
                    self.price_streamer.unsubscribe(params['symbol'], self)
                    continue
                else:
                    logger.error(f"[!!] order {trade.buy_order_id} Price is missing, check bot...")

            if trade.buy_price and params['price'] < trade.buy_price * (1 - self.stop_loss_trigger):

                if  params['price'] * float(trade.buy_quantity) < float(symbol_info.min_notional):
                    #logger.info(f"[!] {params['symbol']} Order notional of {trade.buy_quantity * params['price']} below min notional, current price {params['price']}")
                    self.price_streamer.unsubscribe(params['symbol'], self)
                    await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                      buy_order_id=trade.buy_order_id, health="ERROR",
                                      reason="Notional value below minimum")
                    continue

                resp = await self.cancel_order(trade.symbol, client_order_id=trade.sell_order_id)
                if resp['error']:
                    logger.error(resp['message'])
                    if 'Unknown order sent' in resp['message']:
                        self.send_notification(f"{emoji.emojize(':x:', use_aliases=True)} Trade id {trade.id} Order Cloid {trade.sell_order_id} SELL {trade.sell_quantity} {trade.symbol} @ {trade.sell_price} cannot be cancelled. Order is unknown to the exchange")
                        await self.delete_order_model(client_order_id=trade.sell_order_id)
                        await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                buy_order_id=trade.buy_order_id, health="ERROR",
                                                reason="Sell order is not found in exchange, could have been cancelled externally")
                    continue
                order_id = f"SELL-LOSS_{trade.buy_order_id.split('_')[1]}"
                sell_price = params['price'] * 0.995
                await self.orders_queue.put({
                    'symbol': trade.symbol,
                    'exchange': 'BINANCE',
                    'side': 'SELL',
                    'price': sell_price,
                    'order_id': order_id,
                    'buy_order_id': trade.buy_order_id,
                    'quantity': trade.buy_quantity
                })

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
            trades_models = await self.get_trade_models()
            open_trades_models = [trade for trade in trades_models if trade.sell_status != "FILLED" and trade.health != "ERROR"]

            for trade_model in open_trades_models:
                symbol_info = self.get_symbol_info(trade_model.symbol)
                if trade_model.buy_status == "NEW" and datetime.utcnow() - trade_model.buy_time > self.parse_time(self.order_timeout):
                    await self.cancel_order(symbol=trade_model.symbol, client_order_id=trade_model.buy_order_id)
                    order_model = self.get_order_model(client_order_id=trade_model.buy_order_id)
                    if order_model:
                        #await self.delete_order_model(client_order_id=trade_model.buy_order_id)
                        pass
                    #await self.delete_trade_model(buy_order_id=trade_model.buy_order_id)
                    pass

                if trade_model.buy_status == "FILLED" and trade_model.sell_status in ["NEW", "PARTIALLY_FILLED"]:
                    market_price_resp = await self.get_avg_price(trade_model.symbol)
                    if market_price_resp['error']:
                        logger.error(market_price_resp['message'])
                        continue
                    market_price = float(market_price_resp['result'])

                    if market_price < float(trade_model.buy_price) * (1 - self.stop_loss_trigger):  # we've gone below our stop loss
                        if trade_model.buy_price < market_price * 1.005:
                            continue  # no need to stop stop-losses

                        logger.warning(
                            f"[!] Market price for {trade_model.symbol} has gone below stop loss trigger, placing stop loss sell")

                        if trade_model.buy_quantity_executed * market_price < symbol_info.min_notional:
                            logger.info("[!] The notional size of the order is below minimum")
                            await self.update_trade(side='BUY', exchange_account_id=self.account_model_id, buy_order_id=trade_model.buy_order_id, health="ERROR", reason="Notional value below minimum")
                            continue

                        sell_price = market_price * 0.995

                        resp = await self.cancel_order(trade_model.symbol, client_order_id=trade_model.sell_order_id)
                        if resp['error']:
                            logger.error(resp['message'])
                            if 'Unknown order sent' in resp['message']:
                                #await self.delete_order_model(trade_model.buy_order_id)
                                self.send_admin_notification()

                        order_id = f"SELL-LOSS_{trade_model.buy_order_id.split('_')[1]}"

                        await self.orders_queue.put({
                            'symbol': trade_model.symbol,
                            'exchange': 'BINANCE',
                            'side': 'SELL',
                            'price': sell_price,
                            'quantity': trade_model.buy_quantity,
                            'order_id': order_id,
                            'buy_order_id': trade_model.buy_order_id
                        })

                if trade_model.buy_status == "FILLED" and not trade_model.sell_status in ['NEW', 'FILLED', 'PARTIALLY_FILLED']:
                    if not trade_model.buy_price:
                        logger.error(f"[!] Order has no buy price, check if it was a market order")
                        continue
                    sell_price = trade_model.buy_price * (1 + self.profit_margin)

                    order_id = f"SELL_{trade_model.buy_order_id.split('_')[1][:23]}"

                    asset = await self.get_asset_models(asset=trade_model.base_asset)
                    if not asset:
                        await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                buy_order_id=trade_model.buy_order_id, health="ERROR",
                                                reason="The base asset is missing or depleted")
                        continue
                    if not float(asset.free) + float(asset.locked) >= float(trade_model.buy_quantity_executed):
                        await self.update_trade(side='BUY', exchange_account_id=self.account_model_id,
                                                buy_order_id=trade_model.buy_order_id, health="ERROR",
                                                reason="The base asset is less than the amount bought")
                        if not float(asset.free) * sell_price > symbol_info.min_notional:
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