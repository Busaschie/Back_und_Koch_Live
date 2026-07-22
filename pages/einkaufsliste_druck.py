import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

# --- Page Setup for Printing ---
st.set_page_config(
    page_title="Druckansicht - Wareneinkauf Beleg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- A4 Print & Screen Beautified Styling ---
st.markdown(
    """
<style>
/* 1. DRUCK-MODUS (STRG + P / PDF-Export) */
@media print {
    @page {
        size: A4 portrait;
        margin: 0mm;
    }

    /* Ausblenden aller UI-Elemente und der Sidebar */
    header, 
    footer, 
    .stButton, 
    div[data-testid="stSidebar"], 
    section[data-testid="stSidebar"],
    nav[data-testid="stSidebarNav"],
    div[data-testid="stHeader"], 
    .no-print, 
    .stAlert, 
    hr {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    .main, .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    body {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    .print-container {
        box-shadow: none !important;
        padding: 1cm 1.5cm !important;
        max-width: 21cm !important;
        margin: 0 auto !important;
        border: none !important;
    }
}

/* 2. BILDSCHIRM-VORSCHAU */
.print-container {
    max-width: 850px;
    margin: 20px auto;
    background-color: #ffffff;
    padding: 30px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #000000;
}

.header-table {
    width: 100%;
    margin-bottom: 20px;
    border-bottom: 2px solid #000000;
    padding-bottom: 10px;
}

.header-title {
    font-size: 22px;
    font-weight: bold;
    text-transform: uppercase;
    margin: 0;
}

.header-sub {
    font-size: 13px;
    color: #444444;
    margin-top: 5px;
}

.items-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

.items-table th {
    background-color: #f2f2f2 !important;
    color: #000000;
    font-weight: bold;
    font-size: 12px;
    padding: 8px 6px;
    border: 1px solid #000000 !important;
    text-align: left;
    -webkit-print-color-adjust: exact;
}

.items-table td {
    padding: 6px;
    font-size: 12px;
    border: 1px solid #000000 !important;
    vertical-align: middle;
}

.col-stueck { width: 6%; text-align: center; }
.col-leer1 { width: 6%; text-align: center; }
.col-leer2 { width: 6%; text-align: center; }
.col-bezeichnung { width: 44%; font-weight: 600; }
.col-einheit { width: 10%; text-align: center; }
.col-ep { width: 11%; text-align: right; }
.col-gp { width: 11%; text-align: right; }
.col-korrektur { width: 6%; text-align: center; }

.total-row td {
    font-weight: bold;
    background-color: #fafafa !important;
    font-size: 13px;
    -webkit-print-color-adjust: exact;
}

.footer-section {
    margin-top: 30px;
    width: 100%;
}

.notes-box {
    border: 1px solid #000000;
    height: 60px;
    margin-top: 5px;
    padding: 5px;
    font-size: 11px;
    color: #555555;
}

.signature-table {
    width: 100%;
    margin-top: 40px;
}

.sig-line {
    border-top: 1px solid #000000;
    text-align: center;
    font-size: 11px;
    padding-top: 5px;
}
</style>
""",
    unsafe_allow_html=True,
)

# Task-ID prüfen
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

# --- Oberer Bildschirm-Bereich (In .no-print gewrappt) ---
st.markdown(
    f"""
    <div class="no-print" style="background-color: #e8f4f8; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
        <h4 style="margin:0; color: #1e3d59;">🖨️ Druckansicht aktiv für Vorgangs-ID: {task_id}</h4>
        <p style="margin: 5px 0 0 0; font-size: 13px;">💡 <strong>Tipp:</strong> Drücke <code>STRG + P</code> zum Drucken.</p>
    </div>
""",
    unsafe_allow_html=True,
)


def load_data():
    try:
        # Korrigierter Endpunkt: /shopping_list_beleg
        res = requests.get(
            f"{BASE_URL}/tasks/{task_id}/shopping_list_beleg", timeout=5
        )
        if res.status_code == 200:
            return res.json(), None
        elif res.status_code == 404:
            return (
                None,
                f"Für den Vorgang #{task_id} wurde noch keine Einkaufsliste"
                " gefunden.",
            )
        return (
            None,
            f"Fehler beim Laden der Einkaufsliste (Status: {res.status_code})",
        )
    except Exception as e:
        return None, f"Verbindung zur API fehlgeschlagen: {e}"


data, error = load_data()

if error:
    st.error(error)
elif not data:
    st.warning("Keine Daten für diese Einkaufsliste vorhanden.")
else:
    task_info = data.get("task", {})
    items = data.get("items", [])

    created_at = task_info.get("created_at", "")
    if created_at:
        try:
            created_at_fmt = pd.to_datetime(created_at).strftime(
                "%d.%m.%Y %H:%M"
            )
        except Exception:
            created_at_fmt = created_at
    else:
        created_at_fmt = "Unbekannt"

    df_items = pd.DataFrame(items)

    html_content = f"""
    <div class="print-container">
        <table class="header-table">
            <tr>
                <td>
                    <div class="header-title">Wareneinkauf Beleg</div>
                    <div class="header-sub">Vorgang #{task_id} | Erstellt am: {created_at_fmt}</div>
                </td>
                <td style="text-align: right; vertical-align: bottom;">
                    <div style="font-size: 12px; font-weight: bold;">Status: Offen / In Bearbeitung</div>
                </td>
            </tr>
        </table>

        <table class="items-table">
            <thead>
                <tr>
                    <th class="col-stueck">Stk</th>
                    <th class="col-leer1"></th>
                    <th class="col-leer2"></th>
                    <th class="col-bezeichnung">Bezeichnung</th>
                    <th class="col-einheit">Einheit</th>
                    <th class="col-ep">Einzelpreis</th>
                    <th class="col-gp">Gesamtpreis</th>
                    <th class="col-korrektur">Kor.</th>
                </tr>
            </thead>
            <tbody>
    """

    if df_items.empty:
        html_content += """
            <tr>
                <td colspan="8" style="text-align: center; color: #666; font-style: italic;">Keine Artikel in dieser Einkaufsliste.</td>
            </tr>
        """
    else:
        df_filtered = df_items[df_items["menge"] > 0]
        gesamtsumme = df_filtered["gesamt_preis"].sum()
        gesamt_artikel = df_filtered["menge"].sum()

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
                <td class="col-bezeichnung">Bestellung Gesamt</td>
                <td class="col-einheit"></td>
                <td class="col-ep"></td>
                <td class="col-gp">{gesamtsumme:,.2f} €</td>
                <td class="col-korrektur">€</td>
            </tr>
        """

    html_content += """
            </tbody>
        </table>

        <div class="footer-section">
            <div style="font-size: 11px; font-weight: bold; margin-bottom: 3px;">Anmerkungen / Korrekturen:</div>
            <div class="notes-box"></div>

            <table class="signature-table">
                <tr>
                    <td style="width: 45%;">
                        <div class="sig-line">Unterschrift Käufer / Einkäufer</div>
                    </td>
                    <td style="width: 10%;"></td>
                    <td style="width: 45%;">
                        <div class="sig-line">Unterschrift Prüfung / Kasse</div>
                    </td>
                </tr>
            </table>
        </div>
    </div>
    """

    st.html(html_content)