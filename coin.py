from telegram import ParseMode
from sqlalchemy import Column, Integer, Float, ForeignKey, String, DateTime, create_engine
from sqlalchemy.orm import relationship
import traceback
import logging
import urllib2
import json
from pytz import timezone

import datetime

from db_base import Base, Session, engine, session
import config

Base.metadata.bind = engine

cmc_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=1000'
cmc_cap_url = 'https://api.coinmarketcap.com/v1/global/'
cc_url = 'https://www.cryptocompare.com/api/data/coinlist/'
cc_coin_dict = None 

price_message = u"""
{} (<b>{}</b>) at {:%I}:{:%M%p}
USD: <b>${}</b>
BTC: \u0243{}
1h: {}%
24h: {}%
"""

class Coin(Base):
    __tablename__ = 'coin'

    id = Column(Integer, primary_key=True)

    wallets = relationship("Wallet", back_populates='coin') 

    cmc_id = Column(Integer, nullable=False)
    name = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)
    rank = Column(Integer, nullable=False)
    price_usd = Column(Float, nullable=False)
    price_btc = Column(Float, nullable=False)
    change_1h = Column(Float, nullable=True)
    change_24h = Column(Float, nullable=True)
    change_7d = Column(Float, nullable=True)
    marketcap = Column(Integer, nullable=True)
    volume_24h = Column(Integer, nullable=True)
    updated = Column(DateTime, nullable=False)

    def __init__(self, data):
        self.cmc_id = data['id']
        self.name = data['name']
        self.symbol = data['symbol']
        self.rank = int(data['rank'])
        self.price_usd = float(data['price_usd'])
        self.price_btc = float(data['price_btc'])

        if data['percent_change_1h']:
            self.change_1h = float(data['percent_change_1h'])
        if data['percent_change_24h']:
            self.change_24h = float(data['percent_change_24h'])
        if data['percent_change_7d']:
            self.change_7d = float(data['percent_change_7d'])
        if data['market_cap_usd']:
            self.marketcap = data['market_cap_usd']
        if data['24h_volume_usd']:
            self.volume_24h = int(float(data['24h_volume_usd']))
        self.updated = datetime.datetime.utcnow()

    def update(self, data):
        self.rank = int(data['rank'])
        self.price_usd = float(data['price_usd'])
        self.price_btc = float(data['price_btc'])
        if data['percent_change_1h']:
            self.change_1h = float(data['percent_change_1h'])
        if data['percent_change_24h']:
            self.change_24h = float(data['percent_change_24h'])
        if data['percent_change_7d']:
            self.change_7d = float(data['percent_change_7d'])
        if data['market_cap_usd']:
            self.marketcap = data['market_cap_usd']
        if data['24h_volume_usd']:
            self.volume_24h = int(float(data['24h_volume_usd']))
        self.updated = datetime.datetime.utcnow()

    def price(self):
        logging.log(logging.INFO, self.updated)
        logging.log(logging.INFO, "price")
        utc = self.updated.replace(tzinfo=timezone('UTC'))
        pst = utc.astimezone(timezone('America/Los_Angeles'))
        return price_message.format(self.name, self.symbol, pst, pst, self.price_usd, self.price_btc, self.change_1h, self.change_24h)

    def cap(self):
        return "{} Market Cap:\n<b>${:,}</b> ({:+}%)".format(self.symbol, self.marketcap, self.change_24h)

    def dominance(self):
        dom_arr = []
        cap_all = json.load(urllib2.urlopen(cmc_cap_url))['total_market_cap_usd']
        dom = "{}%".format(round(self.marketcap/cap_all*100, 2))
        dom_arr.append(str(self.rank))
        dom_arr.append(str(self.symbol))
        dom_arr.append(dom)
        return dom_arr

    def index(self):
        """ This will return index data as list of strings for pretty printing """
        index = []
        index.append(str(self.rank))
        index.append(str(self.symbol))
        index.append("${}".format(round(self.price_usd, 3)))
        index.append("{:+}%".format(self.change_24h))
        return index

    def volume(self):
            return "{} 24h Volume:\n<b>${:,}</b>".format(self.symbol, self.volume_24h)

def index(bot, update):
    message = "<b>Top 10 Coins:</b>"
    message_list = [["#", "Symbol", "Price", "24h"]]
    message_builder = ""

    # get top 10 coins
    top10 = session.query(Coin).order_by(Coin.rank.asc()).limit(10).all()
    for coin in top10:
        message_list.append(coin.index())

    max_len = [max(len(x) for x in line)+2 for line in zip(*message_list)]

    for index, m in enumerate(message_list):
        if index == 0:
            message_builder += "\n<b>{:<6}{:<8}{:<18}{:<}</b>".format(m[0], m[1], m[2], m[3])
        else:
            message_builder += "\n{:<{}}{:<{}}{:<{}}{}".format(m[0],
                            2*max_len[0]-len(m[0])-1, m[1],
                            2*max_len[1]-len(m[1])-len(m[0])-1, m[2],
                            2*max_len[2]+max_len[1]-len(m[0])-len(m[1])-len(m[2])-4, m[3])

    message += message_builder

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.HTML)

def get_price(bot, update):
    message_list = update.message.text.split()
    if len(message_list) == 1:
        update.message.reply_text("You forgot to add a coin! Try /p <coin>")

    coin_str = message_list[1]
    coin = get_coin_from_input(coin_str)
    
    if coin_str in ['prl', 'xrb']:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Nice shill coin Ryan",
                         parse_mode=ParseMode.HTML)
    if coin is None:
        message = "CJ SUCKS".format(coin_str)
    else:
        message = coin.price()

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.HTML)

def dominance(bot, update):
    message = "<b>Top 10 Coins:</b>"
    message_list = [["Rank", "Symbol", "Dominance"]]
    message_builder = ""

    # get top 10 coins
    top10 = session.query(Coin).order_by(Coin.rank.asc()).limit(10).all()
    for coin in top10:
        message_list.append(coin.dominance())

    max_len = [max(len(x) for x in line)+2 for line in zip(*message_list)]

    for index, m in enumerate(message_list):
        if index == 0:
            message_builder += "\n<b>{:<6}{:<8}{:<18}</b>".format(m[0], m[1], m[2])
        else:
            message_builder += "\n{:<{}}{:<{}}{}".format(m[0], 2*max_len[0]-len(m[0])-1, m[1], 2*max_len[1]-len(m[1])-len(m[0])-1, m[2])

    message += message_builder

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.HTML)

################################################################################
########################### HELPER FUNCTIONS BELOW #############################
################################################################################

def get_coin_from_input(s):
    coin = session.query(Coin).filter((Coin.name.ilike(s)) | \
                                      (Coin.symbol.ilike(s)) | \
                                      (Coin.cmc_id.ilike(s))).first()
    return coin

def get_market_cap(bot, update):
    try:
        coin_str = update.message.text.split()[1]
        if coin_str.lower() == 'all' or coin_str.lower() == "total":
            # get total market cap
            data = json.load(urllib2.urlopen(cmc_cap_url))
            message = "Total Market Cap: <b>${:,}</b>".format(int(float(data['total_market_cap_usd'])))
        else:
            message = get_coin_from_input(coin_str).cap()
    except IndexError:
        data = json.load(urllib2.urlopen(cmc_cap_url))
        message = "Total Market Cap: <b>${:,}</b>".format(int(float(data['total_market_cap_usd'])))

    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.HTML)

def get_volume(bot, update):
    try:
        coin_str = update.message.text.split()[1]
        message = get_coin_from_input(coin_str).volume()
    except IndexError:
        data = json.load(urllib2.urlopen(cmc_cap_url))
        message = "Market 24h Volume: <b>${:,}</b>".format(int(float(data['total_24h_volume_usd'])))
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.HTML)

def get_cmc_coin_list():
    response = urllib2.urlopen(cc_url)
    coin_list = json.load(response)['Data']

    coin_dict = {}

    for sym, coin in coin_list.iteritems():
        coin_dict[coin['Name'].strip().lower()] = sym
        coin_dict[coin['CoinName'].strip().lower()] = sym

    return coin_dict

################################################################################
############################## Called to Update DB #############################
################################################################################

def update_coins(bot, job):
    # Start by getting the list from CMC
    session = Session()
    try:
        logging.log(logging.INFO, "running update")
        request = urllib2.urlopen(cmc_url)
        data = json.load(request)

        for d in data:
            # logging.log(logging.INFO, "working on {}".format(d['id']))
            # try to find by name
            coin = session.query(Coin).filter(Coin.cmc_id == d['id']).first()
            if coin is not None:
                coin.update(d)
            else:
                coin = Coin(d)
            # else create the coin
            session.add(coin)
        session.commit()
        logging.log(logging.INFO, "update success")
    except Exception as e:
        logging.log(logging.ERROR, "Update Ran into an error {}".format(e))
        traceback.print_exc()
    session.close()

    # lets set the cc dict
    global cc_coin_dict
    cc_coin_dict = get_cmc_coin_list()
