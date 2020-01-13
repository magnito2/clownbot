![alt text](https://github.com/magnito2/clownbot/blob/master/clone-front/public/images/icon/clown.png "Clown Bot")

# [clownbot](http://server.sontran.us:8081/)
A cryptocurrency trader for binance and bittrex

This bot uses external signals fetched from telegram channels to place trades.
Other settings are provided by the user.

## Warning
**This project is still under development. Use it to learn. use it to trade at your own risk.**

## Installation in Linux (tested in Ubuntu). 
*windows users should be able to follow with some minor adjustments*
1. Pull the repo
2. Install the requirements
  * Ensure you have python >= 3.6, mysql and node js installed.
  * Create a new python virtual environment and activate it. `virtualenv venv` then `. /venv/bin/activate`
  * To install the python dependencies **inside your virtual environment**, type `pip install -i requirements.txt` and enter
  * To install node js dependencies for the dashboard;
      - `cd clone-front`
      - type `npm install` and enter
3. Create a mysql database
4. Create a `.flaskenv` file with the following fields
   *  `FLASK_APP=dashboard/flaskapp.py`
   *  `DATABASE_URL=mysql://root:@localhost/clown` #or whichever name you like
   *  `MAIL_USERNAME=you@yourdomain.com`
   *  `MAIL_PASSWORD=youmailpassword` #read more from flask documentation about email support
   *  `BOT_ADDRESS=http://localhost:5080/signal` #change port later if this address is in use
   *  `SECURITY_PASSWORD_SALT=your salt`
   *  `HMAC_KEY=your hmac key`
   *  `JWT_SECRET_KEY=`
   *  `SECRET_KEY=`
   *  `ADMINS=`
   *  `FLASK_RUN_PORT=5000`
5. Create a `config.ini` file with the following fields
    * `[DEFAULT]`
    * `Telegram_API_ID = your telegram id`
    * `Telegram_API_HASH = your telegram hash`
    * `LOG_LEVEL = 10` #or preferred log level

    * `[SQLALCHEMY]`
    * `DATABASE_URI = mysql://username:password@localhost/clown` #checkout sqlalchemy database url format

    * `[HTTP_SIGNAL_RECIEVER]`
    * `PORT=5080`
    
6.  Create migrations for the database

    *with the virtual environment activate*
    * `flask db migrate`
    * `flask db upgrade`
7. Launch!! 
    *there are 3 modules
    * shell 1 with venv active, `python main.py`
    * shell 2 with venv active,  `flask run`
    * shell 3 without venv, `cd clone-front`, `npm start`
    
### Optional

You can use systemctl to run the bot. that will require additional setup. Also you can build the frontend react js module.

## Version 2 coming out soon.
