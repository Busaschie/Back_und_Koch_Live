from datetime import datetime
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

st.set_page_config(layout="wide", page_title="Gesamtübersicht Kontostände")

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


# --- CSS für A4 Druck und Sidebar-Ausblendung ---
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
        border-bottom: 2px solid #000000;
        padding-bottom: 6px;
        margin-bottom: 15px;
    }

    .title-main {
        font-size: 20px;
        font-weight: bold;
        text-transform: uppercase;
    }

    .title-sub {
        font-size: 11px;
        color: #444444;
        margin-top: 3px;
    }

    .summary-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .summary-table th, .summary-table td {
        border: 1px solid #000000 !important;
        padding: 6px 8px;
    }

    .summary-table th {
        background-color: #f2f2f2 !important;
        font-weight: bold;
        text-align: left;
        -webkit-print-color-adjust: exact;
    }

    .summary-box {
        border: 1.5px solid #000000;
        padding: 12px;
        margin-top: 20px;
        background-color: #fafafa !important;
        font-size: 12px;
        -webkit-print-color-adjust: exact;
    }

    .summary-line {
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
    }

    .summary-line:last-child {
        margin-bottom: 0;
        padding-top: 6px;
        border-top: 1px solid #000000;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def load_print_data():
    try:
        user_res = requests.get(f"{BASE_URL}/users", timeout=5)
        if user_res.status_code != 200:
            return None, "Fehler beim Laden der Benutzerliste."

        users = user_res.json()
        print_dataset = []
        gesamt_kontostand = 0.0

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

            gesamt_kontostand += balance
            print_dataset.append({
                "buchnummer": u["buchnummer"],
                "name": f"{u['vorname']} {u['nachname']}",
                "balance": balance,
            })

        # Auszahlungswert für den Einkauf ermitteln
        einkauf_aktuell = 0.0
        shopping_res = requests.get(
            f"{BASE_URL}/tasks/{task_id}/shopping_list", timeout=5
        )
        if shopping_res.status_code == 200:
            s_data = shopping_res.json()
            items = s_data.get("items", [])
            for itm in items:
                einkauf_aktuell += float(itm.get("gesamt_preis", 0.0))

        ueberschuss = gesamt_kontostand - einkauf_aktuell

        return {
            "dataset": print_dataset,
            "gesamt_kontostand": gesamt_kontostand,
            "einkauf_aktuell": einkauf_aktuell,
            "ueberschuss": ueberschuss,
        }, None
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


st.markdown(
    f"""
    <div class="no-print" style="background-color: #e8f4f8; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
        <h4 style="margin:0; color: #1e3d59;">🖨️ Kontostände Übersicht (Vorgang #{task_id})</h4>
        <p style="margin: 5px 0 0 0; font-size: 13px;">💡 Drücke <code>STRG + P</code> zum Drucken.</p>
    </div>
""",
    unsafe_allow_html=True,
)

if st.button("🔄 Daten frisch synchronisieren", key="sync_btn"):
    st.rerun()

context, error = load_print_data()

if error:
    st.error(error)
elif not context or not context.get("dataset"):
    st.warning("Keine Daten verfügbar.")
else:
    druck_zeitpunkt = datetime.now().strftime("%d.%m.%Y um %H:%M")

    html_gesamt = f"""
<div class="a4-page">
<div class="title-header">
<div class="title-main">Gesamtübersicht Kontostände</div>
<div class="title-sub">Vorgangs-ID #{task_id} | Stichtag: {druck_zeitpunkt}</div>
</div>

<table class="summary-table">
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

    gesamt_str = f"{context['gesamt_kontostand']:,.2f} €".replace(".", ",")
    einkauf_str = f"{context['einkauf_aktuell']:,.2f} €".replace(".", ",")
    ueberschuss_str = f"{context['ueberschuss']:,.2f} €".replace(".", ",")

    html_gesamt += f"""
</table>

<div class="summary-box">
<div class="summary-line">
<span>Aktueller Kontostand (Gesamt):</span>
<span>{gesamt_str}</span>
</div>
<div class="summary-line">
<span>Bar ausgezahlt für aktuellen Einkauf (Warenwert):</span>
<span>{einkauf_str}</span>
</div>
<div class="summary-line">
<span>Verbleibender Überschuss / Restsaldo:</span>
<span>{ueberschuss_str}</span>
</div>
</div>
</div>
"""

    st.html(html_gesamt)