from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator


#DATABASE_URL =  "mysql+pymysql://root:@localhost:3306/backkoch"
DATABASE_URL =  "sqlite:///b_und_k.db"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autoflush=False,autocommit=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session,None,None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
