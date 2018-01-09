import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ochl
from matplotlib.dates import MinuteLocator, HourLocator, DayLocator, \
WeekdayLocator, MonthLocator, date2num, DateFormatter
import matplotlib.ticker as ticker
import urllib2
import json
import datetime
import re
matplotlib.rcParams['timezone'] = 'US/Pacific'
import config

histmin_url = 'https://min-api.cryptocompare.com/data/histominute?fsym={}&tsym=USD&limit=120&aggregate={}&e=CCCAGG'
histhour_url = 'https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym=USD&limit=120&aggregate={}&e=CCCAGG'
histday_url = 'https://min-api.cryptocompare.com/data/histoday?fsym={}&tsym=USD&limit=120&aggregate={}&e=CCCAGG'

# class Chart:

def chart_handler(bot, update):
    """
    Inputs are defined as /c <coin> <time>

    Charts described below:
    1m - Hist to Minute, 2hrs
    5m - Hist to Minute, 10hrs
    15m - Hist to Minute, 32hrs
    1hr - Hist to Hour, 5 days
    3hr - Hist to Hour, 2 weeks
    12hr - Hist to Hour, 2 months
    1dy - Hist to Day, 4 months
    3dy - Hist to Day, 9 months
    7dy - Hist to Day, 1 yr
    """
    # TODO make the coin list a global variable... Maybe a object or something.
    if len(update.message.text.split(" ")) < 3:
        bot.send_message(chat_id=update.message.chat_id,
                         text="""
/c <coin> <candle time> - Get the chart of a coin and specify the candlestick time
Example: /c eth 15m will make a chart with eth where the candlestick duration is 15minutes.

Time Options:
Right now there are a fixed set of candlestick size options, with time periods shown in parenthesis:
1m (2h), 5m (10h), 15m (32h), 1hr (5d), 3hr (2wk), 12hr (2m), 1dy (4m), 3dy (9m), 7dy (1y)
""")
        return

    user_input = split_user_input(update.message.text)

    coin, time, period = user_input[0], int(user_input[1]), user_input[2]
    candle_t = "{}{}".format(time, period)

    # TODO write a function to scale all paramaters based on a char and a number
    # or just a dict????
    if period == "m" or period == "min" or period == "minute":
        url = histmin_url.format(coin, time)
        formatter = DateFormatter('%b %d %I:%M%p')
        # dirty constants
        if time == 1:
            # every 15 min... THIS NEEDS OBJECTS CLEARLY TODO
            locator = MinuteLocator(interval = 15)
            minor = MinuteLocator(interval = 3)
            scale = 1
            formatter = DateFormatter('%I:%M%p')
        if time == 5:
            locator = HourLocator(interval = 2)
            minor = HourLocator(interval = 1)
            scale = 5
        if time == 15:
            locator = HourLocator(interval = 5)
            minor = HourLocator(interval = 1)
            scale = 15
    elif period == "h" or period == "hour" or period == "hr":
        url = histhour_url.format(coin, time)
        formatter = DateFormatter('%b %d %Y')
        if time == 1:
            locator = HourLocator(interval = 18)
            minor = HourLocator(interval = 3)
            scale = 60
        if time == 3:
            locator = DayLocator(interval = 2)
            locator = HourLocator(interval = 8)
            scale = 180
        if time == 12:
            locator = WeekdayLocator(interval = 2)
            minor = DayLocator(interval = 2)
            scale = 12*60
    elif period == "d" or period == "day" or period == "dy":
        url = histday_url.format(coin, time)
        formatter = DateFormatter('%b %d %Y')
        if time == 1:
            scale = 60*24
            locator = WeekdayLocator(interval = 3)
            minor = DayLocator(interval = 3)
        if time == 3:
            formatter = DateFormatter('%b %Y')
            scale = 60*24*3
            locator = MonthLocator(interval = 1)
            minor = MonthLocator(interval = 1)
        if time == 7:
            formatter = DateFormatter('%b %Y')
            scale = 60*24*7
            locator = MonthLocator(interval = 3)
            minor = MonthLocator(interval = 3)

    data = json.load(urllib2.urlopen(url))['Data']
    
    gen_chart(data, coin, candle_t, locator, formatter, minor, scale)

    bot.send_photo(chat_id=update.message.chat_id,
                   photo=open('tmp.png'))

def split_user_input(i):
    work_list = []
    i = i.split(" ")

    work_list.append(config.coin_list[i[1].lower()])
    time_period = re.findall('\d+|\D+', i[2])

    time, period = time_period[0], time_period[1]

    work_list.append(time)
    work_list.append(period)

    return work_list

def gen_chart(data, coin, candle_t, locator, major_f, minor_l, scale):
    """ 
        A helper function to generate a chart from the data returned from 
    """
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