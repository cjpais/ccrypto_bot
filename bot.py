import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    InlineQueryHandler, Job
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
import urllib2
import json
import threading
import time

import keys
import chart
import config
from portfolio import portfolio_message_handler, list_portfolio

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

cmc_coin_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=1000'
cmc_10_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=10'
cmc_cap_url = 'https://api.coinmarketcap.com/v1/global/'
cc_coin_list = 'https://www.cryptocompare.com/api/data/coinlist/'

def price_updater():
    data = json.load(urllib2.urlopen(cmc_coin_url))
    smalldata = json.load(urllib2.urlopen(cmc_10_url))
    config.price_list = data

    # todo this could be an object but yolo
    for coin_data in data:
        config.price_dict[coin_data['symbol']] = coin_data
    logging.log(logging.INFO, "loaded coins")
    threading.Timer(60, price_updater).start()

def help(bot, update):
    helptext = """
/git - Github Repository URL
/p <coin> - Get Price of coin
/i - Get the top 10 coins, display price and percentage of total market cap
/cap <coin> - Get the market cap of a coin or use 'all' to get total market cap

/c <coin> <candle time> - Get the chart of a coin and specify the candlestick time
Example: /c eth 15m will make a chart with eth where the candlestick duration is 15minutes.

Time Options:
Right now there are a fixed set of time options:
1m, 5m, 15m, 1hr, 3hr, 12hr, 1dy, 3dy, 7dy
                """
    bot.send_message(chat_id=update.message.chat_id,
                     text=helptext)

def get_coin_data(symbol):
    try:
        return config.price_dict[symbol]
    except KeyError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Invalid Coin {}".format(symbol))
        return None

def price(bot, update):
    symbol = update.message.text[3:].upper()

    data = get_coin_data(symbol)
    if data is None:
        return

    name = data['name']
    usd = data['price_usd']
    btc = round(float(data['price_btc']),6)
    hour = data['percent_change_1h']
    day = data['percent_change_24h']

    prices = u"""
{} (<b>{}</b>):
USD: <b>${}</b>
BTC: \u0243{}
1h: {}%
24h: {}%
                          """.format(name, symbol, usd, btc, hour, day)

    bot.send_message(chat_id=update.message.chat_id,
                     text=prices,
                     parse_mode=telegram.ParseMode.HTML)

def cap(bot,update):
    coin = update.message.text[5:].lower()
    cap = "{} Market Cap <b>${:,}</b>"

    if coin == 'market' or coin == 'all' or coin == "total":
        response = json.load(urllib2.urlopen(cmc_cap_url))
        message = cap.format('Total', int(float(response['total_market_cap_usd'])))
    else:
        d = get_coin_data(coin)
        if d is None:
            return
        message = cap.format(d['symbol'], int(float(d['market_cap_usd'])))

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=telegram.ParseMode.HTML)


def index(bot, update):
    total = json.load(urllib2.urlopen(cmc_cap_url))['total_market_cap_usd']
    response = json.load(urllib2.urlopen(cmc_10_url))
    message = "<b>Top 10 Coins:</b>\n"
    message += "<b>{:<7}{:<13}{:<18}{:<13}{}</b>".format("Rank", \
                                                                 "Symbol", \
                                                                 "Price", \
                                                                 "24h", \
                                                                 "% Cap")
    line = "\n<b>{:>4}{:>13}</b>{:>14}{:>12}%{:>12}%"

    for index, data in enumerate(response):
        dom = round(float(data['market_cap_usd'])/total*100, 2)
        price = "${}".format(data['price_usd'])
        message += line.format(index+1, data['symbol'], price, data['percent_change_24h'], dom)

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=telegram.ParseMode.HTML)

def github(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="https://github.com/sipjca/ccrypto_bot")

def get_coin_list():
    response = urllib2.urlopen(cc_coin_list)
    coin_list = json.load(response)['Data']

    coin_dict = {}

    for sym, coin in coin_list.iteritems():
        coin_dict[coin['Name'].strip().lower()] = sym
        coin_dict[coin['CoinName'].strip().lower()] = sym

    return coin_dict

updater = Updater(keys.bot_key)

# jq = updater.job_queue
dp = updater.dispatcher

config.coin_list = get_coin_list()
price_updater()

# Crypto Handlers
dp.add_handler(CommandHandler(['h', 'help'], help))
dp.add_handler(CommandHandler('p', price))
dp.add_handler(CommandHandler('cap', cap))
dp.add_handler(CommandHandler(['i','index'], index))
dp.add_handler(CommandHandler('c', chart.chart_handler))
dp.add_handler(CommandHandler(['git', 'github'], github))
dp.add_handler(CommandHandler('pf', list_portfolio))
dp.add_handler(MessageHandler(Filters.text, portfolio_message_handler))


updater.start_polling()
updater.idle()
