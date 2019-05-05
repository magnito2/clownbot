from .. import db
from datetime import datetime

class StartUp(db.Model):

    __tablename__="startups"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f"<Startup({self.id}, {self.timestamp})"