from datetime import date
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"


def format_buchnummer(val):
    """Formatiert einen Wert (z.B. 12342020) zu 'XXXX/YYYY'."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if len(val_str) > 4:
        return f"{val_str[:-4]}/{val_str[-4:]}"
    return val_str


# Seite auf weites Layout stellen
st.set_page_config(layout="wide")

# --- Custom-CSS für als Buttons formatierte Links ---
# KORREKTUR: unsafe_allow_html=True statt unsafe_html=True
st.markdown("""
<style>
.custom-link-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background-color: #f0f2f6;
    color: #31333F !important;
    padding: 0.4rem 0.8rem;
    border-radius: 0.5rem;
    text-decoration: none !important;
    font-weight: 500;
    font-size: 14px;
    border: 1px solid rgba(49, 51, 63, 0.2);
    transition: background-color 0.16s ease-in-out;
    width: 100%;
    text-align: center;
    box-sizing: border-box;
    height: 38px;
}
.custom-link-btn:hover {
    background-color: #e0e4ec;
    border-color: rgba(49, 51, 63, 0.4);
    color: #31333F !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. SESSION STATE INITIALISIERUNG (GLOBAL)
# ==========================================
if "create_mode" not in st.session_state:
    st.session_state.create_mode = False

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
            df_temp = df[["vorname", "nachname", "buchnummer"]].copy()
            df_temp["buchnummer"] = df_temp["buchnummer"].apply(format_buchnummer)
            st.session_state.global_users = df_temp
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


# Daten einmalig laden
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


if st.session_state.current_task_data is None:
    load_task_into_state(st.session_state.selected_date)

df_one_task_gefiltert = st.session_state.current_task_data
aktuelle_task_id = st.session_state.current_task_id
db_status = st.session_state.current_db_status
db_status_buchung = st.session_state.current_db_status_buchung

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
            column_config={
                "shop_date": st.column_config.DateColumn("Einkaufsdatum", format="DD.MM.YYYY")
            },
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
                load_task_into_state(neues_datum)
                st.rerun()

# --- RECHTE SEITE ---
with col_rechts:
    with st.container(border=True):
        st.subheader(f"Bestellvorgang (Ausgewählt: {st.session_state.selected_date})")

        # --- SCHRITT 1 ---
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

                            # Vorgangs-Cache zurücksetzen, um Liste links sofort zu erneuern
                            st.session_state.global_tasks = None

                            st.session_state.selected_date = str(shop_date)
                            load_task_into_state(str(shop_date))
                            st.session_state.create_mode = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")
            else:
                st.dataframe(
                    df_one_task_gefiltert,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "id": None,
                        "monat": st.column_config.TextColumn("MONAT"),
                        "jahr": st.column_config.TextColumn("JAHR"),
                        "shop_date": st.column_config.DateColumn("SHOP DATE", format="DD.MM.YYYY"),
                        "abgabe_date": st.column_config.DateColumn("ABGABE DATE", format="DD.MM.YYYY"),
                        "geld_date": st.column_config.DateColumn("GELD DATE", format="DD.MM.YYYY"),
                    }
                )

                # HTML-Link mit korrigiertem unsafe_allow_html Argument
                st.write("")
                st.markdown(
                    '<a href="/hausgeld_abbuchung_druck" target="_blank" class="custom-link-btn">🖨️ Hausgeld Abbuchungsliste drucken</a>',
                    unsafe_allow_html=True)

        # --- SCHRITT 2 ---
        with st.expander("Schritt 2: Sammelbuchung"):
            aktives_datum = st.session_state.selected_date
            ist_gespeichert = (str(db_status).strip().upper() == "DONE")
            df_mit_status = df_user_gefiltert.copy()

            if ist_gespeichert:
                aktuelle_betraege = []
                for _, row in df_mit_status.iterrows():
                    buchnummer = str(row["buchnummer"]).replace("/", "")
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
                button_text = "🔒 Beträge gespeichert (Status: DONE)"
            else:
                df_mit_status["betrag"] = "Bitte wählen..."
                disabled_spalten = ["vorname", "nachname", "buchnummer"]
                button_deaktiviert = False
                button_text = "💾 Beträge in Wallet speichern & abschließen"

            if ist_gespeichert:
                spalten_konfiguration = {
                    "vorname": st.column_config.TextColumn("VORNAME"),
                    "nachname": st.column_config.TextColumn("NACHNAME"),
                    "buchnummer": st.column_config.TextColumn("BUCHNUMMER"),
                    "betrag": st.column_config.TextColumn("BETRAG", help="Gebuchter Betrag", width="medium")
                }
            else:
                spalten_konfiguration = {
                    "vorname": st.column_config.TextColumn("VORNAME"),
                    "nachname": st.column_config.TextColumn("NACHNAME"),
                    "buchnummer": st.column_config.TextColumn("BUCHNUMMER"),
                    "betrag": st.column_config.SelectboxColumn(
                        "BETRAG", help="Betrag des Nutzers", width="medium",
                        options=["Bitte wählen...", "0", "7", "13", "15", "25"], required=True,
                    )
                }

            editor_key = f"sammelbuchung_{aktives_datum}_{str(db_status).strip().upper()}"
            df_editiert = st.data_editor(df_mit_status, column_config=spalten_konfiguration, disabled=disabled_spalten,
                                         hide_index=True, width="stretch", key=editor_key)

            # HTML-Links neben dem Speicher-Button
            st.write("")
            col_s2_1, col_s2_2, col_s2_3 = st.columns([4, 2, 2])
            with col_s2_1:
                click_save_wallet = st.button(button_text, type="primary", disabled=button_deaktiviert,
                                              key="save_wallet_btn", width="stretch")
            with col_s2_2:
                st.markdown(
                    '<a href="/einkaufszettel_druck" target="_blank" class="custom-link-btn">📝 Einkaufszettel drucken</a>',
                    unsafe_allow_html=True)
            with col_s2_3:
                st.markdown('<a href="/waren_druck" target="_blank" class="custom-link-btn">📦 Warenliste drucken</a>',
                            unsafe_allow_html=True)

            if click_save_wallet:
                gueltige_buchungen = df_editiert[
                    (df_editiert["betrag"] != "Bitte wählen...") & (df_editiert["betrag"] != "0")]
                if gueltige_buchungen.empty:
                    st.warning("Keine gültigen Beträge zum Speichern ausgewählt.")
                elif aktuelle_task_id is None:
                    st.error("Keine gültige task_id gefunden.")
                else:
                    erfolgreich = 0
                    fehler = 0
                    for index, row in gueltige_buchungen.iterrows():
                        buchnummer = str(row["buchnummer"]).replace("/", "")
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
                        wallet_payload = {"task_id": aktuelle_task_id, "buchnummer": buchnummer, "betrag": betrag,
                                          "old_amount": old_amount, "new_amount": new_amount,
                                          "grund": f"Sammelbuchung von {date.today()}", "date": str(date.today())}
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
                            status_response = requests.put(status_url, params={"new_state": "DONE"}, timeout=5)
                            if status_response.status_code in [200, 201]:
                                st.success("🎉 Buchungen gespeichert und Status auf DONE gesetzt!")
                                st.session_state.current_db_status = "DONE"
                            else:
                                st.warning(f"Buchungen OK, aber Status-Update fehlgeschlagen: {status_response.text}")
                        except Exception as e:
                            st.warning(f"Fehler bei der Verbindung zum Status-Update: {e}")
                        st.rerun()
                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Buchung(en) fehlgeschlagen.")

        # --- SCHRITT 3 ---
        # Standardmäßig zugeklappt (expanded=False)
        with st.expander("Schritt 3: Einkaufsliste", expanded=False):
            aktives_datum = st.session_state.selected_date
            if "global_waren" not in st.session_state or st.session_state.global_waren is None:
                try:
                    waren_response = requests.get(f"{BASE_URL}/waren", timeout=5)
                    if waren_response.status_code == 200:
                        st.session_state.global_waren = pd.DataFrame(waren_response.json())
                    else:
                        st.session_state.global_waren = pd.DataFrame()
                except Exception as e:
                    st.error(f"Fehler beim Laden der Waren: {e}")
                    st.session_state.global_waren = pd.DataFrame()

            df_waren = st.session_state.global_waren.copy()

            if df_waren.empty:
                st.info("Keine Waren in der Datenbank vorhanden.")
            elif aktuelle_task_id is None:
                st.warning("Bitte wähle zuerst links einen gültigen Einkaufsvorgang aus (Schritt 1), um fortzufahren.")
            else:
                df_waren = df_waren.sort_values(by="kategorie")
                if "bestellmenge" not in df_waren.columns:
                    df_waren["bestellmenge"] = 0

                kategorie_edits = {}
                einzigartige_kategorien = df_waren["kategorie"].unique()

                with st.form("bestellung_form"):
                    st.markdown("#### Artikel nach Kategorien")
                    for kat in einzigartige_kategorien:
                        df_kat = df_waren[df_waren["kategorie"] == kat].copy()
                        with st.container(border=True):
                            st.markdown(f"**📂 {str(kat).upper()}**")
                            spalten_konfig_waren = {
                                "bezeichnung": st.column_config.TextColumn("BEZEICHNUNG", disabled=True),
                                "menge": st.column_config.NumberColumn("VORHANDENE MENGE", disabled=True),
                                "art": st.column_config.TextColumn("ART", disabled=True),
                                "preis": st.column_config.NumberColumn("PREIS (€)", format="%.2f €", disabled=True),
                                "bestellmenge": st.column_config.NumberColumn("BESTELLMENGE", min_value=0,
                                                                              max_value=1000, step=1, required=True),
                                "id": None,
                                "kategorie": None,
                            }
                            edited_df = st.data_editor(df_kat, column_config=spalten_konfig_waren, hide_index=True,
                                                       width="stretch", key=f"editor_{kat}_{aktives_datum}")
                            kategorie_edits[kat] = edited_df

                    st.write("---")

                    # HTML-Link neben dem Form-Speicherbutton
                    col_s3_1, col_s3_2 = st.columns([2, 1])
                    with col_s3_1:
                        submitted_bestellung = st.form_submit_button("🛒 Bestellung speichern",
                                                                     type="primary", width="stretch")
                    with col_s3_2:
                        st.markdown(
                            '<a href="/waren_druck" target="_blank" class="custom-link-btn">🛒 Wareneinkauf Beleg</a>',
                            unsafe_allow_html=True)

                if submitted_bestellung:
                    alle_bestellungen = []
                    for kat, df_edited in kategorie_edits.items():
                        gueltige_bestellungen = df_edited[df_edited["bestellmenge"] > 0]
                        if not gueltige_bestellungen.empty:
                            alle_bestellungen.append(gueltige_bestellungen)

                    if not alle_bestellungen:
                        st.warning("Es wurden keine Bestellmengen eingetragen.")
                    else:
                        df_finale_bestellung = pd.concat(alle_bestellungen)
                        erfolgreich = 0
                        fehler = 0
                        for _, row in df_finale_bestellung.iterrows():
                            einzelpreis = float(row["preis"])
                            bestellmenge = int(row["bestellmenge"])
                            gesamt_preis = einzelpreis * bestellmenge

                            bestell_payload = {
                                "task_id": aktuelle_task_id,
                                "bezeichnung": str(row["bezeichnung"]),
                                "menge": bestellmenge,
                                # Verhindert, dass 'None' oder 'NaN' an die API geschickt wird, falls leer:
                                "art": str(row["art"]) if pd.notna(row.get("art")) else "",
                                "preis": einzelpreis,
                                "gesamt_preis": gesamt_preis
                            }
                            try:
                                response = requests.post(f"{BASE_URL}/bestellungen/save", json=bestell_payload,
                                                         timeout=5)
                                if response.status_code in [200, 201]:
                                    erfolgreich += 1
                                else:
                                    fehler += 1
                            except:
                                fehler += 1

                        if erfolgreich > 0:
                            st.success(
                                f"🎉 {erfolgreich} Artikel erfolgreich für den Vorgang (ID: {aktuelle_task_id}) bestellt!")
                        if fehler > 0:
                            st.error(f"⚠️ {fehler} Bestellung(en) fehlgeschlagen. Bitte API-Verbindung prüfen.")
                        st.rerun()

        # --- SCHRITT 4 ---
        with st.expander("Schritt 4: Abbuchung"):
            aktives_datum = st.session_state.selected_date
            ist_buchung_gespeichert = (str(db_status_buchung).strip().upper() == "DONE")
            df_abbuchung = df_user_gefiltert.copy()

            with st.form("abbuchung_form"):
                if ist_buchung_gespeichert:
                    if f"archiv_abbuchungen_{aktives_datum}" not in st.session_state:
                        archivierte_abbuchungen = []
                        for _, row in df_abbuchung.iterrows():
                            buchnummer = str(row["buchnummer"]).replace("/", "")
                            try:
                                wallet_response = requests.get(f"{BASE_URL}/wallets/last",
                                                               params={"buchnummer": buchnummer}, timeout=2)
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
                    df_abbuchung["aktuelles_guthaben"] = 0.0
                    df_abbuchung["abbuchung"] = 0.0
                    disabled_spalten_4 = ["vorname", "nachname", "buchnummer", "aktuelles_guthaben"]
                    button_deaktiviert_4 = False
                    button_text_4 = "💾 Beträge abbuchen & in Wallet speichern"

                if ist_buchung_gespeichert:
                    spalten_konfiguration_4 = {
                        "vorname": st.column_config.TextColumn("VORNAME"),
                        "nachname": st.column_config.TextColumn("NACHNAME"),
                        "buchnummer": st.column_config.TextColumn("BUCHNUMMER"),
                        "aktuelles_guthaben": None,
                        "abbuchung": st.column_config.NumberColumn("ABGEBUCHTER BETRAG", format="%.2f €",
                                                                   width="medium")
                    }
                else:
                    spalten_konfiguration_4 = {
                        "vorname": st.column_config.TextColumn("VORNAME"),
                        "nachname": st.column_config.TextColumn("NACHNAME"),
                        "buchnummer": st.column_config.TextColumn("BUCHNUMMER"),
                        "aktuelles_guthaben": None,
                        "abbuchung": st.column_config.NumberColumn("ABZUBUCHENDER BETRAG", min_value=0.0,
                                                                   max_value=1000.0, step=0.01, format="%.2f €",
                                                                   width="medium")
                    }

                df_editiert_4 = st.data_editor(df_abbuchung, column_config=spalten_konfiguration_4,
                                               disabled=disabled_spalten_4, hide_index=True, width="stretch",
                                               key=f"abb_ed_{aktives_datum}_{db_status_buchung}")
                submitted_4 = st.form_submit_button(button_text_4, type="primary")

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
                        buchnummer = str(row["buchnummer"]).replace("/", "")
                        abbuchungs_betrag = float(row["abbuchung"])
                        altes_guthaben = 0.0
                        try:
                            wallet_response = requests.get(f"{BASE_URL}/wallets/last",
                                                           params={"buchnummer": buchnummer}, timeout=5)
                            if wallet_response.status_code == 200:
                                altes_guthaben = float(wallet_response.json().get("new_amount", 0.0))
                        except:
                            altes_guthaben = 0.0

                        neues_guthaben = altes_guthaben - abbuchungs_betrag
                        wallet_payload = {"task_id": aktuelle_task_id, "buchnummer": buchnummer,
                                          "betrag": -abbuchungs_betrag, "old_amount": altes_guthaben,
                                          "new_amount": neues_guthaben,
                                          "grund": f"Abbuchung Einkaufsliste vom {date.today()}",
                                          "date": str(date.today())}
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
                            status_url = f"{BASE_URL}/tasks/{aktuelle_task_id}/update_status_buchung"
                            status_response = requests.put(status_url, params={"new_state": "DONE"}, timeout=5)
                            if status_response.status_code in [200, 201]:
                                st.success("🎉 Abbuchungen erfolgreich durchgeführt!")
                                st.session_state.current_db_status_buchung = "DONE"
                        except Exception as e:
                            st.warning(f"Fehler beim Aktualisieren des Buchungsstatus: {e}")
                        st.rerun()