from sqlalchemy import Column, Integer, String, create_engine, exists
from sqlalchemy.orm import relationship

from db_base import Base, Session, engine, session
import config

# engine = create_engine(config.build_db)
Base.metadata.bind = engine

bio_helptext = ""

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    wallets = relationship("Wallet", back_populates="user")
    
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=True)
    bio = Column(String(512), nullable=True)

    def __init__(self, t_id, fn, ln, un):
        self.telegram_id    = t_id
        self.first_name     = fn
        self.last_name      = ln
        self.username       = un
        self.bio            = None

    def set_bio(self, s):
        self.bio = s

    def get_bio(self):
        if not self.bio:
            return "{} has no bio".format(self.first_name)
        return self.bio

    def get_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def get_first_name(self):
        return self.first_name

    def get_last_name(self):
        return self.last_name

def get_or_create_user(user_data):
    t_id = user_data.id
    first_name = user_data.first_name
    last_name = user_data.last_name
    try:
        username = user_data.username
    except KeyError:
        username = None

    if session.query(exists().where(User.telegram_id==t_id)).scalar():
        # get user
        user = session.query(User).filter(User.telegram_id==t_id).first()
    else:
        # create a new user
        user = User(t_id, first_name, last_name, username)
        session.add(user)
        session.commit()
        session.flush()
    return user

def bio(bot, update):
    message = update.message.text.split()

    if len(message) == 1:
        update.message.reply_text(bio_helptext)
        return

    if message[1].lower() == 'add':
        # go get the user and then set their bio to what the following text is.
        # Do this with a .join(' ') from the list
        pass
    else:
        # the user has queried someone elses bio
        for entity in update.message.parse_entities().iterkeys():
            if entity.user is not None:
                pass #TODO
            