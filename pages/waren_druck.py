from datetime import datetime
import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

st.set_page_config(layout="wide", page_title="Artikelliste Druckansicht")

task_id = st.session_state.get("print_task_id")

if task_id:
    task_id = int(task_id)
else:
    task_id = 1


# --- CSS für zweispaltiges A4-Drucklayout & Ausblenden der Navigation ---
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
            padding: 0.8cm 1.2cm !important;
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

    .header-box {
        border-bottom: 2px solid #000;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }

    .title {
        font-size: 20px;
        font-weight: bold;
        text-transform: uppercase;
    }

    .category-title {
        font-size: 11px;
        font-weight: bold;
        background-color: #e6e6e6 !important;
        padding: 2px 8px;
        border: 1px solid #000;
        text-transform: uppercase;
        margin-top: 8px;
        margin-bottom: 4px;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    .two-column-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }

    .item-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 10px;
    }

    .item-table td {
        border: 1px solid #000 !important;
        padding: 2px 5px;
    }

    .item-name { width: 60% }
    .item-qty { width: 20%; text-align: center; }
    .item-price { width: 20%; text-align: right; }
    </style>
""",
    unsafe_allow_html=True,
)


def load_waren_data():
    try:
        res = requests.get(f"{BASE_URL}/waren", timeout=5)
        if res.status_code == 200:
            return res.json(), None
        return None, "Fehler beim Laden der Warenliste."
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


st.markdown(
    f"""
    <div class="no-print" style="background-color: #e8f4f8; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
        <h4 style="margin:0; color: #1e3d59;">🖨️ Artikelliste Druckansicht (Vorgang #{task_id})</h4>
        <p style="margin: 5px 0 0 0; font-size: 13px;">💡 Drücke <code>STRG + P</code> zum Drucken.</p>
    </div>
""",
    unsafe_allow_html=True,
)

if st.button("🔄 Daten frisch synchronisieren", key="sync_btn"):
    st.rerun()

waren_liste, error = load_waren_data()

if error:
    st.error(error)
elif not waren_liste:
    st.warning("Keine Waren in der Datenbank vorhanden.")
else:
    druck_zeitpunkt = datetime.now().strftime("%d.%m.%Y um %H:%M")
    df = pd.DataFrame(waren_liste)

    html_content = f"""
<div class="a4-page">
<div class="header-box">
<div style="font-size: 8px; color: #444;">Preise sind lediglich Richtwerte! Abweichungen zum tatsächlichen Preis bleiben vorbehalten.<br>Die Abrechnung erfolgt nach Kassenzettel und kann auf Anfrage eingesehen werden.<br>Stand: {druck_zeitpunkt} | Vorgang #{task_id}</div>
</div>
"""

    if "kategorie" in df.columns:
        kategorien = df["kategorie"].unique()
        for kat in kategorien:
            kat_items = df[df["kategorie"] == kat].to_dict(orient="records")
            half = (len(kat_items) + 1) // 2
            left_items = kat_items[:half]
            right_items = kat_items[half:]

            # Kategorie als Titel formatiert (Anfangsbuchstabe groß)
            kat_title = str(kat).title()

            html_content += f'<div class="category-title">{kat_title}</div>'
            html_content += '<div class="two-column-grid">'

            # Links
            html_content += '<table class="item-table">'
            for row in left_items:
                bezeichnung = row["bezeichnung"]
                einheit = (
                    row.get("art", "Stk.")
                    if pd.notna(row.get("art"))
                    else "Stk."
                )
                menge = (
                    f"{row['menge']} {einheit}"
                    if pd.notna(row["menge"])
                    else f"1 {einheit}"
                )
                preis_val = (
                    float(row["preis"]) if pd.notna(row["preis"]) else 0.0
                )
                preis_str = f"{preis_val:,.2f} €".replace(".", ",")

                html_content += f"""
<tr>
<td class="item-name">{bezeichnung}</td>
<td class="item-qty">{menge}</td>
<td class="item-price">{preis_str}</td>
</tr>
"""
            html_content += "</table>"

            # Rechts
            html_content += '<table class="item-table">'
            for row in right_items:
                bezeichnung = row["bezeichnung"]
                einheit = (
                    row.get("art", "Stk.")
                    if pd.notna(row.get("art"))
                    else "Stk."
                )
                menge = (
                    f"{row['menge']} {einheit}"
                    if pd.notna(row["menge"])
                    else f"1 {einheit}"
                )
                preis_val = (
                    float(row["preis"]) if pd.notna(row["preis"]) else 0.0
                )
                preis_str = f"{preis_val:,.2f} €".replace(".", ",")

                html_content += f"""
<tr>
<td class="item-name">{bezeichnung}</td>
<td class="item-qty">{menge}</td>
<td class="item-price">{preis_str}</td>
</tr>
"""
            html_content += "</table>"
            html_content += "</div>"

    html_content += "</div>"
    st.html(html_content)