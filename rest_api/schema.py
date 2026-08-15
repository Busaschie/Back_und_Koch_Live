from pydantic import BaseModel, Field
#from sqlalchemy import Date, Text
from enum import Enum
from datetime import date
from typing import Optional

#-----------------------------------------------
# Wallet
#-----------------------------------------------
class WalletBase(BaseModel):
    date:date
    grund:str | None = None
    old_amount:float
    betrag:float
    new_amount:float
    buchnummer:str

class WalletRead(WalletBase):
    id:int
    task_id:int
    schritt:str | None = None

class WalletCreate(WalletBase):
    task_id: int
    schritt: str | None = None

class WalletBaseUser(WalletBase):
    id:int

#-----------------------------------------------
# Task
#-----------------------------------------------
class TaskStatus(str,Enum):
    OPEN = "OPEN"
    DONE = "DONE"

class TaskBase(BaseModel):
    date:date
    monat:str | None = None
    jahr:int | None = None
    geld_date:date
    abgabe_date:date
    shop_date:date


class TaskRead(TaskBase):
    id:int

class TaskCreate(TaskBase):
    pass

class TaskUpdateState(TaskRead):
    status_betrag: TaskStatus = TaskStatus.OPEN
    status_waren: TaskStatus = TaskStatus.OPEN
    status_buchung: TaskStatus = TaskStatus.OPEN

#-----------------------------------------------
# User
#-----------------------------------------------
class UserBase(BaseModel):
    vorname:str | None = None
    nachname:str | None = None
    zimmer_nr:int | None = None
    buchnummer:str | None = None

class UserRead(UserBase):
    id:int
    #WalletBase:list[WalletRead]

class UserCreate(UserBase):
    pass

class UserKontostandRead(BaseModel):
    id: int
    vorname: str
    nachname: str
    buchnummer: str
    zimmer_nr: int
    aktueller_kontostand: float

    class Config:
        from_attributes = True

#-----------------------------------------------
# Waren
#-----------------------------------------------
# Schema für die eingehenden Update-Daten
class WarenCreate(BaseModel):
    bezeichnung: Optional[str] = None
    kategorie: Optional[str] = None
    menge: int
    art: Optional[str] = None
    preis: float

class WarenUpdate(BaseModel):
    bezeichnung: Optional[str] = None
    kategorie: Optional[str] = None
    menge: int
    art: Optional[str] = None
    preis: float

# Schema für die Antwort (Response)
class WarenRead(BaseModel):
    id: int
    bezeichnung: Optional[str]
    kategorie: Optional[str]
    menge: int
    art: Optional[str]
    preis: float

    class Config:
        from_attributes = True

#-----------------------------------------------
# Bestellung
#-----------------------------------------------
class BestellungBase(BaseModel):
    bezeichnung:str | None = None
    bestellmenge:int
    preis:float
    gesamt_preis:float
    art: Optional[str]
    menge: int
    task_id:int

class BestellungRead(BestellungBase):
    id:int

class BestellungCreate(BestellungBase):
    pass
