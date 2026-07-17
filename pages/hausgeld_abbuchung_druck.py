import requests
import pandas as pd
import streamlit as st
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Seite konfigurieren
st.set_page_config(layout="wide", page_title="Hausgeld Abbuchung Druckansicht")

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
        padding: 1.2cm 1.5cm;
        margin: 25px auto;
        font-family: 'Arial', sans-serif;
        color: #000000;
        box-shadow: 0 0 10px rgba(0,0,0,0.15);
        border: 1px solid #cccccc;
        box-sizing: border-box;
    }

    /* Header & Layout */
    .header-container {
        display: grid;
        grid-template-columns: 1fr auto;
        border-bottom: 2px solid #000000;
        padding-bottom: 4px;
        margin-bottom: 12px;
    }
    .title {
        font-size: 20px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .date-badge {
        font-size: 18px;
        font-weight: bold;
    }

    .sub-title {
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 12px;
    }

    .info-text {
        font-size: 11.5px;
        line-height: 1.4;
        margin-bottom: 15px;
    }

    /* Haupttabelle */
    .main-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        margin-bottom: 20px;
    }
    .main-table th, .main-table td {
        border: 1px solid #000000;
        padding: 6px 8px;
        text-align: left;
        vertical-align: middle;
    }
    .main-table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }

    .amount-subtext {
        font-size: 10px;
        color: #555555;
        margin-top: 2px;
    }

    /* Checkbox-Kästchen Style */
    .box-container {
        display: inline-flex;
        align-items: center;
        margin-right: 10px;
        font-size: 11.5px;
        white-space: nowrap;
    }
    .checkbox-mimic {
        width: 12px;
        height: 12px;
        border: 1px solid #000000;
        margin-right: 3px;
        display: inline-block;
        background-color: #ffffff;
    }

    /* Fußbereich */
    .footer-block {
        margin-top: 20px;
        font-size: 12px;
        line-height: 1.5;
    }
    .signature-row {
        margin-top: 30px;
        border-top: 1px solid #000000;
        width: 250px;
        text-align: center;
        padding-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)


# --- API Ladedaten ---
def load_abbuchung_daten():
    try:
        # 1. Daten aus der offenen Task holen
        monat_jahr = datetime.now().strftime("%B %Y")
        geld_date_str = "wird bekannt gegeben"
        shop_date_str = "wird bekannt gegeben"

        task_res = requests.get(f"{BASE_URL}/tasks/open", timeout=5)
        if task_res.status_code == 200 and task_res.json():
            open_task = task_res.json()[0]

            # Monat und Jahr aus dem Task extrahieren (falls vorhanden, sonst aktuell)
            if "monat" in open_task and open_task["monat"]:
                monat_jahr = f"{open_task['monat']}"
                if "jahr" in open_task and open_task["jahr"]:
                    monat_jahr += f" {open_task['jahr']}"

            # Datumsfelder konvertieren
            if "geld_date" in open_task and open_task["geld_date"]:
                try:
                    geld_date_str = datetime.strptime(open_task["geld_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
                except:
                    geld_date_str = str(open_task["geld_date"])

            if "shop_date" in open_task and open_task["shop_date"]:
                try:
                    shop_date_str = datetime.strptime(open_task["shop_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
                except:
                    shop_date_str = str(open_task["shop_date"])

        # 2. Alle User laden
        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste."

        users = user_res.json()
        print_dataset = []

        # 3. Wallets für Kontostand laden
        for u in users:
            wallet_res = requests.get(f"{BASE_URL}/wallets/wallet_user", params={"buchnummer": u["buchnummer"]},
                                      timeout=5)
            wallets = wallet_res.json() if wallet_res.status_code == 200 else []

            # Letzten Eintrag ermitteln für das aktuelle Guthaben
            current_balance = 0.0
            if wallets:
                df_w = pd.DataFrame(wallets)
                if "date" in df_w.columns:
                    df_w = df_w.sort_values(by="date", ascending=False)
                    current_balance = float(df_w.iloc[0]["new_amount"])

            print_dataset.append({
                "user": u,
                "balance": current_balance
            })

        context_data = {
            "monat_jahr": monat_jahr,
            "geld_date": geld_date_str,
            "shop_date": shop_date_str,
            "dataset": print_dataset
        }
        return context_data, None
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


# --- Bildschirm-Steuerung ---
st.write("### 🖨️ Hausgeld-Abbuchungsliste Druckansicht")
st.info(
    "💡 **Drucker-Tipp:** Drücke am PC `STRG + P`, um dieses Dokument direkt als offizielle A4-Vorlage auszudrucken.")

if st.button("🔄 Daten frisch synchronisieren"):
    st.rerun()

st.write("---")

context, error = load_abbuchung_daten()

if error:
    st.error(error)
elif not context:
    st.warning("Keine Daten verfügbar.")
else:
    # Erlaubte Standard-Zubuchungsbeträge
    MOEGLICHE_BETRAEGE = [7, 10, 13, 15, 20, 25]

    # HTML Aufbau (ohne Einrückungen linksbündig wegen Streamlit-Markdown-Bug)
    html_gesamt = f"""
<div class="a4-page">
<div class="header-container">
<div class="title">Back- und Kocheinkauf</div>
<div class="date-badge">{context['monat_jahr']}</div>
</div>

<div class="sub-title">Bitte bis, {context['geld_date']} in die Liste eintragen.</div>

<div class="info-text">
<strong>Hinweis:</strong> Auf die ausreichende Deckung der Hausgeldkonten muss selbständig geachtet werden.<br>
Bei mangelnder Deckung und ohne Unterschrift erfolgt keine Buchung für den Back- und Kocheinkauf.<br>
Keine automatische Erinnerung. Es kann max. € 30,- auf dem Konto vorhanden sein.<br><br>
Der nächste Back- und Kocheinkauf findet voraussichtlich am <strong>{context['shop_date']}</strong> statt.
</div>

<table class="main-table">
<tr>
<th style="width: 30%;">Name</th>
<th style="width: 18%;">Buchnr.</th>
<th style="width: 37%;">Betrag</th>
<th style="width: 15%;">Unterschrift</th>
</tr>
"""

    for item in context["dataset"]:
        user = item["user"]
        balance = item["balance"]

        balance_str = f"{balance:,.2f} €".replace(".", ",")
        formatierte_nr = format_buchnummer(user["buchnummer"])

        # Spalte 1 Name und Kontostand generieren
        html_gesamt += f"""
<tr>
<td>
<strong>{user['vorname']} {user['nachname']}</strong>
<div class="amount-subtext">{balance_str}</div>
</td>
<td>{formatierte_nr}</td>
<td>
"""

        # Spalte 3: Dynamische Kästchenberechnung (Betrag + Kontostand < 30)
        kaestchen_sichtbar = 0
        for betrag in MOEGLICHE_BETRAEGE:
            if (balance + betrag) < 30.0:
                html_gesamt += f"""
<div class="box-container"><span class="checkbox-mimic"></span>{betrag}€</div>
"""
                kaestchen_sichtbar += 1

        if kaestchen_sichtbar == 0:
            html_gesamt += """<span style="color:#666; font-style:italic; font-size:11px;">Konto voll (Max. 30€)</span>"""

        # Spalte 4: Unterschrift blanko anhängen
        html_gesamt += """
</td>
<td>&nbsp;</td>
</tr>
"""

    # Abschluss der Tabelle und Zahlstellen-Infotext anhängen
    html_gesamt += """
</table>

<div class="footer-block">
<strong>An die Zahlstelle:</strong><br>
Wir bitten die o.g. Beträge von dem jeweiligen Hausgeldkonto abzubuchen und für die Teilnahme am Back- und Kocheinkauf bereitzustellen.<br>
Vielen Dank!
<div class="signature-row">Unterschrift Projektleitung / Zahlstelle</div>
</div>
</div>
"""

    # Ausgabe des bereinigten HTML-Strings
    st.html(html_gesamt)