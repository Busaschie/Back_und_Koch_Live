# app.py
import streamlit as st

# 1. Seiten definieren (Pfade zeigen jetzt in den views-Ordner!)
page_vorgaenge = st.Page(
    "pages/vorgang.py",
    title="📋 Einkäufe & Vorgänge",
    default=True
)

page_user = st.Page(
    "pages/user.py",
    title="👥 Benutzerverwaltung"
)

page_waren = st.Page(
    "pages/waren.py",
    title="👥 Warenverwaltung"
)

page_waren_druck = st.Page(
    "pages/waren_druck.py",
    title="👥 Warenliste drucken"
)
page_einkaufszettel_druck = st.Page(
    "pages/einkaufszellel_druck.py",
    title="👥 Einkaufszettel drucken"
)
page_hausgeld = st.Page(
    "pages/hausgeld_abbuchung_druck.py",
    title="👥 Hausgeld Buchung"
)
page_userkonto = st.Page(
    "pages/userkonto_druck.py",
    title="👥 User Kontostand"
)
# 2. Navigation erstellen und ausführen
pg = st.navigation([page_vorgaenge, page_user, page_waren, page_waren_druck, page_einkaufszettel_druck, page_hausgeld, page_userkonto])
pg.run()