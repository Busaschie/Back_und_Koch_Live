from datetime import datetime
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

st.set_page_config(
    layout="wide", page_title="Hausgeld Abbuchung Druckansicht"
)

task_id = st.session_state.get("print_task_id")

if task_id:
    task_id = int(task_id)
else:
    st.error(
        "Keine aktive Vorgangs-ID gefunden! Bitte wähle zuerst auf der"
        " Hauptseite einen Vorgang aus."
    )
    if st.button("🔙 Zurück zur Hauptseite"):
        st.switch_page("main.py")
    st.stop()


def format_buchnummer(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if len(val_str) > 4:
        return f"{val_str[:-4]}/{val_str[-4:]}"
    return val_str


# --- CSS: Ausblenden der Sidebar & optimierter A4-Druck ---
st.markdown(
    """
    <style>
    /* 1. DRUCK-MODUS */
    @media print {
        @page {
            size: A4 portrait;
            margin: 0mm;
        }

        header, 
        footer, 
        .stButton, 
        div[data-testid="stSidebar"], 
        section[data-testid="stSidebar"],
        nav[data-testid="stSidebarNav"],
        div[data-testid="stHeader"], 
        .no-print, 
        .stAlert {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
        }

        .main, .main .block-container {
            padding: 0px !important;
            margin: 0px !important;
            width: 100% !important;
            max-width: 100% !important;
        }

        body {
            background-color: #ffffff !important;
        }

        .a4-page {
            box-shadow: none !important;
            border: none !important;
            margin: 0 auto !important;
            padding: 1cm 1.5cm !important;
            width: 100% !important;
            max-width: 21cm !important;
        }
    }

    /* 2. BILDSCHIRM-VORSCHAU */
    .a4-page {
        background: white;
        width: 21cm;
        min-height: 29.7cm;
        padding: 1.2cm 1.5cm;
        margin: 20px auto;
        font-family: 'Arial', sans-serif;
        color: #000000;
        box-shadow: 0 0 10px rgba(0,0,0,0.15);
        border: 1px solid #cccccc;
        box-sizing: border-box;
    }

    .title-header {
        text-align: center;
        border-bottom: 2px solid #000000;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }

    .title-main {
        font-size: 20px;
        font-weight: bold;
        text-transform: uppercase;
    }

    .title-sub {
        font-size: 11px;
        color: #333333;
        margin-top: 4px;
    }

    .user-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        margin-top: 10px;
    }

    .user-table th, .user-table td {
        border: 1px solid #000000 !important;
        padding: 5px 6px;
        vertical-align: middle;
    }

    .user-table th {
        background-color: #f2f2f2 !important;
        font-weight: bold;
        text-align: left;
        -webkit-print-color-adjust: exact;
    }

    .amount-subtext {
        font-size: 10px;
        font-weight: bold;
        color: #000000;
    }

    .box-container {
        display: inline-block;
        margin-right: 12px;
        font-size: 11px;
    }

    .checkbox-mimic {
        display: inline-block;
        width: 11px;
        height: 11px;
        border: 1px solid #000000;
        margin-right: 3px;
        vertical-align: middle;
    }

    .footer-notes {
        font-size: 10px;
        line-height: 1.3;
        margin-top: 15px;
        border-top: 1px solid #000000;
        padding-top: 8px;
    }

    .bold-alert {
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def load_print_data():
    try:
        abgabe_str = "wird bekannt gegeben"

        # 1. Abfrage des spezifischen Tasks über die task_id
        task_res = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=5)
        raw_date = None

        if task_res.status_code == 200 and task_res.json():
            task_data = task_res.json()
            if isinstance(task_data, list) and len(task_data) > 0:
                task_data = task_data[0]

            if isinstance(task_data, dict):
                # Priorität auf geld_date legen!
                raw_date = (
                        task_data.get("geld_date")
                        or task_data.get("gald_date")
                        or task_data.get("abgabe_date")
                )

        # Fallback: Falls Einzelabfrage fehlschlägt, alle Tasks durchsuchen
        if not raw_date:
            all_tasks_res = requests.get(f"{BASE_URL}/tasks/", timeout=5)
            if all_tasks_res.status_code == 200 and isinstance(all_tasks_res.json(), list):
                for t in all_tasks_res.json():
                    if t.get("id") == task_id:
                        raw_date = (
                                t.get("geld_date")
                                or t.get("gald_date")
                                or t.get("abgabe_date")
                        )
                        break

        # Datum von YYYY-MM-DD auf DD.MM.YYYY formatieren
        if raw_date:
            try:
                clean_date = str(raw_date).split("T")[0].strip()
                abgabe_str = datetime.strptime(clean_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                abgabe_str = str(raw_date)

        # 2. Benutzer und Kontostände laden
        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste.", abgabe_str

        users = user_res.json()
        print_dataset = []

        for u in users:
            wallet_res = requests.get(
                f"{BASE_URL}/wallets/wallet_user",
                params={"buchnummer": u["buchnummer"]},
                timeout=5,
            )
            wallets = wallet_res.json() if wallet_res.status_code == 200 else []

            balance = 0.0
            if wallets:
                df_w = pd.DataFrame(wallets)
                if not df_w.empty and "date" in df_w.columns:
                    df_w = df_w.sort_values(by="date", ascending=False)
                    balance = float(df_w.iloc[0]["new_amount"])

            print_dataset.append({"user": u, "balance": balance})

        return print_dataset, None, abgabe_str
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}", "wird bekannt gegeben"


st.markdown(
    f"""
    <div class="no-print" style="background-color: #e8f4f8; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
        <h4 style="margin:0; color: #1e3d59;">🖨️ Hausgeld Abbuchung Druckansicht (Vorgang #{task_id})</h4>
        <p style="margin: 5px 0 0 0; font-size: 13px;">💡 Drücke <code>STRG + P</code> zum Drucken.</p>
    </div>
""",
    unsafe_allow_html=True,
)

if st.button("🔄 Daten frisch synchronisieren", key="sync_btn"):
    st.rerun()

dataset, error, abgabe_termin = load_print_data()

if error:
    st.error(error)
elif not dataset:
    st.warning("Keine Benutzerdaten verfügbar.")
else:
    druck_zeitpunkt = datetime.now().strftime("%d.%m.%Y um %H:%M")
    MOEGLICHE_BETRAEGE = [5, 7, 10, 15, 20, 25]

    html_gesamt = f"""
<div class="a4-page">
<div class="title-header">
<div class="title-main">Abbuchung Hausgeld</div>
<div class="title-sub">Gültig für Vorgang #{task_id} | Erstellt am: {druck_zeitpunkt}</strong></div>
<div class="title-sub" style="font-size: 16px">Eintragen bis: <strong>{abgabe_termin}</strong></div>
</div>
<table class="user-table">
<tr>
<th style="width: 24%;">Name / Kontostand</th>
<th style="width: 10%;">Buchnummer</th>
<th style="width: 46%;">Möglicher Abbuchungsbetrag</th>
<th style="width: 20%;">Unterschrift</th>
</tr>
"""

    for item in dataset:
        user = item["user"]
        balance = item["balance"]
        balance_str = f"{balance:,.2f} €".replace(".", ",")
        formatierte_nr = format_buchnummer(user["buchnummer"])

        html_gesamt += f"""
<tr>
<td>
<strong>{user['vorname']} {user['nachname']}</strong>
<div class="amount-subtext">{balance_str}</div>
</td>
<td>{formatierte_nr}</td>
<td>
"""

        kaestchen_sichtbar = 0
        for betrag in MOEGLICHE_BETRAEGE:
            if (balance + betrag) < 30.0:
                html_gesamt += f"""
<div class="box-container"><span class="checkbox-mimic"></span>{betrag}€</div>
"""
                kaestchen_sichtbar += 1

        if kaestchen_sichtbar == 0:
            html_gesamt += """<span style="color:#666; font-style:italic; font-size:11px;">Konto voll (Max. 30€)</span>"""

        html_gesamt += """
</td>
<td>&nbsp;</td>
</tr>
"""

    html_gesamt += """
</table>
<div class="footer-notes">
<span class="bold-alert">Hinweis:</span> Die Abbuchung erfolgt durch die Verwaltung. Der gewählte Betrag wird dem Benutzerkonto gutgeschrieben. Max. Kontostand: 30,00 €.
</div>
</div>
"""

    st.html(html_gesamt)