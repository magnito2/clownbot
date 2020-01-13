from dashboard.models import Signal
from dashboard import db
from flask_seeder import Seeder

class SeedSignalsTable(Seeder):

    signal_dicts = [
        {
            'name': 'QualitySignalsChannel',
            'description': 'get the best signals and make money, boom',
            'short_name': 'QSC'
        },
        {
            'name': 'CQSScalpingFree',
            'description': 'Best scalpers signal',
            'short_name': 'CQSF'
        },
        {
            'name': 'CryptoPingXrayBot',
            'description': 'Another of the ping family',
            'short_name': 'XPING'
        },
    ]

    def run(self):
        for signal_dict in self.signal_dicts:
            signal = Signal(name=signal_dict['name'], description=signal_dict['description'], short_name=signal_dict['short_name'])
            db.session.add(signal)
        db.session.commit()