import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://localhost:8000"

# --- Page Setup for Printing ---
st.set_page_config(
    page_title="Druckansicht - Wareneinkauf Beleg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- A4 Print & Screen Beautified Styling ---
st.markdown("""
<style>
/* Hide Streamlit components during printing */
@media print {
    header, [data-testid="stSidebar"], [data-testid="stHeader"], footer, .stButton, div.stAlert, hr {
        display: none !important;
    }
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
    }
    @page {
        size: A4 portrait;
        margin: 15mm 10mm 15mm 10mm;
    }
    body {
        background-color: #ffffff;
        color: #000000;
    }
    .print-container {
        box-shadow: none !important;
        padding: 0 !important;
        max-width: 100% !important;
    }
}

/* Beautiful styling for both browser preview and print */
.print-container {
    max-width: 850px;
    margin: 30px auto;
    padding: 30px;
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1a202c;
}

.beleg-header {
    text-align: center;
    margin-bottom: 25px;
    border-bottom: 2px solid #1a202c;
    padding-bottom: 15px;
}

.beleg-header h1 {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 2px;
    margin: 0 0 5px 0;
    text-transform: uppercase;
    color: #1a202c;
}

.beleg-header .sub-title {
    font-size: 13px;
    color: #4a5568;
    margin: 0;
    letter-spacing: 1px;
}

.meta-grid {
    width: 100%;
    margin-bottom: 25px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 12px;
}

.meta-grid table {
    width: 100%;
    border-collapse: collapse;
}

.meta-grid td {
    padding: 4px 0;
    font-size: 13px;
    color: #4a5568;
}

/* The Table grid - exact aligned based on printout template */
.invoice-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

.invoice-table th {
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    color: #2d3748;
    border-bottom: 2px solid #2d3748;
    padding: 8px 6px;
    letter-spacing: 0.5px;
}

.invoice-table td {
    padding: 8px 6px;
    font-size: 12.5px;
    color: #2d3748;
    border-bottom: 1px solid #edf2f7;
}

/* Column Widths & Alignments matching the template */
.col-stueck {
    width: 8%;
    text-align: center;
}

.col-leer1, .col-leer2 {
    width: 8%;
    text-align: center;
    color: #cbd5e1;
}

.col-bezeichnung {
    width: 34%;
    text-align: left;
}

.col-einheit {
    width: 10%;
    text-align: center;
}

.col-ep {
    width: 10%;
    text-align: right;
}

.col-gp {
    width: 12%;
    text-align: right;
}

.col-korrektur {
    width: 10%;
    text-align: right;
    color: #a0aec0;
}

/* Totals styling */
.total-row td {
    font-weight: 700;
    font-size: 13.5px;
    border-top: 2px solid #2d3748;
    border-bottom: 2px double #2d3748;
    padding: 12px 6px;
    color: #1a202c;
}

.footer-note {
    margin-top: 40px;
    text-align: center;
    font-size: 11px;
    color: #a0aec0;
    border-top: 1px dashed #e2e8f0;
    padding-top: 15px;
}
</style>
""", unsafe_allow_html=True)

# Navigation and top interactive bar (hidden during print)
col_nav1, col_nav2 = st.columns([1, 1])
with col_nav1:
    if st.button("🔙 Zurück zum Vorgang", use_container_width=True):
        st.switch_page("pages/vorgang.py")
with col_nav2:
    st.button("🖨️ Beleg jetzt drucken / Als PDF speichern", use_container_width=True, type="primary")
    st.markdown("""
        <script>
        const buttons = window.parent.document.querySelectorAll('button');
        const printBtn = Array.from(buttons).find(el => el.textContent.includes('Beleg jetzt drucken'));
        if (printBtn) {
            printBtn.onclick = function() { window.print(); };
        }
        </script>
    """, unsafe_allow_html=True)

st.write("---")

# Active task sequence fetching
task_id = st.session_state.get("print_task_id")
if not task_id:
    query_params = st.query_params
    if "task_id" in query_params:
        task_id = query_params["task_id"]

if task_id:
    try:
        task_id = int(task_id)
        # Fetching order entries
        response = requests.get(f"{BASE_URL}/bestellung", params={"task_id": task_id}, timeout=5)

        if response.status_code == 200:
            df_all = pd.DataFrame(response.json())
            if not df_all.empty and "task_id" in df_all.columns:
                df_filtered = df_all[df_all["task_id"] == task_id].copy()
            else:
                df_filtered = df_all.copy()
        else:
            response_fallback = requests.get(f"{BASE_URL}/bestellung", timeout=5)
            if response_fallback_status_code == 200:
                df_all = pd.DataFrame(response_fallback.json())
                if not df_all.empty and "task_id" in df_all.columns:
                    df_filtered = df_all[df_all["task_id"] == task_id].copy()
                else:
                    df_filtered = pd.DataFrame()
            else:
                df_filtered = pd.DataFrame()
    except Exception as e:
        st.error(f"Fehler bei Verbindung mit der DB-Schnittstelle: {e}")
        df_filtered = pd.DataFrame()

    if not df_filtered.empty:
        if "gesamt_preis" not in df_filtered.columns:
            df_filtered["gesamt_preis"] = df_filtered["menge"] * df_filtered["preis"]

        gesamtsumme = df_filtered["gesamt_preis"].astype(float).sum()
        gesamt_artikel = df_filtered["menge"].astype(int).sum()

        # CRITICAL FIX: Strings komplett linksbündig ohne vorgelagerte Leerzeichen aufbauen!
        html_content = f"""
<div class="print-container">
<div class="beleg-header">
<h1>Bestellung</h1>
<div class="sub-title">Einkaufsvorgang ID: {task_id}</div>
</div>
<div class="meta-grid">
<table>
<tr>
<td><strong>Belegnummer:</strong> RE-{task_id:05d}</td>
<td style="text-align: right;"><strong>Datum:</strong> {pd.Timestamp.now().strftime('%d.%m.%Y')}</td>
</tr>
<tr>
<td><strong>Projekt:</strong> Wareneinkauf</td>
<td style="text-align: right;"><strong>Status:</strong> Abgeschlossen</td>
</tr>
</table>
</div>
<table class="invoice-table">
<thead>
<tr>
<th class="col-stueck">Stück</th>
<th class="col-leer1"></th>
<th class="col-leer2"></th>
<th class="col-bezeichnung">Bezeichnung</th>
<th class="col-einheit">Einheit</th>
<th class="col-ep">EP</th>
<th class="col-gp">GP</th>
<th class="col-korrektur">Korrektur</th>
</tr>
</thead>
<tbody>
"""

        for _, row in df_filtered.iterrows():
            bezeichnung = row.get("bezeichnung", "")
            menge = int(row.get("menge", 0))
            preis = float(row.get("preis", 0.0))
            gesamt = float(row.get("gesamt_preis", 0.0))
            einheit = row.get("einheit", "Stk.")

            html_content += f"""
<tr>
<td class="col-stueck">{menge}</td>
<td class="col-leer1">___</td>
<td class="col-leer2">___</td>
<td class="col-bezeichnung">{bezeichnung}</td>
<td class="col-einheit">{einheit}</td>
<td class="col-ep">{preis:,.2f} €</td>
<td class="col-gp">{gesamt:,.2f} €</td>
<td class="col-korrektur">€</td>
</tr>
"""

        html_content += f"""
<tr class="total-row">
<td class="col-stueck">{gesamt_artikel}</td>
<td class="col-leer1">___</td>
<td class="col-leer2">___</td>
<td class="col-bezeichnung">Bestellung</td>
<td class="col-einheit"></td>
<td class="col-ep"></td>
<td class="col-gp">{gesamtsumme:,.2f} €</td>
<td class="col-korrektur">€</td>
</tr>
</tbody>
</table>
<div class="footer-note">
Vielen Dank für den Einkauf! &bull; Dokument automatisch gedruckt über Streamlit-Belegwesen
</div>
</div>
"""

        # Jetzt wird das HTML fehlerfrei gerendert
        st.markdown(html_content, unsafe_allow_html=True)

    else:
        st.info(f"Keine Bestellungen für die Vorgangs-ID {task_id} in der Datenbank vorhanden.")
else:
    st.error("Keine aktive Vorgangs-ID gefunden! Bitte wählen Sie zuerst einen Vorgang aus.")