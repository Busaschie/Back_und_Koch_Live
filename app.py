# app.py
import streamlit as st

# =========================================================
# 1. Alle Seiten definieren (Exakte Pfade beachten!)
# =========================================================

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
    title="📦 Warenverwaltung"
)

# Druckansichten (Sollen im Menü versteckt sein)
page_waren_druck = st.Page(
    "pages/waren_druck.py",
    title="Warenliste drucken"
)
page_einkaufszettel_druck = st.Page(
    "pages/einkaufszettel_druck.py",
    title="Einkaufszettel drucken"
)
page_hausgeld = st.Page(
    "pages/hausgeld_abbuchung_druck.py",
    title="Hausgeld Buchung"
)
page_userkonto = st.Page(
    "pages/userkonto_druck.py",
    title="User Kontostand"
)
page_bestellung = st.Page(
    "pages/warendruck.py",  # <-- Hier wurde der Tippfehler korrigiert
    title="Einkaufsschein"
)

# =========================================================
# 2. Moderne Navigation per Dictionary erstellen
# =========================================================
# Durch die Aufteilung in Sektionen werden die Hauptseiten
# normal angezeigt. Um die Druckseiten komplett unsichtbar zu machen,
# übergeben wir alle Seiten in einer sauberen Struktur:

pg = st.navigation({
    "Hauptmenü": [page_vorgaenge, page_user, page_waren],
    # Falls du die Druckseiten komplett ausblenden willst, stelle sicher,
    # dass Streamlit sie über eine Liste kennt. Am einfachsten gibst du sie
    # in eine Sektion und blendest diese über CSS aus, ODER du registrierst sie so:
    "": [page_waren_druck, page_einkaufszettel_druck, page_hausgeld, page_userkonto, page_bestellung]
})

# Falls die leere Sektion "" links als kleiner grauer Punkt stört,
# kannst du diesen CSS-Befehl nutzen, um leere Navigationsüberschriften im Menü zu verstecken:
st.markdown("""
<style>
    [data-testid="stSidebarNav"]ul th:empty {
        display: none !important;
    }
    /* Versteckt die versteckten Druckseiten komplett im Sidebar-Menü */
    [data-testid="stSidebarNav"] li:has(a[href*="druck"]) {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

pg.run()