from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
 
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String(250), nullable=False)
    last_name = Column(String(250), nullable=False)
 
class Coin(Base):
    __tablename__ = 'coins'

    id = Column(Integer, primary_key=True)
    # name = Column(String(20))
    symbol = Column(String(5))
    amount = Column(Float)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

engine = create_engine('sqlite:///db/cryptobot.db')
 
Base.metadata.create_all(engine)