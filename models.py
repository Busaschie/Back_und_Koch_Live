from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, Enum, DateTime, func
from datetime import datetime
from sqlalchemy.orm import relationship

class BaseRepr:
    """ generischhe __repr__Methode
        alle Klassen, die von  BaseRepr erben, bekommen automatisch eine
        def __repr__-Methode
    """
    def __repr__(self):
        fields = ", ".join(
            f"{col.name}={getattr(self, col.name)!r}"
            for col in self.__table__.columns
        )
        return f"<{self.__class__.__name__}({fields})>"
#
class Wallet(Base,BaseRepr):
     __tablename__="wallet"
     id = Column(Integer,primary_key=True)
     date = Column(Date)
     grund = Column(String(100))
     old_amount = Column(Integer)
     new_amount = Column(Integer)
     task_id = Column(Integer)
     betrag = Column(Integer)
     buchnummer = Column(String(10))

#
class Admin(Base,BaseRepr):
    __tablename__="admin"
    id = Column(Integer, primary_key=True)
    username = Column(String(20),nullable=False,unique=True)
    password = Column(String(100))

#
class User(Base,BaseRepr):
    __tablename__="user"
    id = Column(Integer, primary_key=True)
    vorname = Column(String(20),nullable=False,unique=True)
    nachname = Column(String(40), nullable=False, unique=True)
    zimmer_nr = Column(Integer)
    buchnummer = Column(String(10))
#
class Task(Base,BaseRepr):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True)
    date = Column(Date, server_default=func.now())
    monat = Column(String(50))
    jahr = Column(Integer)
    shop_date = Column(Date)
    abgabe_date = Column(Date)
    geld_date = Column(Date)
    status_betrag = Column(Enum("OPEN", "DONE"), nullable=False, default="OPEN")
    status_waren = Column(Enum("OPEN", "DONE"), nullable=False, default="OPEN")
    status_buchung = Column(Enum("OPEN", "DONE"), nullable=False, default="OPEN")
#
class Artikel(Base, BaseRepr):
    __tablename__ = "waren"
    id = Column(Integer, primary_key=True)
    bezeichnung = Column(String(250))
    kategorie = Column(String(150))
    menge = Column(Integer)
    art = Column(String(20))
    preis = Column(Integer)

