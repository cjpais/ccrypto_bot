from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, Job
import telegram
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
import urllib2
import os
import keys
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ochl
import json
import matplotlib.ticker as ticker
import datetime as datetime
from pytz import timezone
import pytz

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_coin_list():
    response = urllib2.urlopen('https://www.cryptocompare.com/api/data/coinlist/')
    coin_list = json.load(response)['Data']

    coin_dict = {}

    for sym, coin in coin_list.iteritems():
        coin_dict[coin['Name'].strip().lower()] = sym
        coin_dict[coin['CoinName'].strip().lower()] = sym

    return coin_dict

def price(bot, update):
    # TODO catch error and tell user they fucked up
    coin = coin_list[update.message.text[3:].lower()]
    usd, btc, day = get_price(coin)

    bot.send_message(chat_id=update.message.chat_id,
                     text="""
{}:
USD: <b>{}</b>
BTC: {}
24h: {}%
                          """.format(coin, usd, btc, day),
                     parse_mode=telegram.ParseMode.HTML)

def cap(bot,update):
    coin = coin_list[update.message.text[5:].lower()]

    response = urllib2.urlopen('https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms=BTC,USD'.format(coin))
    cap = json.load(response)['DISPLAY'][coin]['USD']['MKTCAP']

    bot.send_message(chat_id=update.message.chat_id,
                     text="Market Cap ({})\n<b>{}</b>".format(coin, cap),
                     parse_mode=telegram.ParseMode.HTML)

# huhlol this doesnt even need to be a method, it was originally to clean it up
# but this is fine
def get_price(coin):
    response = urllib2.urlopen('https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms=BTC,USD'.format(coin))

    price_data = json.load(response)
    usd_price_data = price_data['DISPLAY'][coin]['USD']
    btc_price_data = price_data['RAW'][coin]['BTC']

    return usd_price_data['PRICE'].replace(' ',''), \
           btc_price_data['PRICE'], \
           usd_price_data['CHANGEPCT24HOUR']

def three_chart(bot,update):
    coin = coin_list[update.message.text[4:].lower()]

    response = urllib2.urlopen('https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym=USD&limit=72&aggregate=3&e=CCCAGG'.format(coin))
    data = json.load(response)['Data']

    chart = gen_chart(data, coin, 6)

    bot.send_photo(chat_id=update.message.chat_id,
                   photo=open('tmp.png'))

def sixty_chart(bot,update):
    coin = coin_list[update.message.text[5:].lower()]
    response = urllib2.urlopen('https://min-api.cryptocompare.com/data/histoday?fsym={}&tsym=USD&limit=60&aggregate=3&e=CCCAGG'.format(coin))
    data = json.load(response)['Data']
    chart = gen_chart(data, coin, 10)

    bot.send_photo(chat_id=update.message.chat_id,
                   photo=open('tmp.png'))

def day_chart(bot,update):
    coin = coin_list[update.message.text[3:].lower()]
    response = urllib2.urlopen('https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym=USD&limit=24&aggregate=3&e=CCCAGG'.format(coin))
    data = json.load(response)['Data']
    chart = gen_chart(data, coin, 12)

    bot.send_photo(chat_id=update.message.chat_id,
                   photo=open('tmp.png'))

def tracker_callback(bot, job):
    now_resp = urllib2.urlopen('https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms=BTC,USD'.format(job.context["coin"]))
    now_data = json.load(response)['RAW'][job.context['coin']]['USD']
    now_price = now_data['PRICE'] 
    now_time = now_data['LASTUPDATE'] 

    hour_time = now_time - 3600
    hour_resp = urllib2.urlopen('https://min-api.cryptocompare.com/data/pricehistorical?fsyms={}&tsyms=BTC,USD&ts={}'.format(job.context["coin"], hour_time))
    hour_price = json.load(response)[job.context['coin']]['USD']

    percent = (now_price - hour_price) / hour_price
    print "percent {}, coin {}".format(percent, job.context['coin'])
     
    if percent < .05 and percent > -.05:
        jobs[job.context["coin"]] = jq.run_once(tracker_callback, 300, job.context)
    elif (percent > .05 and percent < .1) or (percent < -.05 and percent > -.1): 
        jobs[job.context["coin"]] = jq.run_once(tracker_callback, 7200, job.context)
        track_response(bot, job.context["update"], job.context["coin"], percent)
    elif percent > .1 or percent < -.1:
        jobs[job.context["coin"]] = jq.run_once(tracker_callback, 7200, job.context)
        track_response(bot, job.context["update"], job.context["coin"], percent)

def track(bot, update): 
    coin = coin_list[update.message.text[3:].lower()]
    try:
        job = jobs[coin]
    except KeyError:
        jobs[coin] = jq.run_once(tracker_callback, 0, context={"coin": coin, "update": update}) 
        bot.send_message(chat_id=update.message.chat_id,
                         text="Now tracking {}".format(coin))
    
def track_response(bot, update, coin, percent):
    
    pass

def gen_chart(data, coin, numdisp):
    close = [d['close'] for d in data]
    opens = [d['open'] for d in data]
    high = [d['high'] for d in data]
    low = [d['low'] for d in data]
    dates = [d['time'] for d in data]

    fig, ax = plt.subplots()

    fig.patch.set_facecolor('#2f3d45')

    ax.set_facecolor('#2f3d45')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    
    ax.spines['top'].set_alpha(0)
    ax.spines['right'].set_alpha(0)
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')

    plt.ylabel('Price of {} in USD'.format(coin))

    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    def mydate(x,pos):
        try:
            return xdate[int(x)]
        except IndexError:
            print "error"
            return ''

    candlestick2_ochl(ax, opens, close, high, low, width=.7, colordown='#f22800', colorup='#00ce03', alpha=.75)

    xdate = [datetime.datetime.fromtimestamp(d, tz=pytz.utc).astimezone(timezone('US/Pacific')).strftime("%d/%m/%y %I:%M%p GMT") for d in dates]

    ax.xaxis.set_major_locator(ticker.MaxNLocator(numdisp))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(mydate))
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig('tmp.png', facecolor='#2f3d45')

updater = Updater(keys.bot_key)

jobs = {}
coin_list = get_coin_list()
print "built coin list"

jq = updater.job_queue
dp = updater.dispatcher

# Crypto Handlers
dp.add_handler(CommandHandler('p', price))
dp.add_handler(CommandHandler('cap', cap))
dp.add_handler(CommandHandler('c', day_chart))
dp.add_handler(CommandHandler('c3', three_chart))
dp.add_handler(CommandHandler('c60', sixty_chart))
dp.add_handler(CommandHandler('t', track))

updater.start_polling()
updater.idle()
