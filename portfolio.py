from sqlalchemy import create_engine, exists, and_
from sqlalchemy.orm import sessionmaker
import re
from telegram import ParseMode
import logging

import config
from db_manager import Base, User, Coin

engine = create_engine('sqlite:////data/cryptobot.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()

def portfolio_message_handler(bot, update):
    # Check if user exists in db
    logging.log(logging.INFO, update.message.from_user)
    t_id = update.message.from_user.id
    first_name = update.message.from_user.first_name 
    last_name = update.message.from_user.last_name

    user = get_user(t_id, first_name, last_name)

    # This will take the message, convert it into an action and return the
    # response... Maybe not the best programming practice but fuck it! This is
    # for fun and ease.
    message = get_message(update.message.text.split(' '), user)

    if message is None:
        # if no action
        return
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=message)

def get_message(input, user):
    # We do this so that we can not accidentally add
    if input[0] == "add" or input[0] == "bought":
        # determine if input[1] is <number> or <number><coin>
        message = add_coin(user, input)
    elif input[0] == "sold" or input[0] == "remove":
        message = remove_coin(user, input)
    return message

def add_coin(user, input):
    num, sym = get_num_coins(input)

    coin = session.query(Coin).filter(and_(Coin.user == user, Coin.symbol == sym)).first()
    print coin
    # if the user has this coin simply add to it, otherwise set it up
    if coin:
        coin.amount += num
        session.commit()
    else:
        coin = Coin(symbol=sym, amount=num, user=user)
        session.add(coin)
        session.commit()
    return "{} added".format(sym)

def remove_coin(user, input):
    num, sym = get_num_coins(input)

    coin = session.query(Coin).filter(and_(Coin.user == user, Coin.symbol == sym)).first()
    if coin:
        if num == "all":
            return "You have sold all of your {}{}".format(coin.amount, sym)
            session.delete(coin)
            session.commit()
        else:
            coin.amount -= num
            session.commit()
            return "You have sold {} of your {}. {} {} remaining".format(num, sym, coin.amount, sym)
    else:
        # dont remove someting thats not there
        return "You have no {} to remove you fuck".format(sym)


def get_num_coins(input):
    if len(input) == 3:
        if input[1] == 'all':
            num = input[1]
        else:
            num = float(input[1])
        coin = input[2].upper()
    else:
        num_coins = re.findall('\d+|\D+', input[1])
        num = float(num_coins[0])
        coin = num_coins[1].upper()

    return num, coin

def list_portfolio(bot, update):
    t_id = update.message.chat.id
    first_name = update.message.chat.first_name 
    last_name = update.message.chat.last_name

    user = get_user(t_id, first_name, last_name)
    print user
    print user.first_name
    print user.last_name
    pf = session.query(Coin).filter(Coin.user == user).all()
    if pf is None:
        message = "{} has no coins in their portfolio".format(user.first_name)
    else:
        message = "<b>{}'s Portfolio</b>".format(user.first_name)
        total_value = 0
        total_change = 0
        for coin in pf:
            cd = config.price_dict[coin.symbol.upper()]
            amount_val = float(cd['price_usd'])*coin.amount
            dollar_change = amount_val*(float(cd['percent_change_24h'])/100)

            total_value += amount_val
            total_change += dollar_change

            message += "\n{} {}: ${:,} (${:,})".format(coin.amount, coin.symbol, amount_val, dollar_change)
        message += "\n\n$ Change over 24h: ${:,}".format(total_change)
        message += "\nTotal Value: <b>${:,}</b>".format(total_value)
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.HTML)

def get_user(t_id, first_name, last_name):
    if session.query(exists().where(User.telegram_id==t_id)).scalar():
        # get user
        user = session.query(User).filter(User.telegram_id==t_id).first()
    else:
        # create a new user
        user = User(telegram_id=t_id, first_name=first_name, last_name=last_name)
        session.add(user)
        session.commit()
        session.flush()
    return user