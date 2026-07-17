import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://localhost:8000" # unicorn -> restapi
#BASE_URL = "127.0.0.1:8000" # alternative IP

import streamlit as st
import pandas as pd
import requests

# 1. Daten holen und DataFrame erstellen
response = requests.get(f"{BASE_URL}/users")
df = pd.DataFrame(response.json())

# 2. Bestehende Spalten filtern
df_gefiltert = df[['vorname', 'nachname']].copy()

# 3. Eine neue, leere Spalte für die Auswahl hinzufügen (z. B. mit einem Standardwert)
df_gefiltert['Status'] = 'Bitte wählen...'

# 4. Den Data Editor mit Dropdown-Konfiguration anzeigen
df_editiert = st.data_editor(
    df_gefiltert,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "app.py",
            help="Wähle einen Status für den Nutzer",
            width="medium",
            options=["Bitte wählen...", "Aktiv", "Inaktiv"],
            required=True,
        )
    },
    disabled=["vorname", "nachname"], # Verhindert, dass man die Namen editiert
    hide_index=True,
)

# In 'df_editiert' stehen jetzt die vom Benutzer ausgewählten Werte!

#def welcome():
#user = st.session_state.get("user")
#st.text(user)
#user = user["nachname"]

#st.title("User Client")
#st.text(user)

#if st.session_state["user"]:
#    welcome()

#if st.session_state["is_logged_in"] and "user" in st.session_state:
 #   welcome()
#else:
#    login()