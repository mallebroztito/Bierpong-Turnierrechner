import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
import tempfile

st.title("🍻 TBV Bierpong Turnierrechner")

# Teamnamen festlegen
if "teams_festgelegt" not in st.session_state:
    st.session_state.teamnamen = ["" for _ in range(5)]
    with st.form("teamnamen_form"):
        st.subheader("Teamnamen eingeben")
        for i in range(5):
            st.session_state.teamnamen[i] = st.text_input(f"Team {chr(65+i)}", value=f"Team {chr(65+i)}")
        submitted = st.form_submit_button("Teamnamen speichern")
        if submitted:
            st.session_state.teams_festgelegt = True
            st.rerun()
    st.stop()

# Initialisiere Session State beim ersten Aufruf
if "tabelle" not in st.session_state:
    teams = st.session_state.teamnamen
    st.session_state.teams = teams
    st.session_state.tabelle = {
        team: {"Punkte": 0, "Differenz": 0, "Spiele": 0} for team in teams
    }
    st.session_state.spiele = [
        (teams[0], teams[1]),
        (teams[2], teams[3]),
        (teams[0], teams[4]),
        (teams[1], teams[2]),
        (teams[0], teams[3]),
        (teams[1], teams[3]),
        (teams[0], teams[2]),
        (teams[3], teams[4]),
        (teams[1], teams[4]),
        (teams[2], teams[4])
    ]
    st.session_state.ergebnisse = []

# Ergebnis-Eingabe
with st.form("ergebnis_form"):
    st.subheader("Spiel eintragen")
    offene_spiele = [spiel for spiel in st.session_state.spiele if spiel not in [e["spiel"] for e in st.session_state.ergebnisse]]

    if offene_spiele:
        aktuelles_spiel = offene_spiele[0]
        team1, team2 = aktuelles_spiel
        b1 = st.number_input(f"Becher {team1}", min_value=0, max_value=10, step=1)
        b2 = st.number_input(f"Becher {team2}", min_value=0, max_value=10, step=1)
        ergebnis = st.selectbox("Ergebnis (aus Sicht von Team 1)", ["s", "sv", "nv", "n"], format_func=lambda x: {
            "s": "Sieg (3 Punkte)",
            "sv": "Sieg in Verlängerung (2:1)",
            "nv": "Niederlage in Verlängerung (1:2)",
            "n": "Niederlage (0:3)"
        }[x])
        submitted = st.form_submit_button("Eintragen")

        if submitted:
            punkte = {team1: 0, team2: 0}
            if ergebnis == "s":
                punkte[team1] = 3
            elif ergebnis == "sv":
                punkte[team1] = 2
                punkte[team2] = 1
            elif ergebnis == "nv":
                punkte[team1] = 1
                punkte[team2] = 2
            elif ergebnis == "n":
                punkte[team2] = 3

            st.session_state.tabelle[team1]["Punkte"] += punkte[team1]
            st.session_state.tabelle[team2]["Punkte"] += punkte[team2]
            st.session_state.tabelle[team1]["Differenz"] += b2 - b1
            st.session_state.tabelle[team2]["Differenz"] += b1 - b2
            st.session_state.tabelle[team1]["Spiele"] += 1
            st.session_state.tabelle[team2]["Spiele"] += 1
            st.session_state.ergebnisse.append({"spiel": aktuelles_spiel, "b1": b1, "b2": b2, "ergebnis": ergebnis})
            st.success(f"Ergebnis für {team1} vs {team2} eingetragen!")
            st.rerun()
    else:
        st.info("Alle Spiele wurden eingetragen!")

# Tabelle anzeigen
st.subheader("🏆 Aktuelle Tabelle")
df = pd.DataFrame(st.session_state.tabelle).T
sortiert = df.sort_values(by=["Punkte", "Differenz"], ascending=False)

def highlight_rangierung(row):
    style = ["" for _ in row.index]
    if row.name == sortiert.index[0]:
        style = ["background-color: lightgreen" for _ in row.index]
    elif row.name in sortiert.index[1:3]:
        style = ["background-color: lightyellow" for _ in row.index]
    return style

st.dataframe(sortiert.style.apply(highlight_rangierung, axis=1), use_container_width=True)

# Legende
st.markdown("""
**Legende:**  
🟩 Platz 1 = Finale  
🟨 Platz 2–3 = Halbfinale
""")

# PDF Export Funktion
def export_to_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Bierpong Turnier Tabelle", ln=True, align='C')
    pdf.ln(10)

    # Tabellenkopf
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(50, 10, "Team", border=1)
    pdf.cell(30, 10, "Punkte", border=1)
    pdf.cell(30, 10, "Differenz", border=1)
    pdf.cell(30, 10, "Spiele", border=1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for index, row in dataframe.iterrows():
        pdf.cell(50, 10, index, border=1)
        pdf.cell(30, 10, str(row["Punkte"]), border=1)
        pdf.cell(30, 10, str(row["Differenz"]), border=1)
        pdf.cell(30, 10, str(row["Spiele"]), border=1)
        pdf.ln()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    return tmp_file.name

# PDF Download-Button
if st.button("📄 Tabelle als PDF exportieren"):
    pdf_path = export_to_pdf(sortiert)
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        href = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="bierpong_tabelle.pdf">📥 PDF herunterladen</a>'
        st.markdown(href, unsafe_allow_html=True)

# Reset-Knopf
if st.button("🔁 Turnier zurücksetzen"):
    for key in ["tabelle", "teams_festgelegt", "teamnamen", "spiele", "ergebnisse"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
