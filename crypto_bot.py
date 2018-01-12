import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job,\
                         CallbackQueryHandler
import urllib2
import json
import os
import sys
from threading import Thread

import config
import coin
import wallet
import chart
import user
from db_base import Base, engine

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

def error(bot, update, error):
    logger.warning('Update "{}" caused error "{}"'.format(update, error))

def about(bot, update):
    aboutext = """
Donate to me:
BTC: 15XkP2Xb2AATkWZnHurwJFeuGAkTFaeDPx
BCH: 15cpS8t6BYQ1K5LkXaxW6uvszvZC2sxUhJ
ETH: 0xa8c8717e0e9E7AcE97d448F89642Ad1FEe4ae6fF

Any ERC20 should be the same as ETH.
"""
    update.message.reply_text(aboutext)

def help(bot, update):
    # Send help message to the respective chat
    helptext = """
/h - Display this help menu
/p <coin> - Get the price of a coin with some additional data
/cap <coin> - Get the market cap of a coin. If you use 'all' or 'total' for coin it will return the Total Market Cap
/i - Get the top 10 coins and display their price and 24hr percent change
/c <coin> <time> - Build a chart for a coin. Use /c to get more help

/about - About this bot and my donation addresses
"""
    update.message.reply_text(helptext)

def request(bot, update):
    # not sure how this is going to be done yet
    pass

def main():
    Base.metadata.create_all(engine)

    updater = Updater(config.bot_key)
    dp = updater.dispatcher

    jq = updater.job_queue
    jq.run_repeating(coin.update_coins, interval=30, first=0)

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(bot, update):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    dp.add_handler(CommandHandler(['h', 'help'], help))
    dp.add_handler(CommandHandler(['a', 'about'], about))
    dp.add_handler(CommandHandler(['p', 'price'], coin.get_price))
    dp.add_handler(CommandHandler(['cap'], coin.get_market_cap))
    dp.add_handler(CommandHandler(['i', 'index'], coin.index))
    dp.add_handler(CommandHandler(['d', 'dom', 'domination'], coin.domination))
    dp.add_handler(CommandHandler(['c', 'chart'], chart.chart_handler))
    dp.add_handler(CallbackQueryHandler(chart.handle_button))
    dp.add_handler(CommandHandler('r', restart, filters=Filters.user(username=['@cj_pais', '@hate2truck'])))
    dp.add_handler(CommandHandler(['w', 'wallet', 'pf', 'portfolio'], wallet.wallet))
    dp.add_handler(CommandHandler(['rq', 'request', 'f', 'feature'], request))
    dp.add_handler(CommandHandler('bio', user.bio))
    dp.add_handler(MessageHandler(Filters.text, wallet.wallet_message_handler))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()
    pass

if __name__ == '__main__':
    main()