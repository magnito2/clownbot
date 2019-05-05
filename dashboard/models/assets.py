from .. import db
from datetime import datetime

class Asset(db.Model):

    __tablename__="assets"

    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(64))
    name = db.Column(db.String(64))
    free = db.Column(db.String(128))
    locked = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def serialize(self):
        return {
            'name': self.name,
            'free' : self.free,
            'locked': self.locked,
            'timestamp': self.timestamp
        }

    def __repr__(self):
        return f"<Asset({self.id}, {self.name}, free {self.free}, locked {self.locked})>"