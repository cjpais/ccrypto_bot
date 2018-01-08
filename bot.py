import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    InlineQueryHandler, Job
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
import urllib2
import json

import keys
import chart
import config

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

cmc_coin_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=300/'
cmc_10_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=10'
cmc_cap_url = 'https://api.coinmarketcap.com/v1/global/'
cc_coin_list = 'https://www.cryptocompare.com/api/data/coinlist/'

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

def price(bot, update):
    coin = update.message.text[3:]
    name, symbol, usd, btc, hour, day = get_price(coin)
    btc = round(float(btc),6)

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

def get_price(coin):
    response = urllib2.urlopen(cmc_coin_url)
    price_data = json.load(response)

    coin = coin.lower()

    for data in price_data:
        if data['name'].lower() == coin or \
           data['id'].lower() == coin or \
           data['symbol'].lower() == coin:
            return data['name'], \
                   data['symbol'], \
                   data['price_usd'], \
                   data['price_btc'], \
                   data['percent_change_1h'], \
                   data['percent_change_24h']

def cap(bot,update):
    coin = update.message.text[5:].lower()
    cap = "{} Market Cap <b>${:,}</b>"

    if coin == 'market' or coin == 'all' or coin == "total":
        response = json.load(urllib2.urlopen(cmc_cap_url))
        message = cap.format('Total', int(float(response['total_market_cap_usd'])))
    else:
        response = urllib2.urlopen(cmc_coin_url)
        data = json.load(response)
        for d in data:
            if d['name'].lower() == coin or \
               d['id'].lower() == coin or \
               d['symbol'].lower() == coin:
                message = cap.format(d['symbol'], int(float(d['market_cap_usd'])))
                break

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=telegram.ParseMode.HTML)


def index(bot, update):
    total = json.load(urllib2.urlopen(cmc_cap_url))['total_market_cap_usd']
    response = json.load(urllib2.urlopen(cmc_10_url))
    message = "<b>Top 10 Coins:</b>"
    line = "\n<b>{}. {}</b> ${} ({}%)"

    for index, data in enumerate(response):
        dom = round(float(data['market_cap_usd'])/total*100, 2)
        message += line.format(index+1, data['symbol'], data['price_usd'], dom)

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

# Crypto Handlers
dp.add_handler(CommandHandler(['h', 'help'], help))
dp.add_handler(CommandHandler('p', price))
dp.add_handler(CommandHandler('cap', cap))
dp.add_handler(CommandHandler(['i','index'], index))
dp.add_handler(CommandHandler('c', chart.chart_handler))
dp.add_handler(CommandHandler(['git', 'github'], github))

updater.start_polling()
updater.idle()
