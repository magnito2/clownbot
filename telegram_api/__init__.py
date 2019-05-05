'''
Entry.
The telegram api. Recieves signals from telegram and broadcasts events.
'''
from telethon import TelegramClient, events
import logging, asyncio
from .tg_signals import CQSScalpingFree, MagnitoCrypto, QualitySignalsChannel

logger = logging.getLogger('clone.tg')
logging.getLogger('clone.tg').setLevel(level=logging.DEBUG)
logging.getLogger('telethon').setLevel(level=logging.ERROR)
api_id = 895830
api_hash = '318d4db283d08faa09644784e5e7a360'


class MyTelegramClient:

    def __init__(self, binance_queues, bittrex_queues, signal_channels_list):
        self.client = TelegramClient('session_name', api_id, api_hash)
        self.binance_queues = binance_queues
        self.bittrex_queues = bittrex_queues
        self.outgoing_messages_queue = asyncio.Queue()
        self.signal_channels = signal_channels_list
        self._signal_channel_ids = {}


    async def my_event_handler(self, event):
        try:
            text = str(event.raw_text)
            chat = await event.get_input_chat()

            signal = None

            for channel in self.signal_channels:
                if channel.channel_id == chat.channel_id:
                    logger.info(f"[+] Channel {channel.name} has recived a signal {text}")
                    signal = channel.process(text)
                    break

            if signal:
                if signal['side'] == "BUY":
                    if signal['exchange'] == "BINANCE":
                        logger.info(f"********Putting {signal} into queues")
                        for queue in self.binance_queues:
                            await queue.put(signal)
                    elif signal['exchange'] == "BITTREX":
                        logger.info(f"********Putting {signal} into queues")
                        for queue in self.bittrex_queues:
                            await queue.put(signal)
                else:
                    logger.debug(f"Signal not captured, signal is {signal}")
            else:
                logger.error(f"[!] {text} is not a signal")
        except Exception as e:
            logger.exception(e)

    async def run(self):
        self.client.add_event_handler(self.my_event_handler, events.NewMessage(chats=tuple([channel.name for channel in self.signal_channels])))
        await self.client.start()

        for channel in self.signal_channels:
            chat = await self.client.get_input_entity(channel.name)
            if chat:
                logger.info(f"[+] Adding {channel.name} to signals list")
                channel.channel_id = chat.channel_id if hasattr(chat, 'channel_id') else chat.user_id

        await self.client.run_until_disconnected()

    async def send_message_loop(self):
        while not self.client._sender.is_connected():
            await asyncio.sleep(30)
        while True:
            try:
                message = await asyncio.wait_for(self.outgoing_messages_queue.get(), timeout=10)
                logger.info(f"[+] Recieved a new message, {message}")
                await self.client.send_message(message['id'], message['message'])
            except asyncio.TimeoutError:
                logger.info("[+] Timeout timeout")
            except Exception as e:
                logger.exception(e)