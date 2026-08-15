from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import pandas as pd
import requests
import streamlit as st
import time

BASE_URL = "http://localhost:8000"


def format_buchnummer(val):
    """Formatiert einen Wert (z.B. 12342020) zu 'XXXX/YYYY'."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if len(val_str) > 4:
        return f"{val_str[:-4]}/{val_str[-4:]}"
    return val_str


def format_de_datum(val):
    if not val:
        return "kein Datum"
    if isinstance(val, (datetime, date)):
        return val.strftime("%d.%m.%Y")
    try:
        clean_str = str(val).split("T")[0].strip()
        return datetime.strptime(clean_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception:
        return str(val)


# ==========================================
# ASYNCHRONE HELPER-FUNKTIONEN (THREADPOOL)
# ==========================================
# --- Schritt 2 Async Helpers ---
def fetch_task_wallets_map(task_id: int, schritt: str):
    """
    Holt alle Wallet-Einträge für eine bestimmte task_id und den angegebenen schritt.
    Gibt ein Dictionary zurück: {buchnummer: betrag}
    """
    if not task_id:
        return {}
    try:
        response = requests.get(
            f"{BASE_URL}/wallets/wallet_task",
            params={"task_id": task_id, "schritt": schritt},  # <--- NEU: task_id und schritt
            timeout=5
        )
        if response.status_code == 200:
            wallets = response.json()
            wallets_map = {}
            for w in wallets:
                bnum = str(w.get("buchnummer", "")).strip()
                if bnum:
                    wallets_map[bnum] = w.get("betrag", 0.0)
            return wallets_map
    except Exception as e:
        st.error(f"Fehler beim Laden der Wallet-Daten ({schritt}): {e}")
    return {}


def process_save_wallet_s2(data):
    row, task_id = data
    buchnummer = str(row["buchnummer"]).replace("/", "")
    betrag = float(row["betrag"])
    old_amount = 0.0

    try:
        wallet_response = requests.get(
            f"{BASE_URL}/wallets/last",
            params={"buchnummer": buchnummer},
            timeout=5,
        )
        if wallet_response.status_code == 200:
            old_amount = float(wallet_response.json().get("new_amount", 0))
    except Exception:
        old_amount = 0.0

    formatted_date_zwei = format_de_datum(date.today())

    new_amount = old_amount + betrag
    wallet_payload = {
        "task_id": task_id,
        "buchnummer": buchnummer,
        "betrag": betrag,
        "old_amount": old_amount,
        "new_amount": new_amount,
        "grund": f"Sammelbuchung von {formatted_date_zwei}",
        "date": str(date.today()),
        "schritt": "zwei",
    }

    try:
        post_response = requests.post(
            f"{BASE_URL}/wallets/save", json=wallet_payload, timeout=5
        )
        return post_response.status_code in [200, 201]
    except Exception:
        return False


# --- Schritt 3 Async Helpers ---
def process_save_bestellung_s3(data):
    row, task_id = data
    einzelpreis = float(row["preis"])
    bestellmenge = int(row["bestellmenge"])
    gesamt_preis = round(einzelpreis * bestellmenge, 2)

    # Versuch 'menge' als Zahl zu konvertieren, falls das Backend int/float erwartet
    raw_menge = row.get("menge", "")
    try:
        val_menge = float(raw_menge) if "." in str(raw_menge) else int(raw_menge)
    except (ValueError, TypeError):
        val_menge = str(raw_menge)

    bestell_payload = {
        "task_id": int(task_id),
        "bezeichnung": str(row["bezeichnung"]),
        "bestellmenge": int(bestellmenge),
        "menge": val_menge,
        "art": str(row["art"]),
        "preis": float(einzelpreis),
        "gesamt_preis": float(gesamt_preis),
    }

    # Falls das Backend eine ID oder Kategorie erwartet, mitsenden:
    if "id" in row and pd.notna(row["id"]):
        bestell_payload["waren_id"] = int(row["id"])
        bestell_payload["id"] = int(row["id"])
    elif "waren_id" in row and pd.notna(row["waren_id"]):
        bestell_payload["waren_id"] = int(row["waren_id"])

    if "kategorie" in row and pd.notna(row["kategorie"]):
        bestell_payload["kategorie"] = str(row["kategorie"])

    try:
        response = requests.post(
            f"{BASE_URL}/bestellung/save", json=bestell_payload, timeout=5
        )
        if response.status_code in [200, 201]:
            return True, None
        else:
            return (
                False,
                f"❌ '{row['bezeichnung']}': HTTP {response.status_code} - {response.text}",
            )
    except Exception as e:
        return (
            False,
            f"❌ '{row['bezeichnung']}': Verbindung fehlgeschlagen: {str(e)}",
        )

# --- Schritt 4 Async Helper ---
def process_save_abbuchung_s4(data):
    row, task_id = data
    buchnummer = str(row["buchnummer"]).replace("/", "").strip()
    try:
        abbuchungs_betrag = float(row["abbuchung"])
    except (ValueError, TypeError):
        abbuchungs_betrag = 0.0

    if abbuchungs_betrag < 0:
        return False, f"❌ '{row.get('vorname', '')}': Betrag darf nicht negativ sein."

    old_amount = 0.0
    try:
        wallet_response = requests.get(
            f"{BASE_URL}/wallets/last",
            params={"buchnummer": buchnummer},
            timeout=5,
        )
        if wallet_response.status_code == 200:
            old_amount = float(wallet_response.json().get("new_amount", 0.0))
    except Exception:
        old_amount = 0.0

    formatted_date_zwei = format_de_datum(date.today())

    new_amount = old_amount - abbuchungs_betrag
    wallet_payload = {
        "task_id": int(task_id),
        "buchnummer": buchnummer,
        "betrag": -abbuchungs_betrag,  # Bei 0,00 € wird -0.0 bzw. 0.0 übertragen
        "old_amount": old_amount,
        "new_amount": new_amount,
        "grund": f"Abbuchung von {formatted_date_zwei}",
        "date": str(date.today()),
        "schritt": "vier"
    }

    try:
        post_response = requests.post(
            f"{BASE_URL}/wallets/save", json=wallet_payload, timeout=5
        )
        if post_response.status_code in [200, 201]:
            return True, None
        else:
            return (
                False,
                f"❌ Abbuchung für '{row.get('vorname', '')} {row.get('nachname', '')}' fehlgeschlagen (HTTP {post_response.status_code})",
            )
    except Exception as e:
        return (
            False,
            f"❌ '{row.get('vorname', '')} {row.get('nachname', '')}': Verbindung fehlgeschlagen: {str(e)}",
        )


# Seite auf weites Layout stellen
st.set_page_config(layout="wide")

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
            st.session_state.global_users = pd.DataFrame(
                columns=["vorname", "nachname", "buchnummer"]
            )
    return st.session_state.global_users


def load_tasks_once():
    if st.session_state.global_tasks is None:
        try:
            response = requests.get(f"{BASE_URL}/tasks", timeout=5)
            df = pd.DataFrame(response.json())

            if not df.empty and "shop_date" in df.columns:
                # In echtes Datum umwandeln, damit korrekt sortiert werden kann
                df["shop_date_dt"] = pd.to_datetime(df["shop_date"])

                # Sortieren: Neuestes Datum zuerst (ascending=False)
                df = df.sort_values(by="shop_date_dt", ascending=False)

                # Hilfsspalte wieder entfernen
                df = df.drop(columns=["shop_date_dt"])

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
        # Da df_task_gefiltert jetzt sortiert ist, ist Zeile 0 das aktuellste Datum
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
        df = (
            pd.DataFrame(data)
            if isinstance(data, list)
            else pd.DataFrame([data])
            if isinstance(data, dict)
            else pd.DataFrame()
        )
        erwartete_spalten = ["id", "monat", "jahr", "geld_date", "abgabe_date", "shop_date"]
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
        if st.button("⚙️ Neuer Vorgang", use_container_width=True):
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
        formatted_date = format_de_datum(st.session_state.get("selected_date"))
        st.subheader(f"Bestellvorgang (Ausgewählt: {formatted_date})")

        # --- SCHRITT 1 ---
        with st.expander("Schritt 1: Vorgangs-Informationen festlegen", expanded=True):
            if st.session_state.create_mode:
                st.markdown("### ➕ Neuen Vorgang anlegen")
                with st.form("new_task_form", clear_on_submit=True):
                    col_y, col_m = st.columns(2)
                    with col_y:
                        jahr = st.number_input("Jahr", min_value=2020, max_value=2100, value=2026)
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
                    geld_date = st.date_input("Geld eintragen bis")
                    abgabe_date = st.date_input("Bestellung abgeben bis ")
                    shop_date = st.date_input("Einkaufs-Datum")

                    col_btn_save, col_btn_cancel = st.columns([1, 1])
                    with col_btn_save:
                        submitted = st.form_submit_button("💾 Speichern", use_container_width=True)
                    with col_btn_cancel:
                        canceled = st.form_submit_button("❌ Abbrechen", use_container_width=True)

                if canceled:
                    st.session_state.create_mode = False
                    st.rerun()

                if submitted:
                    payload = {
                        "date": str(shop_date),
                        "monat": str(monat),
                        "jahr": int(jahr),
                        "geld_date": str(geld_date),
                        "abgabe_date": str(abgabe_date),
                        "shop_date": str(shop_date),
                    }
                    try:
                        response = requests.post(f"{BASE_URL}/tasks/save", json=payload)
                        if response.status_code in [200, 201]:
                            st.success("🎉 Vorgang erfolgreich in der DB gespeichert!")
                            st.cache_data.clear()

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
                        "geld_date": st.column_config.DateColumn("GELD DATE", format="DD.MM.YYYY"),
                        "abgabe_date": st.column_config.DateColumn("BESTELLUNG DATE", format="DD.MM.YYYY"),
                        "shop_date": st.column_config.DateColumn("SHOP DATE", format="DD.MM.YYYY"),
                    },
                )

                st.write("")
                col_s1_1, col_s1_2 = st.columns([6, 2])
                with col_s1_1:
                    st.write("")
                with col_s1_2:
                    if aktuelle_task_id is not None:
                        st.session_state.print_task_id = aktuelle_task_id
                        if st.button(
                            "🖨️ Hausgeld Abbuchungsliste drucken",
                            type="secondary",
                            use_container_width=True,
                        ):
                            st.switch_page("pages/hausgeld_abbuchung_druck.py")
                    else:
                        st.button(
                            "🖨️ Hausgeld Abbuchungsliste drucken",
                            disabled=True,
                            use_container_width=True,
                        )

        # --- SCHRITT 2 ---
        with st.expander("Schritt 2: Sammelbuchung"):
            aktives_datum = st.session_state.selected_date
            ist_gespeichert = str(db_status).strip().upper() == "DONE"
            df_mit_status = df_user_gefiltert.copy()

            if ist_gespeichert:
                # 1. Einmalige Abfrage an den korrekten Endpunkt /wallets/wallet_task
                wallets_map = fetch_task_wallets_map(aktuelle_task_id, schritt="zwei")

                # 2. Beträge anhand der Buchnummer exakt für diesen Task zuordnen
                def get_betrag_for_row(row):
                    clean_bnum = str(row["buchnummer"]).replace("/", "").strip()
                    return wallets_map.get(clean_bnum, "0")

                df_mit_status["betrag"] = df_mit_status.apply(get_betrag_for_row, axis=1)

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
                    "betrag": st.column_config.TextColumn(
                        "BETRAG (€)", help="Gebuchter Betrag", width="medium"
                    ),
                }
            else:
                spalten_konfiguration = {
                    "vorname": st.column_config.TextColumn("VORNAME"),
                    "nachname": st.column_config.TextColumn("NACHNAME"),
                    "buchnummer": st.column_config.TextColumn("BUCHNUMMER"),
                    "betrag": st.column_config.SelectboxColumn(
                        "BETRAG",
                        help="Betrag des Nutzers",
                        width="medium",
                        options=["Bitte wählen...", "0", "7", "10", "13", "15", "20", "25"],
                        required=True,
                    ),
                }

            editor_key = f"sammelbuchung_{aktives_datum}_{aktuelle_task_id}_{str(db_status).strip().upper()}"

            with st.form("sammelbuchung_form"):
                df_editiert = st.data_editor(
                    df_mit_status,
                    column_config=spalten_konfiguration,
                    disabled=disabled_spalten,
                    hide_index=True,
                    width="stretch",
                    key=editor_key,
                )
                click_save_wallet = st.form_submit_button(
                    button_text,
                    type="primary",
                    disabled=button_deaktiviert,
                    use_container_width=True,
                )

            st.write("")
            col_s2_1, col_s2_2, col_s2_3 = st.columns([2, 2, 2])
            with col_s2_1:
                if aktuelle_task_id is not None:
                    st.session_state.print_task_id = aktuelle_task_id
                    if st.button("🖨️ Kontostände drucken", type="secondary", use_container_width=True):
                        st.switch_page("pages/userkonto_druck.py")
                else:
                    st.button("📝 Kontostände", disabled=True, use_container_width=True)
            with col_s2_2:
                if aktuelle_task_id is not None:
                    st.session_state.print_task_id = aktuelle_task_id
                    if st.button("📝 Einkaufszettel drucken", type="secondary", use_container_width=True):
                        st.switch_page("pages/einkaufszettel_druck.py")
                else:
                    st.button("📝 Einkaufszettel", disabled=True, use_container_width=True)

            with col_s2_3:
                if aktuelle_task_id is not None:
                    st.session_state.print_task_id = aktuelle_task_id
                    if st.button("📦 Warenliste drucken", type="secondary", use_container_width=True):
                        st.switch_page("pages/waren_druck.py")
                else:
                    st.button("📦 Warenliste", disabled=True, use_container_width=True)

            if click_save_wallet:
                # 0-Euro Beträge werden explizit mitgespeichert
                gueltige_buchungen = df_editiert[df_editiert["betrag"] != "Bitte wählen..."]

                if gueltige_buchungen.empty:
                    st.warning("Keine gültigen Beträge zum Speichern ausgewählt.")
                elif aktuelle_task_id is None:
                    st.error("Keine gültige task_id gefunden.")
                else:
                    save_tasks = [(row, aktuelle_task_id) for _, row in gueltige_buchungen.iterrows()]

                    # Asynchrones Speichern aller Wallet-Einträge
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        ergebnisse = list(executor.map(process_save_wallet_s2, save_tasks))

                    erfolgreich = sum(ergebnisse)
                    fehler = len(ergebnisse) - erfolgreich

                    if erfolgreich > 0:
                        # Asynchroner Aufruf zum Aktualisieren des Status auf DONE
                        def update_status_async(task_id):
                            try:
                                status_url = f"{BASE_URL}/tasks/{task_id}/update_status_betrag"
                                res = requests.put(
                                    status_url, params={"new_state": "DONE"}, timeout=5
                                )
                                return res.status_code in [200, 201], res.text
                            except Exception as ex:
                                return False, str(ex)


                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(update_status_async, aktuelle_task_id)
                            status_success, status_msg = future.result()

                        if status_success:
                            st.success("🎉 Buchungen gespeichert und Status auf DONE gesetzt!")
                            st.session_state.current_db_status = "DONE"
                        else:
                            st.warning(
                                f"Buchungen OK, aber Status-Update fehlgeschlagen: {status_msg}"
                            )
                        st.rerun()

                    if fehler > 0:
                        st.error(f"⚠️ {fehler} Buchung(en) fehlgeschlagen.")

        # --- SCHRITT 3 ---
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
                st.warning(
                    "Bitte wähle zuerst links einen gültigen Einkaufsvorgang aus (Schritt 1), um fortzufahren."
                )
            else:
                db_status_waren = "OPEN"
                bestellte_artikel_anzahl = 0
                gespeicherte_bestellungen = []

                try:
                    task_res = requests.get(
                        f"{BASE_URL}/tasks/{aktuelle_task_id}/status_betrag", timeout=5
                    )
                    if task_res.status_code == 200:
                        task_data = task_res.json()
                        db_status_waren = str(task_data.get("status_waren", "OPEN")).upper()

                    bestellung_res = requests.get(
                        f"{BASE_URL}/bestellung/{aktuelle_task_id}/bestellung_task",
                        timeout=5,
                    )
                    if bestellung_res.status_code == 200:
                        data_best = bestellung_res.json()
                        if isinstance(data_best, list):
                            gespeicherte_bestellungen = data_best
                            bestellte_artikel_anzahl = len(gespeicherte_bestellungen)
                except Exception as e:
                    st.warning(f"Konnte Status/Bestellungen nicht abfragen: {e}")

                ist_status_done = db_status_waren == "DONE"
                df_waren = df_waren.sort_values(by="kategorie")

                mengen_map = {}
                if gespeicherte_bestellungen:
                    for b in gespeicherte_bestellungen:
                        bezeichnung = b.get("bezeichnung")
                        bestellmenge = b.get("bestellmenge", 0)
                        if bezeichnung:
                            mengen_map[bezeichnung] = bestellmenge

                if ist_status_done:
                    df_waren["bestellmenge"] = (
                        df_waren["bezeichnung"].map(mengen_map).fillna(0).astype(int)
                    )
                    button_deaktiviert_bestellung = True
                    button_text_bestellung = (
                        f"🔒 Bestellung gespeichert ({bestellte_artikel_anzahl} Artikel)"
                    )
                    st.info(
                        f"📦 Status: DONE. Für diesen Vorgang wurden bereits {bestellte_artikel_anzahl} Artikel in der Datenbank gespeichert."
                    )
                else:
                    df_waren["bestellmenge"] = 0
                    button_deaktiviert_bestellung = False
                    button_text_bestellung = "🛒 Bestellung speichern & abschließen"

                st.markdown(
                    """
                    <style>
                    div[data-testid="stVerticalBlock"] > div {
                        gap: 0.2rem !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                kategorie_edits = {}
                einzigartige_kategorien = df_waren["kategorie"].unique()

                with st.form("bestellung_form"):
                    st.markdown("#### Artikel nach Kategorien")

                    tabs = st.tabs([f"📂 {str(kat).upper()}" for kat in einzigartige_kategorien])

                    for i, kat in enumerate(einzigartige_kategorien):
                        with tabs[i]:
                            df_kat = df_waren[df_waren["kategorie"] == kat].copy()

                            col_h1, col_h2, col_h3, col_h4 = st.columns([4, 2, 2, 3])
                            col_h1.markdown("**BEZEICHNUNG**")
                            col_h2.markdown("**ART**")
                            col_h3.markdown("**PREIS (€)**")
                            col_h4.markdown("**BESTELLMENGE**")
                            st.divider()

                            edited_rows = []

                            with st.container(height=350):
                                for idx, row in df_kat.iterrows():
                                    c1, c2, c3, c4 = st.columns([4, 2, 2, 3])

                                    c1.write(row["bezeichnung"])
                                    c2.write(f"{row['menge']} {row['art']}")
                                    c3.write(f"{float(row['preis']):.2f} €")

                                    key_input = f"num_{kat}_{idx}_{aktuelle_task_id}"

                                    if ist_status_done:
                                        best_val = int(row["bestellmenge"])
                                        c4.write(f"**{best_val}**")
                                    else:
                                        val = c4.number_input(
                                            label=f"Menge {row['bezeichnung']}",
                                            min_value=0,
                                            max_value=1000,
                                            step=1,
                                            value=int(row["bestellmenge"]),
                                            key=key_input,
                                            label_visibility="collapsed",
                                        )
                                        row["bestellmenge"] = val

                                    st.markdown(
                                        "<hr style='margin: 4px 0; border: none; border-top: 1px solid #e6e6e6;'>",
                                        unsafe_allow_html=True,
                                    )

                                    edited_rows.append(row)

                            kategorie_edits[kat] = pd.DataFrame(edited_rows)

                    st.write("---")

                    submitted_bestellung = st.form_submit_button(
                        button_text_bestellung,
                        type="primary",
                        use_container_width=True,
                        disabled=button_deaktiviert_bestellung,
                    )

                st.write("")
                col_s3_1, col_s3_2 = st.columns([2, 1])
                with col_s3_1:
                    st.write("")
                with col_s3_2:
                    if aktuelle_task_id is not None:
                        st.session_state.print_task_id = aktuelle_task_id
                        if st.button("🛒 Wareneinkauf Beleg", type="secondary", use_container_width=True):
                            st.switch_page("pages/einkaufsliste_druck.py")
                    else:
                        st.button("🛒 Wareneinkauf Beleg", disabled=True, use_container_width=True)

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
                        save_tasks = [
                            (row, aktuelle_task_id) for _, row in df_finale_bestellung.iterrows()
                        ]

                        with ThreadPoolExecutor(max_workers=10) as executor:
                            ergebnisse = list(executor.map(process_save_bestellung_s3, save_tasks))

                        erfolgreich = sum(1 for success, _ in ergebnisse if success)
                        fehler_details = [
                            err_msg for success, err_msg in ergebnisse if not success and err_msg
                        ]

                        if erfolgreich > 0:
                            try:
                                status_url = f"{BASE_URL}/tasks/{aktuelle_task_id}/update_status_waren"
                                status_response = requests.put(
                                    status_url, params={"new_state": "DONE"}, timeout=5
                                )
                                if status_response.status_code in [200, 201]:
                                    st.success(
                                        f"🎉 {erfolgreich} Artikel gespeichert und Status auf DONE gesetzt!"
                                    )
                                else:
                                    st.warning(
                                        f"Bestellung gesichert, aber Status-Update fehlgeschlagen: {status_response.text}"
                                    )
                            except Exception as e:
                                st.warning(f"Fehler bei der Verbindung zum Status-Update: {e}")

                        if fehler_details:
                            st.error("⚠️ Folgende Artikel konnten nicht gespeichert werden:")
                            for fehler in fehler_details:
                                st.code(fehler, language="txt")

                        if erfolgreich > 0 and not fehler_details:
                            st.cache_data.clear()
                            st.rerun()

        # --- SCHRITT 4 ---
        with st.expander("Schritt 4: Abbuchung", expanded=False):
            aktives_datum = st.session_state.selected_date
            ist_buchung_gespeichert = str(db_status_buchung).strip().upper() == "DONE"
            df_abbuchung = df_user_gefiltert.copy()

            if ist_buchung_gespeichert:
                # 1. Einmalige Abfrage an /wallets/wallet_task (analog zu Schritt 2)
                wallets_map = fetch_task_wallets_map(aktuelle_task_id, schritt="vier")


                def get_abbuchung_for_row(row):
                    clean_bnum = str(row["buchnummer"]).replace("/", "").strip()
                    val = wallets_map.get(clean_bnum, "0")
                    try:
                        # Da Abbuchungen als negativer Betrag gespeichert werden, nehmen wir den Betrag positiv
                        return abs(float(val))
                    except (ValueError, TypeError):
                        return 0.0


                df_abbuchung["aktuelles_guthaben"] = 0.0
                df_abbuchung["abbuchung"] = df_abbuchung.apply(get_abbuchung_for_row, axis=1)

                disabled_spalten_4 = [
                    "vorname",
                    "nachname",
                    "buchnummer",
                    "aktuelles_guthaben",
                    "abbuchung",
                ]
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
                    "abbuchung": st.column_config.NumberColumn(
                        "ABGEBUCHTER BETRAG", format="%.2f €", width="medium"
                    ),
                }
            else:
                spalten_konfiguration_4 = {
                    "vorname": st.column_config.TextColumn("VORNAME"),
                    "nachname": st.column_config.TextColumn("NACHNAME"),
                    "buchnummer": st.column_config.TextColumn("BUCHNUMMER"),
                    "aktuelles_guthaben": None,
                    "abbuchung": st.column_config.NumberColumn(
                        "ABZUBUCHENDER BETRAG",
                        min_value=0.0,
                        max_value=1000.0,
                        step=0.01,
                        format="%.2f €",
                        required=True,
                    ),
                }

            editor_key_4 = f"abbuchung_{aktives_datum}_{aktuelle_task_id}_{str(db_status_buchung).strip().upper()}"

            with st.form("abbuchung_form"):
                df_editiert_4 = st.data_editor(
                    df_abbuchung,
                    column_config=spalten_konfiguration_4,
                    disabled=disabled_spalten_4,
                    hide_index=True,
                    width="stretch",
                    key=editor_key_4,
                )
                submitted_4 = st.form_submit_button(
                    button_text_4,
                    type="primary",
                    disabled=button_deaktiviert_4,
                    use_container_width=True,
                )

            if submitted_4:
                # Jetzt >= 0.0, damit 0-Euro-Zeilen ebenfalls berücksichtigt werden
                gueltige_abbuchungen = df_editiert_4[df_editiert_4["abbuchung"] >= 0.0]

                if gueltige_abbuchungen.empty:
                    st.warning("Keine Beträge zur Abbuchung eingetragen.")
                elif aktuelle_task_id is None:
                    st.error("Keine gültige task_id gefunden.")
                else:
                    abbuchung_tasks = [
                        (row, aktuelle_task_id) for _, row in gueltige_abbuchungen.iterrows()
                    ]

                    # 1. Asynchrones Speichern der Wallet-Abbuchungen
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        ergebnisse = list(
                            executor.map(process_save_abbuchung_s4, abbuchung_tasks)
                        )

                    erfolgreich = sum(1 for success, _ in ergebnisse if success)
                    fehler_details = [
                        err_msg for success, err_msg in ergebnisse if not success and err_msg
                    ]

                    # 2. Asynchrones Status-Update auf DONE (analog zu Schritt 2)
                    if erfolgreich > 0:
                        def update_status_buchung_async(task_id):
                            try:
                                status_url = f"{BASE_URL}/tasks/{task_id}/update_status_buchung"
                                res = requests.put(
                                    status_url, params={"new_state": "DONE"}, timeout=5
                                )
                                return res.status_code in [200, 201], res.text
                            except Exception as ex:
                                return False, str(ex)


                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(update_status_buchung_async, aktuelle_task_id)
                            status_success, status_msg = future.result()

                        if status_success:
                            st.success("🎉 Abbuchungen erfolgreich gespeichert und Status auf DONE gesetzt!")
                            st.session_state.current_db_status_buchung = "DONE"
                        else:
                            st.warning(
                                f"Abbuchung OK, aber Status-Update fehlgeschlagen: {status_msg}"
                            )

                        load_task_into_state(aktives_datum)
                        st.rerun()

                    if fehler_details:
                        st.error("⚠️ Folgende Abbuchungen schlugen fehl:")
                        for fehler in fehler_details:
                            st.code(fehler, language="txt")