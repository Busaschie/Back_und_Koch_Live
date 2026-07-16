# RestService
from models import User, Task, Wallet, Admin
from database import get_db
from schema import *
from crud import UserRepository, TaskRepository, WalletRepository
from fastapi import FastAPI, Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

import datetime

user_router = APIRouter(prefix="/users")
wallet_router = APIRouter(prefix="/wallets")
task_router = APIRouter(prefix="/tasks")

#-------------
# User
#-------------
@user_router.get("/", response_model = list[UserRead])
def get_all_user(db:Session = Depends(get_db)):
    repo = UserRepository(db)
    return repo.find_all_users()

@user_router.post("/create", response_model = UserRead)
def create_user(user_create:UserCreate, db:Session = Depends(get_db)):
    repo = UserRepository(db)
    new_user = User(**user_create.model_dump()) # konverieren UserCreate to User (DB) / model_dump() -> dict
    #new_user = User(vorname = user_create.vorname, nachname = user_create.nachname, zimmer_nr = user_create.zimmer_nr, buchnummer = user_create.buchnummer)
    return repo.create(new_user)

'''@user_router.post("/authenticate", response_model = UserRead)
def authenticate_user(user_login:UserLogin, db: Session = Depends(get_db)):
    print("user_login", user_login)
    repo = UserRepository(db)
    user = repo.find_user_by_credentials(user_login.username, user_login.password)
    if not user:
        raise HTTPException(status_code = 401, detail = "Invalid credentials")
    return user

'''
#-------------
# Task
#-------------
@task_router.get("/", response_model = list[TaskRead])
def get_all_task(db:Session = Depends(get_db)):
    repo = TaskRepository(db)
    return repo.find_all_tasks()

@task_router.get("/one_task", response_model = list[TaskRead])
def get_one_task(shop_date:date, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    return repo.find_one_tasks(shop_date)

@task_router.get("/{task_id}/status_betrag", response_model=TaskUpdateState)
def get_task_status_betrag(task_id: int, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    status = repo.find_status_betrag_tasks(task_id)
    if not status:
        raise HTTPException(
            detail=f"Task mit der ID {task_id} wurde nicht gefunden."
        )
    return status

@task_router.put("/{task_id}/update_status_betrag", response_model=TaskUpdateState)
def update_status_betrag_task(task_id: int, new_state: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    try:
        updated_task = repo.update_status_betrag_tasks(task_id, new_state)
    except ValueError as e:
        raise HTTPException(
            detail=str(e)
        )
    if not updated_task:
        raise HTTPException(
            detail=f"Task mit ID {task_id} wurde nicht gefunden."
        )
    return updated_task

@task_router.put("/{task_id}/update_status_waren", response_model=TaskUpdateState)
def update_status_waren_task(task_id: int, new_state: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    try:
        updated_task = repo.update_status_waren_tasks(task_id, new_state)
    except ValueError as e:
        raise HTTPException(
            detail=str(e)
        )
    if not updated_task:
        raise HTTPException(
            detail=f"Task mit ID {task_id} wurde nicht gefunden."
        )
    return updated_task

@task_router.put("/{task_id}/update_status_buchung", response_model=TaskUpdateState)
def update_status_buchung_task(task_id: int, new_state: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    try:
        updated_task = repo.update_status_buchung_tasks(task_id, new_state)
    except ValueError as e:
        raise HTTPException(
            detail=str(e)
        )
    if not updated_task:
        raise HTTPException(
            detail=f"Task mit ID {task_id} wurde nicht gefunden."
        )
    return updated_task

@task_router.get("/open", response_model = list[TaskRead])
def get_open_task(db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    return repo.find_open_tasks()

#@task_router.post("/", response_model = TaskRead) # Query
@task_router.post("/save", response_model = TaskRead) # Pfad
def create_new_task(task_create:TaskCreate, db:Session = Depends(get_db)):
    repo = TaskRepository(db)
    new_task = Task(**task_create.model_dump()) # konverieren TaskCreate to Task (DB) / model_dump() -> dict
    #new_task = Task(date = task_create.date, monat = task_create.monat, jahr = task_create.jahr, shop_date = task_create.shop_date, abgabe_date = task_create.abgabe_date, geld_date = task_create.geld_date, status = TaskStatus.OPEN)
    return repo.create_task(new_task)

'''

@task_router.get("/{user_id}/todos2", response_model = list[TodoRead])
def get_all_open_todo_by_userid(user_id:int, db:Session = Depends(get_db)):
    repo = TodoRepository(db)
    return repo.find_open_todos_by_user(user_id)
'''

#-------------
# Wallet
#-------------
@wallet_router.get("/", response_model = list[WalletRead])
def get_all_wallet(db:Session = Depends(get_db)):
    repo = WalletRepository(db)
    return repo.find_all_wallets()

@wallet_router.get("/wallet_user", response_model = list[WalletRead])
def get_wallet_buchnummer(buchnummer:str, db: Session = Depends(get_db)):
    repo = WalletRepository(db)
    return repo.find_wallet_by_buchnummer(buchnummer)

@wallet_router.get("/wallet_task", response_model = list[WalletRead])
def get_wallet_task(task_id:int, db: Session = Depends(get_db)):
    repo = WalletRepository(db)
    return repo.find_wallet_by_task(task_id)

@wallet_router.get("/last", response_model = WalletRead)
def get_wallet_last_task(buchnummer:str, db: Session = Depends(get_db)):
    repo = WalletRepository(db)
    return repo.find_wallet_last_task_user(buchnummer)

@wallet_router.post("/save", response_model = WalletRead) # Pfad
def create_new_wallet(wallet_create:WalletCreate, db:Session = Depends(get_db)):
    repo = WalletRepository(db)
    new_wallet = Wallet(**wallet_create.model_dump()) # konverieren TaskCreate to Task (DB) / model_dump() -> dict
    return repo.create_wallet(new_wallet)

