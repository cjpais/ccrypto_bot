import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ochl
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import urllib2
import json

cc_coin_list = 'https://www.cryptocompare.com/api/data/coinlist/'

def get_coin_list():
    response = urllib2.urlopen(cc_coin_list)
    coin_list = json.load(response)['Data']

    coin_dict = {}

    for sym, coin in coin_list.iteritems():
        coin_dict[coin['Name'].strip().lower()] = sym
        coin_dict[coin['CoinName'].strip().lower()] = sym

    return coin_dict

def gen_chart(data, coin, numdisp):
    """ 
        A helper function to generate a chart from the data returned from 
    """
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

    candlestick2_ochl(ax, opens, close, high, low, width=.7, colordown='#f22800', colorup='#00ce03', alpha=.75)

    # ax.xaxis.set_major_locator(ticker.MaxNLocator(numdisp))
    # ax.xaxis_date()
    # ax.xaxis.set_major_formatter()

    fig.savefig('tmp.png', facecolor='#2f3d45')

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
    coin_list = get_coin_list()
    coin = coin_list[update.message.text[3:].lower()]
    response = urllib2.urlopen('https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym=USD&limit=24&aggregate=3&e=CCCAGG'.format(coin))
    data = json.load(response)['Data']
    chart = gen_chart(data, coin, 12)

    bot.send_photo(chat_id=update.message.chat_id,
                   photo=open('tmp.png'))