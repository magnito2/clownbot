'''
Check if traders are okay, if not, restart them.
'''
import asyncio, logging
from datetime import datetime, timedelta

logger = logging.getLogger('clone.monitor')

class Monitor:

    def __init__(self, celebro):
        self.keep_running = True
        self._check_list = []
        self.check_alive_duration = 5*60
        self.allowed_dead_counts = 2
        self.celebro = celebro

    async def run(self):
        for trader in self.celebro.exchange_traders:
            trader_check = {
                'key': trader.api_key,
                'last_alive': datetime.utcnow(),
                'dead_counts': 0,
                'account_id': trader.account_model_id
            }
            self._check_list.append(trader_check)
            await trader.orders_queue.put({
                'alive_check' : True,
                'monitor': self
            })

        while self.keep_running:
            '''
            Send a package to the traders every 5 minutes, if it does not get consumed in 5 minutes, log. 
            2 unconsumed packages warrant a restart of the trader. also tell admin.
            '''
            await asyncio.sleep(self.check_alive_duration)
            logger.info('[+] Checking traders are alive')
            for trader_check in self._check_list:
                if datetime.utcnow() - trader_check['last_alive'] < timedelta(seconds=self.check_alive_duration):
                    trader_l = [trader for trader in self.celebro.exchange_traders if trader.api_key == trader_check['key']]
                    if not trader_l:
                        logger.error(f"[+] Trader {trader_check['key']} not found")
                        continue
                    trader = trader_l[0]
                    await trader.orders_queue.put({
                        'alive_check': True,
                        'monitor': self
                    })
                    continue
                else:
                    trader_check['dead_counts'] += 1

                if trader_check['dead_counts'] > self.allowed_dead_counts:
                    logger.error(f'Trader {trader.username} is dead as dodo, restarting it')
                    await self.celebro.reload_account(trader_check['account_id'])
                    continue
            if (datetime.utcnow() - self.celebro.last_bot_restart).seconds > self.celebro.bot_restart_interval:
                #await self.celebro.restart_bot()
                pass

    async def confirm_alive(self, api_key):
        for trader_check in self._check_list:
            if trader_check['key'] == api_key:
                trader_check['last_alive'] = datetime.utcnow()
                trader_check['dead_counts'] = 0