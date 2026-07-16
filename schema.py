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
    new_amount:float
    betrag:float
    #user_id:UserRead.id
    #task_id:TaskRead.id
    buchnummer:str
    task_id:int

class WalletRead(WalletBase):
    id:int

class WalletCreate(WalletBase):
    pass

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
    shop_date:date
    abgabe_date:date
    geld_date:date

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
    vorname:str
    nachname:str
    zimmer_nr:int | None = None
    buchnummer:str | None = None

class UserRead(UserBase):
    id:int
    #WalletBase:list[WalletRead]

class UserCreate(UserBase):
    pass

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
    menge:int
    preis:float
    task_id:int

class BestellungRead(BestellungBase):
    id:int

class BestellungCreate(BestellungBase):
    pass
