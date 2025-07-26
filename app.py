import streamlit as st
import pandas as pd
import os
from datetime import datetime
import random
import base64
import requests

# === Gruppenzuordnung ===
GROUPS = ["A", "B", "C"]
GROUP_LOG = "gruppen_log.csv"

def assign_group():
    if not os.path.exists(GROUP_LOG):
        df = pd.DataFrame({"gruppe": GROUPS, "anzahl": [0]*len(GROUPS)})
        df.to_csv(GROUP_LOG, index=False)
    df = pd.read_csv(GROUP_LOG)
    min_count = df["anzahl"].min()
    candidates = df[df["anzahl"] == min_count]["gruppe"].tolist()
    selected = random.choice(candidates)
    df.loc[df["gruppe"] == selected, "anzahl"] += 1
    df.to_csv(GROUP_LOG, index=False)
    return selected

# === Initialisierung ===
if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "english_level" not in st.session_state:
    st.session_state.english_level = None
if "gruppe" not in st.session_state:
    st.session_state.gruppe = assign_group()
if "antworten" not in st.session_state:
    st.session_state.antworten = []

# === Bilddaten ===
image_folder = "images"
image_files = sorted([
    f for f in os.listdir(image_folder)
    if f.lower().endswith(".jpg") and f.startswith(f"{st.session_state.gruppe}_")
])

total_items = len(image_files)
max_step = total_items * 2

# === App-Flow ===
st.title("🧪 Comic-Experiment")

if st.session_state.step == 0:
    st.markdown("""
    Willkommen zum Experiment!  
    Sie werden mehrere Comic-Seiten sehen und danach jeweils Fragen beantworten.  
    Bitte beantworten Sie alles aufmerksam.
    """)
    english_level = st.selectbox("Wie schätzen Sie Ihre Englischkenntnisse ein?",
                                 ["Sehr gut", "Gut", "Mittel", "Schlecht", "Sehr schlecht"])
    if st.button("Start"):
        st.session_state.english_level = english_level
        st.session_state.startzeit = datetime.now().isoformat()
        st.session_state.step += 1
        st.rerun()

# === Comic- & Fragerunden ===
elif 1 <= st.session_state.step <= max_step:
    item_index = (st.session_state.step - 1) // 2

    if item_index >= len(image_files):
        st.error("🚫 Kein weiteres Bild verfügbar.")
        st.stop()

    current_image = image_files[item_index]

    # === Ungerade Schritte: Comic + Freitext
    if st.session_state.step % 2 == 1:
        st.image(os.path.join(image_folder, current_image), caption=f"Comic {item_index + 1}")
        st.markdown("**Bitte beschreiben Sie kurz den Inhalt des Comics in einem Satz:**")
        text_input = st.text_input("Ihre Beschreibung:", key=f"text_{item_index}")
        if st.button("Weiter"):
            st.session_state.responses.append({
                "comic": current_image,
                "beschreibung": text_input
            })
            st.session_state.step += 1
            st.rerun()

    # === Gerade Schritte: Likert-Skalenfragen
    else:
        st.markdown("**Bitte bewerten Sie den Comic:**")

        q1 = st.radio("War der Comic inhaltlich verständlich?",
                      ["1 (Stimme überhaupt nicht zu)", "2", "3", "4", "5 (Stimme voll zu)"],
                      key=f"q1_{item_index}")
        q2 = st.radio("Wie schnell konnten Sie den Comic verstehen?",
                      ["1 (Sehr langsam)", "2", "3", "4", "5 (Sehr schnell)"],
                      key=f"q2_{item_index}")
        q3 = st.radio("Waren Sie gelangweilt?",
                      ["1 (Gar nicht)", "2", "3", "4", "5 (Sehr)"],
                      key=f"q3_{item_index}")
        if st.button("Weiter"):
            st.session_state.responses[-1].update({
                "verständlichkeit": q1,
                "geschwindigkeit": q2,
                "langweilig": q3
            })

            # ✅ Antworten sammeln
            antwort_row = [
                datetime.now().isoformat(),
                st.session_state.gruppe,
                item_index + 1,
                current_image,
                st.session_state.responses[-1].get("beschreibung", ""),
                q1,
                q2,
                st.session_state.startzeit
            ]
            st.session_state.antworten.append(antwort_row)

            st.session_state.step += 1
            st.rerun()

# === Ergebnisse an GitHub senden ===
if st.session_state.step > max_step and st.session_state.antworten:
    token = st.secrets["github"]["token"]
    repo = "elisabz/comic_experiment"
    branch = "main"

    filename = f"Results/group_{st.session_state.gruppe}_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    output_lines = ["timestamp,gruppe,comic_index,filename,antwort,frage1,frage2,startzeit"]
    for row in st.session_state.antworten:
        output_lines.append(",".join(map(str, row)))

    output_csv = "\n".join(output_lines)
    encoded_content = base64.b64encode(output_csv.encode("utf-8")).decode("utf-8")

    api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "message": f"Add response file {filename}",
        "content": encoded_content,
        "branch": branch
    }

    response = requests.put(api_url, headers=headers, json=data)

    if response.status_code == 201:
        st.succes

