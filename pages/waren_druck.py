import requests
import pandas as pd
import streamlit as st
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Seite auf weites Layout stellen
st.set_page_config(layout="wide", page_title="Artikelliste Druckansicht")

# --- CSS für echtes zweispaltiges A4-Drucklayout ---
st.markdown("""
    <style>
    /* Streamlit UI-Elemente für den Druck verbergen */
    @media print {
        header, footer, .stButton, div[data-testid="stSidebar"], div[data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
        }
        body {
            background-color: #ffffff;
            color: #000000;
        }
    }

    /* A4 Styling auf dem Bildschirm & Drucker */
    .a4-page {
        background: white;
        width: 21cm;
        min-height: 29.7cm;
        padding: 1.2cm 1.5cm;
        margin: 0 auto;
        font-family: 'Arial', sans-serif;
        color: #333333;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    @media print {
        .a4-page {
            width: 100%;
            height: auto;
            box-shadow: none;
            padding: 0;
            margin: 0;
        }
    }

    /* Dokumenten-Header Stil */
    .doc-header {
        border-bottom: 2px solid #000000;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .doc-title {
        font-size: 24px;
        font-weight: bold;
        text-transform: uppercase;
        margin: 0;
    }
    .doc-meta {
        font-size: 11px;
        color: #555555;
        text-align: right;
        margin-top: -20px;
    }
    .disclaimer {
        font-size: 11px;
        font-style: italic;
        margin-bottom: 15px;
        line-height: 1.3;
    }

    /* Kategorie Balken */
    .category-title {
        font-size: 14px;
        font-weight: bold;
        background-color: #f2f2f2;
        padding: 4px 8px;
        margin-top: 15px;
        margin-bottom: 5px;
        border-left: 4px solid #333333;
        text-transform: uppercase;
    }

    /* Das 2-Spalten Layout-Raster für die Tabellen */
    .two-column-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0px 30px; /* Horizontale Lücke zwischen linker und rechter Tabelle */
        width: 100%;
    }

    .item-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        margin-bottom: 5px;
    }

    .item-table td {
        padding: 4px 4px;
        border-bottom: 1px solid #e0e0e0;
        vertical-align: top;
    }

    .item-name {
        width: 55%;
        font-weight: normal;
    }
    .item-qty {
        width: 25%;
        color: #555555;
        text-align: left;
    }
    .item-price {
        width: 20%;
        text-align: right;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# --- API-Ladefunktion ---
def load_all_waren():
    try:
        response = requests.get(f"{BASE_URL}/waren", timeout=5)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Fehler beim Laden der Waren: {e}")
    return pd.DataFrame()


df_waren = load_all_waren()

# --- Steuerungselemente (Nur auf dem Bildschirm sichtbar) ---
st.write("### 🖨️ Zweispaltige Artikelliste Druckansicht")
st.info(
    "💡 **Tipp zum Drucken:** Klicke im Browser auf Datei -> Drucken (oder `STRG + P`). Die Steuerung verschwindet im PDF automatisch.")

if st.button("🔄 Ansicht aktualisieren"):
    st.rerun()

st.write("---")

# ==========================================
# RENDERN DER A4-SEITE
# ==========================================
if df_waren.empty:
    st.warning("Keine Waren-Daten zum Generieren der Druckseite vorhanden.")
else:
    # Haupt-HTML Container ohne jegliche Einrückung starten
    html_content = f"""
<div class="a4-page">
<div class="doc-header">
<div class="doc-title">Waren- & Artikelliste</div>
<div class="doc-meta">Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</div>
</div>
<div class="disclaimer">
Preise sind lediglich Richtwerte! Abweichungen zum tatsächlichen Preis bleiben vorbehalten.<br>
Die Abrechnung erfolgt nach Kassenzettel und kann auf Anfrage eingesehen werden.<br>
<strong>Pro Person nur 3 TK Artikel im Eisfach!</strong>
</div>
"""

    # Eindeutige Kategorien holen
    kategorien = sorted(df_waren["kategorie"].unique())

    for kat in kategorien:
        html_content += f'<div class="category-title">{str(kat).upper()}</div>'

        # Holen und sortieren aller Artikel dieser Kategorie
        df_kat = df_waren[df_waren["kategorie"] == kat].sort_values(by="bezeichnung")
        items = df_kat.to_dict(orient="records")

        # Aufteilen in linke und rechte Hälfte für die 2 Spalten
        half = (len(items) + 1) // 2
        left_items = items[:half]
        right_items = items[half:]

        # Grid für die zwei Spalten starten
        html_content += '<div class="two-column-grid">'

        # ---- LINKE SPALTE DER KATEGORIE ----
        html_content += '<table class="item-table">'
        for row in left_items:
            bezeichnung = row["bezeichnung"]
            einheit = row.get("art", "Stk.") if pd.notna(row.get("art")) else "Stk."
            menge = f"{row['menge']} {einheit}" if pd.notna(row['menge']) else f"1 {einheit}"
            preis_val = float(row["preis"]) if pd.notna(row["preis"]) else 0.0
            preis_str = f"{preis_val:,.2f} €".replace(".", ",")

            html_content += f"""
<tr>
<td class="item-name">{bezeichnung}</td>
<td class="item-qty">{menge}</td>
<td class="item-price">{preis_str}</td>
</tr>
"""
        html_content += '</table>'

        # ---- RECHTE SPALTE DER KATEGORIE ----
        html_content += '<table class="item-table">'
        for row in right_items:
            bezeichnung = row["bezeichnung"]
            einheit = row.get("art", "Stk.") if pd.notna(row.get("art")) else "Stk."
            menge = f"{row['menge']} {einheit}" if pd.notna(row['menge']) else f"1 {einheit}"
            preis_val = float(row["preis"]) if pd.notna(row["preis"]) else 0.0
            preis_str = f"{preis_val:,.2f} €".replace(".", ",")

            html_content += f"""
<tr>
<td class="item-name">{bezeichnung}</td>
<td class="item-qty">{menge}</td>
<td class="item-price">{preis_str}</td>
</tr>
"""
        # Falls die rechte Spalte leer ist, eine leere Zeile für die Symmetrie einfügen
        if not right_items:
            html_content += '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>'

        html_content += '</table>'

        # Grid für diese Kategorie schließen
        html_content += '</div>'

    html_content += "</div>"

    # Render das HTML nativ über st.html ohne Markdown-Interferenzen
    st.html(html_content)