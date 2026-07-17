import requests
import pandas as pd
import streamlit as st
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Seite konfigurieren
st.set_page_config(layout="wide", page_title="A4 Abrechnung Druckansicht")


# --- Hilfsfunktion zur Formatierung der Buchnummer ---
def format_buchnummer(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if len(val_str) > 4:
        return f"{val_str[:-4]}/{val_str[-4:]}"
    return val_str


# --- CSS für exakte A4-Seitenumbrüche und Look & Feel des Scans ---
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
            page-break-after: always; /* WICHTIG: Erzwingt eine neue Seite pro User */
            box-shadow: none !important;
            margin: 0px !important;
            border: none !important;
            height: 29.3cm; /* Verhindert das Erzeugen leerer Zwischenseiten */
        }
    }

    /* Bildschirm-Vorschau Styling (simuliert A4-Blätter) */
    .a4-page {
        background: white;
        width: 21cm;
        height: 29.7cm;
        padding: 1.2cm 1.5cm;
        margin: 25px auto;
        font-family: 'Arial', sans-serif;
        color: #000000;
        box-shadow: 0 0 10px rgba(0,0,0,0.15);
        border: 1px solid #cccccc;
        box-sizing: border-box;
    }

    /* Überschrift & Header-Layout */
    .title {
        font-size: 22px;
        font-weight: bold;
        text-transform: uppercase;
        border-bottom: 2px solid #000000;
        padding-bottom: 4px;
        margin-bottom: 15px;
    }

    .user-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 13px;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 6px;
        text-decoration: underline;
    }

    /* Tabellen Styling (Letzte Buchungen) */
    .booking-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        margin-bottom: 15px;
    }
    .booking-table th, .booking-table td {
        border: 1px solid #000000;
        padding: 5px 8px;
        text-align: left;
    }
    .booking-table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }

    /* Blanko-Bestelltabelle */
    .order-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        margin-top: 5px;
    }
    .order-table th, .order-table td {
        border: 1px solid #000000;
        padding: 7px 6px; /* Bietet Platz für händische Notizen */
    }
    .order-table th {
        background-color: #f2f2f2;
    }

    /* Unterschriften & Fußnoten */
    .signature-block {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 50px;
        margin-top: 35px;
        font-size: 12px;
    }
    .sig-line {
        border-top: 1px solid #000000;
        text-align: center;
        padding-top: 5px;
        margin-top: 20px;
    }
    .footer-notes {
        font-size: 10.5px;
        line-height: 1.4;
        margin-top: 25px;
    }
    .bold-alert {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# --- API Ladedaten (User, Letzte Tasks & Wallets) ---
def load_print_data():
    try:
        abgabe_str = "wird bekannt gegeben"
        task_res = requests.get(f"{BASE_URL}/tasks/open", timeout=5)
        if task_res.status_code == 200 and task_res.json():
            open_task = task_res.json()[0]
            if "abgabe_date" in open_task and open_task["abgabe_date"]:
                try:
                    abgabe_str = datetime.strptime(open_task["abgabe_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
                except:
                    abgabe_str = str(open_task["abgabe_date"])

        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste."

        users = user_res.json()
        print_dataset = []

        for u in users:
            wallet_res = requests.get(f"{BASE_URL}/wallets/wallet_user", params={"buchnummer": u["buchnummer"]},
                                      timeout=5)
            wallets = wallet_res.json() if wallet_res.status_code == 200 else []
            print_dataset.append({
                "user": u,
                "wallets": wallets,
                "abgabe_date": abgabe_str
            })

        return print_dataset, None
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


# --- Bildschirm-Steuerung ---
st.write("### 🖨️ Automatische A4-Sammelmappe zum Ausdrucken")
st.info(
    "💡 **Drucker-Tipp:** Drücke am PC `STRG + P`. Jeder Benutzer wird automatisch sauber getrennt auf ein eigenes A4-Blatt gedruckt.")

if st.button("🔄 Daten frisch synchronisieren"):
    st.rerun()

st.write("---")

dataset, error = load_print_data()

if error:
    st.error(error)
elif not dataset:
    st.warning("Keine Benutzerdaten verfügbar.")
else:
    html_gesamt = ""
    druck_zeitpunkt = datetime.now().strftime('%d.%m.%Y um %H:%M')

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

        # WICHTIG: Die Zeilen sind ganz an den linken Rand gerückt (keine Tabs/Leerzeichen am Zeilenanfang),
        # damit Markdown es niemals als Code-Block missversteht!
        html_gesamt += f"""
<div class="a4-page">
<div class="title">Back- & Kocheinkauf</div>
<div class="user-grid">
<div>
<strong>Name:</strong> {user['vorname']} {user['nachname']} / Zimmer: {user['zimmer_nr']}<br>
<strong>Buchnummer:</strong> {formatierte_nr}
</div>
<div style="text-align: right;">
<strong>Zur Verfügung:</strong> <span style="font-size:16px; font-weight:bold;">{zur_verfuegung_str}</span><br>
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
                raw_date = b.get('date', '')
                try:
                    formatted_b_date = datetime.strptime(raw_date.split("T")[0], "%Y-%m-%d").strftime("%d.%m.%Y")
                except:
                    formatted_b_date = str(raw_date)

                b_betrag = float(b.get('betrag', 0.0))
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
<div style="margin-top: 15px; font-size: 13px; font-weight: bold;">
Abgabetermin ist der <span style="text-decoration: underline;">{abgabe_termin}</span>*
</div>
<div class="section-title" style="margin-top: 15px;">Hier Bitte die Ware eintragen**:</div>
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
<div style="border-bottom: 1px dashed #444; margin-top: 18px;"></div>
<div style="border-bottom: 1px dashed #444; margin-top: 18px;"></div>
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

    # Verwendung der nativen HTML-Komponente von Streamlit schützt vor fehlerhaftem Markdown-Parsing
    st.html(html_gesamt)