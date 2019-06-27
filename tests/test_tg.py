import asyncio
from telegram_api import MagnitoCrypto, MyTelegramClient
from telegram_api.tg_signals import QualitySignalsChannel
from telethon import events, TelegramClient
import re

import logging
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

API_ID = 764712
API_HASH = '7cafe35bbe46581841f17243f6fefd40'

tg_kwargs = {
    'API_ID' : API_ID,
    'API_HASH' : API_HASH
}

async def tester():
    print("[+] Testing the working of Telegram API")
    mag_crypt = MagnitoCrypto(QualitySignalsChannel)
    my_tg_client = MyTelegramClient([],[],[mag_crypt], tg_kwargs)
    producers = asyncio.create_task(my_tg_client.run())
    await asyncio.gather(producers)

async def process_msg(event):
    try:
        print(event.client)
        pat = ".*#([A-Z]+)\nUp signal on (Binance|Bittrex)\n[\s\S]*price: (\d+\.\d+) BTC\n[\s\S]*"
        print(f"[+] New message recieved from {await event.get_input_chat()}")
        text = str(event.raw_text)
        chat = await event.get_input_chat()
        print(f"The chat is {chat}")
        print(f"[+] Handling {text}")
        signal_raw = re.search(pat, text)
        print(signal_raw.groups())

    except Exception as e:
        print(e)

async def test_send_message():
    params = {'id': '+254711545789', 'message': 'Hello wowd'}
    client = TelegramClient('clown_bot', API_ID, API_HASH)
    await client.start()
    entity = await client.get_entity('beannsofts_bot')
    client.add_event_handler(process_msg, events.NewMessage(chats=tuple(['me', 'magnitocrypto','CryptoPingNovemberBot'])))
    await client.send_message(entity, params['message'])
    #producers = asyncio.create_task(my_tg_client.client.send_message(params['id'], params['message']))
    #prod = asyncio.create_task((my_tg_client.client.get_entity('CryptoPingNovemberBot')))
    #nov_bot = await asyncio.gather(prod)
    await client.run_until_disconnected()


asyncio.run(test_send_message())