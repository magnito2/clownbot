from .. import db
from datetime import datetime


class Portfolio(db.Model):
    __tablename__ = "portfolios"
    id = db.Column(db.Integer, primary_key=True)
    exchange_account_id = db.Column(db.Integer, db.ForeignKey('exchange_account.id'), nullable=False)
    btc_value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def serialize(self, acc=None):
        return {
            'timestamp': self.timestamp.isoformat(),
            'btc_value': self.btc_value,
        }

    @classmethod
    def create_labels(cls, user):
        accounts = user.exchange_accounts
        timestamps = []
        for account in accounts:
            for portfolio in account.portfolio:
                if portfolio.timestamp not in timestamps:
                    timestamps.append(portfolio.timestamp)
        min_t = min(timestamps)
        max_t = max(timestamps)
        labels_len = 100
        delta = (max_t - min_t)/labels_len
        labels = []
        for i in range(labels_len):
            lab = min_t + delta * i
            labels.append(lab)

        return labels

    @classmethod
    def serialize_with_labels(cls, labels, portfolios):
        stamps = [portfolio.timestamp for portfolio in portfolios]
        values = []
        for label in labels:
            try:
                x1 = cls.max_below(label, stamps)
                x2 = cls.min_above(label, stamps)
                if not x1 or not x2:
                    values.append(0)
                    continue
                y1 = [portfolio.btc_value for portfolio in portfolios if portfolio.timestamp == x1][0]
                y2 = [portfolio.btc_value for portfolio in portfolios if portfolio.timestamp == x2][0]
                value = cls.interpolate(x1, x2, y1, y2, label)
                values.append(value)
            except Exception as e:
                print(e)
        return values

    @staticmethod
    def interpolate(x1, x2, y1, y2, x_value):
        if not x1 or not x2 or not y1 or not y2:
            return 0
        x_diff = x2 - x1
        y_diff = y2 - y1
        y_value = y1 + y_diff * (x_value - x1)/x_diff
        return y_value

    @staticmethod
    def max_below(value, value_list):
        below_values = [val for val in value_list if val < value]
        if not below_values:
            return None
        return max(below_values)

    @staticmethod
    def min_above(value, value_list):
        above_values = [val for val in value_list if val > value]
        if not above_values:
            return None
        return min(above_values)
