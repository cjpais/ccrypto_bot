import keys

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import urllib2
import json

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="""
Welcome to ccrypto bot!\n\n
Use /p {coin name or symbol}") to get the current\n
price
                          """
                    )

# def help(bot, update):
#     bot.send_message(chat_id=update.message.chat_id,
#                      text="Something to help")

# def coins(bot, update):
    # list the coins from coinmarketcap... in a non overwhelming way

def price(bot, update):
    coin = update.message.text[3:]

    name, usd, btc, hour, day = get_price(coin)

    bot.send_message(chat_id=update.message.chat_id,
                     text="""
{}:
USD: {}
BTC: {}
1h: {}%
24h: {}%
                          """.format(name, usd, btc, hour, day))

def get_price(coin):
    response = urllib2.urlopen('https://api.coinmarketcap.com/v1/ticker/')
    price_data = json.load(response)

    coin = coin.lower()

    for data in price_data:
        if data['name'].lower() == coin or \
           data['id'].lower() == coin or \
           data['symbol'].lower() == coin:
            return data['name'], \
                   data['price_usd'], \
                   data['price_btc'], \
                   data['percent_change_1h'], \
                   data['percent_change_24h']

u = Updater(keys.bot_key)

dp = u.dispatcher

dp.add_handler(CommandHandler('start', start))
# dp.add_handler(CommandHandler(['help', 'h'], help))
# dp.add_handler(CommandHandler(['coins', 'c'], coins))
dp.add_handler(CommandHandler(['price', 'p'], price))

u.start_polling()
u.idle()