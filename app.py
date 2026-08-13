import streamlit as st
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

def call_gemini_analysis(client_message: str) -> dict:
    prompt = f"""
Tu es LeadPilot, un assistant IA destiné aux artisans plombiers.

Analyse le message client suivant :

MESSAGE CLIENT :
{client_message}

Règles strictes :
- Ne JAMAIS inventer un prix.
- Ne JAMAIS inventer une disponibilité.
- Ne JAMAIS inventer une adresse.
- Si une information importante manque, indique-la.
- Les réponses proposées doivent être courtes, professionnelles et naturelles.

Retourne UNIQUEMENT un JSON valide avec exactement cette structure :

{{
  "urgency": "faible|moyenne|haute",
  "urgency_reason": "une phrase courte expliquant pourquoi",
  "summary": "résumé en une phrase de la demande",
  "extracted_info": {{
    "probleme": "",
    "lieu": "",
    "moment": ""
  }},
  "missing_info": [],
  "suggested_responses": [
    "réponse 1 prête à copier",
    "réponse 2 alternative"
  ]
}}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.6-flash:generateContent"
        f"?key={API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        raw = json.loads(response.read().decode("utf-8"))

    text = raw["candidates"][0]["content"]["parts"][0]["text"].strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


st.set_page_config(
    page_title="LeadPilot",
    page_icon="🔧",
    layout="centered"
)

st.title("🔧 LeadPilot")
st.caption("Assistant IA pour répondre plus vite aux demandes clients")

client_message = st.text_area(
    "Message du client",
    height=160,
    placeholder="Exemple : Bonjour, j'ai une fuite sous mon évier depuis ce matin. Pouvez-vous intervenir aujourd'hui ?"
)

if st.button(
    "Analyser avec LeadPilot",
    type="primary",
    use_container_width=True
):
    if not client_message.strip():
        st.warning("Colle d'abord un message client.")
    elif not API_KEY:
        st.error("Clé Gemini introuvable dans le fichier .env.")
    else:
        with st.spinner("Analyse en cours..."):
            try:
                result = call_gemini_analysis(client_message)
            except Exception as e:
                st.error(f"Erreur pendant l'analyse : {e}")
                st.stop()

        colors = {
            "haute": "🔴",
            "moyenne": "🟠",
            "faible": "🟢"
        }

        urgency = result.get("urgency", "faible")

        st.subheader(
            f"{colors.get(urgency, '⚪')} Urgence : {urgency.capitalize()}"
        )

        st.write(result.get("urgency_reason", ""))

        st.markdown("### Résumé")
        st.write(result.get("summary", ""))

        st.markdown("### Informations détectées")

        for key, value in result.get("extracted_info", {}).items():
            if value:
                st.write(f"- **{key.capitalize()}** : {value}")

        missing = result.get("missing_info", [])

        if missing:
            st.markdown("### ⚠️ Informations manquantes")

            for item in missing:
                st.write(f"- {item}")

        st.markdown("### Réponses proposées")

        for i, response_text in enumerate(
            result.get("suggested_responses", []),
            1
        ):
            st.markdown(f"**Option {i}**")
            st.code(response_text, language=None)
