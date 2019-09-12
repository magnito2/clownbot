import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')

    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')

    ADMINS = os.environ.get('ADMINS')

    HMAC_KEY = os.environ.get('HMAC_KEY')

    STATIC_FOLDER = basedir + "/static"

    SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'security/register_user.html'
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CONFIRMABLE = True

    SECURITY_EMAIL_SENDER = "Clown Bot"

    SECURITY_RESET_URL = "/reset-password"

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    BOT_ADDRESS = os.environ.get('BOT_ADDRESS')

    FRONTEND_URL = "http://localhost:3000"
