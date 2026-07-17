import streamlit as st
import requests
import pandas as pd
from datetime import date

BASE_URL = "http://localhost:8000"  # uvicorn -> restapi

# Seite auf weites Layout stellen, damit links und rechts genug Platz ist
st.set_page_config(layout="wide")
# Merken, ob wir gerade einen neuen Vorgang erstellen
if "create_mode" not in st.session_state:
    st.session_state.create_mode = False

# ==========================================
# 0. Session State Initialisierung
# ==========================================
# Wir merken uns das aktuell ausgewählte Datum. Standard ist das "2026-07-13"
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()


# ==========================================
# API-Abfragen
# ==========================================
@st.cache_data
def get_api_data_user():
    try:
        response = requests.get(f"{BASE_URL}/users")
        df = pd.DataFrame(response.json())
        return df[['vorname', 'nachname', 'buchnummer']].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der API (User): {e}")
        return pd.DataFrame(columns=['vorname', 'nachname', 'buchnummer'])

df_user_gefiltert = get_api_data_user()


@st.cache_data
def get_api_data_task():
    try:
        response = requests.get(f"{BASE_URL}/tasks")
        df = pd.DataFrame(response.json())
        return df[['shop_date']].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der API (Tasks): {e}")
        return pd.DataFrame(columns=['shop_date'])

df_task_gefiltert = get_api_data_task()


# Cache wird hier basierend auf dem 'shop_date' gesteuert
@st.cache_data
def get_api_one_task(shop_date: str):
    try:
        params = {"shop_date": shop_date}
        response = requests.get(f"{BASE_URL}/tasks/one_task", params=params)

        # Sicherstellen, dass die API 200 OK geliefert hat
        if response.status_code != 200:
            st.error(f"API-Fehler ({response.status_code}): {response.text}")
            return pd.DataFrame(columns=['id', 'monat', 'jahr', 'shop_date', 'abgabe_date', 'geld_date'])

        data = response.json()

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()

        erwartete_spalten = ['id', 'monat', 'jahr', 'shop_date', 'abgabe_date', 'geld_date']
        vorhandene_spalten = [col for col in erwartete_spalten if col in df.columns]
        return df[vorhandene_spalten].copy()

    except Exception as e:
        st.error(f"Fehler beim Laden der Detail-API: {e}")
        return pd.DataFrame(columns=['id', 'monat', 'jahr', 'shop_date', 'abgabe_date', 'geld_date'])


# ==========================================
# 1. NAVIGATION (Ganz oben über die volle Breite)
# ==========================================
with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_spacer = st.columns([1, 1, 1, 7])
    with nav_col1:
        st.link_button("Vorgänge", "http://localhost:8501/app.py", width='stretch')
    with nav_col2:
        st.link_button("Konten", "https://deine-website.de/dashboard", width='stretch')
    with nav_col3:
        st.link_button("Waren", "https://deine-website.de/settings", width='stretch')
st.write("---")  # Trennlinie

# ==========================================
# MAIN LAYOUT (Aufteilung in Links und Rechts)
# ==========================================
col_links, col_rechts = st.columns([2, 8])

# --- LINKE SEITE: Container für Einkäufe ---
with col_links:
    with st.container(border=True):
        st.subheader("📋 Einkäufe")

        # Schaltet den Erstellungsmodus an und erzwingt ein Update der UI
        if st.button("⚙️ Neuer Vorgang", width='stretch'):
            st.session_state.create_mode = True
            st.rerun()


        # INTERAKTIVE TABELLE: Zeilenauswahl aktivieren
        event = st.dataframe(
            df_task_gefiltert,
            hide_index=True,
            width='stretch',
            on_select="rerun",  # Triggert einen App-Rerun bei Klick
            selection_mode="single-row"  # Erlaubt das Auswählen genau einer Zeile
        )

        # Ausgelesene Zeile im Session State speichern
        selected_rows = event.get("selection", {}).get("rows", [])
        if selected_rows:
            selected_idx = selected_rows[0]
            # Setze das Datum im Session-State auf das angeklickte Datum
            st.session_state.selected_date = str(df_task_gefiltert.iloc[selected_idx]['shop_date'])

# Lade die Detail-Daten für das aktuell ausgewählte Datum
df_one_task_gefiltert = get_api_one_task(shop_date=st.session_state.selected_date)
st.write("df_one_task_gefiltert", df_one_task_gefiltert)

# --- RECHTE SEITE: Die 4 aufklappbaren Übersichten ---
with col_rechts:
    with st.container(border=True):
        st.subheader(f"Bestellvorgang (Ausgewählt: {st.session_state.selected_date})")

        # Expander 1
        with st.expander("Schritt 1: Vorgangs-Informationen festlegen", expanded=True):

            if st.session_state.create_mode:
                st.markdown("### ➕ Neuen Vorgang anlegen")

                # Wir nutzen st.form, damit die API erst beim Klick auf Speichern aufgerufen wird
                with st.form("new_task_form", clear_on_submit=True):

                    # Eingabefelder passend zu deiner Task-Struktur
                    col_y, col_m = st.columns(2)
                    with col_y:
                        jahr = st.number_input("Jahr", min_value=2020, max_value=2100, value=2026)
                    with col_m:
                        monat = st.selectbox(
                            "Monat",
                            options=["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
                        )

                    shop_date = st.date_input("Shop-Datum (shop_date)")
                    abgabe_date = st.date_input("Abgabetermin (abgabe_date)")
                    geld_date = st.date_input("Geld erhalten am (geld_date)")

                    # Formular-Aktionstasten
                    col_btn_save, col_btn_cancel = st.columns([1, 1])

                    with col_btn_save:
                        submitted = st.form_submit_button("💾 Speichern", width='stretch')
                    with col_btn_cancel:
                        canceled = st.form_submit_button("❌ Abbrechen", width='stretch')

                # Logik beim Abbrechen
                if canceled:
                    st.session_state.create_mode = False
                    st.rerun()

                # Logik beim Speichern
                if submitted:
                    # JSON-Payload für deine FastAPI @task_router.post("/") Route vorbereiten
                    payload = {
                        "date": str(shop_date),  # Das geforderte "date" Feld hinzugefügt
                        "monat": str(monat),  # Als String konvertiert (Fehlerbehebung 2)
                        "jahr": str(jahr),  # Zur Sicherheit ebenfalls als String
                        "shop_date": str(shop_date),
                        "abgabe_date": str(abgabe_date),
                        "geld_date": str(geld_date)
                    }

                    try:
                        # POST-Request an deine API senden
                        response = requests.post(f"{BASE_URL}/tasks/save/", json=payload)

                        if response.status_code in [200, 201]:
                            st.success("🎉 Vorgang erfolgreich in der Datenbank gespeichert!")
                            # Cache leeren, damit die linke Liste das neue Datum sofort anzeigt
                            st.cache_data.clear()

                            # Setze das neu erstellte Datum als aktiv
                            st.session_state.selected_date = str(shop_date)
                            st.session_state.create_mode = False
                            st.rerun()
                        else:
                            st.error(f"Fehler beim Speichern ({response.status_code}): {response.text}")
                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")

            else:
                # Normaler Modus: Nur das schreibgeschützte DataFrame anzeigen
                st.dataframe(df_one_task_gefiltert, hide_index=True, width='stretch', column_config={"id": None})

        # Expander 2
        with st.expander("Schritt 2: Sammelbuchung"):
            # Initialer Zustand der Spalte "Betrag"
            df_mit_status = df_user_gefiltert.copy()
            df_mit_status["Betrag"] = "Bitte wählen..."

            # Der Data Editor gibt uns die editierten Zeilen zurück
            df_editiert = st.data_editor(
                df_mit_status,
                column_config={
                    "Betrag": st.column_config.SelectboxColumn(
                        "Betrag",
                        help="Wähle einen Betrag für den Nutzer",
                        width="medium",
                        options=["Bitte wählen...", "0", "7", "13", "15", "25"],
                        required=True,
                    )
                },
                disabled=["vorname", "nachname", 'buchnummer'],
                hide_index=True,
                width='stretch',
                key="sammelbuchung"
            )

            # Speicher-Button anstelle des Link-Buttons
            if st.button("💾 Beträge in Wallet speichern", type="primary", key="save_wallet_btn"):
                # Nur Zeilen filtern, die einen gültigen Betrag gewählt haben (nicht "Bitte wählen..." oder "0")
                gueltige_buchungen = df_editiert[
                    (df_editiert["Betrag"] != "Bitte wählen...") &
                    (df_editiert["Betrag"] != "0")
                    ]

                if gueltige_buchungen.empty:
                    st.warning("Keine gültigen Beträge zum Speichern ausgewählt.")
                elif df_one_task_gefiltert.empty:
                    st.error("Kein aktiver Vorgang ausgewählt. Die task_id konnte nicht ermittelt werden.")
                else:
                    try:
                        aktuelle_task_id = int(df_one_task_gefiltert.iloc[0]["id"])
                        st.write("task_id", aktuelle_task_id)
                    except Exception as e:
                        st.error(f"Fehler: Die ID des aktuellen Vorgangs konnte nicht gelesen werden. ({e})")
                        st.stop()
                    erfolgreich = 0
                    fehler = 0

                    # Wir gehen Zeile für Zeile durch
                    for index, row in gueltige_buchungen.iterrows():
                        buchnummer = row["buchnummer"]
                        betrag = int(row["Betrag"])
                        st.write("betrag", betrag)
                        st.write("buchnummer", buchnummer)

                        # 1. Letzten Wallet-Eintrag des Users holen, um "old_amount" zu bestimmen
                        old_amount = 0.0
                        st.write("old_amount", old_amount)
                        try:
                            # Wir nehmen an, dass deine API eine Route hat, um das aktuelle Guthaben/letzten Eintrag zu holen
                            # Falls nicht vorhanden, musst du diese API-Route ggf. anpassen
                            wallet_response = requests.get(f"{BASE_URL}/wallets/last?buchnummer={buchnummer}")
                            st.write("wallet_response", BASE_URL, buchnummer, wallet_response)
                            if wallet_response.status_code == 200:
                                last_entry = wallet_response.json()
                                st.write(last_entry)
                                # Hole den Wert "new_amount" des letzten Eintrags
                                old_amount = int(last_entry.get("new_amount", 0))
                                st.write("old_amount", old_amount)
                        except Exception as e:
                            # Falls kein Eintrag existiert oder API fehlschlägt, starten wir bei 0
                            old_amount = 0.0

                        # 2. Berechne den neuen Stand
                        new_amount = old_amount + betrag
                        st.write("new_amount plus betrag", new_amount)

                        # 3. Payload für den API-Eintrag zusammenbauen
                        grund = "Sammelbuchung von " + str(date.today())
                        wallet_payload = {
                            "buchnummer": buchnummer,
                            "betrag": betrag,
                            "old_amount": old_amount,  # optional, falls deine DB das speichert
                            "new_amount": new_amount,
                            "task_id": aktuelle_task_id,
                            "grund": grund,
                            "date": str(date.today())  # Oder ein anderes gewünschtes Datum
                        }
                        st.write(wallet_payload)

                        # 4. Eintrag in der DB-Wallet speichern via POST
                        try:
                            post_response = requests.post(f"{BASE_URL}/wallets/save", json=wallet_payload)
                            st.write("post_response", post_response)
                            if post_response.status_code in [200, 201]:
                                erfolgreich += 1
                            else:
                                fehler += 1
                                st.error(f"Fehler bei Buchnummer {buchnummer}: {post_response.text}")
                        except Exception as e:
                            fehler += 1
                            st.error(f"Verbindungsfehler bei Buchnummer {buchnummer}: {e}")

                    # Statusmeldung ausgeben
                    if erfolgreich > 0:
                        st.success(f"🎉 {erfolgreich} Buchung(en) erfolgreich in der Wallet gespeichert!")
                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Buchung(en) konnten nicht gespeichert werden.")

                    # Optional: Seite neu laden, um Editor zurückzusetzen
                    if fehler == 0:
                        st.rerun()

        # Expander 3
        with st.expander("Schritt 3: Einkaufsliste"):
            st.dataframe(df_user_gefiltert, hide_index=True, width='stretch')

        # Expander 4
        with st.expander("Schritt 4: Abbuchung"):
            df_mit_status = df_user_gefiltert.copy()
            df_mit_status["Betrag"] = "Bitte wählen..."

            df_editiert = st.data_editor(
                df_mit_status,
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        help="Wähle einen Status für den Nutzer",
                        width="medium",
                        options=["0", "7", "13", "15", "25"],
                        required=True,
                    )
                },
                disabled=["vorname", "nachname"],
                hide_index=True,
                width='stretch',
                key="abbuchung"
            )