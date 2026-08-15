from sqlalchemy import func
from models import User, Admin, Wallet, Task, Waren, Bestellung
from sqlalchemy.orm import Session
from schema import WarenUpdate, WarenCreate, UserBase
from datetime import date
#from util import hash_password, verify_password

#import bcrypt

'''
# ----------------------
# Admin
# ----------------------
class AdminRepository():
    def __init__(self, session:Session):
        self.session=session
'''
# ----------------------
# Task
# ----------------------
class TaskRepository():
    def __init__(self, session:Session):
        self.session=session

    def find_all_tasks(self)-> list[Task]:
        return self.session.query(Task).order_by(Task.id.desc()).all()

    def find_open_tasks(self)-> list[Task]:
        return self.session.query(Task).filter(Task.status_betrag == "OPEN").all()

    def find_status_betrag_tasks(self, task_id: int) -> Task | None:
        return (
            self.session.query(Task)
            .filter(Task.id == task_id)
            .first()
        )

    def find_status_buchung_tasks(self, task_id: int) -> Task | None:
        return (
            self.session.query(Task)
            .filter(Task.id == task_id)
            .first()
        )

    def update_status_betrag_tasks(self, task_id:int, new_state:str)->Task | None:
        allowed = {"OPEN","DONE"}
        if new_state not in allowed:
            raise ValueError(f"Invalid State, allowed: {allowed}")
        task = self.session.get(Task,task_id)
        if not task:
            return None
        task.status_betrag = new_state
        self.session.commit()
        self.session.refresh(task)
        return task

    def update_status_waren_tasks(self, task_id:int, new_state:str)->Task | None:
        allowed = {"OPEN","DONE"}
        if new_state not in allowed:
            raise ValueError(f"Invalid State, allowed: {allowed}")
        task = self.session.get(Task,task_id)
        if not task:
            return None
        task.status_waren = new_state
        self.session.commit()
        self.session.refresh(task)
        return task

    def update_status_buchung_tasks(self, task_id: int, new_state: str) -> Task | None:
        allowed = {"OPEN", "DONE"}
        if new_state not in allowed:
            raise ValueError(f"Invalid State, allowed: {allowed}")
        task = self.session.get(Task, task_id)
        if not task:
            return None
        task.status_buchung = new_state
        self.session.commit()
        self.session.refresh(task)
        return task

    def find_one_tasks(self, shop_date:date) -> list[Task]:
        #statement = select(Task).where(Task.shop_date == shop_date)
        #result = self.session.execute(statement)
        #return list(result.scalars().all())
        query = (
            self.session.query(Task)
            .filter(Task.shop_date == shop_date)
            #.filter(Task.status == "OPEN")
        )
        return query.all()

    def create_task(self, task:Task) -> Task:
        existing = self.session.query(Task).filter(Task.monat==task.monat, Task.jahr==task.jahr).first()
        if existing:
            raise ValueError("Task existiert bereits!")
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

# ----------------------
# User
# ----------------------
class UserRepository():
    def __init__(self, session:Session):
        self.session = session

    def find_all_users(self)-> list[User]:
        return self.session.query(User).all()

    def create(self, user:User) -> User:
        existing = self.session.query(User).filter(User.buchnummer == user.buchnummer).first()
        if existing:
            raise ValueError("User existiert bereits!")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_user_by_buchnummer(self, buchnummer: str, user_data: UserBase) -> User | None:
        # 1. User suchen
        db_user = self.session.query(User).filter(User.buchnummer == buchnummer).first()
        if not db_user:
            return None
        # 2. Werte übertragen (setzt vorname, nachname, zimmer in der DB)
        update_dict = user_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_user, key, value)
        # 3. Speichern
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def delete_user_and_wallets_by_buchnummer(self, buchnummer: str) -> bool:
        """
        Löscht alle Wallet-Einträge eines Users und danach den User selbst
        basierend auf der Buchnummer.
        Gibt True zurück, wenn der User gelöscht wurde, ansonsten False.
        """
        # 1. Prüfen, ob der User überhaupt existiert
        db_user = self.session.query(User).filter(User.buchnummer == buchnummer).first()
        if not db_user:
            return False
        try:
            # 2. Alle Wallet-Einträge mit dieser Buchnummer löschen
            # (Importiere das Wallet-Modell, falls noch nicht geschehen, z.B. aus deiner models.py)
            self.session.query(Wallet).filter(Wallet.buchnummer == buchnummer).delete(synchronize_session=False)
            # 3. Den User selbst löschen
            self.session.delete(db_user)
            # 4. Änderungen in der DB festschreiben
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e


    def find_all_users_with_latest_balance(self):
        # 1. Subquery: Höchste Wallet-ID je Buchnummer finden (über alle Tasks hinweg)
        sub_stmt = (
            self.session.query(
                Wallet.buchnummer,
                func.max(Wallet.id).label("max_wallet_id")
            )
            .group_by(Wallet.buchnummer)
            .subquery()
        )

        # 2. Main Query: User per LEFT JOIN mit Subquery und Wallet verknüpfen
        results = (
            self.session.query(
                User.id.label("user_id"),
                User.vorname,
                User.nachname,
                User.buchnummer,
                User.zimmer_nr,
                func.coalesce(Wallet.new_amount, 0.0).label("aktueller_kontostand")
            )
            .outerjoin(sub_stmt, User.buchnummer == sub_stmt.c.buchnummer)
            .outerjoin(Wallet, Wallet.id == sub_stmt.c.max_wallet_id)
            .order_by(User.nachname.asc(), User.vorname.asc())
            .all()
        )

        # WICHTIG: Die Rows explizit als Dictionary mappen, damit Pydantic / FastAPI
        # die Schlüssel 'vorname', 'nachname', 'buchnummer' etc. erkennt!
        return [
            {
                "id": row.user_id,
                "vorname": row.vorname,
                "nachname": row.nachname,
                "buchnummer": row.buchnummer,
                "zimmer_nr": row.zimmer_nr,
                "aktueller_kontostand": float(row.aktueller_kontostand),
            }
            for row in results
        ]

# ----------------------
# Wallet
# ----------------------
class WalletRepository():
    def __init__(self, session:Session):
        self.session=session

    def create_wallet(self, id:Wallet) -> Wallet:
        #existing = self.session.query(User).filter(User.buchnummer == user.buchnummer).first()
        #if existing:
        #    raise ValueError("User existiert bereits!")
        self.session.add(id)
        self.session.commit()
        self.session.refresh(id)
        return id

    def find_all_wallets(self)->list[Wallet]:
        return self.session.query(Wallet).all()

    def find_wallet_by_buchnummer(self,buchnummer:str)->list[Wallet]:
        return self.session.query(Wallet).filter(Wallet.buchnummer==buchnummer).all()

    def find_wallet_by_task(self, task_id: int, schritt: str) -> list[Wallet]:
        return (self.session.query(Wallet).filter(Wallet.task_id==task_id, Wallet.schritt==schritt).all())

    def find_wallet_last_task_user(self,buchnummer:str)->Wallet:
        return self.session.query(Wallet).filter(Wallet.buchnummer==buchnummer).order_by(Wallet.id.desc()).first()
        #return self.session.query(Wallet).filter(Wallet.buchnummer==buchnummer).all()


# ----------------------
# Waren
# ----------------------
class WarenRepository():
    def __init__(self, session:Session):
        self.session=session

    def create_waren(self, waren_data: WarenCreate) -> Waren:
        # 1. SQLAlchemy-Objekt aus den Pydantic-Daten erstellen
        db_waren = Waren(**waren_data.model_dump())
        # 2. In die Datenbank einfügen
        self.session.add(db_waren)
        self.session.commit()
        self.session.refresh(db_waren)
        return db_waren

    def find_all_waren(self)->list[Waren]:
        return self.session.query(Waren).all()

    def update_waren(self, waren_id: int, waren_data: WarenUpdate) -> Waren | None:
        # 1. Artikel aus der DB laden (jetzt mit self.session statt self.db)
        db_waren = self.session.query(Waren).filter(Waren.id == waren_id).first()
        if not db_waren:
            return None
        # 2. Werte dynamisch übertragen
        update_dict = waren_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_waren, key, value)
        # 3. Speichern und aktualisieren
        self.session.commit()
        self.session.refresh(db_waren)
        return db_waren

    def delete_ware(self, waren_id: int) -> Waren | None:
        db_waren = self.session.query(Waren).filter(Waren.id == waren_id).first()
        if not db_waren:
            return None
        try:
            self.session.delete(db_waren)
            self.session.commit()
            return db_waren  # Das Objekt im Speicher zurückgeben (OHNE refresh!)
        except Exception:
            self.session.rollback()
            return None

# ----------------------
# Bestellung
# ----------------------
class BestellungRepository():
    def __init__(self, session:Session):
        self.session=session

    def create_bestellung(self, id:Bestellung) -> Bestellung:
        #existing = self.session.query(User).filter(User.buchnummer == user.buchnummer).first()
        #if existing:
        #    raise ValueError("User existiert bereits!")
        self.session.add(id)
        self.session.commit()
        self.session.refresh(id)
        return id

    def find_all_bestellung(self)->list[Bestellung]:
        return self.session.query(Bestellung).all()

    def find_bestellung_by_task(self,task_id:int)->list[Bestellung]:
        return self.session.query(Bestellung).filter(Bestellung.task_id==task_id).all()

# ----------------------
# Tolls
# ----------------------

    '''
    def update_wallet_state(self, todo_id:int, new_state:str)->Wallet | None:
        allowed = {"OPEN","IN_PROGRESS","DONE"}
        if new_state not in allowed:
            raise ValueError(f"Invalid State, allowed: {allowed}")
        wallet = self.session.get(Wallet,todo_id)
        if not wallet:
            return None
        wallet.state = new_state
        self.session.commit()
        self.session.refresh(wallet)
        return wallet

    def new_wallet_by_user(self, user_id: int, wallet: Wallet) -> Wallet:
        user = self.session.get(User, user_id)
        user.wallets.append(wallet)
        self.session.commit()
        self.session.refresh(wallet)
        return wallet

   def find_open_todos_by_user(self,user_id:int)->list[Wallet]:
        return (self.session.query(Wallet).filter(Wallet.user_id == user_id, Wallet.state == "OPEN").all())

    def find_open_wallet_by_user(self, user_id: int) -> list[Wallet]:
        query = (
            self.session.query(Wallet)
            .filter(Wallet.user_id == user_id)
            .filter(Wallet.state == "OPEN")
        )
        return query.all()

    def delete_wallet(self, todo_id:int)-> Wallet | None:
        """ """
        wallet = self.session.get(Wallet,todo_id)
        if wallet is  None:
            return None
        self.session.delete(wallet)
        self.session.commit()
        return wallet

    def delete_all_done_wallet(self,user_id:int)->int:
        wallet = (
            self.session.query(wallet)
            .filter(
                Wallet.user_id == user_id,
                Wallet.state == "DONE"
            )
            .all()
        )
        count = len(wallet)
        for wall in wallet:
            self.session.delete(wall)
        self.session.commit()
        return  count
'''
    '''
        def find_user_by_id(self, id:int)-> User | None:
            return self.session.get(User, id)

        def delete_user(self, user_id:int)-> User | None:
            user = self.session.get(User, user_id)
            if user is None:
                return None
            self.session.delete(user)
            self.session.commit()
            return user

        def find_user_by_credentials(self, username:str, password:str)->User | None:
            #hashed = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
            stored_user = self.session.query(User).filter(User.username == username).first()
            if not stored_user:
                return None
            return  stored_user if verify_password(password, stored_user.password) else None

    '''