import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'krb2wSPWmW8c1R-82DkF7A'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = "magnusotwani@gmail.com"
    MAIL_PASSWORD = "izyudvoyitvjgqsn"

    SECURITY_PASSWORD_SALT = "$2b$12$UoI9MPk8Z5C54aliCZxTyu"

    RECAPTCHA_PUBLIC_KEY = "6LdQemAUAAAAAMHl64OR_uzU8Cde9l_iIO8mzjFi"
    RECAPTCHA_PRIVATE_KEY = "6LdQemAUAAAAAPhsgYHuqYC5mvR0CzqfN502RuFF"

    ADMINS = ['magnusotwani@gmail.com']
    # DEBUG = True

    HMAC_KEY = "Gmc8gWKlZGaxipc4lww12g"

    STATIC_FOLDER = basedir + "/static"

    SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'security/register_user.html'
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CONFIRMABLE = True

    SECURITY_RESET_URL = "/reset-password"

    JWT_SECRET_KEY = 'C-yiJqXMN6yEDnMpCxNtag'

    BOT_ADDRESS = "http://localhost:8080/signal"

    FRONTEND_URL = "http://localhost:3000"
