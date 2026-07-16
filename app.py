from datetime import date
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"  # uvicorn -> restapi

# Seite auf weites Layout stellen, damit links und rechts genug Platz ist
st.set_page_config(layout="wide")

# Merken, ob wir gerade einen neuen Vorgang erstellen
if "create_mode" not in st.session_state:
    st.session_state.create_mode = False

# ==========================================
# 0. Session State Initialisierung
# ==========================================
# Wir merken uns das aktuell ausgewählte Datum. Standard ist das heutige Datum.
if "selected_date" not in st.session_state:
    st.session_state.selected_date = str(date.today())

# NEU: Speichert den Status "gespeichert" pro Datum, um den "Date-Switch"-Bug zu verhindern
if "gespeicherte_schritte" not in st.session_state:
    st.session_state.gespeicherte_schritte = {}


# ==========================================
# API-Abfragen
# ==========================================
@st.cache_data
def get_api_data_user():
    try:
        response = requests.get(f"{BASE_URL}/users")
        df = pd.DataFrame(response.json())
        return df[["vorname", "nachname", "buchnummer"]].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der API (User): {e}")
        return pd.DataFrame(columns=["vorname", "nachname", "buchnummer"])


df_user_gefiltert = get_api_data_user()


@st.cache_data
def get_api_data_task():
    try:
        response = requests.get(f"{BASE_URL}/tasks")
        df = pd.DataFrame(response.json())
        return df[["shop_date"]].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der API (Tasks): {e}")
        return pd.DataFrame(columns=["shop_date"])


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
            return pd.DataFrame(
                columns=[
                    "id",
                    "monat",
                    "jahr",
                    "shop_date",
                    "abgabe_date",
                    "geld_date",
                ]
            )

        data = response.json()

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()

        erwartete_spalten = [
            "id",
            "monat",
            "jahr",
            "shop_date",
            "abgabe_date",
            "geld_date",
        ]
        vorhandene_spalten = [
            col for col in erwartete_spalten if col in df.columns
        ]
        return df[vorhandene_spalten].copy()

    except Exception as e:
        st.error(f"Fehler beim Laden der Detail-API: {e}")
        return pd.DataFrame(
            columns=["id", "monat", "jahr", "shop_date", "abgabe_date", "geld_date"]
        )


# ==========================================
# 1. NAVIGATION (Ganz oben über die volle Breite)
# ==========================================
with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_spacer = st.columns([1, 1, 1, 7])
    with nav_col1:
        st.link_button("Vorgänge", "http://localhost:8501/app.py", width="stretch")
    with nav_col2:
        st.link_button(
            "Konten", "https://deine-website.de/dashboard", width="stretch"
        )
    with nav_col3:
        st.link_button("Waren", "https://deine-website.de/settings", width="stretch")
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
        if st.button("⚙️ Neuer Vorgang", width="stretch"):
            st.session_state.create_mode = True
            st.rerun()

        # INTERAKTIVE TABELLE: Zeilenauswahl aktivieren
        event = st.dataframe(
            df_task_gefiltert,
            hide_index=True,
            width="stretch",
            on_select="rerun",  # Triggert einen App-Rerun bei Klick
            selection_mode="single-row",  # Erlaubt das Auswählen genau einer Zeile
        )

        # Ausgelesene Zeile im Session State speichern
        selected_rows = event.get("selection", {}).get("rows", [])
        if selected_rows:
            selected_idx = selected_rows[0]
            # Setze das Datum im Session-State auf das angeklickte Datum
            st.session_state.selected_date = str(
                df_task_gefiltert.iloc[selected_idx]["shop_date"]
            )

# Lade die Detail-Daten für das aktuell ausgewählte Datum
df_one_task_gefiltert = get_api_one_task(shop_date=st.session_state.selected_date)

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
                        jahr = st.number_input(
                            "Jahr", min_value=2020, max_value=2100, value=2026
                        )
                    with col_m:
                        monat = st.selectbox(
                            "Monat",
                            options=[
                                "Januar",
                                "Februar",
                                "März",
                                "April",
                                "Mai",
                                "Juni",
                                "Juli",
                                "August",
                                "September",
                                "Oktober",
                                "November",
                                "Dezember",
                            ],
                        )

                    shop_date = st.date_input("Shop-Datum (shop_date)")
                    abgabe_date = st.date_input("Abgabetermin (abgabe_date)")
                    geld_date = st.date_input("Geld erhalten am (geld_date)")

                    # Formular-Aktionstasten
                    col_btn_save, col_btn_cancel = st.columns([1, 1])

                    with col_btn_save:
                        submitted = st.form_submit_button(
                            "💾 Speichern", width="stretch"
                        )
                    with col_btn_cancel:
                        canceled = st.form_submit_button(
                            "❌ Abbrechen", width="stretch"
                        )

                # Logik beim Abbrechen
                if canceled:
                    st.session_state.create_mode = False
                    st.rerun()

                # Logik beim Speichern
                if submitted:
                    # JSON-Payload für deine FastAPI @task_router.post("/") Route vorbereiten
                    payload = {
                        "date": str(shop_date),
                        "monat": str(monat),
                        "jahr": str(jahr),
                        "shop_date": str(shop_date),
                        "abgabe_date": str(abgabe_date),
                        "geld_date": str(geld_date),
                    }

                    try:
                        # POST-Request an deine API senden
                        response = requests.post(
                            f"{BASE_URL}/tasks/save/", json=payload
                        )

                        if response.status_code in [200, 201]:
                            st.success(
                                "🎉 Vorgang erfolgreich in der Datenbank gespeichert!"
                            )
                            # Cache leeren, damit die linke Liste das neue Datum sofort anzeigt
                            st.cache_data.clear()

                            # Setze das neu erstellte Datum als aktiv
                            st.session_state.selected_date = str(shop_date)
                            st.session_state.create_mode = False
                            st.rerun()
                        else:
                            st.error(
                                f"Fehler beim Speichern ({response.status_code}): {response.text}"
                            )
                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")

            else:
                # Normaler Modus: Nur das schreibgeschützte DataFrame anzeigen
                st.dataframe(
                    df_one_task_gefiltert,
                    hide_index=True,
                    width="stretch",
                    column_config={"id": None},
                )

        # Expander 2
        with st.expander("Schritt 2: Sammelbuchung"):
            aktives_datum = st.session_state.selected_date

            # Holt den Speicher-Status für das aktuell ausgewählte Datum
            ist_gespeichert = st.session_state.gespeicherte_schritte.get(
                aktives_datum, False
            )

            # Kopie der User-Daten erstellen
            df_mit_status = df_user_gefiltert.copy()

            # Daten-Vorbereitung je nach Speicher-Status
            if ist_gespeichert:
                # WENN BEREITS GESPEICHERT: Wir holen die eingegebenen Einzelbeträge aus der Wallet DB
                aktuelle_betraege = []
                for _, row in df_mit_status.iterrows():
                    buchnummer = row["buchnummer"]
                    try:
                        wallet_response = requests.get(
                            f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5
                        )
                        if wallet_response.status_code == 200:
                            last_entry = wallet_response.json()
                            # ÄNDERUNG: Wir holen "betrag" (den eingegebenen Buchungsbetrag) statt "new_amount"
                            aktuelle_betraege.append(
                                str(last_entry.get("betrag", "0"))
                            )
                        else:
                            aktuelle_betraege.append("0")
                    except:
                        aktuelle_betraege.append("0")

                df_mit_status["betrag"] = aktuelle_betraege
                # Gesperrte Spalten, wenn bereits gespeichert
                disabled_spalten = ["vorname", "nachname", "buchnummer", "betrag"]
                button_deaktiviert = True
                button_text = "🔒 Beträge erfolgreich in Wallet gespeichert"
            else:
                # WENN NOCH NICHT GESPEICHERT: Normaler Auswahl-Modus
                df_mit_status["betrag"] = "Bitte wählen..."
                disabled_spalten = ["vorname", "nachname", "buchnummer"]
                button_deaktiviert = False
                button_text = "💾 Beträge in Wallet speichern"

            # 1. Dynamische Spaltenkonfiguration vorbereiten
            if ist_gespeichert:
                # Nach dem Speichern: Reine Textanzeige für den eingegebenen Betrag (ohne Selectbox-Pfeil)
                spalten_konfiguration = {
                    "betrag": st.column_config.TextColumn(
                        "Betrag",
                        help="Gebuchter Betrag für diesen Vorgang",
                        width="medium"
                    )
                }
            else:
                # Vor dem Speichern: Selectbox für die feste Auswahl
                spalten_konfiguration = {
                    "betrag": st.column_config.SelectboxColumn(
                        "Betrag",
                        help="Betrag des Nutzers",
                        width="medium",
                        options=["Bitte wählen...", "0", "7", "13", "15", "25"],
                        required=True,
                    )
                }

            # 2. Der Data Editor mit dynamischer Config
            df_editiert = st.data_editor(
                df_mit_status,
                column_config=spalten_konfiguration,
                disabled=disabled_spalten,
                hide_index=True,
                width="stretch",
                key=f"smmelbuchung{aktives_datum}",
            )

            # Der Speicher-Button
            if st.button(
                    button_text,
                    type="primary",
                    disabled=button_deaktiviert,
                    key="save_wallet_btn",
            ):
                gueltige_buchungen = df_editiert[
                    (df_editiert["betrag"] != "Bitte wählen...")
                    & (df_editiert["betrag"] != "0")
                    ]

                if gueltige_buchungen.empty:
                    st.warning("Keine gültigen Beträge zum Speichern ausgewählt.")
                elif df_one_task_gefiltert.empty:
                    st.error(
                        "Kein aktiver Vorgang ausgewählt. Die task_id konnte nicht ermittelt werden."
                    )
                else:
                    try:
                        aktuelle_task_id = int(df_one_task_gefiltert.iloc[0]["id"])
                    except Exception as e:
                        st.error(
                            f"Fehler: Die ID des aktuellen Vorgangs konnte nicht gelesen werden. ({e})"
                        )
                        st.stop()

                    erfolgreich = 0
                    fehler = 0

                    for index, row in gueltige_buchungen.iterrows():
                        buchnummer = row["buchnummer"]
                        betrag = float(row["betrag"])

                        old_amount = 0.0
                        try:
                            wallet_response = requests.get(
                                f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5
                            )
                            if wallet_response.status_code == 200:
                                last_entry = wallet_response.json()
                                old_amount = float(last_entry.get("new_amount", 0))
                        except:
                            old_amount = 0.0

                        new_amount = old_amount + betrag

                        wallet_payload = {
                            "task_id": aktuelle_task_id,
                            "buchnummer": buchnummer,
                            "betrag": betrag,
                            "old_amount": old_amount,
                            "new_amount": new_amount,
                            "grund": f"Sammelbuchung von {date.today()}",
                            "date": str(date.today()),
                        }

                        try:
                            post_response = requests.post(
                                f"{BASE_URL}/wallets/save",
                                json=wallet_payload,
                                timeout=5,
                            )
                            if post_response.status_code in [200, 201]:
                                erfolgreich += 1
                            else:
                                fehler += 1
                                st.error(
                                    f"Fehler bei Buchnummer {buchnummer}: {post_response.text}"
                                )
                        except Exception as e:
                            fehler += 1
                            st.error(
                                f"Verbindungsfehler bei Buchnummer {buchnummer}: {e}"
                            )

                    if erfolgreich > 0:
                        st.success(
                            f"🎉 {erfolgreich} Buchung(en) erfolgreich gespeichert!"
                        )
                        # Status spezifisch für dieses Datum auf True setzen
                        st.session_state.gespeicherte_schritte[aktives_datum] = True
                        st.rerun()
                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Buchung(en) fehlgeschlagen.")

        # Expander 3
        with st.expander("Schritt 3: Einkaufsliste"):
            st.dataframe(df_user_gefiltert, hide_index=True, width="stretch")

        # Expander 4
        with st.expander("Schritt 4: Abbuchung"):
            aktives_datum = st.session_state.selected_date

            # Holt den Speicher-Status für das aktuell ausgewählte Datum
            ist_gespeichert = st.session_state.gespeicherte_schritte.get(
                aktives_datum, False
            )

            # Kopie der User-Daten erstellen
            df_mit_status = df_user_gefiltert.copy()

            # Daten-Vorbereitung je nach Speicher-Status
            if ist_gespeichert:
                # WENN BEREITS GESPEICHERT: Wir holen die aktuellen Beträge aus der Wallet DB
                aktuelle_betraege = []
                for _, row in df_mit_status.iterrows():
                    buchnummer = row["buchnummer"]
                    try:
                        wallet_response = requests.get(
                            f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5
                        )
                        if wallet_response.status_code == 200:
                            last_entry = wallet_response.json()
                            aktuelle_betraege.append(
                                str(last_entry.get("new_amount", "0"))
                            )
                        else:
                            aktuelle_betraege.append("0")
                    except:
                        aktuelle_betraege.append("0")

                df_mit_status["betrag"] = aktuelle_betraege
                # Gesperrte Spalten, wenn bereits gespeichert
                disabled_spalten = ["vorname", "nachname", "buchnummer", "betrag"]
                button_deaktiviert = True
                button_text = "🔒 Beträge erfolgreich in Wallet gespeichert"
            else:
                # WENN NOCH NICHT GESPEICHERT: Normaler Auswahl-Modus
                df_mit_status["betrag"] = "Bitte wählen..."
                # KORREKTUR: "betrag" darf hier NICHT in disabled_spalten sein!
                disabled_spalten = ["vorname", "nachname", "buchnummer"]
                button_deaktiviert = False
                button_text = "💾 Beträge in Wallet speichern"

            # 1. Dynamische Spaltenkonfiguration vorbereiten
            if ist_gespeichert:
                # Nach dem Speichern: Einfache Textspalte zur korrekten Anzeige beliebiger Kontostände
                spalten_konfiguration = {
                    "betrag": st.column_config.TextColumn(
                        "Betrag",
                        help="Aktuelles Guthaben in der Wallet",
                        width="medium"
                    )
                }
            else:
                # Vor dem Speichern: Selectbox für die feste Auswahl
                spalten_konfiguration = {
                    "betrag": st.column_config.SelectboxColumn(
                        "Betrag",
                        help="Betrag des Nutzers",
                        width="medium",
                        options=["Bitte wählen...", "0", "7", "13", "15", "25"],
                        required=True,
                    )
                }

            # 2. Der Data Editor mit dynamischer Config
            df_editiert = st.data_editor(
                df_mit_status,
                column_config=spalten_konfiguration,  # Hier wird die dynamische Config übergeben
                disabled=disabled_spalten,
                hide_index=True,
                width="stretch",
                key=f"abbuchung{aktives_datum}",
            )

            # Der Speicher-Button
            if st.button(
                    button_text,
                    type="primary",
                    disabled=button_deaktiviert,
                    key="save_wallet_btn_2",
            ):
                gueltige_buchungen = df_editiert[
                    (df_editiert["betrag"] != "Bitte wählen...")
                    & (df_editiert["betrag"] != "0")
                    ]

                if gueltige_buchungen.empty:
                    st.warning("Keine gültigen Beträge zum Speichern ausgewählt.")
                elif df_one_task_gefiltert.empty:
                    st.error(
                        "Kein aktiver Vorgang ausgewählt. Die task_id konnte nicht ermittelt werden."
                    )
                else:
                    try:
                        aktuelle_task_id = int(df_one_task_gefiltert.iloc[0]["id"])
                    except Exception as e:
                        st.error(
                            f"Fehler: Die ID des aktuellen Vorgangs konnte nicht gelesen werden. ({e})"
                        )
                        st.stop()

                    erfolgreich = 0
                    fehler = 0

                    for index, row in gueltige_buchungen.iterrows():
                        buchnummer = row["buchnummer"]
                        betrag = float(row["betrag"])

                        old_amount = 0.0
                        try:
                            wallet_response = requests.get(
                                f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5
                            )
                            if wallet_response.status_code == 200:
                                last_entry = wallet_response.json()
                                old_amount = float(last_entry.get("new_amount", 0))
                        except:
                            old_amount = 0.0

                        new_amount = old_amount + betrag

                        wallet_payload = {
                            "task_id": aktuelle_task_id,
                            "buchnummer": buchnummer,
                            "betrag": betrag,
                            "old_amount": old_amount,
                            "new_amount": new_amount,
                            "grund": f"Sammelbuchung von {date.today()}",
                            "date": str(date.today()),
                        }

                        try:
                            post_response = requests.post(
                                f"{BASE_URL}/wallets/save",
                                json=wallet_payload,
                                timeout=5,
                            )
                            if post_response.status_code in [200, 201]:
                                erfolgreich += 1
                            else:
                                fehler += 1
                                st.error(
                                    f"Fehler bei Buchnummer {buchnummer}: {post_response.text}"
                                )
                        except Exception as e:
                            fehler += 1
                            st.error(
                                f"Verbindungsfehler bei Buchnummer {buchnummer}: {e}"
                            )

                    if erfolgreich > 0:
                        st.success(
                            f"🎉 {erfolgreich} Buchung(en) erfolgreich gespeichert!"
                        )
                        # Status spezifisch für dieses Datum auf True setzen
                        st.session_state.gespeicherte_schritte[aktives_datum] = True
                        st.rerun()
                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Buchung(en) fehlgeschlagen.")
