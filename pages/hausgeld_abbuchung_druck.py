from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# from pages.vorgang import shop_date

BASE_URL = "http://localhost:8000"

st.set_page_config(layout="wide", page_title="Hausgeld Abbuchung Druckansicht")

task_id = st.session_state.get("print_task_id")

################################################################
# Maxbetrag Eintragen
################################################################
maxbetrag = 30

################################################################
# Zeile 277 eintragen der verschiedenen Abbuchbaren Beträge
################################################################

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
            margin: 0mm; /* Entfernt die Browser-Ränder */
        }

        /* Ausblenden aller Nicht-Druck-Elemente */
        header, 
        footer, 
        .stButton, 
        div[data-testid="stSidebar"], 
        section[data-testid="stSidebar"],
        nav[data-testid="stSidebarNav"],
        div[data-testid="stHeader"], 
        header[data-testid="stHeader"],
        .no-print, 
        .stAlert {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
        }

        /* Streamlit-Abstände (Padding/Margin) komplett zurücksetzen */
        html, body, .stApp, .stAppViewContainer, .stMain, .main, 
        .block-container, div[data-testid="stVerticalBlock"] {
            padding: 0 !important;
            margin: 0 !important;
            top: 0 !important;
            background-color: #ffffff !important;
        }

        /* Container genau an A4 anpassen */
        .a4-page {
            box-shadow: none !important;
            border: none !important;
            margin: 0 !important;
            padding: 0.8cm 1.2cm !important; /* Etwas reduziertes Padding, damit alles auf eine Seite passt */
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
        margin-bottom: 12px;
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
        font-size: 10px; /* Leicht verkleinert für bessere Verteilung */
        margin-top: 8px;
    }

    .user-table th, .user-table td {
        border: 1px solid #000000 !important;
        padding: 3px 5px; /* Etwas kompaktere Zeilenhöhe */
        vertical-align: middle;
    }

    .user-table th {
        background-color: #f2f2f2 !important;
        font-weight: bold;
        text-align: left;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    .amount-subtext {
        font-size: 10px;
        font-weight: bold;
        color: #000000;
    }

    .box-container {
        display: inline-block;
        margin-right: 5px;
        font-size: 10px;
    }

    .checkbox-mimic {
        display: inline-block;
        width: 10px;
        height: 10px;
        border: 1px solid #000000;
        margin-right: 3px;
        vertical-align: middle;
    }

    .footer-notes {
        font-size: 10px;
        line-height: 1.2;
        margin-top: 10px;
        border-top: 1px solid #000000;
        padding-top: 6px;
    }

    .bold-alert {
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def fetch_user_balance(u):
    """Hilfsfunktion für den parallelen Abruf des Kontostands eines einzelnen Benutzers"""
    try:
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

        return {"user": u, "balance": balance}
    except Exception:
        return {"user": u, "balance": 0.0}


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
            if all_tasks_res.status_code == 200 and isinstance(
                all_tasks_res.json(), list
            ):
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
                abgabe_str = datetime.strptime(clean_date, "%Y-%m-%d").strftime(
                    "%d.%m.%Y"
                )
            except Exception:
                abgabe_str = str(raw_date)

        # 2. Benutzer laden
        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste.", abgabe_str

        users = user_res.json()

        # 3. Parallele/Asynchrone Abfrage der Kontostände
        with ThreadPoolExecutor(max_workers=10) as executor:
            print_dataset = list(executor.map(fetch_user_balance, users))

        return print_dataset, None, abgabe_str
    except Exception as e:
        return (
            None,
            f"Verbindung zur API fehlgeschlagen: {e}",
            "wird bekannt gegeben",
        )


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
    MOEGLICHE_BETRAEGE = [7, 10, 13, 15, 20, 25]

    html_gesamt = f"""
<div class="a4-page">
<div class="title-header">
<div class="title-main">Abbuchung Hausgeld</div>
<div class="title-sub">Gültig für Vorgang #{task_id} | Erstellt am: {druck_zeitpunkt}</strong></div>
<div class="title-sub" style="font-size: 16px">Bitte bis: <strong>{abgabe_termin}</strong> in die Liste eintragen.</div>
</div>
<div class="title-sub"><strong>Hinweis:</strong> Auf die ausreichende Deckung der Hausgeldkonten muss selbständig geachtet werden.<br>Bei mangelnder Deckung und ohne Unterschrift erfolgt keine Buchung für den Back- und Kocheinkauf.<br>Keine automatische Erinnerung. Es kann <strong>max € {maxbetrag},-</strong> auf dem Konto vohanden sein.</div>

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
            if (balance + betrag) < maxbetrag:
                html_gesamt += f"""
<div class="box-container"><span class="checkbox-mimic"></span>{betrag}€</div>
"""
                kaestchen_sichtbar += 1

        if kaestchen_sichtbar == 0:
            html_gesamt += f"""<span style="color:#666; font-style:italic; font-size:11px;">Konto voll (Max. {maxbetrag}€)</span>"""

        html_gesamt += """
</td>
<td>&nbsp;</td>
</tr>
"""

    html_gesamt += f"""
</table>
<div class="footer-notes">
<span class="bold-alert"><strong>An die Zahlstelle:</strong> Wir bitte die o.g. Beträge von dem jeweiligen Hausgeldkonto abzubuchen und für die Teilnahme am Back- und Kocheinkauf bereitzustellen.</span>
</div>
</div>
"""

    st.html(html_gesamt)