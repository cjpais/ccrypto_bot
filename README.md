# CJ's Crypto Bot

CJ's Crypto Bot is a Telegram chat bot that will give users various bits of information about cryptocurrencies. This bot heavily relies on the API provided by coinmarketcap.com and from cryptocompare to generate candlestick charts. This is built off of Python 2.7.

### Developing

To run this bot a few things are necessary. First you need to get your own Telegram API key. To do this message Telegram's BotFather. Once you have the key for your bot create a .py file called keys.py. In this file you should have something like `bot_key = "KEY GOES HERE"`. This key is used to run your bot.

You also will need to install requirements.txt. This can be done through `pip install -r requirements.txt`. This will install all of the required python libraries. You should now be able to run the bot with `python crypto_bot.py` and begin messaging it. See usage below for help with commands.

### Usage