from telethon.sync import TelegramClient
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# Remember to use your own values from my.telegram.org!
api_id = config.get('DEFAULT','Telegram_API_ID')
api_hash = config.get('DEFAULT','Telegram_API_HASH')

with TelegramClient('test', api_id, api_hash) as client:

    client.send_message('CryptoPingNovemberBot', '/start U4yPDpcG5PJKNKdzWGBnPc9R')