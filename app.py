import streamlit as st
import os
from datetime import datetime
import pandas as pd

# === Konfiguration ===
st.set_page_config(page_title="Comic Experiment", layout="centered")

# === Session-Initialisierung ===
if "step" not in st.session_state:
    st.session_state.step = 0  # Schritte: 0 = Intro, 1 = Comic 1, ..., 12 = Ende
if "responses" not in st.session_state:
    st.session_state.responses = []

# === Bildpfade ===
image_files = [f"comic{i}.png" for i in range(1, 7)]  # comic1.png bis comic6.png im /Images-Ordner

# === Schritt 0: Einführung ===
if st.session_state.step == 0:
    st.title("🧠 Comic-Experiment")
    st.markdown("""
    Willkommen zum Experiment!  
    Sie werden sechs Comic-Seiten sehen. Danach beantworten Sie einige Fragen.  
    Bitte beantworten Sie ehrlich und aufmerksam.
    """)
    english_level = st.selectbox("Wie schätzen Sie Ihre Englischkenntnisse ein?",
                                 ["Sehr gut", "Gut", "Mittel", "Schlecht", "Sehr schlecht"])
    if st.button("Start"):
        st.session_state.english_level = english_level
        st.session_state.step += 1
        st.rerun()

# === Schritte 1–12: Comic-Items ===
elif 1 <= st.session_state.step <= 12:
    item_index = (st.session_state.step - 1) // 2  # 0–5 für Comic 1–6
    if st.session_state.step % 2 == 1:
        # === Schritt A: Comic zeigen + Freitextfrage ===
        st.image(os.path.join("Images", image_files[item_index]), caption=f"Comic {item_index + 1}")
        st.markdown("**Bitte beschreiben Sie kurz den Inhalt des Comics in einem Satz:**")
        text_input = st.text_input("Ihre Beschreibung:", key=f"text_{item_index}")
        if st.button("Weiter"):
            st.session_state.responses.append({"comic": image_files[item_index], "beschreibung": text_input})
            st.session_state.step += 1
            st.rerun()
    else:
        # === Schritt B: Likert-Skalenfragen ===
        st.markdown("**Bitte bewerten Sie den Comic:**")

        q1 = st.radio("War der Comic inhaltlich verständlich?",
                      ["1 (Stimme überhaupt nicht zu)", "2", "3", "4", "5 (Stimme voll zu)"], key=f"q1_{item_index}")
        q2 = st.radio("Wie schnell konnten Sie den Comic verstehen?",
                      ["1 (Sehr langsam)", "2", "3", "4", "5 (Sehr schnell)"], key=f"q2_{item_index}")
        q3 = st.radio("Waren Sie gelangweilt?",
                      ["1 (Gar nicht)", "2", "3", "4", "5 (Sehr)"], key=f"q3_{item_index}")
        if st.button("Weiter"):
            st.session_state.responses[-1].update({
                "verständlichkeit": q1,
                "geschwindigkeit": q2,
                "langweilig": q3
            })
            st.session_state.step += 1
            st.rerun()

# === Schritt 13: Abschluss + Speicherung ===
elif st.session_state.step == 13:
    st.success("🎉 Vielen Dank für Ihre Teilnahme!")

    # Ergebnisse speichern
    df = pd.DataFrame(st.session_state.responses)
    df["englischkenntnisse"] = st.session_state.english_level
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"antworten_{timestamp}.csv"
    df.to_csv(filename, index=False)

    st.write("Ihre Antworten wurden gespeichert.")
    st.dataframe(df)
    st.balloons()
