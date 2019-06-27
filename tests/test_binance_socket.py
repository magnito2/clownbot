from binance.binance import Streamer
import asyncio


def user_stream():
    print("\nUser Stream examples\n")

    stream = Streamer()

    async def stop():
        await(asyncio.sleep(5))
        stream.close_all()
        asyncio.get_event_loop().stop()

    def on_user_data(data):
        print("new user data: ", data)

    stream.start_user('', on_user_data)

    asyncio.Task(stop())

    asyncio.get_event_loop().run_forever()

def data_streams():
    print("\nData Stream examples\n")

    stream = Streamer()

    async def stop():
        await(asyncio.sleep(5))
        stream.close_all()
        asyncio.get_event_loop().stop()

    async def on_order_book(data):
        print("order book canges - ", data)
        print("full orderbook - ", stream.get_order_book("ETHBTC"))

    stream.add_order_book("ETHBTC", on_order_book)


    async def on_candlestick(data):
        print("new candlesticks - ", data)
        print("all candlesticks- ", stream.get_candlesticks("ETHBTC"))

    stream.add_candlesticks("ETHBTC", "1m", on_candlestick)


    async def on_trades(data):
        print("trade update - ", data)

    stream.add_trades("ETHBTC", on_trades)

    asyncio.Task(stop())

    asyncio.get_event_loop().run_forever()


#user_stream()
data_streams()