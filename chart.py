import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ochl
from matplotlib.dates import MinuteLocator, HourLocator, DayLocator, \
WeekdayLocator, MonthLocator, date2num, DateFormatter
import matplotlib.ticker as ticker
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ChatAction

import urllib2
import json
import datetime
import re
matplotlib.rcParams['timezone'] = 'US/Pacific'

import config
import coin

import logging

histmin_url = 'https://min-api.cryptocompare.com/data/histominute?fsym={}&tsym=USD&limit=120&aggregate={}&e=CCCAGG'
histhour_url = 'https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym=USD&limit=120&aggregate={}&e=CCCAGG'
histday_url = 'https://min-api.cryptocompare.com/data/histoday?fsym={}&tsym=USD&limit=120&aggregate={}&e=CCCAGG'

# class Chart:
chart_dict = {'1m':{'time': 1, 'locator': MinuteLocator(interval = 15), 'major_f': DateFormatter('%I:%M%p'), 'minor_l': MinuteLocator(interval = 3), 'scale': 1, 'url': histmin_url},
              '1min':{'time': 1, 'locator': MinuteLocator(interval = 15), 'major_f': DateFormatter('%I:%M%p'), 'minor_l': MinuteLocator(interval = 3), 'scale': 1, 'url': histmin_url},
              '5m':{'time': 5, 'locator': HourLocator(interval = 2), 'major_f': DateFormatter('%b %d %I:%M%p'), 'minor_l': HourLocator(interval = 1), 'scale': 5, 'url': histmin_url},
              '5min':{'time': 5, 'locator': HourLocator(interval = 2), 'major_f': DateFormatter('%b %d %I:%M%p'), 'minor_l': HourLocator(interval = 1), 'scale': 5, 'url': histmin_url},
              '15m':{'time': 15, 'locator': HourLocator(interval = 5), 'major_f': DateFormatter('%b %d %I:%M%p'), 'minor_l': HourLocator(interval = 1), 'scale': 15, 'url': histmin_url},
              '15min':{'time': 15, 'locator': HourLocator(interval = 5), 'major_f': DateFormatter('%b %d %I:%M%p'), 'minor_l': HourLocator(interval = 1), 'scale': 15, 'url': histmin_url},
              '1h':{'time': 1, 'locator': HourLocator(interval = 18), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': HourLocator(interval = 3), 'scale': 60, 'url': histhour_url},
              '1hr':{'time': 1, 'locator': HourLocator(interval = 18), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': HourLocator(interval = 3), 'scale': 60, 'url': histhour_url},
              '3h':{'time': 3, 'locator': DayLocator(interval = 2), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': HourLocator(interval = 8), 'scale': 60*3, 'url': histhour_url},
              '3hr':{'time': 3, 'locator': DayLocator(interval = 2), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': HourLocator(interval = 8), 'scale': 60*3, 'url': histhour_url},
              '12h':{'time': 12, 'locator': WeekdayLocator(interval = 2), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': DayLocator(interval = 2), 'scale': 60*12, 'url': histhour_url},
              '12hr':{'time': 12, 'locator': WeekdayLocator(interval = 2), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': DayLocator(interval = 2), 'scale': 60*12, 'url': histhour_url},
              '1d':{'time': 1, 'locator': WeekdayLocator(interval = 3), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': DayLocator(interval = 3), 'scale': 60*24, 'url': histday_url},
              '1dy':{'time': 1, 'locator': WeekdayLocator(interval = 3), 'major_f': DateFormatter('%b %d %Y'), 'minor_l': DayLocator(interval = 3), 'scale': 60*24, 'url': histday_url},
              '3d':{'time': 3, 'locator': MonthLocator(interval = 1), 'major_f': DateFormatter('%b %Y'), 'minor_l': MonthLocator(interval = 1), 'scale': 60*24*3, 'url': histday_url},
              '3dy':{'time': 3, 'locator': MonthLocator(interval = 1), 'major_f': DateFormatter('%b %Y'), 'minor_l': MonthLocator(interval = 1), 'scale': 60*24*3, 'url': histday_url},
              '7d':{'time': 7, 'locator': MonthLocator(interval = 3), 'major_f': DateFormatter('%b %Y'), 'minor_l': MonthLocator(interval = 3), 'scale': 60*24*7, 'url': histday_url},
              '7dy':{'time': 7, 'locator': MonthLocator(interval = 3), 'major_f': DateFormatter('%b %Y'), 'minor_l': MonthLocator(interval = 3), 'scale': 60*24*7, 'url': histday_url},
              }

chart_helptext = """
Usage:
/c <coin> - List out all time options for the chart, click one and your chart is returned
/c <coin> <candle time> - Get the chart of a coin and specify the candlestick time
Example: /c eth 15m will make a chart with eth where the candlestick duration is 15minutes.

Time Options:
Right now there are a fixed set of candlestick size options, with time periods shown in parenthesis:
1m (2h), 5m (10h), 15m (32h), 1hr (5d), 3hr (2wk), 12hr (2m), 1dy (4m), 3dy (9m), 7dy (1y)
"""

# TODO TODO TODO TODO we need to make sure that any coin is caught rather than just the symbol

def chart_handler(bot, update):
    """
    Inputs are defined as /c <coin> <time>

    Charts described below:
    1m - Hist to Minute, 2hrs
    5m - Hist to Minute, 10hrs
    15m - Hist to Minute, 32hrs
    1hr - Hist to Hour, 5 days
    3hr - Hist to Hour, 3 weeks
    12hr - Hist to Hour, 2 months
    1dy - Hist to Day, 4 months
    3dy - Hist to Day, 9 months
    7dy - Hist to Day, 1 yr
    """
    message = update.message.text.split()
    if len(message) == 1 or len(message) > 3:
        # send the helptext to the user
        bot.send_chat_action(chat_id=update.message.chat_id,
                         action=ChatAction.TYPING)
        bot.send_message(chat_id=update.message.chat_id,
                         text=chart_helptext)
        return
    elif len(message) == 2:
        # TODO validate the coin
        bot.send_chat_action(chat_id=update.message.chat_id,
                         action=ChatAction.TYPING)
        coin = split_user_input(update.message.text)[0]

        # display a keyboard
        chart_keyboard = [[InlineKeyboardButton("2 Hours", callback_data='{},1m'.format(coin)),
             InlineKeyboardButton("10 Hours", callback_data='{},5m'.format(coin)),
             InlineKeyboardButton("32 Hours", callback_data='{},15m'.format(coin))],
             [InlineKeyboardButton("5 Days", callback_data='{},1h'.format(coin)),
             InlineKeyboardButton("2 Weeks", callback_data='{},3h'.format(coin)),
             InlineKeyboardButton("2 Months", callback_data='{},12h'.format(coin))],
             [InlineKeyboardButton("4 Months", callback_data='{},1d'.format(coin)),
             InlineKeyboardButton("9 Months", callback_data='{},3d'.format(coin)),
             InlineKeyboardButton("1 Year", callback_data='{},7d'.format(coin))]]
        reply_markup = InlineKeyboardMarkup(chart_keyboard)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Chart of {} for the past:".format(coin),
                         reply_markup=reply_markup)
    else:
        # the user has put in the full command for generating a chart (legacy)
        user_input = split_user_input(update.message.text)

        coin, time, period = user_input[0], int(user_input[1]), user_input[2]
        candle_t = "{}{}".format(time, period)
        
        gen_chart(coin, candle_t)

        bot.send_photo(chat_id=update.message.chat_id,
                       photo=open('tmp.png'))

def handle_button(bot, update):
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id,
                         action=ChatAction.TYPING)

    cd = update.callback_query.data.split(',')
    logging.log(logging.INFO, "{}\n{}".format(cd, update.callback_query.data))
    bot.send_message(chat_id=update.callback_query.message.chat_id,
                     text="Generating {} chart of {}...".format(cd[1], cd[0]))
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id,
                         action=ChatAction.TYPING)

    gen_chart(cd[0], cd[1])
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id,
                         action=ChatAction.UPLOAD_PHOTO)
    bot.send_photo(chat_id=update.callback_query.message.chat_id,
                   photo=open('tmp.png'))

def get_symbol_from_string(s):
    pass

# Split this into get_coin_data, get_time, get_period
def split_user_input(i):
    work_list = []
    i = i.split(" ")

    logging.log(logging.INFO, coin.cc_coin_dict is None)
    
    # if the coin dictionary hasnt loaded yet wait to get the coin
    while coin.cc_coin_dict is None:
        pass 
    work_list.append(coin.cc_coin_dict[i[1].lower()])

    try:
        time_period = re.findall('\d+|\D+', i[2])
        time, period = time_period[0], time_period[1]
        work_list.append(time)
        work_list.append(period)
    except IndexError:
        pass

    return work_list

def gen_chart(coin, candle_t):
    """ 
        A helper function to generate a chart from the data returned from 
    """
    chart_data = chart_dict[candle_t]
    time = chart_data['time']
    scale = chart_data['scale']
    locator = chart_data['locator']
    major_f = chart_data['major_f']
    minor_l = chart_data['minor_l']

    url = chart_data['url'].format(coin, time)
    data = json.load(urllib2.urlopen(url))['Data']

    close = [d['close'] for d in data]
    opens = [d['open'] for d in data]
    high = [d['high'] for d in data]
    low = [d['low'] for d in data]

    # this is one of the ugliest things ive seen in python... sorry
    date_time = [date2num(datetime.datetime.fromtimestamp(d['time'])) for d in data]
    
    quotes = [[date_time[i], opens[i], close[i], high[i], low[i]] for i in range(len(date_time))]

    fig, ax = plt.subplots(figsize=(20, 14))

    fig.patch.set_facecolor('#2f3d45')

    ax.set_facecolor('#2f3d45')
    ax.xaxis.label.set_color('white')
    
    ax.spines['top'].set_alpha(0)
    ax.spines['right'].set_alpha(0)
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')

    plt.title('{} Candlestick of {} in PST'.format(candle_t, coin), color='white', size=30, y=1.05)
    plt.ylabel('Price of {} in USD'.format(coin), color='white', size=20, labelpad=15)
    plt.xlabel('Time', color='white', size=20, labelpad=15)

    ax.tick_params(axis='x', colors='white', labelsize = 15, which='both', length=5)
    ax.tick_params(axis='y', colors='white', labelsize = 15, length=5)
    ax.grid(True, color='#626c7f')

    line_rect = candlestick_ochl(ax, quotes, width=0.0006*scale, colordown='#f22800', colorup='#00ce03', alpha=.75)
    for line in line_rect[0]:
        line.set_c('black')
        line.set_linewidth(1)
    for rect in line_rect[1]:
        rect.set_ec('black')
        rect.set_linewidth(.8)
        rect.set_linestyle('solid')

    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(major_f)
    ax.xaxis.set_minor_locator(minor_l)
    
    fig.savefig('tmp.png', facecolor='#2f3d45', bbox_inches='tight', pad_inches = 0.4)