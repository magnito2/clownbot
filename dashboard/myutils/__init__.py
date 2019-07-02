import requests
from flask_security.signals import password_reset, reset_password_instructions_sent
from flask_security.utils import config_value, get_token_status, hash_data, hash_password, \
    url_for_security, verify_hash
from flask_security.recoverable import generate_reset_password_token, send_password_reset_notice

from flask import current_app as app
from werkzeug.local import LocalProxy

from flask_mail import Message

# Convenient references
_security = LocalProxy(lambda: app.extensions['security'])

_datastore = LocalProxy(lambda: _security.datastore)

def get_binance_symbols():
    try:
        exc_info = requests.get("https://api.binance.com/api/v1/exchangeInfo")
        symbols_info = exc_info.json()['symbols']
        symbol_names = [symbol['symbol'] for symbol in symbols_info]
        return {'error': False, 'result': symbol_names}
    except Exception as e:
        return {'error': True, 'message': str(e)}

def get_bittrex_symbols():
    try:
        markets_resp = requests.get('https://api.bittrex.com/api/v1.1/public/getmarkets')
        markets_resp_json = markets_resp.json()
        if markets_resp_json['success'] == False:
            return {'error': True, 'message': markets_resp_json['message']}
        markets = markets_resp_json['result']
        symbols = [market['MarketName'] for market in markets]
        return {'error': False, 'result': symbols}
    except Exception as e:
        return {'error': True, 'message': str(e)}

def send_reset_password_instructions(user):
    """Sends the reset password instructions email for the specified user.
    :param user: The user to send the instructions to
    """
    token = generate_reset_password_token(user)
    reset_link = frontend_url('reset-password', token=token)

    print(f"[+] The security is {_security}")


    if config_value('SEND_PASSWORD_RESET_EMAIL'):
        send_mail(config_value('EMAIL_SUBJECT_PASSWORD_RESET'),
                            user.email, 'reset_instructions',
                            user=user, reset_link=reset_link)

    reset_password_instructions_sent.send(
        app._get_current_object(), user=user, token=token
    )

def frontend_url(resource, token):
    return app.config['FRONTEND_URL'] + "/" + resource +"/" + token

def update_password(user, password):
    """Update the specified user's password
    :param user: The user to update_password
    :param password: The unhashed new password
    """
    user.password = hash_password(password)
    _datastore.put(user)
    _datastore.commit()
    send_password_reset_notice(user)
    password_reset.send(app._get_current_object(), user=user)

def send_mail(subject, recipient, template, **context):
    """Send an email via the Flask-Mail extension.

    :param subject: Email subject
    :param recipient: Email recipient
    :param template: The name of the email template
    :param context: The context to render the template with
    """

    context.setdefault('security', _security)
    context.update(_security._run_ctx_processor('mail'))

    sender = str(_security.email_sender)
    if isinstance(sender, LocalProxy):
        sender = sender._get_current_object()

    msg = Message(subject,
                  sender=sender,
                  recipients=[recipient])

    ctx = ('security/email', template)
    if config_value('EMAIL_PLAINTEXT'):
        msg.body = _security.render_template('%s/%s.txt' % ctx, **context)
    if config_value('EMAIL_HTML'):
        msg.html = _security.render_template('%s/%s.html' % ctx, **context)

    if _security._send_mail_task:
        _security._send_mail_task(msg)
        return

    mail = app.extensions.get('mail')
    mail.send(msg)
