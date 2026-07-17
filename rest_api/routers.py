# RestService
from models import User, Task, Wallet, Bestellung
from database import get_db
from schema import *
from crud import UserRepository, TaskRepository, WalletRepository, WarenRepository, BestellungRepository
from fastapi import FastAPI, Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session


user_router = APIRouter(prefix="/users", tags=["User"])
wallet_router = APIRouter(prefix="/wallets", tags=["Wallets"])
task_router = APIRouter(prefix="/tasks", tags=["Task"])
waren_router = APIRouter(prefix="/waren", tags=["Waren"])
bestellung_router = APIRouter(prefix="/bestellung", tags=["Bestellung"])

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

@task_router.get("/{task_id}/status_buchung", response_model=TaskUpdateState)
def get_task_status_buchung(task_id: int, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    status = repo.find_status_buchung_tasks(task_id)
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

# -------------
# Waren
# -------------
@waren_router.get("/", response_model=list[WarenRead])
def get_all_waren(db: Session = Depends(get_db)):
    repo = WarenRepository(db)
    return repo.find_all_waren()

@waren_router.get("/waren_task", response_model=list[WarenRead])
def get_waren_task(task_id: int, db: Session = Depends(get_db)):
    repo = WarenRepository(db)
    return repo.find_waren_by_task(task_id)

@waren_router.post("/save", response_model=WarenRead)
def create_new_waren(waren_create: WarenCreate, db: Session = Depends(get_db)):
    repo = WarenRepository(db)
    # Wir übergeben das Pydantic-Schema direkt an das Repository
    return repo.create_waren(waren_create)

@waren_router.put("/{waren_id}/update_waren", response_model=WarenRead)
def update_waren(
        waren_id: int,
        waren_data: WarenUpdate,
        db: Session = Depends(get_db)
):
    repo = TaskRepository(db)
    try:
        updated_waren = repo.update_waren(waren_id, waren_data)
    except Exception as e:
        # Fängt unerwartete DB-Fehler oder Validierungsfehler ab
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Aktualisieren: {str(e)}"
        )
    if not updated_waren:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artikel mit ID {waren_id} wurde nicht gefunden."
        )
    return updated_waren

# -------------
# Bestellung
# -------------
@bestellung_router.get("/", response_model=list[BestellungRead])
def get_all_bestellung(db: Session = Depends(get_db)):
    repo = BestellungRead(db)
    return repo.find_all_bestellung()

@bestellung_router.get("/bestellung_task", response_model=list[BestellungRead])
def get_bestellung_task(bestellung_id: int, db: Session = Depends(get_db)):
    repo = BestellungRead(db)
    return repo.find_bestellung_by_task(bestellung_id)

@bestellung_router.post("/save", response_model=BestellungRead)  # Pfad
def create_new_bestellung(bestellung_create: BestellungCreate, db: Session = Depends(get_db)):
    repo = BestellungRead(db)
    new_bestellung = Bestellung(**bestellung_create.model_dump())
    return repo.create_bestellung(new_bestellung)
