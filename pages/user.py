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

# ==========================================
# 0. SESSION STATE INITIALISIERUNG
# ==========================================
if "selected_user_index" not in st.session_state:
    st.session_state.selected_user_index = None

if "users_list" not in st.session_state:
    st.session_state.users_list = None

if "create_mode" not in st.session_state:
    st.session_state.create_mode = False

if "manual_booking_mode" not in st.session_state:
    st.session_state.manual_booking_mode = False


# --- API-Ladefunktionen ---
def load_users():
    """Lädt alle User aus der Datenbank."""
    try:
        response = requests.get(f"{BASE_URL}/users", timeout=5)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.session_state.users_list = df
            return df
    except Exception as e:
        st.error(f"Fehler beim Laden der User-Daten: {e}")
    st.session_state.users_list = pd.DataFrame()
    return st.session_state.users_list


def load_wallets_by_buchnummer(buchnummer: str):
    reine_buchnummer = str(buchnummer).replace("/", "")
    try:
        wallet_response = requests.get(
            f"{BASE_URL}/wallets/wallet_user",
            params={"buchnummer": reine_buchnummer},
            timeout=5,
        )
        if wallet_response.status_code == 200:
            return pd.DataFrame(wallet_response.json())
    except Exception as e:
        st.warning(f"Fehler beim Laden der Wallet-Daten: {e}")
    return pd.DataFrame()

# CSS zum Anpassen der Farbe des "Neuer Artikel"-Buttons
st.markdown(
    """
    <style>
    /* Passt nur den Primary-Button an */
    div.stButton > button[kind="primary"] {
        background-color: #41ad5a !important; /* Hier deine Wunschfarbe (z. B. Grün) */
        color: white !important;               /* Textfarbe */
        border-color: #28a745 !important;
    }
    /* Hover-Effekt (wenn man mit der Maus drüber fährt) */
    div.stButton > button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# User initial oder bei Bedarf laden
if st.session_state.users_list is None:
    load_users()

df_users = st.session_state.users_list

# ==========================================
# MAIN LAYOUT
# ==========================================
col_links, col_rechts = st.columns([3, 7])

# --- LINKE SEITE: User-Auswahlliste & Buttons ---
with col_links:
    with st.container(border=True):
        st.subheader("👥 Benutzerverwaltung")

        # Button zum Starten des Erstellungsprozesses
        if st.button("➕ Neuer User", width="stretch", type="primary"):
            st.session_state.create_mode = True
            st.session_state.manual_booking_mode = False
            st.session_state.selected_user_index = None

            # WICHTIG: Tabellen-Auswahl im Session State zurücksetzen!
            if "user_select_table" in st.session_state:
                del st.session_state["user_select_table"]

            st.rerun()

        # NEUER GRÜNER BUTTON ZUM DRUCKEN DER KONTOSTÄNDE
        if st.button("🖨️ Kontostände drucken", width="stretch", type="secondary"):
            st.switch_page("pages/userkonto_druck.py")

        st.write("---")

        if df_users.empty:
            st.info("Keine Benutzer in der Datenbank gefunden.")
        else:
            df_anzeige = df_users[["vorname", "nachname"]].copy()

            column_config_links = {
                "vorname": st.column_config.TextColumn("VORNAME"),
                "nachname": st.column_config.TextColumn("NACHNAME"),
            }

            event = st.dataframe(
                df_anzeige,
                column_config=column_config_links,
                hide_index=True,
                width="stretch",
                on_select="rerun",
                selection_mode="single-row",
                key="user_select_table",
            )

            selected_rows = event.get("selection", {}).get("rows", [])

            # Nur verarbeiten, wenn WIRKLICH ein User ausgewählt wurde und nicht "Neuer User" aktiv ist
            if selected_rows and not st.session_state.create_mode:
                neuer_index = selected_rows[0]
                if st.session_state.selected_user_index != neuer_index:
                    st.session_state.manual_booking_mode = False

                st.session_state.selected_user_index = neuer_index

# --- RECHTE SEITE: Formulare ---
with col_rechts:
    # ----------------------------------------------------
    # FALL A: Neuer User wird angelegt
    # ----------------------------------------------------
    if st.session_state.create_mode:
        with st.container(border=True):
            st.subheader("➕ Neuen Benutzer anlegen")

            with st.form("create_user_form", clear_on_submit=True):
                col_v, col_n = st.columns(2)
                with col_v:
                    neu_vorname = st.text_input("Vorname", value="")
                with col_n:
                    neu_nachname = st.text_input("Nachname", value="")

                col_b, col_e = st.columns(2)
                with col_b:
                    neu_buchnummer = st.text_input(
                        "Buchnummer (8-stellig, z.B. 12342020)", value=""
                    )
                with col_e:
                    neu_zimmer = st.number_input(
                        "Zellennummer",
                        min_value=1,
                        max_value=999,
                        step=1,
                        value=100,
                    )

                st.write("")
                col_save_neu, col_cancel, col_spacer = st.columns([3, 3, 4])
                with col_save_neu:
                    create_submitted = st.form_submit_button(
                        "💾 User speichern", width="stretch"
                    )
                with col_cancel:
                    create_canceled = st.form_submit_button(
                        "❌ Abbrechen", type="secondary", width="stretch"
                    )

            if create_submitted:
                if not neu_vorname or not neu_nachname or not neu_buchnummer:
                    st.error(
                        "Bitte fülle alle Pflichtfelder (Vorname, Nachname, Buchnummer) aus."
                    )
                else:
                    saubere_buchnummer = (
                        str(neu_buchnummer).replace("/", "").strip()
                    )

                    payload = {
                        "vorname": neu_vorname,
                        "nachname": neu_nachname,
                        "zimmer_nr": int(neu_zimmer),
                        "buchnummer": saubere_buchnummer,
                    }
                    try:
                        response = requests.post(
                            f"{BASE_URL}/users/create", json=payload, timeout=5
                        )
                        if response.status_code in [200, 201]:
                            st.success(
                                f"🎉 Benutzer {neu_vorname} {neu_nachname} erfolgreich angelegt!"
                            )
                            st.session_state.create_mode = False
                            load_users()
                            st.rerun()
                        else:
                            # Sichere Fehlerbehandlung (verhindert JSONDecodeError)
                            try:
                                err_detail = response.json().get("detail", response.text)
                            except Exception:
                                err_detail = response.text or f"HTTP Fehler {response.status_code}"
                            st.error(f"Fehler beim Anlegen: {err_detail}")

                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")

    # ----------------------------------------------------
    # FALL B: Bestehender User ausgewählt (Bearbeiten)
    # ----------------------------------------------------
    elif st.session_state.selected_user_index is not None and not df_users.empty:
        idx = st.session_state.selected_user_index
        user_row = df_users.iloc[idx]
        user_id = int(user_row["id"])

        rohe_buchnummer = str(user_row["buchnummer"]).replace("/", "")
        formatierte_buchnummer = format_buchnummer(rohe_buchnummer)
        zimmer = str(user_row["zimmer_nr"])

        # Oberer Container: User-Daten editieren
        with st.container(border=True):
            st.subheader("📝 Benutzerdetails bearbeiten")

            with st.form("edit_user_form", clear_on_submit=False):
                col_v, col_n = st.columns(2)
                with col_v:
                    vorname = st.text_input(
                        "Vorname", value=str(user_row["vorname"])
                    )
                with col_n:
                    nachname = st.text_input(
                        "Nachname", value=str(user_row["nachname"])
                    )

                col_b, col_e = st.columns(2)
                with col_b:
                    st.text_input(
                        "Buchnummer", disabled=True, value=formatierte_buchnummer
                    )
                with col_e:
                    zimmer = st.text_input(
                        "Zellennummer", value=str(user_row["zimmer_nr"])
                    )

                st.write("")
                col_save, col_delete, col_spacer = st.columns([2, 2, 6])

                with col_save:
                    save_submitted = st.form_submit_button(
                        "💾 Speichern", width="stretch"
                    )
                with col_delete:
                    delete_submitted = st.form_submit_button(
                        "🗑️ Löschen", type="secondary", width="stretch"
                    )

            # --- Logik: Speichern ---
            if save_submitted:
                payload = {
                    "vorname": vorname,
                    "nachname": nachname,
                    "zimmer_nr": zimmer,
                }
                try:
                    response = requests.put(
                        f"{BASE_URL}/users/{rohe_buchnummer}/update_user",
                        json=payload,
                        timeout=5,
                    )
                    if response.status_code in [200, 201]:
                        st.success("🎉 Benutzerdaten erfolgreich aktualisiert!")
                        load_users()
                        st.rerun()
                    else:
                        st.error(f"Fehler beim Speichern: {response.text}")
                except Exception as e:
                    st.error(f"Verbindung zur API fehlgeschlagen: {e}")

            # --- Logik: Löschen ---
            if delete_submitted:
                try:
                    response = requests.delete(
                        f"{BASE_URL}/users/{rohe_buchnummer}/delete_user",
                        timeout=5,
                    )
                    if response.status_code == 200:
                        st.success(
                            "🔥 Benutzer und alle verknüpften Wallet-Einträge gelöscht!"
                        )
                        st.session_state.selected_user_index = None
                        if "user_select_table" in st.session_state:
                            del st.session_state["user_select_table"]
                        load_users()
                        st.rerun()
                    else:
                        st.error(f"Fehler beim Löschen: {response.text}")
                except Exception as e:
                    st.error(f"Verbindung zur API fehlgeschlagen: {e}")

        st.write("")

        # Unterer Container: Wallet-Buchungen anzeigen & Manuelle Buchung
        with st.container(border=True):
            st.subheader(
                f"💳 Wallet-Buchungsverlauf (Buchnummer: {formatierte_buchnummer})"
            )

            # BUTTON ZUM ÖFFNEN DES MANUELLEN BUCHUNGSFORMULARS
            if not st.session_state.manual_booking_mode:
                if st.button(
                        "💶 Manuelle Buchung durchführen",
                        type="primary",
                        width="stretch",
                ):
                    st.session_state.manual_booking_mode = True
                    st.rerun()

            # FORMULAR FÜR MANUELLE BUCHUNG
            if st.session_state.manual_booking_mode:
                with st.container(border=True):
                    st.markdown("### 💶 Manuelle Buchung")
                    with st.form("manual_booking_form", clear_on_submit=True):
                        col_art, col_betrag = st.columns(2)
                        with col_art:
                            buchungs_art = st.selectbox(
                                "Buchungsart",
                                options=[
                                    "Hinzubuchen (+)",
                                    "Abbuchen (-)",
                                ],
                            )
                        with col_betrag:
                            betrag_eingabe = st.number_input(
                                "Betrag in €",
                                min_value=0.01,
                                max_value=10000.00,
                                step=0.50,
                                value=10.00,
                                format="%.2f",
                            )

                        grund_eingabe = st.text_input(
                            "Grund der Buchung / Verwendungszweck",
                            placeholder="z.B. Manuelle Einzahlung, Korrektur, Extra-Guthaben",
                        )

                        st.write("")
                        col_b_save, col_b_cancel, col_b_spacer = st.columns(
                            [3, 3, 4]
                        )
                        with col_b_save:
                            booking_submitted = st.form_submit_button(
                                "💾 Buchung ausführen", width="stretch"
                            )
                        with col_b_cancel:
                            booking_canceled = st.form_submit_button(
                                "❌ Abbrechen",
                                type="secondary",
                                width="stretch",
                            )

                    if booking_canceled:
                        st.session_state.manual_booking_mode = False
                        st.rerun()

                    if booking_submitted:
                        if not grund_eingabe.strip():
                            st.error(
                                "Bitte gib einen Grund für die Buchung an."
                            )
                        else:
                            old_amount = 0.0
                            try:
                                wallet_res = requests.get(
                                    f"{BASE_URL}/wallets/last",
                                    params={"buchnummer": rohe_buchnummer},
                                    timeout=5,
                                )
                                if wallet_res.status_code == 200:
                                    old_amount = float(
                                        wallet_res.json().get(
                                            "new_amount", 0.0
                                        )
                                    )
                            except Exception:
                                old_amount = 0.0

                            is_deposit = "Hinzubuchen" in buchungs_art
                            betrag_final = (
                                betrag_eingabe if is_deposit else -betrag_eingabe
                            )
                            new_amount = old_amount + betrag_final

                            wallet_payload = {
                                "task_id": 0,
                                "buchnummer": rohe_buchnummer,
                                "betrag": betrag_final,
                                "old_amount": old_amount,
                                "new_amount": new_amount,
                                "grund": grund_eingabe.strip(),
                                "date": str(date.today()),
                            }

                            try:
                                post_response = requests.post(
                                    f"{BASE_URL}/wallets/save",
                                    json=wallet_payload,
                                    timeout=5,
                                )
                                if post_response.status_code in [200, 201]:
                                    st.success(
                                        f"🎉 Buchung von {betrag_final:+.2f} € erfolgreich durchgeführt!"
                                    )
                                    st.session_state.manual_booking_mode = False
                                    st.rerun()
                                else:
                                    st.error(
                                        f"Fehler beim Speichern der Buchung: {post_response.text}"
                                    )
                            except Exception as e:
                                st.error(
                                    f"Verbindung zur API fehlgeschlagen: {e}"
                                )

            st.write("---")

            # WALLET-TABELLE ANZEIGEN
            df_wallets = load_wallets_by_buchnummer(rohe_buchnummer)

            if df_wallets.empty:
                st.info(
                    "Für diesen Benutzer existieren noch keine Wallet-Buchungen."
                )
            else:
                # Sortierung nach Wallet-ID absteigend (neuste zuerst)
                if "id" in df_wallets.columns:
                    df_wallets = df_wallets.sort_values(
                        by="id", ascending=False
                    )

                column_config_wallets = {
                    "id": None,
                    "task_id": st.column_config.NumberColumn("VORGANGS-ID"),
                    "buchnummer": None,
                    "betrag": st.column_config.NumberColumn(
                        "BETRAG", format="%.2f €"
                    ),
                    "old_amount": st.column_config.NumberColumn(
                        "SALDO ALT", format="%.2f €"
                    ),
                    "new_amount": st.column_config.NumberColumn(
                        "SALDO NEU", format="%.2f €"
                    ),
                    "grund": st.column_config.TextColumn("VERWENDUNGSZWECK"),
                    "date": st.column_config.DateColumn(
                        "DATUM", format="DD.MM.YYYY"
                    ),
                }

                st.dataframe(
                    df_wallets,
                    column_config=column_config_wallets,
                    hide_index=True,
                    width="stretch",
                )
    else:
        st.info(
            "👈 Bitte wähle links einen Benutzer aus oder klicke auf 'Neuer User'."
        )