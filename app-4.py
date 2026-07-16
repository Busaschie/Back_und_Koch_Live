import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://localhost:8000"  # uvicorn -> restapi

# Seite auf weites Layout stellen, damit links und rechts genug Platz ist
st.set_page_config(layout="wide")


# API-Abfrage (wird von Streamlit gecacht)
@st.cache_data
def get_api_data_user():
    try:
        response = requests.get(f"{BASE_URL}/users")
        df = pd.DataFrame(response.json())
        return df[['vorname', 'nachname', 'buchnummer']].copy()
    except Exception as e:
        # Falls die API mal offline ist, stürzt die App nicht ab
        st.error(f"Fehler beim Laden der API: {e}")
        return pd.DataFrame(columns=['vorname', 'nachname', 'buchnummer'])

df_user_gefiltert = get_api_data_user()

@st.cache_data
def get_api_data_task():
    try:
        response = requests.get(f"{BASE_URL}/tasks")
        df = pd.DataFrame(response.json())
        #st.write(df)
        return df[['shop_date']].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der API: {e}")
        return pd.DataFrame(columns=['shop_date'])

df_task_gefiltert = get_api_data_task()

@st.cache_data
def get_api_one_task(shop_date: str):
    try:
        params = {"shop_date": shop_date}
        response = requests.get(f"{BASE_URL}/tasks/tasks1", params=params)
        data = response.json()
        if isinstance(data, dict):
            df = pd.DataFrame(data, index=[0])
            st.write("Verfügbare Spalten im DataFrame:", df.columns.tolist())
        else:
            df = pd.DataFrame(data)
        return df[['monat', 'jahr', 'shop_date', 'abgabe_date', 'geld_date']].copy()
    except Exception as e:
        st.error(f"Fehler beim Laden der API: {e}")
        return pd.DataFrame(columns=['monat', 'jahr', 'shop_date', 'abgabe_date', 'geld_date'])

gewuenschtes_datum = "2026-07-13"
df_one_task_gefiltert = get_api_one_task(shop_date=gewuenschtes_datum)

# ==========================================
# 1. NAVIGATION (Ganz oben über die volle Breite)
# ==========================================
with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_spacer = st.columns([1, 1, 1, 7])
    with nav_col1:
        # Link zu deiner Startseite (oder externen URL)
        st.link_button("Vorgänge", "http://localhost:8501/app.py", width='stretch')
    with nav_col2:
        st.link_button("Konten", "https://deine-website.de/dashboard", width='stretch')
    with nav_col3:
        st.link_button("Waren", "https://deine-website.de/settings", width='stretch')
st.write("---")  # Trennlinie

# ==========================================
# MAIN LAYOUT (Aufteilung in Links und Rechts)
# ==========================================
# 20% Breite für Links (Einkäufe), 80% Breite für Rechts (Übersichten)
col_links, col_rechts = st.columns([2, 8])

# --- LINKE SEITE: Container für Einkäufe ---
with col_links:
    with st.container(border=True):
        st.subheader("📋 Einkäufe")
        #st.link_button("Neuer Task", "http://localhost:8501/app.py", width='stretch')
        #st.page_link("http://localhost:8501/app.py", label="Neuer Task", use_container_width=True)
        if st.button("Neuer Vorgang", use_container_width=True):
            st.rerun()
        st.dataframe(df_task_gefiltert, hide_index=True, width='stretch')



# --- RECHTE SEITE: Die 4 aufklappbaren Übersichten ---
with col_rechts:
    with st.container(border=True):
        st.subheader("Bestellvorgang")

        # Expander 1
        with st.expander("Schritt 1: Vorgangs-Informationen festlegen", expanded=True):
            st.dataframe(df_one_task_gefiltert, hide_index=True, width='stretch')

        # Expander 2
        with st.expander("Schritt 2: Sammelbuchung"):
            # Kopie erstellen und die Status-Spalte für das Dropdown hinzufügen
            df_mit_status = df_user_gefiltert.copy()
            df_mit_status["Betrag"] = "Bitte wählen..."

            # Der Data Editor
            df_editiert = st.data_editor(
                df_mit_status,
                column_config={
                    "Betrag": st.column_config.SelectboxColumn(
                        "Betrag",  # Spaltenüberschrift in der Tabelle
                        help="Wähle einen Betrag für den Nutzer",
                        width="medium",
                        options=["Betrag", "0", "13", "15", "25"],
                        required=True,
                    )
                },
                disabled=["vorname", "nachname", 'buchnummer'],  # Namen sind schreibgeschützt
                hide_index=True,
                width='stretch',
                key="sammelbuchung"  # Eindeutiger Key für Streamlit
            )
            st.link_button("Speichern", "http://localhost:8501/app.py", width='content')

        # Expander 3
        with st.expander("Schritt 3: Einkaufsliste"):
            st.dataframe(df_user_gefiltert, hide_index=True, width='stretch')

        # Expander 4
        with st.expander("Schritt 4: Abbuchung"):
            # Kopie erstellen und die Status-Spalte für das Dropdown hinzufügen
            df_mit_status = df_user_gefiltert.copy()
            df_mit_status["Betrag"] = "Bitte wählen..."

            # Der Data Editor
            df_editiert = st.data_editor(
                df_mit_status,
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status",  # Spaltenüberschrift in der Tabelle
                        help="Wähle einen Status für den Nutzer",
                        width="medium",
                        options=["0", "13", "15", "25"],
                        required=True,
                    )
                },
                disabled=["vorname", "nachname"],  # Namen sind schreibgeschützt
                hide_index=True,
                width='stretch',
                key="abbuchung"  # Eindeutiger Key für Streamlit
            )