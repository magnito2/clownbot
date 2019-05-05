from wtforms import Form, BooleanField, StringField, PasswordField, validators

class ApiSettingsForm(Form):
    exchange = StringField('Exchange', validators=[
        validators.DataRequired(),
        validators.AnyOf(['BINANCE','BITTREX'])
    ])
    api_key = StringField('API_KEY', validators=[validators.DataRequired()])
    api_secret = StringField('API_SECRET', validators=[validators.DataRequired()])