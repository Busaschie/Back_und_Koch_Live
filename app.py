from datetime import date
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

# Seite auf weites Layout stellen
st.set_page_config(layout="wide")

# ==========================================
# 0. SESSION STATE INITIALISIERUNG (GLOBAL)
# ==========================================
if "create_mode" not in st.session_state:
    st.session_state.create_mode = False

# Globaler Cache im Session State, um API-Abfragen beim Tippen komplett zu blockieren
if "global_users" not in st.session_state:
    st.session_state.global_users = None

if "global_tasks" not in st.session_state:
    st.session_state.global_tasks = None


# --- Einmalige API-Ladefunktionen ---
def load_users_once():
    if st.session_state.global_users is None:
        try:
            response = requests.get(f"{BASE_URL}/users", timeout=5)
            df = pd.DataFrame(response.json())
            st.session_state.global_users = df[["vorname", "nachname", "buchnummer"]].copy()
        except Exception as e:
            st.error(f"Fehler beim Laden der User-Daten: {e}")
            st.session_state.global_users = pd.DataFrame(columns=["vorname", "nachname", "buchnummer"])
    return st.session_state.global_users


def load_tasks_once():
    if st.session_state.global_tasks is None:
        try:
            response = requests.get(f"{BASE_URL}/tasks", timeout=5)
            df = pd.DataFrame(response.json())
            st.session_state.global_tasks = df[["shop_date"]].copy()
        except Exception as e:
            st.error(f"Fehler beim Laden der Task-Daten: {e}")
            st.session_state.global_tasks = pd.DataFrame(columns=["shop_date"])
    return st.session_state.global_tasks


# Daten einmalig laden (Diese Variablen nutzen wir im restlichen Code)
df_user_gefiltert = load_users_once()
df_task_gefiltert = load_tasks_once()

# --- Selected Date & Task Details im Session State verwalten ---
if "selected_date" not in st.session_state:
    if not df_task_gefiltert.empty:
        st.session_state.selected_date = str(df_task_gefiltert.iloc[0]["shop_date"])
    else:
        st.session_state.selected_date = str(date.today())

if "current_task_data" not in st.session_state:
    st.session_state.current_task_data = None
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None
if "current_db_status" not in st.session_state:
    st.session_state.current_db_status = "OPEN"
if "current_db_status_buchung" not in st.session_state:
    st.session_state.current_db_status_buchung = "OPEN"


def fetch_api_one_task(shop_date: str):
    try:
        params = {"shop_date": shop_date}
        response = requests.get(f"{BASE_URL}/tasks/one_task", params=params, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data]) if isinstance(data,
                                                                                                  dict) else pd.DataFrame()
        erwartete_spalten = ["id", "monat", "jahr", "shop_date", "abgabe_date", "geld_date"]
        return df[[col for col in erwartete_spalten if col in df.columns]].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der Detail-API: {e}")
        return None


def fetch_task_statuses(task_id: int):
    try:
        response = requests.get(f"{BASE_URL}/tasks/{task_id}/status_betrag", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                status_betrag = data.get("status_betrag") or "OPEN"
                status_buchung = data.get("status_buchung") or "OPEN"
                return str(status_betrag).upper(), str(status_buchung).upper()
    except Exception as e:
        st.warning(f"Status-Abfrage fehlgeschlagen: {e}")
    return "OPEN", "OPEN"


def load_task_into_state(shop_date: str):
    df_task = fetch_api_one_task(shop_date)
    if df_task is not None and not df_task.empty:
        st.session_state.current_task_data = df_task
        st.session_state.current_task_id = int(df_task.iloc[0]["id"])

        s_betrag, s_buchung = fetch_task_statuses(st.session_state.current_task_id)
        st.session_state.current_db_status = s_betrag
        st.session_state.current_db_status_buchung = s_buchung
    else:
        st.session_state.current_task_data = pd.DataFrame()
        st.session_state.current_task_id = None
        st.session_state.current_db_status = "OPEN"
        st.session_state.current_db_status_buchung = "OPEN"


# Erstmaliges Laden beim App-Start sicherstellen
if st.session_state.current_task_data is None:
    load_task_into_state(st.session_state.selected_date)

# Shortcuts für den restlichen UI-Code definieren
df_one_task_gefiltert = st.session_state.current_task_data
aktuelle_task_id = st.session_state.current_task_id
db_status = st.session_state.current_db_status
db_status_buchung = st.session_state.current_db_status_buchung

# ==========================================
# 1. NAVIGATION
# ==========================================
with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_spacer = st.columns([1, 1, 1, 7])
    with nav_col1:
        st.link_button("Vorgänge", "http://localhost:8501/app.py", width="stretch")
    with nav_col2:
        st.link_button("Konten", "https://deine-website.de/dashboard", width="stretch")
    with nav_col3:
        st.link_button("Waren", "https://deine-website.de/settings", width="stretch")
st.write("---")

# ==========================================
# MAIN LAYOUT
# ==========================================
col_links, col_rechts = st.columns([2, 8])

# --- LINKE SEITE ---
with col_links:
    with st.container(border=True):
        st.subheader("📋 Einkäufe")
        if st.button("⚙️ Neuer Vorgang", width="stretch"):
            st.session_state.create_mode = True
            st.rerun()

        event = st.dataframe(
            df_task_gefiltert,
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
        )

        selected_rows = event.get("selection", {}).get("rows", [])
        if selected_rows:
            selected_idx = selected_rows[0]
            neues_datum = str(df_task_gefiltert.iloc[selected_idx]["shop_date"])

            # WICHTIG: Nur wenn sich das Datum ändert, triggern wir die API-Abfragen!
            if st.session_state.selected_date != neues_datum:
                st.session_state.selected_date = neues_datum
                load_task_into_state(neues_datum)  # Daten neu in den Session State laden
                st.rerun()

# --- RECHTE SEITE ---
with col_rechts:
    with st.container(border=True):
        st.subheader(f"Bestellvorgang (Ausgewählt: {st.session_state.selected_date})")

        # Schritt 1
        with st.expander("Schritt 1: Vorgangs-Informationen festlegen", expanded=True):
            if st.session_state.create_mode:
                st.markdown("### ➕ Neuen Vorgang anlegen")
                with st.form("new_task_form", clear_on_submit=True):
                    col_y, col_m = st.columns(2)
                    with col_y:
                        jahr = st.number_input("Jahr", min_value=2020, max_value=2100, value=2026)
                    with col_m:
                        monat = st.selectbox("Monat",
                                             options=["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
                                                      "August", "September", "Oktober", "November", "Dezember"])
                    shop_date = st.date_input("Shop-Datum (shop_date)")
                    abgabe_date = st.date_input("Abgabetermin (abgabe_date)")
                    geld_date = st.date_input("Geld erhalten am (geld_date)")

                    col_btn_save, col_btn_cancel = st.columns([1, 1])
                    with col_btn_save:
                        submitted = st.form_submit_button("💾 Speichern", width="stretch")
                    with col_btn_cancel:
                        canceled = st.form_submit_button("❌ Abbrechen", width="stretch")

                if canceled:
                    st.session_state.create_mode = False
                    st.rerun()

                if submitted:
                    payload = {"date": str(shop_date), "monat": str(monat), "jahr": str(jahr),
                               "shop_date": str(shop_date), "abgabe_date": str(abgabe_date),
                               "geld_date": str(geld_date)}
                    try:
                        response = requests.post(f"{BASE_URL}/tasks/save/", json=payload)
                        if response.status_code in [200, 201]:
                            st.success("🎉 Vorgang erfolgreich in der DB gespeichert!")
                            st.cache_data.clear()
                            st.session_state.selected_date = str(shop_date)
                            load_task_into_state(str(shop_date))  # Direkt neu laden
                            st.session_state.create_mode = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")
            else:
                st.dataframe(df_one_task_gefiltert, hide_index=True, width="stretch", column_config={"id": None})

        # Schritt 2 (0 API-Calls bei Betragseingabe!)
        with st.expander("Schritt 2: Sammelbuchung"):
            aktives_datum = st.session_state.selected_date
            ist_gespeichert = (str(db_status).strip().upper() == "DONE")

            df_mit_status = df_user_gefiltert.copy()

            if ist_gespeichert:
                # NUR bei DONE fragen wir einmalig die letzten Beträge ab (da diese schreibgeschützt geladen werden)
                aktuelle_betraege = []
                for _, row in df_mit_status.iterrows():
                    buchnummer = row["buchnummer"]
                    try:
                        wallet_response = requests.get(f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer},
                                                       timeout=5)
                        if wallet_response.status_code == 200:
                            aktuelle_betraege.append(str(wallet_response.json().get("betrag", "0")))
                        else:
                            aktuelle_betraege.append("0")
                    except:
                        aktuelle_betraege.append("0")

                df_mit_status["betrag"] = aktuelle_betraege
                disabled_spalten = ["vorname", "nachname", "buchnummer", "betrag"]
                button_deaktiviert = True
                button_text = "🔒 Beträge erfolgreich gespeichert (Status: DONE)"
            else:
                # Bei OPEN sind es nun absolut 0 API-Calls, egal wie viele Beträge du änderst!
                df_mit_status["betrag"] = "Bitte wählen..."
                disabled_spalten = ["vorname", "nachname", "buchnummer"]
                button_deaktiviert = False
                button_text = "💾 Beträge in Wallet speichern & abschließen"

            # Spaltenkonfiguration
            if ist_gespeichert:
                spalten_konfiguration = {
                    "betrag": st.column_config.TextColumn("Betrag", help="Gebuchter Betrag", width="medium")
                }
            else:
                spalten_konfiguration = {
                    "betrag": st.column_config.SelectboxColumn(
                        "Betrag",
                        help="Betrag des Nutzers",
                        width="medium",
                        options=["Bitte wählen...", "0", "7", "13", "15", "25"],
                        required=True,
                    )
                }

            editor_key = f"sammelbuchung_{aktives_datum}_{str(db_status).strip().upper()}"

            df_editiert = st.data_editor(
                df_mit_status,
                column_config=spalten_konfiguration,
                disabled=disabled_spalten,
                hide_index=True,
                width="stretch",
                key=editor_key,
            )

            if st.button(button_text, type="primary", disabled=button_deaktiviert, key="save_wallet_btn"):
                gueltige_buchungen = df_editiert[
                    (df_editiert["betrag"] != "Bitte wählen...") & (df_editiert["betrag"] != "0")
                    ]

                if gueltige_buchungen.empty:
                    st.warning("Keine gültigen Beträge zum Speichern ausgewählt.")
                elif aktuelle_task_id is None:
                    st.error("Keine gültige task_id gefunden.")
                else:
                    erfolgreich = 0
                    fehler = 0

                    for index, row in gueltige_buchungen.iterrows():
                        buchnummer = row["buchnummer"]
                        betrag = float(row["betrag"])

                        old_amount = 0.0
                        try:
                            wallet_response = requests.get(f"{BASE_URL}/wallets/last",
                                                           params={"buchnummer": buchnummer}, timeout=5)
                            if wallet_response.status_code == 200:
                                old_amount = float(wallet_response.json().get("new_amount", 0))
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
                            post_response = requests.post(f"{BASE_URL}/wallets/save", json=wallet_payload, timeout=5)
                            if post_response.status_code in [200, 201]:
                                erfolgreich += 1
                            else:
                                fehler += 1
                        except:
                            fehler += 1

                    if erfolgreich > 0:
                        try:
                            status_url = f"{BASE_URL}/tasks/{aktuelle_task_id}/update_status_betrag"
                            status_response = requests.put(
                                status_url,
                                params={"new_state": "DONE"},
                                timeout=5
                            )
                            if status_response.status_code in [200, 201]:
                                st.success("🎉 Buchungen gespeichert und Status auf DONE gesetzt!")
                                # Wichtig: Direkt im State auf DONE stellen, damit beim Rerun alles gesperrt ist
                                st.session_state.current_db_status = "DONE"
                            else:
                                st.warning(f"Buchungen OK, aber Status-Update fehlgeschlagen: {status_response.text}")
                        except Exception as e:
                            st.warning(f"Fehler bei der Verbindung zum Status-Update: {e}")

                        st.rerun()
                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Buchung(en) fehlgeschlagen.")

        # Schritt 3
        with st.expander("Schritt 3: Einkaufsliste"):
            st.dataframe(df_user_gefiltert, hide_index=True, width="stretch")

        # Schritt 4: Abbuchung (Mit st.form -> Absolut KEIN Laden bei der Eingabe!)
        with st.expander("Schritt 4: Abbuchung"):
            aktives_datum = st.session_state.selected_date
            ist_buchung_gespeichert = (str(db_status_buchung).strip().upper() == "DONE")

            df_abbuchung = df_user_gefiltert.copy()

            # Wir packen alles in ein Formular.
            # Dadurch blockiert Streamlit JEGLICHEN automatischen Rerun beim Tippen!
            with st.form("abbuchung_form"):

                if ist_buchung_gespeichert:
                    # NUR bei DONE holen wir einmalig die archivierten Beträge
                    if f"archiv_abbuchungen_{aktives_datum}" not in st.session_state:
                        archivierte_abbuchungen = []
                        for _, row in df_abbuchung.iterrows():
                            buchnummer = row["buchnummer"]
                            try:
                                wallet_response = requests.get(
                                    f"{BASE_URL}/wallets/last",
                                    params={"buchnummer": buchnummer},
                                    timeout=2
                                )
                                if wallet_response.status_code == 200:
                                    gebuchter_wert = abs(float(wallet_response.json().get("betrag", 0.0)))
                                    archivierte_abbuchungen.append(gebuchter_wert)
                                else:
                                    archivierte_abbuchungen.append(0.0)
                            except:
                                archivierte_abbuchungen.append(0.0)
                        st.session_state[f"archiv_abbuchungen_{aktives_datum}"] = archivierte_abbuchungen

                    df_abbuchung["aktuelles_guthaben"] = 0.0
                    df_abbuchung["abbuchung"] = st.session_state[f"archiv_abbuchungen_{aktives_datum}"]

                    disabled_spalten_4 = ["vorname", "nachname", "buchnummer", "aktuelles_guthaben", "abbuchung"]
                    button_deaktiviert_4 = True
                    button_text_4 = "🔒 Abbuchung abgeschlossen (Status: DONE)"
                else:
                    # WENN OPEN: Keine APIs, keine Verzögerung
                    df_abbuchung["aktuelles_guthaben"] = 0.0
                    df_abbuchung["abbuchung"] = 0.0

                    disabled_spalten_4 = ["vorname", "nachname", "buchnummer", "aktuelles_guthaben"]
                    button_deaktiviert_4 = False
                    button_text_4 = "💾 Beträge abbuchen & in Wallet speichern"

                # Spaltenkonfiguration
                if ist_buchung_gespeichert:
                    spalten_konfiguration_4 = {
                        "aktuelles_guthaben": None,
                        "abbuchung": st.column_config.NumberColumn(
                            "Abgebuchter Betrag (€)",
                            format="%.2f €",
                            width="medium"
                        )
                    }
                else:
                    spalten_konfiguration_4 = {
                        "aktuelles_guthaben": None,
                        "abbuchung": st.column_config.NumberColumn(
                            "Abzubuchender Betrag (€)",
                            min_value=0.0,
                            max_value=1000.0,
                            step=0.01,
                            format="%.2f €",
                            width="medium"
                        )
                    }

                # Der Data Editor innerhalb des Formulars
                df_editiert_4 = st.data_editor(
                    df_abbuchung,
                    column_config=spalten_konfiguration_4,
                    disabled=disabled_spalten_4,
                    hide_index=True,
                    width="stretch",
                    key=f"abb_ed_{aktives_datum}_{db_status_buchung}",
                )

                # Der Absendeknopf des Formulars (st.form_submit_button)
                submitted_4 = st.form_submit_button(
                    button_text_4,
                    type="primary",
                    disabled=button_deaktiviert_4
                )

            # Verarbeitung nach dem Klick auf "Speichern" (außerhalb des Formulars)
            if submitted_4:
                gueltige_abbuchungen = df_editiert_4[df_editiert_4["abbuchung"] > 0.0]

                if gueltige_abbuchungen.empty:
                    st.warning("Keine Beträge zur Abbuchung eingetragen.")
                elif aktuelle_task_id is None:
                    st.error("Keine gültige task_id gefunden.")
                else:
                    erfolgreich = 0
                    fehler = 0

                    for index, row in gueltige_abbuchungen.iterrows():
                        buchnummer = row["buchnummer"]
                        abbuchungs_betrag = float(row["abbuchung"])

                        altes_guthaben = 0.0
                        try:
                            wallet_response = requests.get(
                                f"{BASE_URL}/wallets/last",
                                params={"buchnummer": buchnummer},
                                timeout=5
                            )
                            if wallet_response.status_code == 200:
                                altes_guthaben = float(wallet_response.json().get("new_amount", 0.0))
                        except:
                            altes_guthaben = 0.0

                        neues_guthaben = altes_guthaben - abbuchungs_betrag

                        wallet_payload = {
                            "task_id": aktuelle_task_id,
                            "buchnummer": buchnummer,
                            "betrag": -abbuchungs_betrag,
                            "old_amount": altes_guthaben,
                            "new_amount": neues_guthaben,
                            "grund": f"Abbuchung Einkaufsliste vom {date.today()}",
                            "date": str(date.today()),
                        }

                        try:
                            post_response = requests.post(
                                f"{BASE_URL}/wallets/save",
                                json=wallet_payload,
                                timeout=5
                            )
                            if post_response.status_code in [200, 201]:
                                erfolgreich += 1
                            else:
                                fehler += 1
                        except:
                            fehler += 1

                    if erfolgreich > 0:
                        try:
                            status_url = f"{BASE_URL}/tasks/{aktuelle_task_id}/update_status_buchung"
                            status_response = requests.put(
                                status_url,
                                params={"new_state": "DONE"},
                                timeout=5
                            )
                            if status_response.status_code in [200, 201]:
                                st.success("🎉 Abbuchungen erfolgreich gespeichert!")
                                st.session_state.current_db_status_buchung = "DONE"
                                if f"archiv_abbuchungen_{aktives_datum}" in st.session_state:
                                    del st.session_state[f"archiv_abbuchungen_{aktives_datum}"]
                            else:
                                st.warning(f"Status-Update fehlgeschlagen: {status_response.text}")
                        except Exception as e:
                            st.warning(f"Fehler beim Status-Update: {e}")

                        st.rerun()
                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Abbuchung(en) fehlgeschlagen.")