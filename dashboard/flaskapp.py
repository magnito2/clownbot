from . import app, db, user_datastore
from .models import User, ExchangeAccount

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'ExchangeAccount': ExchangeAccount, 'user_datastore' : user_datastore}