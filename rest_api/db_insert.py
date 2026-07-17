from database import SessionLocal
from models import User, Wallet, Task, Waren
from datetime import date, datetime


# Datenbanksitzung öffnen
session = SessionLocal()

try:
    # Neuen Benutzer erstellen
    new_user_1 = User(
        vorname="Niko",
        nachname="Busa",
        zimmer_nr=123,
        buchnummer="1232020"
    )
    new_user_2 = User(
        vorname="Hans",
        nachname="Maier",
        zimmer_nr=243,
        buchnummer="1392021"
    )

    new_wallet_1 = Wallet(
        date = date(2026, 4, 1),
        grund = "Buchung",
        old_amount = 10,
        new_amount = 15,
        task_id = 1,
        betrag = 5,
        buchnummer = "1232020"
    )
    new_wallet_2 = Wallet(
        date = date(2026, 1, 1),
        grund = "Buchung",
        old_amount = 10,
        new_amount = 15,
        task_id = 1,
        betrag = 5,
        buchnummer = "1392021"
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

    new_ware_1 = Waren(bezeichnung = "Fleisch", kategorie = "Kühlware", menge = 500, art = "Gramm", preis = 3.99)
    new_ware_2 = Waren(bezeichnung = "Steak", kategorie = "Kühlware", menge = 500, art = "Gramm", preis = 9.99)
    new_ware_3 = Waren(bezeichnung = "Salat", kategorie = "Gemüse", menge = 1, art = "Stück", preis = 3.99)
    new_ware_4 = Waren(bezeichnung = "Orange", kategorie = "Gemüse", menge = 5, art = "Stück", preis = 2.99)
    new_ware_5 = Waren(bezeichnung = "Eisbergsalat", kategorie = "Gemüse", menge = 1, art = "Stück", preis = 1.99)
    new_ware_6 = Waren(bezeichnung = "Pfeffer", kategorie = "Gewütze", menge = 1, art = "Streuer", preis = 3.99)
    new_ware_7 = Waren(bezeichnung = "Paprika", kategorie = "Gewütze", menge = 1, art = "Streuer", preis = 3.99)
    new_ware_8 = Waren(bezeichnung = "Backpulver", kategorie = "Extras", menge = 10, art = "Stück", preis = 3.99)
    new_ware_9 = Waren(bezeichnung = "Hefe", kategorie = "Extras", menge = 5, art = "Stück", preis = 3.99)
    new_ware_10 = Waren(bezeichnung = "Eier", kategorie = "Milchware", menge = 1, art = "Packung", preis = 3.99)

    # Benutzer speichern
    #session.add_all([new_user_1, new_user_2, new_wallet_1, new_wallet_2, new_task])
    #session.add(new_user_1)
    #session.add(new_wallet_1)
    session.add(new_task)
    session.add_all([new_ware_1, new_ware_2, new_ware_3, new_ware_4, new_ware_5, new_ware_6, new_ware_7, new_ware_8, new_ware_9, new_ware_10])

    session.commit()

    print("Benutzer erfolgreich gespeichert.")

except Exception as e:
    session.rollback()
    print(f"Fehler: {e}")

finally:
    session.close()