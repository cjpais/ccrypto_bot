from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import config
 
engine = create_engine(config.docker_db)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()
Base.metadata.bind = engine
Base.metadata.create_all(engine)