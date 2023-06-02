from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATBASE_URL = "postgresql://akkyaqqs:AYGua5atDOWK-5TEKUqDeqB4DPM6bdSv@rajje.db.elephantsql.com/akkyaqqs"

engine = create_engine(
    SQLALCHEMY_DATBASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
