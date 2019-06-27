from utils import run_in_executor
import asyncio, json
from models import create_session, Order, Asset, Trade, Portfolio, ExchangeAccount
from trader import BinanceTrader
import uuid

def create_account():

    with open("keys.json", 'r') as f:
        json_kwargs = json.load(f)
        kwargs = json_kwargs['binance']
        params = {
            'api_key': kwargs['api_key'],
            'api_secret': kwargs['secret_key'],
            'percent_size': kwargs['min_order_size'],
            'profit_margin': kwargs['profit_margin'],
            'order_timeout': kwargs['order_cancel_seconds'],
            'stop_loss_trigger': kwargs['stop_loss_trigger'],
            'user_id': kwargs['user_id'],
            'user_tg_id': kwargs['user_tg_id'],
            'receive_notifications': kwargs['receive_notifications'],
            'subscribed_signals': [signal for signal in kwargs['signals']],
            'use_fixed_amount_per_order': kwargs['use_fixed_amount_per_order'],
            'fixed_amount_per_order': kwargs['fixed_amount_per_order'],
            'exchange_account_model_id': ['id'],
            'exchange': 'BINANCE'
        }
        trader = BinanceTrader(**kwargs)
        return trader

@run_in_executor
def save_trade_in_db():
    pass

async def loop_save(acc):
    trader = acc
    count = 0
    buy_order_id = None
    while True:
        print("[+] saving random data to db")
        await asyncio.sleep(3)
        count += 1
        if count % 2:
            buy_order_id = f'BUY_{str(uuid.uuid4())[:24]}'
            trade_model_params = {
                'exchange': 'BINANCE',
                'symbol': 'BTCUSDT',
                'buy_order_id': buy_order_id,
                'buy_status': 'NEW',
                'buy_quantity_executed': 0,
                'side': 'BUY',
                'exchange_account_id': 1
            }
        else:
            trade_model_params = {
                'buy_order_id': buy_order_id,
                'sell_order_id': f'SELL_{buy_order_id.split("_")[1]}',
                'sell_status': 'NEW',
                'sell_quantity_executed': 0,
                'side': 'SELL',
            }
        print('Updating trade')
        await trader.update_trade(**trade_model_params)

async def main():
    account = create_account()
    await asyncio.create_task(loop_save(account))

if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")