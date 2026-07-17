import requests
import pandas as pd
import streamlit as st
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Seite konfigurieren
st.set_page_config(layout="wide", page_title="Gesamtübersicht Kontostände")

# Holt sich die task_id direkt aus dem globalen Session-State
task_id = st.session_state.get("print_task_id")

if task_id:
    task_id = int(task_id)
    # optional zur visuellen Kontrolle:
    st.info(f"Druckansicht aktiv für Vorgangs-ID: {task_id}")

    # HIER kommt dein ganz normaler Code hin, um die Daten vom Backend zu laden:
    # response = requests.get(f"{BASE_URL}/tasks/{task_id}/details")
else:
    st.error("Keine aktive Vorgangs-ID gefunden! Bitte wähle zuerst auf der Hauptseite einen Vorgang aus.")

    # Ein kleiner Button, um den Nutzer zurück zur Hauptseite zu bringen
    if st.button("🔙 Zurück zur Hauptseite"):
        st.switch_page("main.py")  # Falls deine Hauptdatei main.py heißt, sonst anpassen
    st.stop()

# --- Hilfsfunktion zur Formatierung der Buchnummer ---
def format_buchnummer(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if len(val_str) > 4:
        return f"{val_str[:-4]}/{val_str[-4:]}"
    return val_str


# --- CSS für exakte A4-Darstellung und sauberen Ausdruck ---
st.markdown("""
    <style>
    /* Ausblenden der Streamlit-UI beim Ausdruck */
    @media print {
        header, footer, .stButton, div[data-testid="stSidebar"], div[data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container {
            padding: 0px !important;
            margin: 0px !important;
        }
        body {
            background-color: #ffffff;
        }
        .a4-page {
            box-shadow: none !important;
            margin: 0px !important;
            border: none !important;
        }
    }

    /* Bildschirm-Vorschau Styling (simuliert ein A4-Blatt) */
    .a4-page {
        background: white;
        width: 21cm;
        min-height: 29.7cm;
        padding: 1.5cm 1.8cm;
        margin: 25px auto;
        font-family: 'Arial', sans-serif;
        color: #000000;
        box-shadow: 0 0 10px rgba(0,0,0,0.15);
        border: 1px solid #cccccc;
        box-sizing: border-box;
    }

    /* Header & Titel */
    .title-block {
        border-bottom: 2px solid #000000;
        padding-bottom: 5px;
        margin-bottom: 20px;
    }
    .main-title {
        font-size: 22px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .sub-title {
        font-size: 14px;
        font-weight: normal;
        color: #333333;
        margin-top: 3px;
    }

    /* Tabelle */
    .overview-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-bottom: 25px;
    }
    .overview-table th, .overview-table td {
        border: 1px solid #000000;
        padding: 6px 10px;
        text-align: left;
    }
    .overview-table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }

    /* Berechnungs- und Infoblock am Ende */
    .summary-box {
        margin-top: 20px;
        font-size: 13px;
        line-height: 1.6;
        border-top: 1px dashed #000000;
        padding-top: 12px;
    }
    .summary-line {
        display: flex;
        justify-content: space-between;
        max-width: 550px;
        margin-bottom: 4px;
    }
    .summary-label {
        font-weight: bold;
    }

    .print-date {
        font-size: 10px;
        color: #555555;
        margin-top: 30px;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)


# --- API Datenabruf ---
def load_overview_data():
    try:
        # 1. Alle Benutzer laden
        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste."
        users = user_res.json()

        # 2. Aktive/offene Einkaufstask laden für Beträge
        einkauf_aktuell = 0.0
        task_res = requests.get(f"{BASE_URL}/tasks/open", timeout=5)
        if task_res.status_code == 200 and task_res.json():
            open_task = task_res.json()[0]
            # Betrag aus der DB auslesen (z.B. Feld 'warenwert' oder 'einkauf_summe', hier als Fallback 0.0)
            einkauf_aktuell = float(open_task.get("warenwert", 0.0))

        # 3. Kontostände aus den Wallets sammeln
        print_dataset = []
        gesamt_kontostand = 0.0

        for u in users:
            wallet_res = requests.get(f"{BASE_URL}/wallets/wallet_user", params={"buchnummer": u["buchnummer"]},
                                      timeout=5)
            wallets = wallet_res.json() if wallet_res.status_code == 200 else []

            current_balance = 0.0
            if wallets:
                df_w = pd.DataFrame(wallets)
                if "date" in df_w.columns:
                    df_w = df_w.sort_values(by="date", ascending=False)
                    current_balance = float(df_w.iloc[0]["new_amount"])

            gesamt_kontostand += current_balance
            print_dataset.append({
                "buchnummer": u["buchnummer"],
                "name": f"{u['vorname']} {u['nachname']}",
                "balance": current_balance
            })

        # Sortieren nach Name für eine saubere alphabetische Liste
        print_dataset = sorted(print_dataset, key=lambda x: x["name"])

        context_data = {
            "dataset": print_dataset,
            "gesamt_kontostand": gesamt_kontostand,
            "einkauf_aktuell": einkauf_aktuell,
            "ueberschuss": gesamt_kontostand - einkauf_aktuell
        }
        return context_data, None

    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


# --- Bildschirm-UI (wird beim Drucken ausgeblendet) ---
st.write("### 🖨️ Gesamtübersicht aller Kontostände drucken")
st.info(
    "💡 **Tipp zum Drucken:** Drücke `STRG + P`, um die Liste sauber formatiert als A4-Dokument zu drucken oder als PDF zu speichern.")

if st.button("🔄 Ansicht aktualisieren"):
    st.rerun()

st.write("---")

context, error = load_overview_data()

if error:
    st.error(error)
elif not context:
    st.warning("Keine Daten vorhanden.")
else:
    druck_zeitpunkt = datetime.now().strftime('%d.%m.%Y um %H:%M')

    # HTML Aufbau ohne Einrückungen am Zeilenanfang (wichtig!)
    html_gesamt = f"""
<div class="a4-page">
<div class="title-block">
<div class="main-title">Back- & Kocheinkauf</div>
<div class="sub-title">Gesamtübersicht aller Personen und Kontostände</div>
</div>

<table class="overview-table">
<tr>
<th style="width: 25%;">Buchnummer</th>
<th style="width: 50%;">Name</th>
<th style="width: 25%; text-align: right;">Kontostand</th>
</tr>
"""

    for item in context["dataset"]:
        formatierte_nr = format_buchnummer(item["buchnummer"])
        user_balance_str = f"{item['balance']:,.2f} €".replace(".", ",")

        html_gesamt += f"""
<tr>
<td>{formatierte_nr}</td>
<td>{item['name']}</td>
<td style="text-align: right; font-weight: bold;">{user_balance_str}</td>
</tr>
"""

    # Formatierung der finalen Summenbeträge
    gesamt_str = f"{context['gesamt_kontostand']:,.2f} €".replace(".", ",")
    einkauf_str = f"{context['einkauf_aktuell']:,.2f} €".replace(".", ",")
    ueberschuss_str = f"{context['ueberschuss']:,.2f} €".replace(".", ",")

    html_gesamt += f"""
</table>

<div class="summary-box">
<div class="summary-line">
<span class="summary-label">Aktueller Kontostand (Gesamt):</span>
<span>{gesamt_str}</span>
</div>
<div class="summary-line">
<span class="summary-label">Bar ausgezahlt für aktuellen Einkauf (Warenwert):</span>
<span>{einkauf_str}</span>
</div>
<div class="summary-line" style="border-top: 1px solid #000; margin-top: 4px; padding-top: 4px;">
<span class="summary-label">Alter Kontostand jetzt Überschuss in Bar für aktuellen Einkauf:</span>
<span style="font-weight: bold;">{ueberschuss_str}</span>
</div>
</div>

<div class="print-date">Druckdatum: {druck_zeitpunkt} Uhr</div>
</div>
"""

    # Ausgabe über die native HTML-Komponente
    st.html(html_gesamt)