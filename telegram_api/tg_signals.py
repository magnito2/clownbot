import re

class ProcessSignal:

    re_pattern = ''
    name = ''
    channel_id = ''

    @classmethod
    def process(cls, message):
        ''' the re pattern should give the signal
            should return a dict with format
            {
                'signal_name' : channel name
                'symbol': signal_tup[0],
                'exchange': signal_tup[1],
                'side': signal_tup[2],
                'price': float(signal_tup[3]),
                'target_price': float(signal_tup[4]),
                'signal_id': signal_tup[5]
            }
        '''


class CQSScalpingFree(ProcessSignal):

    name = 'CQSScalpingFree'
    re_pattern = "#([A-Z]+_[A-Z]+)\s+\((\w+)\)\n(\w+)\s-\s(\d+\.\d+)\nTarget:\s(\d+\.\d+)[\s\S]+\s#([0-9]{5})"

    @classmethod
    def process(cls, message):

        signal_raw = re.search(cls.re_pattern, message)
        if not signal_raw:
            print(f"[!]Message was not a signal\n{message}")
            f = open('dump.txt', 'w', encoding='utf-8')
            f.write(message)
            f.close()
            return
        signal_tup = signal_raw.groups()
        signal = {
            'signal_name': cls.name,
            'symbol': signal_tup[0],
            'exchange': signal_tup[1],
            'side': signal_tup[2],
            'price': float(signal_tup[3]),
            'target_price': float(signal_tup[4]),
            'signal_id': signal_tup[5]
        }
        return signal

class MagnitoCrypto(ProcessSignal):

    name = 'magnitocrypto'
    #name = "CryptoPingMikeBot"
    #name = "QualitySignalsChannel"
    re_pattern = ""

    def __init__(self, SigClass):
        self.sig_class = SigClass

    def process(self, message):
        return self.sig_class.process(message)


class QualitySignalsChannel(ProcessSignal):

    name = "QualitySignalsChannel"
    #name = 'magnitocrypto'
    re_pattern = ".*\n\n.*\s(Buy|Sell)\s#([A-Z]+)/#([A-Z]+)[\s\S]*#(BINANCE|BITTREX)\n\n[\s\S]*#(\d+)" \
                 "[\s\S]*Entry:\s(\d+\.\d+)\s-\s(\d+\.\d+)[\s\S]*\n[\s\S]*Current\sask:\s(\d+\.\d+)[\s\S]*\n[\s\S]*Target\s1:\s\s(\d+\.\d+)[\s\S]*"

    @classmethod
    def process(cls, message):
        signal_raw = re.search(cls.re_pattern, message)
        if not signal_raw:
            print(f"[!]Message was not a signal\n{message}")
            f = open('dump.txt', 'w', encoding='utf-8')
            f.write(message)
            f.close()
            return
        signal_tup = signal_raw.groups()
        signal = {
            'signal_name': cls.name,
            'symbol': f"{signal_tup[2]}_{signal_tup[1]}",
            'exchange': signal_tup[3],
            'side': "BUY" if signal_tup[0] == "Buy" else "SELL",
            'price': float(signal_tup[6]),
            'target_price': float(signal_tup[8]),
            'signal_id': signal_tup[4]
        }
        return signal

class CryptoPingMikeBot(ProcessSignal):

    re_pattern = ""
    name = "CryptoPingMikeBot"

    @classmethod
    def process(cls, message):
        pass