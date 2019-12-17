'''Astronomy here'''

from test_up_repl import celebro_instance
from datetime import datetime
import time

import asyncio

async def recreate_trades():
    '''We lost trades when we sheepishily took down the database, lets recreate them'''

    print("Recreating the lost trades")

    for trader in celebro_instance.exchange_traders:
        account = trader.account

        start_time = time.time()

        open_orders = account.open_orders()

        for order in open_orders:

            print(f"Adding #{order['symbol']} into trades")
            symbol_info = trader.get_symbol_info(order['symbol'])


            market_price_resp = await trader.get_avg_price(order['symbol'])
            if market_price_resp['error']:
                print(market_price_resp['message'])
                continue
            market_price = float(market_price_resp['result'])

            buy_order_id = order['clientOrderId'].split("_")[1] if len(order['clientOrderId'].split("_")) == 2 else ""
            if not buy_order_id:
                print("no buy order id")
                continue
            trade_params = {
                'exchange': "BINANCE",
                'symbol': order['symbol'],
                'sell_order_id': order['orderId'],
                'buy_time': datetime.utcfromtimestamp(int(order['updateTime']) / 1000),
                'sell_time': datetime.utcfromtimestamp(int(order['updateTime'])/1000),
                'sell_price': order['price'],
                'sell_quantity': order['origQty'],
                'buy_quantity': order['origQty'],
                'buy_quantity_executed': order['origQty'],
                'quote_asset': symbol_info.quote_asset,
                'base_asset': symbol_info.base_asset,
                'sell_status': order['status'],
                'buy_status': 'FILLED',
                'side': 'BUY',
                'buy_order_id': buy_order_id,
                'buy_price' : market_price,
                'signal_id' : 5
            }

            await trader.update_trade(**trade_params)

        if time.time() - start_time < 60*60:
            asyncio.sleep(60*60 - (time.time() - start_time))

if __name__ == "__main__":
    asyncio.run(recreate_trades())