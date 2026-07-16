from database import SessionLocal
from models import User, Wallet, Task
from datetime import date, datetime


# Datenbanksitzung öffnen
session = SessionLocal()

try:
    # Neuen Benutzer erstellen
    new_user_1 = User(
        vorname="Niko",
        nachname="Busa",
        zimmer_nr=123,
        buchnummer="123/2020"
    )
    new_user_2 = User(
        vorname="Hans",
        nachname="Maier",
        zimmer_nr=243,
        buchnummer="139/2021"
    )

    new_wallet_1 = Wallet(
        date = date(2026, 4, 1),
        grund = "Buchung",
        old_amount = 10,
        new_amount = 15,
        task_id = 1,
        betrag = 5,
        buchnummer = "123/2020"
    )
    new_wallet_2 = Wallet(
        date = date(2026, 1, 1),
        grund = "Buchung",
        old_amount = 10,
        new_amount = 15,
        task_id = 1,
        betrag = 5,
        buchnummer = "139/2021"
    )

    new_task = Task(
        date = datetime.now(),
        monat = "April",
        jahr = 2026,
        shop_date = date(2026, 1, 23),
        abgabe_date = date(2026, 1, 11),
        geld_date = date(2026, 1, 1),
        status_betrag = "OPEN",
        status_waren = "OPEN",
        status_buchung = "OPEN"
    )
    # Benutzer speichern
    session.add_all([new_user_1, new_user_2, new_wallet_1, new_wallet_2, new_task])
    #session.add(new_user_1)
    #session.add(new_wallet_1)
    #session.add(new_task)
    session.commit()

    print("Benutzer erfolgreich gespeichert.")

except Exception as e:
    session.rollback()
    print(f"Fehler: {e}")

finally:
    session.close()