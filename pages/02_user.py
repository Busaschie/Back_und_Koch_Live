from datetime import date
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

# Seite auf weites Layout stellen
st.set_page_config(layout="wide")

# ==========================================
# 0. SESSION STATE INITIALISIERUNG
# ==========================================
if "selected_user_index" not in st.session_state:
    st.session_state.selected_user_index = None

if "users_list" not in st.session_state:
    st.session_state.users_list = None


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
    """Lädt alle Wallet-Buchungen für eine bestimmte Buchnummer."""
    try:
        # Passe diesen Endpunkt an deine API-Route an (z. B. /wallets?buchnummer=...)
        params = {"buchnummer": buchnummer}
        response = requests.get(f"{BASE_URL}/wallets", params=params, timeout=5)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception as e:
        st.warning(f"Fehler beim Laden der Wallet-Daten: {e}")
    return pd.DataFrame()


# User initial oder bei Bedarf laden
if st.session_state.users_list is None:
    load_users()

df_users = st.session_state.users_list


# ==========================================
# MAIN LAYOUT
# ==========================================
col_links, col_rechts = st.columns([3, 7])

# --- LINKE SEITE: User-Auswahlliste ---
with col_links:
    with st.container(border=True):
        st.subheader("👥 Benutzerverwaltung")
        
        if df_users.empty:
            st.info("Keine Benutzer in der Datenbank gefunden.")
        else:
            # Für die linke Spalte filtern wir nur Vorname und Nachname für die Anzeige
            df_anzeige = df_users[["vorname", "nachname"]].copy()
            
            # Großgeschriebene Spaltenüberschriften
            column_config_links = {
                "vorname": st.column_config.TextColumn("VORNAME"),
                "nachname": st.column_config.TextColumn("NACHNAME")
            }
            
            event = st.dataframe(
                df_anzeige,
                column_config=column_config_links,
                hide_index=True,
                width="stretch",
                on_select="rerun",
                selection_mode="single-row",
                key="user_select_table"
            )
            
            selected_rows = event.get("selection", {}).get("rows", [])
            if selected_rows:
                st.session_state.selected_user_index = selected_rows[0]

# --- RECHTE SEITE: Details, Bearbeitung & Buchungen ---
with col_rechts:
    idx = st.session_state.selected_user_index
    
    if idx is not None and not df_users.empty and idx < len(df_users):
        # Aktuell ausgewählten User aus dem Dataframe ziehen
        user_row = df_users.iloc[idx]
        user_id = int(user_row["id"])
        buchnummer = str(user_row["buchnummer"])
        
        # ----------------------------------------------------
        # OBERER CONTAINER: User-Daten editieren
        # ----------------------------------------------------
        with st.container(border=True):
            st.subheader("📝 Benutzerdetails bearbeiten")
            
            # Formular für die Editierung (verhindert Reruns beim Tippen)
            with st.form("edit_user_form", clear_on_submit=False):
                col_v, col_n = st.columns(2)
                with col_v:
                    vorname = st.text_input("Vorname", value=str(user_row["vorname"]))
                with col_n:
                    nachname = st.text_input("Nachname", value=str(user_row["nachname"]))
                
                col_b, col_e = st.columns(2)
                with col_b:
                    # Buchnummer wird oft als ID/Key genutzt, evtl. disabled=True setzen falls unveränderlich
                    neue_buchnummer = st.text_input("Buchnummer", value=buchnummer)
                with col_e:
                    # Falls vorhanden, hier weitere Felder einfügen (z.B. E-Mail)
                    email = st.text_input("E-Mail (optional)", value=str(user_row.get("email", "")))
                
                st.write("")
                col_save, col_delete, col_spacer = st.columns([2, 2, 6])
                
                with col_save:
                    save_submitted = st.form_submit_button("💾 Änderungen speichern", width="stretch")
                with col_delete:
                    # Löschen-Bestätigung über ein Sub-Widget oder direkt als Button
                    delete_submitted = st.form_submit_button("🗑️ Benutzer löschen", type="secondary", width="stretch")
            
            # --- Logik: Speichern ---
            if save_submitted:
                payload = {
                    "vorname": vorname,
                    "nachname": nachname,
                    "buchnummer": neue_buchnummer,
                    "email": email
                }
                try:
                    response = requests.put(f"{BASE_URL}/users/{user_id}", json=payload, timeout=5)
                    if response.status_code in [200, 201]:
                        st.success("🎉 Benutzerdaten erfolgreich aktualisiert!")
                        load_users()  # Daten neu laden
                        st.rerun()
                    else:
                        st.error(f"Fehler beim Speichern: {response.text}")
                except Exception as e:
                    st.error(f"Verbindung zur API fehlgeschlagen: {e}")

            # --- Logik: Löschen ---
            if delete_submitted:
                try:
                    # 1. DELETE-Anfrage für den User senden. 
                    # Tipp: Deine Backend-API sollte so gebaut sein, dass bei `DELETE /users/{id}` 
                    # entweder über DB-Kaskadierung (Cascade Delete) oder manuell im Service 
                    # alle Einträge in `wallets` mit dieser `buchnummer` automatisch mitgelöscht werden.
                    response = requests.delete(f"{BASE_URL}/users/{user_id}", timeout=5)
                    
                    if response.status_code in [200, 204]:
                        st.success(f"🔥 Benutzer und alle verknüpften Wallet-Einträge gelöscht!")
                        st.session_state.selected_user_index = None
                        load_users()  # Liste links aktualisieren
                        st.rerun()
                    else:
                        st.error(f"Fehler beim Löschen des Benutzers: {response.text}")
                except Exception as e:
                    st.error(f"Verbindung zur API fehlgeschlagen: {e}")

        st.write("")

        # ----------------------------------------------------
        # UNTERER CONTAINER: Wallet-Buchungen anzeigen
        # ----------------------------------------------------
        with st.container(border=True):
            st.subheader(f"💳 Wallet-Buchungsverlauf (Buchnummer: {buchnummer})")
            
            # Lade Buchungen basierend auf der aktuellen Buchnummer
            df_wallets = load_wallets_by_buchnummer(buchnummer)
            
            if df_wallets.empty:
                st.info("Für diesen Benutzer existieren noch keine Wallet-Buchungen.")
            else:
                # Sortieren nach Datum (neueste zuerst), falls Spalte existiert
                if "date" in df_wallets.columns:
                    df_wallets = df_wallets.sort_values(by="date", ascending=False)
                
                # Konfiguration für eine schöne Anzeige der Wallet-Einträge
                column_config_wallets = {
                    "id": None,                 # ID nicht anzeigen
                    "task_id": st.column_config.NumberColumn("VORGANGS-ID"),
                    "buchnummer": None,         # Buchnummer ausblenden (steht im Header)
                    "betrag": st.column_config.NumberColumn("BETRAG", format="%.2f €"),
                    "old_amount": st.column_config.NumberColumn("SADO ALT", format="%.2f €"),
                    "new_amount": st.column_config.NumberColumn("SALDO NEU", format="%.2f €"),
                    "grund": st.column_config.TextColumn("VERWENDUNGSZWECK"),
                    "date": st.column_config.DateColumn("DATUM", format="DD.MM.YYYY")
                }
                
                st.dataframe(
                    df_wallets,
                    column_config=column_config_wallets,
                    hide_index=True,
                    width="stretch"
                )
    else:
        st.info("👈 Bitte wähle links einen Benutzer aus, um dessen Details und Buchungen anzuzeigen.")