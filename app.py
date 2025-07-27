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
if "vp_nummer" not in st.session_state:
    st.session_state.vp_nummer = f"VP{random.randint(1000,9999)}"

# === Hilfsfunktion zum Initialisieren von Responses ===
def ensure_response_index(idx, current_image):
    while len(st.session_state.responses) <= idx:
        st.session_state.responses.append({
            "comic": current_image,
            "beschreibung": "",
            "verständlichkeit": "",
            "geschwindigkeit": "",
            "langweilig": ""
        })

# === Bilddaten ===
image_folder = "images"
image_files = []

if "gruppe" in st.session_state and st.session_state.step >= 2:
    if os.path.exists(image_folder):
        image_files = sorted([
            f for f in os.listdir(image_folder)
            if f.lower().endswith(".png") and f.startswith(f"{st.session_state.gruppe}_")
        ])
    else:
        st.error("Der Ordner 'images' fehlt. Bitte lade ihn ins Repository.")
        st.stop()

total_items = len(image_files)
max_step = total_items * 2 + 2  # +1 wegen Englischfrage-Schritt

# === App-Flow ===
st.title("Comic-Experiment")

# === Step 0: Einführung + Beispielbild
if st.session_state.step == 0:
    st.markdown("## Willkommen zum Experiment")
    st.markdown("""
    In diesem Experiment werden Sie verschiedene Comic-Seiten sehen und danach jeweils kurze Fragen beantworten.

    Bitte lesen Sie die Inhalte aufmerksam und beantworten Sie die Fragen aufrichtig.
    
    Hier sehen Sie ein Beispiel, wie das Experiement und die gestellten Fragen aussehen:
    """)
    st.image("images/beispiel.png", caption="Beispielcomic (nicht Teil des Experiments)")
    
    st.markdown("""Bitte beschreiben Sie den Inhalt des Comics in einem Satz.""")
    
    st.markdown("""War der Comic inhaltlich verständlich?""")
    
    st.markdown("""Wie schnell konnten Sie den Comic verstehen?""")
    
    st.markdown("""Waren Sie während des Lesens gelangweilt?""")
    
    st.markdown("""Wie spannend fanden Sie den Comic?""")
    if st.button("Weiter"):
        st.session_state.step += 1
        st.rerun()

# === Step 1: Englischkenntnisse
elif st.session_state.step == 1:
    st.markdown("### Bevor es losgeht: Sprachkenntnisse")
    english_level = st.selectbox(
        "Wie schätzen Sie Ihre Englischkenntnisse ein?",
        ["Sehr gut", "Gut", "Mittel", "Schlecht", "Sehr schlecht"]
    )
    if st.button("Start"):
        st.session_state.english_level = english_level
        st.session_state.startzeit = datetime.now().isoformat()
        st.session_state.step += 1
        st.rerun()

# === Comic- & Fragerunden
elif 2 <= st.session_state.step <= max_step - 1:
    item_index = (st.session_state.step - 2) // 2

    if item_index >= len(image_files):
        st.error("Kein weiteres Bild verfügbar.")
        st.stop()

    current_image = image_files[item_index]

    # === Gerade Schritte: Comic + Freitext
    if st.session_state.step % 2 == 0:
        st.image(f"{image_folder}/{current_image}",
                 caption=f"Comic {item_index + 1}")

        q0 = st.selectbox("Kennen Sie diese Comic-Seite?",
                          ["Nein", "Ja"],
                          key=f"q0_{item_index}")

        st.markdown("**Bitte beschreiben Sie den Inhalt des Comics in einem Satz:**")
        text_input = st.text_input("Ihre Beschreibung:", key=f"text_{item_index}")

        if st.button("Weiter"):
            if text_input.strip() == "":
                st.warning("Bitte geben Sie eine Beschreibung ein, bevor Sie fortfahren.")
            else:
                ensure_response_index(item_index, current_image)
                st.session_state.responses[item_index]["bekanntheit"] = q0
                st.session_state.responses[item_index]["beschreibung"] = text_input.strip()
                st.session_state.step += 1
                st.rerun()

    # === Ungerade Schritte: Likert-Skalenfragen
    else:
        st.markdown("**Bitte bewerten Sie den Comic:**")

        ensure_response_index(item_index, current_image)

        q1 = st.radio("War der Comic inhaltlich verständlich?",
                      ["1 (Stimme überhaupt nicht zu)", "2", "3", "4", "5 (Stimme voll zu)"],
                      key=f"q1_{item_index}")
        q2 = st.radio("Wie schnell konnten Sie den Comic verstehen?",
                      ["1 (Sehr langsam)", "2", "3", "4", "5 (Sehr schnell)"],
                      key=f"q2_{item_index}")
        q3 = st.radio("Waren Sie während des Lesens gelangweilt?",
                      ["1 (Gar nicht)", "2", "3", "4", "5 (Sehr)"],
                      key=f"q3_{item_index}")
        q4 = st.radio("Wie spannend fanden Sie den Comic?",
                      ["1 (Gar nicht)", "2", "3", "4", "5 (Sehr)"],
                      key=f"q4_{item_index}")
        if st.button("Weiter"):
            st.session_state.responses[item_index].update({
                "verständlichkeit": q1,
                "geschwindigkeit": q2,
                "langeweile": q3,
                "spannung": q4
            })

            antwort_row = [
                datetime.now().isoformat(),
                st.session_state.vp_nummer,
                st.session_state.english_level,
                st.session_state.gruppe,
                item_index + 1,
                current_image,
                st.session_state.responses[item_index].get("beschreibung", ""),
                q1,
                q2,
                q3,
                q4,
                st.session_state.startzeit
            ]
            st.session_state.antworten.append(antwort_row)
            st.session_state.step += 1
            st.rerun()

# === Ergebnisse an GitHub anhängen + Danke
elif st.session_state.step >= max_step:
    token = st.secrets["github"]["token"]
    repo = "elisabz/comic_experiment"
    branch = "main"
    filename = "Results/responses.csv"

    # Neue Daten vorbereiten
    output_lines = []
    for row in st.session_state.antworten:
        output_lines.append(",".join(map(str, row)))
    new_content = "\n".join(output_lines) + "\n"

    # Datei auf GitHub abrufen
    api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    get_response = requests.get(api_url, headers=headers)

    if get_response.status_code == 200:
        existing = get_response.json()
        existing_content = base64.b64decode(existing['content']).decode('utf-8')
        combined_content = existing_content.strip() + "\n" + new_content
        sha = existing['sha']
    elif get_response.status_code == 404:
        # Datei existiert noch nicht → neue Datei mit Header
        combined_content = "timestamp,vp_nummer,englisch_level,gruppe,comic_index,filename,antwort,frage1,frage2,frage3,startzeit\n" + new_content
        sha = None
    else:
        st.error(f"Fehler beim Abrufen der Datei: {get_response.status_code}")
        st.stop()

    # Datei aktualisieren oder neu anlegen
    encoded_content = base64.b64encode(combined_content.encode("utf-8")).decode("utf-8")
    data = {
        "message": f"Update responses with {st.session_state.vp_nummer}",
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        data["sha"] = sha

    put_response = requests.put(api_url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        st.success("Ihre Antworten wurden erfolgreich übermittelt.")
    else:
        st.error(f"Upload fehlgeschlagen. Fehlercode: {put_response.status_code}")

    st.markdown("## 🎉 Vielen Dank für Ihre Teilnahme!")
    st.markdown("Sie können das Fenster nun schließen.")
