FROM python:2.7

WORKDIR /crypto

RUN pip install python_telegram_bot matplotlib sqlalchemy
ADD . /crypto 

CMD ["python", "bot.py"]
