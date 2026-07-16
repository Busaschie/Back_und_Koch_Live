from datetime import date
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

# Seite auf weites Layout stellen
st.set_page_config(layout="wide")

if "create_mode" not in st.session_state:
    st.session_state.create_mode = False

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

# ==========================================
# 0. Session State Initialisierung (BEHEBT PUNKT 1 & 2)
# ==========================================
# Wenn noch kein Datum gewählt ist ODER das Standarddatum nicht in der Liste existiert,
# wählen wir automatisch das allererste Datum aus der Einkaufsliste links.
if "selected_date" not in st.session_state:
    if not df_task_gefiltert.empty:
        st.session_state.selected_date = str(df_task_gefiltert.iloc[0]["shop_date"])
    else:
        st.session_state.selected_date = str(date.today())

def get_api_one_task(shop_date: str):
    try:
        params = {"shop_date": shop_date}
        response = requests.get(f"{BASE_URL}/tasks/one_task", params=params)
        if response.status_code != 200:
            return pd.DataFrame(columns=["id", "monat", "jahr", "shop_date", "abgabe_date", "geld_date"])
        data = response.json()
        df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame()
        erwartete_spalten = ["id", "monat", "jahr", "shop_date", "abgabe_date", "geld_date"]
        return df[[col for col in erwartete_spalten if col in df.columns]].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der Detail-API: {e}")
        return pd.DataFrame(columns=["id", "monat", "jahr", "shop_date", "abgabe_date", "geld_date"])

# Hilfsfunktion für den status_betrag
def get_task_status(task_id: int) -> str:
    try:
        response = requests.get(f"{BASE_URL}/tasks/{task_id}/status_betrag", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                status_val = data.get("status_betrag") or data.get("status") or "OPEN"
                return str(status_val).upper()
    except Exception as e:
        st.warning(f"Status-Abfrage fehlgeschlagen: {e}")
    return "OPEN"

# Daten für den aktuell ausgewählten Task laden
df_one_task_gefiltert = get_api_one_task(shop_date=st.session_state.selected_date)

aktuelle_task_id = None
db_status = "OPEN"

if not df_one_task_gefiltert.empty:
    try:
        aktuelle_task_id = int(df_one_task_gefiltert.iloc[0]["id"])
        db_status = get_task_status(aktuelle_task_id)
    except Exception as e:
        st.error(f"Fehler beim Ermitteln des DB-Status: {e}")

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
            if st.session_state.selected_date != neues_datum:
                st.session_state.selected_date = neues_datum
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
                        monat = st.selectbox("Monat", options=["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"])
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
                    payload = {"date": str(shop_date), "monat": str(monat), "jahr": str(jahr), "shop_date": str(shop_date), "abgabe_date": str(abgabe_date), "geld_date": str(geld_date)}
                    try:
                        response = requests.post(f"{BASE_URL}/tasks/save/", json=payload)
                        if response.status_code in [200, 201]:
                            st.success("🎉 Vorgang erfolgreich in der DB gespeichert!")
                            st.cache_data.clear()
                            st.session_state.selected_date = str(shop_date)
                            st.session_state.create_mode = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")
            else:
                st.dataframe(df_one_task_gefiltert, hide_index=True, width="stretch", column_config={"id": None})

        # Schritt 2 (BEHEBT PUNKT 3 & 4)
        with st.expander("Schritt 2: Sammelbuchung"):
            aktives_datum = st.session_state.selected_date
            ist_gespeichert = (str(db_status).strip().upper() == "DONE")

            df_mit_status = df_user_gefiltert.copy()

            if ist_gespeichert:
                # NUR BEI DONE: Wir laden die echten Beträge aus der DB
                aktuelle_betraege = []
                for _, row in df_mit_status.iterrows():
                    buchnummer = row["buchnummer"]
                    try:
                        wallet_response = requests.get(f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5)
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
                # BEHEBT PUNKT 3: KEINE API-CALLS während der Eingabe bei "OPEN"!
                # Wir setzen einfach statisch den Standardwert, damit Streamlit flüssig läuft.
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

                    # Erst beim Klick auf den Speicherbutton feuern wir die API-Calls ab!
                    for index, row in gueltige_buchungen.iterrows():
                        buchnummer = row["buchnummer"]
                        betrag = float(row["betrag"])

                        old_amount = 0.0
                        try:
                            wallet_response = requests.get(f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5)
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
                        # BEHEBT PUNKT 4: Richtige URL zum Status-Update aufrufen!
                        try:
                            # Der Parameter laut Swagger lautet 'new_state=DONE'
                            status_url = f"{BASE_URL}/tasks/{aktuelle_task_id}/update_status_betrag"
                            status_response = requests.put(
                                status_url,
                                params={"new_state": "DONE"}, # Nutzt Query-Params 'new_state'
                                timeout=5
                            )
                            if status_response.status_code in [200, 201]:
                                st.success("🎉 Buchungen gespeichert und Status auf DONE gesetzt!")
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

        # Schritt 4 (Abbuchung analog zu Schritt 2 aufgebaut)
        with st.expander("Schritt 4: Abbuchung"):
            ist_gespeichert = (db_status == "DONE")
            df_mit_status = df_user_gefiltert.copy()

            if ist_gespeichert:
                aktuelle_betraege = []
                for _, row in df_mit_status.iterrows():
                    buchnummer = row["buchnummer"]
                    try:
                        wallet_response = requests.get(f"{BASE_URL}/wallets/last", params={"buchnummer": buchnummer}, timeout=5)
                        if wallet_response.status_code == 200:
                            aktuelle_betraege.append(str(wallet_response.json().get("new_amount", "0")))
                        else:
                            aktuelle_betraege.append("0")
                    except:
                        aktuelle_betraege.append("0")

                df_mit_status["betrag"] = aktuelle_betraege
                disabled_spalten = ["vorname", "nachname", "buchnummer", "betrag"]
                button_deaktiviert = True
                button_text = "🔒 Abbuchung abgeschlossen (Status: DONE)"
            else:
                df_mit_status["betrag"] = "Bitte wählen..."
                disabled_spalten = ["vorname", "nachname", "buchnummer"]
                button_deaktiviert = False
                button_text = "💾 Beträge abbuchen"

            if ist_gespeichert:
                spalten_konfiguration = {
                    "betrag": st.column_config.TextColumn("Betrag", help="Aktuelles Guthaben", width="medium")
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

            df_editiert = st.data_editor(
                df_mit_status,
                column_config=spalten_konfiguration,
                disabled=disabled_spalten,
                hide_index=True,
                width="stretch",
                key=f"abbuchung_{aktives_datum}_{db_status}",
            )