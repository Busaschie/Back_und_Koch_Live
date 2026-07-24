from datetime import date
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

# Seite auf weites Layout stellen
st.set_page_config(layout="wide")

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

# ==========================================
# 0. SESSION STATE INITIALISIERUNG
# ==========================================
if "selected_waren_id" not in st.session_state:
    st.session_state.selected_waren_id = None

if "waren_list" not in st.session_state:
    st.session_state.waren_list = None

if "waren_create_mode" not in st.session_state:
    st.session_state.waren_create_mode = False


# --- API-Ladefunktionen ---
def load_waren():
    """Lädt alle Waren aus der Datenbank."""
    try:
        response = requests.get(f"{BASE_URL}/waren", timeout=5)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.session_state.waren_list = df
            return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Waren-Daten: {e}")
    st.session_state.waren_list = pd.DataFrame()
    return st.session_state.waren_list


# Waren initial oder bei Bedarf laden
if st.session_state.waren_list is None:
    load_waren()

df_waren = st.session_state.waren_list

# ==========================================
# MAIN LAYOUT
# ==========================================
col_links, col_rechts = st.columns([3, 7])

# --- LINKE SEITE: Kategorien & Waren-Navigation ---
with col_links:
    with st.container(border=True):
        st.subheader("📦 Warenverwaltung")

        # Button zum Starten des Erstellungsprozesses
        if st.button("➕ Neuer Artikel", width="stretch", type="primary"):
            st.session_state.waren_create_mode = True
            st.session_state.selected_waren_id = None  # Auswahl zurücksetzen
            st.rerun()

        if st.button("📦 Warenliste drucken", type="secondary", use_container_width=True):
            st.switch_page("pages/waren_druck.py")

        st.write("---")

        if df_waren.empty:
            st.info("Keine Artikel in der Datenbank gefunden.")
        else:
            # Gruppieren nach Kategorien für die linke Navigation
            kategorien = sorted(df_waren["kategorie"].unique())

            for kat in kategorien:
                # Jede Kategorie bekommt einen eigenen Expander links
                with st.expander(f"📂 {str(kat).upper()}", expanded=False):
                    df_kat = df_waren[df_waren["kategorie"] == kat]

                    # Einzelne Artikel als klickbare Buttons listen
                    for _, row in df_kat.iterrows():
                        artikel_label = f"{row['bezeichnung']} ({row['menge']} {row.get('art', 'Stk.')})"

                        # Hervorhebung falls aktuell ausgewählt
                        is_selected = st.session_state.selected_waren_id == row["id"]
                        btn_type = "primary" if is_selected else "secondary"

                        if st.button(artikel_label, key=f"nav_item_{row['id']}", width="stretch", type=btn_type):
                            st.session_state.selected_waren_id = row["id"]
                            st.session_state.waren_create_mode = False
                            st.rerun()

# --- RECHTE SEITE: Formulare ---
with col_rechts:
    # ----------------------------------------------------
    # FALL A: Neue Ware anlegen
    # ----------------------------------------------------
    if st.session_state.waren_create_mode:
        with st.container(border=True):
            st.subheader("➕ Neuen Artikel anlegen")

            with st.form("create_waren_form", clear_on_submit=True):
                col_b, col_k = st.columns(2)
                with col_b:
                    neu_bezeichnung = st.text_input("Bezeichnung*", value="")
                with col_k:
                    # Kategorie entweder per Text oder Selectbox (z.B. bestehende Kategorien anbieten)
                    bestehende_kat = list(df_waren["kategorie"].unique()) if not df_waren.empty else []
                    neu_kategorie = st.text_input("Kategorie*", value="")

                col_m, col_a, col_p = st.columns(3)
                with col_m:
                    neu_menge = st.number_input("Vorhandene Menge", min_value=0, step=1, value=0)
                with col_a:
                    neu_art = st.text_input("Einheit (z.B. Stk, Flasche, kg)", value="Stk.")
                with col_p:
                    neu_preis = st.number_input("Preis (€)*", min_value=0.0, max_value=1000.0, step=0.01, format="%.2f",
                                                value=0.0)

                st.write("")
                col_save_neu, col_cancel, _ = st.columns([3, 3, 4])
                with col_save_neu:
                    create_submitted = st.form_submit_button("💾 Artikel speichern", width="stretch")
                with col_cancel:
                    create_canceled = st.form_submit_button("❌ Abbrechen", type="secondary", width="stretch")

            if create_canceled:
                st.session_state.waren_create_mode = False
                st.rerun()

            if create_submitted:
                if not neu_bezeichnung or not neu_kategorie:
                    st.error("Bitte fülle alle Pflichtfelder (*) aus.")
                else:
                    payload = {
                        "bezeichnung": neu_bezeichnung.strip(),
                        "kategorie": neu_kategorie.strip().lower(),
                        "menge": int(neu_menge),
                        "art": neu_art.strip(),
                        "preis": float(neu_preis)
                    }
                    try:
                        response = requests.post(f"{BASE_URL}/waren/save", json=payload, timeout=5)
                        if response.status_code in [200, 201]:
                            st.success(f"🎉 Artikel '{neu_bezeichnung}' erfolgreich angelegt!")
                            st.session_state.waren_create_mode = False
                            load_waren()  # Daten neu aus der DB ziehen
                            st.rerun()
                        else:
                            st.error(f"Fehler: {response.text}")
                    except Exception as e:
                        st.error(f"Verbindung zur API fehlgeschlagen: {e}")

    # ----------------------------------------------------
    # FALL B: Bestehende Ware ausgewählt (Bearbeiten)
    # ----------------------------------------------------
    elif st.session_state.selected_waren_id is not None and not df_waren.empty:
        w_id = st.session_state.selected_waren_id
        waren_row = df_waren[df_waren["id"] == w_id].iloc[0]

        with st.container(border=True):
            st.subheader("📝 Artikeldetails bearbeiten")

            with st.form("edit_waren_form", clear_on_submit=False):
                col_b, col_k = st.columns(2)
                with col_b:
                    bezeichnung = st.text_input("Bezeichnung", value=str(waren_row["bezeichnung"]))
                with col_k:
                    kategorie = st.text_input("Kategorie", value=str(waren_row["kategorie"]))

                col_m, col_a, col_p = st.columns(3)
                with col_m:
                    menge = st.number_input("Vorhandene Menge", min_value=0, step=1, value=int(waren_row["menge"]))
                with col_a:
                    art = st.text_input("Einheit", value=str(waren_row.get("art", "Stk.")))
                with col_p:
                    preis = st.number_input("Preis (€)", min_value=0.0, max_value=1000.0, step=0.01, format="%.2f",
                                            value=float(waren_row["preis"]))

                st.write("")
                col_save, col_delete, _ = st.columns([2, 2, 6])

                with col_save:
                    save_submitted = st.form_submit_button("💾 Speichern", width="stretch")
                with col_delete:
                    delete_submitted = st.form_submit_button("🗑️ Löschen", type="secondary", width="stretch")

            # --- Logik: Speichern ---
            if save_submitted:
                payload = {
                    "bezeichnung": bezeichnung,
                    "kategorie": kategorie,
                    "menge": int(menge),
                    "art": art,
                    "preis": float(preis)
                }
                try:
                    # Nutzt deinen PUT-Endpunkt: /{waren_id}/update_waren
                    response = requests.put(f"{BASE_URL}/waren/{w_id}/update_waren", json=payload, timeout=5)
                    if response.status_code in [200, 201]:
                        st.success("🎉 Artikeldaten erfolgreich aktualisiert!")
                        load_waren()
                        st.rerun()
                    else:
                        st.error(f"Fehler beim Speichern: {response.text}")
                except Exception as e:
                    st.error(f"Verbindung zur API fehlgeschlagen: {e}")

            # --- Logik: Löschen im Frontend ---
            if delete_submitted:
                try:
                    # Explizit int(w_id) nutzen
                    clean_id = int(w_id)

                    response = requests.delete(
                        f"{BASE_URL}/waren/{clean_id}/waren_delete", params={"waren_id": clean_id}, timeout=5)
                    if response.status_code in [200, 204]:
                        st.success("🔥 Artikel erfolgreich gelöscht!")
                        st.session_state.selected_waren_id = None
                        load_waren()
                        st.rerun()
                    else:
                        # Detaillierte Fehlermeldung anzeigen
                        try:
                            err_msg = response.json().get("detail", response.text)
                        except Exception:
                            err_msg = response.text
                        st.error(f"Fehler beim Löschen: {err_msg}")
                except Exception as e:
                    st.error(f"Verbindung zur API fehlgeschlagen: {e}")

    else:
        st.info("👈 Bitte wähle links aus den Kategorien einen Artikel aus oder klicke auf 'Neuer Artikel'.")