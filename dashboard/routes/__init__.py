from .. import app, db
from flask import render_template, request, flash, url_for, redirect
from flask_security import login_required, current_user
from dashboard.models import Order, Trade, ExchangeAccount
from dashboard.forms import ApiSettingsForm

@app.route('/')
@login_required
def home():
    orders = Order.query.all()
    buys = []
    sells = []
    for order in orders:
        if order.side == "BUY" and order.status not in ['CANCELED', 'REJECTED']:
            buys.append(order)
        elif order.side == "SELL" and order.status not in ['CANCELED', 'REJECTED']:
            sells.append(order)
    orders_d = {
        'buys': buys,
        'sells': sells
    }
    return render_template('index.html', orders=orders_d)

@app.route('/settings', methods=['GET'])
@login_required
def settings():
    exchanges = current_user.exchange_accounts
    forms = {
        'binance': ApiSettingsForm(),
        'bittrex': ApiSettingsForm()
    }
    if exchanges:
        for exchange in exchanges:
            forms[exchange.exchange].api_key.data = exchange.api_key
            forms[exchange.exchange].api_secret.data = exchange.api_secret
            forms[exchange.exchange].exchange.data = exchange.exchange
    print(f"[!] Our forms are {forms}")

    forms['binance'].action = url_for("binance_settings")
    forms['bittrex'].action = url_for("bittrex_settings")
    return render_template('settings.html', forms=forms)

@app.route('/binance-settings', methods=['POST'])
@login_required
def binance_settings():
    form = ApiSettingsForm(request.form)
    if form.validate():
        user_accounts = [acc.exchange for acc in current_user.exchange_accounts]
        if form.exchange.data in user_accounts:
            acc = [acc for acc in current_user.exchange_accounts if acc.exchange == form.exchange.data][0]
            acc.api_key = form.api_key.data
            acc.api_secret = form.api_secret.data
            msg = "Updating user account"
            flash("Updating user account", "success")
        else:
            acc = ExchangeAccount(api_key=form.api_key.data, api_secret=form.api_secret.data, exchange=form.exchange.data)
            current_user.exchange_accounts.append(acc)
            flash("creating user account", "success")
        db.commit()
    exchanges = current_user.exchange_accounts
    return redirect(url_for('settings'))

@app.route('/bittrex-settings', methods=['POST'])
@login_required
def bittrex_settings():
    form = ApiSettingsForm(request.form)
    if form.validate():
        user_accounts = [acc.exchange for acc in current_user.exchange_accounts]
        if form.exchange.data in user_accounts:
            acc = [acc for acc in current_user.exchange_accounts if acc.exchange == form.exchange.data][0]
            acc.api_key = form.api_key.data
            acc.api_secret = form.api_secret.data
            flash("Updating user account", "success")
        else:
            acc = ExchangeAccount(api_key=form.api_key.data, api_secret=form.api_secret.data, exchange=form.exchange.data)
            current_user.exchange_accounts.append(acc)
            flash("creating user account", "success")
        db.commit()
    else:
        flash()
    exchanges = current_user.exchange_accounts
    return redirect(url_for('settings'))