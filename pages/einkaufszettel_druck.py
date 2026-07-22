from datetime import datetime
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

# Seite konfigurieren
st.set_page_config(layout="wide", page_title="A4 Abrechnung Druckansicht")

# Task-ID prüfen
task_id = st.session_state.get("print_task_id")

if not task_id:
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


# --- CSS: Perfektes A4 Hochformat ohne Sidebar & ohne leere Zwischenseiten ---
st.markdown(
    """
    <style>
    /* 1. DRUCK-MODUS (STRG + P / PDF-Export) */
    @media print {
        @page {
            size: A4 portrait;
            margin: 0mm; /* Entfernt Standard-Ränder */
        }

        /* Komplettes Ausblenden aller Navigationselemente, 
           Sidebars (stSidebar, stSidebarNav), Header, Buttons & Popups 
        */
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

        /* Hauptcontainer auf die volle Breite dehnen */
        .main, .main .block-container {
            padding: 0px !important;
            margin: 0px !important;
            width: 100% !important;
            max-width: 100% !important;
        }

        body {
            background-color: #ffffff !important;
            margin: 0 !important;
        }

        /* A4 Blatteinstellungen */
        .a4-page {
            box-shadow: none !important;
            border: none !important;
            margin: 0 auto !important;
            padding: 1cm 1.5cm !important;
            width: 100% !important;
            max-width: 21cm !important;
            height: auto !important;
            min-height: 28cm !important;
            page-break-after: always !important; /* Exakter Umbruch pro Person */
            page-break-inside: avoid !important;
            box-sizing: border-box !important;
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

    .title {
        font-size: 20px;
        font-weight: bold;
        text-transform: uppercase;
        border-bottom: 2px solid #000000;
        padding-bottom: 4px;
        margin-bottom: 12px;
    }

    .user-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        font-size: 13px;
        line-height: 1.5;
        margin-bottom: 15px;
    }

    .section-title {
        font-size: 12px;
        font-weight: bold;
        margin-top: 12px;
        margin-bottom: 5px;
        text-decoration: underline;
    }

    .booking-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        margin-bottom: 10px;
    }
    .booking-table th, .booking-table td {
        border: 1px solid #000000 !important;
        padding: 4px 6px;
        text-align: left;
    }
    .booking-table th {
        background-color: #f2f2f2 !important;
        font-weight: bold;
        -webkit-print-color-adjust: exact;
    }

    .order-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        margin-top: 5px;
    }
    .order-table th, .order-table td {
        border: 1px solid #000000 !important;
        padding: 6px 5px;
    }
    .order-table th {
        background-color: #f2f2f2 !important;
        font-weight: bold;
        -webkit-print-color-adjust: exact;
    }

    .signature-block {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 40px;
        margin-top: 30px;
        font-size: 11px;
    }
    .sig-line {
        border-top: 1px solid #000000;
        text-align: center;
        padding-top: 4px;
        margin-top: 15px;
    }
    .footer-notes {
        font-size: 10px;
        line-height: 1.3;
        margin-top: 20px;
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
        task_res = requests.get(f"{BASE_URL}/tasks/open", timeout=5)
        if task_res.status_code == 200 and task_res.json():
            open_task = task_res.json()[0]
            if "abgabe_date" in open_task and open_task["abgabe_date"]:
                try:
                    abgabe_str = datetime.strptime(
                        open_task["abgabe_date"], "%Y-%m-%d"
                    ).strftime("%d.%m.%Y")
                except Exception:
                    abgabe_str = str(open_task["abgabe_date"])

        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste."

        users = user_res.json()
        print_dataset = []

        for u in users:
            wallet_res = requests.get(
                f"{BASE_URL}/wallets/wallet_user",
                params={"buchnummer": u["buchnummer"]},
                timeout=5,
            )
            wallets = wallet_res.json() if wallet_res.status_code == 200 else []
            print_dataset.append(
                {"user": u, "wallets": wallets, "abgabe_date": abgabe_str}
            )

        return print_dataset, None
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


# --- Oberer Bildschirm-Bereich (In .no-print gewrappt = beim Drucken unsichtbar) ---
st.markdown(
    f"""
    <div class="no-print" style="background-color: #e8f4f8; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
        <h4 style="margin:0; color: #1e3d59;">🖨️ Druckansicht aktiv für Vorgangs-ID: {task_id}</h4>
        <p style="margin: 5px 0 0 0; font-size: 13px;">💡 <strong>Tipp:</strong> Drücke <code>STRG + P</code> zum Drucken. Stelle im Druckmenü unbedingt <strong>Hochformat</strong> und <strong>A4</strong> ein!</p>
    </div>
""",
    unsafe_allow_html=True,
)

if st.button("🔄 Daten frisch synchronisieren", key="sync_btn"):
    st.rerun()

dataset, error = load_print_data()

if error:
    st.error(error)
elif not dataset:
    st.warning("Keine Benutzerdaten verfügbar.")
else:
    html_gesamt = ""
    druck_zeitpunkt = datetime.now().strftime("%d.%m.%Y um %H:%M")

    for item in dataset:
        user = item["user"]
        wallets = item["wallets"]
        abgabe_termin = item["abgabe_date"]

        df_w = pd.DataFrame(wallets)
        buchungen_fuenf = []
        zur_verfuegung_val = 0.0

        if not df_w.empty and "date" in df_w.columns:
            df_w = df_w.sort_values(by="date", ascending=False)
            buchungen_fuenf = df_w.head(5).to_dict(orient="records")
            zur_verfuegung_val = float(df_w.iloc[0]["new_amount"])

        zur_verfuegung_str = f"{zur_verfuegung_val:,.2f} €".replace(".", ",")
        formatierte_nr = format_buchnummer(user["buchnummer"])

        html_gesamt += f"""
<div class="a4-page">
<div class="title">Back- & Kocheinkauf</div>
<div class="user-grid">
<div>
<strong>Name:</strong> {user['vorname']} {user['nachname']} / Zimmer: {user['zimmer_nr']}<br>
<strong>Buchnummer:</strong> {formatierte_nr}
</div>
<div style="text-align: right;">
<strong>Zur Verfügung:</strong> <span style="font-size:15px; font-weight:bold;">{zur_verfuegung_str}</span><br>
<span style="font-size:10px; color:#555;">Druckdatum: {druck_zeitpunkt}</span>
</div>
</div>
<div class="section-title">Die letzten fünf Buchungen:</div>
<table class="booking-table">
<tr>
<th style="width: 55%;">Buchungstext</th>
<th style="width: 20%;">Betrag</th>
<th style="width: 25%;">Datum</th>
</tr>
"""

        if not buchungen_fuenf:
            html_gesamt += """<tr><td colspan="3" style="text-align:center; color:#666; font-style:italic;">Keine Buchungen auf dem Konto vorhanden.</td></tr>"""
        else:
            for b in buchungen_fuenf:
                raw_date = b.get("date", "")
                try:
                    formatted_b_date = datetime.strptime(
                        raw_date.split("T")[0], "%Y-%m-%d"
                    ).strftime("%d.%m.%Y")
                except Exception:
                    formatted_b_date = str(raw_date)

                b_betrag = float(b.get("betrag", 0.0))
                b_betrag_str = f"{b_betrag:,.2f} €".replace(".", ",")
                color_style = "color: #b30000;" if b_betrag < 0 else ""

                html_gesamt += f"""
<tr>
<td>{b.get('grund', 'Kein Verwendungszweck angegeben')}</td>
<td style="{color_style} font-weight:bold;">{b_betrag_str}</td>
<td>{formatted_b_date}</td>
</tr>
"""

        html_gesamt += f"""
</table>
<div style="margin-top: 10px; font-size: 12px; font-weight: bold;">
Abgabetermin ist der <span style="text-decoration: underline;">{abgabe_termin}</span>*
</div>
<div class="section-title" style="margin-top: 10px;">Hier Bitte die Ware eintragen**:</div>
<table class="order-table">
<tr>
<th style="width: 10%;">Stück</th>
<th style="width: 48%;">Bezeichnung/Einheit</th>
<th style="width: 14%;">Einzelpreis</th>
<th style="width: 14%;">Gesamtpreis</th>
<th style="width: 14%; font-size:9px; text-align:center; color:#444;">Freilassen</th>
</tr>
"""

        for _ in range(8):
            html_gesamt += """
<tr>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
</tr>
"""

        html_gesamt += f"""
<tr style="background-color: #fcfcfc; font-weight: bold;">
<td colspan="2" style="text-align: right;">Kontostand: {zur_verfuegung_str}</td>
<td style="text-align: right;">Summe:</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
</tr>
</table>
<div class="section-title">Anmerkungen:</div>
<div style="border-bottom: 1px dashed #444; margin-top: 15px;"></div>
<div style="border-bottom: 1px dashed #444; margin-top: 15px;"></div>
<div class="signature-block">
<div class="sig-line">Unterschrift für die Bestellung</div>
<div class="sig-line">Unterschrift bei Erhalt der Lieferung</div>
</div>
<div class="footer-notes">
<span class="bold-alert">Achtung!! Preise können variieren!</span><br>
* Ohne Unterschrift keine Bestellung. Keine automatische Abgabeerinnerung!<br>
** <span class="bold-alert">Pro Person nur 3 TK Artikel im Eisfach!</span>
</div>
</div>
"""

    st.html(html_gesamt)