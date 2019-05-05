import asyncio
from telegram_api import MagnitoCrypto, MyTelegramClient
from telegram_api.tg_signals import QualitySignalsChannel

import logging
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)


async def tester():
    print("[+] Testing the working of Telegram API")
    mag_crypt = MagnitoCrypto(QualitySignalsChannel)
    my_tg_client = MyTelegramClient([],[],[mag_crypt])
    producers = asyncio.create_task(my_tg_client.run())
    await asyncio.gather(producers)

async def test_send_message():
    params = {'id': '+254711545789', 'message': 'Hello wowd'}
    my_tg_client = MyTelegramClient([], [], [])
    await my_tg_client.client.start()
    producers = asyncio.create_task(my_tg_client.client.send_message(params['id'], params['message']))
    await asyncio.gather(producers)

logger = logging.getLogger('clone')
asyncio.run(test_send_message())