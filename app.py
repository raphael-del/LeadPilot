import streamlit as st
import os
import json
import urllib.request
from dotenv import load_dotenv


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="LeadPilot",
    page_icon="🔧",
    layout="centered"
)


# --------------------------------------------------
# GEMINI
# --------------------------------------------------

def call_gemini_analysis(client_message: str) -> dict:

    prompt = f"""
Tu es LeadPilot, un assistant IA destiné aux artisans et petites entreprises de services.

Analyse le message client suivant.

MESSAGE CLIENT :
{client_message}

Règles strictes :
- Ne JAMAIS inventer un prix.
- Ne JAMAIS inventer une disponibilité.
- Ne JAMAIS inventer une adresse.
- Ne JAMAIS inventer une information absente du message.
- Si une information importante manque, indique-la dans missing_info.
- Les réponses proposées doivent être courtes, professionnelles et naturelles.
- L'action recommandée doit être concrète et directement utile à l'artisan.
- Évalue la priorité commerciale uniquement à partir du message fourni.

Retourne UNIQUEMENT un JSON valide.
Ne mets aucun texte avant ou après le JSON.

Utilise exactement cette structure :

{{
    "urgency": "faible|moyenne|haute",
    "urgency_reason": "courte explication du niveau d'urgence",

    "summary": "résumé clair et précis de la demande",

    "extracted_info": {{
        "probleme": "",
        "lieu": "",
        "moment": "",
        "besoin_client": "",
        "intention_client": ""
    }},

    "missing_info": [],

    "recommended_action": "action concrète recommandée à l'artisan",

    "commercial_priority": "faible|moyenne|haute",

    "commercial_priority_reason":
        "courte explication de la priorité commerciale",

    "suggested_responses": [
        "réponse professionnelle prête à copier",
        "réponse alternative plus courte"
    ]
}}
"""

    # IMPORTANT :
    # Si ton ancien modèle fonctionnait déjà, garde exactement son nom ici.
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.6-flash:generateContent"
        f"?key={API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        raw = json.loads(
            response.read().decode("utf-8")
        )

    text = (
        raw["candidates"][0]
        ["content"]
        ["parts"][0]
        ["text"]
        .strip()
    )

    # Gemini peut parfois entourer le JSON avec ```
    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


# --------------------------------------------------
# INTERFACE LEADPILOT
# --------------------------------------------------

st.title("🔧 LeadPilot")

st.caption(
    "Assistant IA pour analyser les demandes clients "
    "et préparer une réponse professionnelle."
)

client_message = st.text_area(
    "Message du client",
    height=150,
    placeholder=(
        "Exemple : Bonjour, j'ai une fuite importante "
        "sous mon évier depuis ce matin. "
        "J'habite à Paris 15e. "
        "Pouvez-vous intervenir aujourd'hui ?"
    )
)


# --------------------------------------------------
# ANALYSE
# --------------------------------------------------

if st.button(
    "Analyser avec LeadPilot",
    use_container_width=True
):

    if not client_message.strip():

        st.warning(
            "Veuillez entrer un message client."
        )

    elif not API_KEY:

        st.error(
            "La clé GEMINI_API_KEY est introuvable."
        )

    else:

        try:

            with st.spinner(
                "LeadPilot analyse la demande..."
            ):

                result = call_gemini_analysis(
                    client_message
                )

            urgency = result.get(
                "urgency",
                "non précisée"
            )

            urgency_reason = result.get(
                "urgency_reason",
                ""
            )

            summary = result.get(
                "summary",
                ""
            )

            extracted = result.get(
                "extracted_info",
                {}
            )

            missing = result.get(
                "missing_info",
                []
            )

            recommended_action = result.get(
                "recommended_action",
                ""
            )

            commercial_priority = result.get(
                "commercial_priority",
                "non précisée"
            )

            commercial_reason = result.get(
                "commercial_priority_reason",
                ""
            )

            responses = result.get(
                "suggested_responses",
                []
            )


            # --------------------------------------
            # RAPPORT
            # --------------------------------------

            st.divider()

            st.header("📊 Rapport LeadPilot")


            # URGENCE
            st.subheader("🚨 Urgence")

            if urgency.lower() == "haute":
                st.error(
                    f"🔴 URGENCE {urgency.upper()}"
                )

            elif urgency.lower() == "moyenne":
                st.warning(
                    f"🟠 URGENCE {urgency.upper()}"
                )

            else:
                st.success(
                    f"🟢 URGENCE {urgency.upper()}"
                )

            if urgency_reason:
                st.write(urgency_reason)


            # RÉSUMÉ
            st.subheader("📝 Résumé")

            st.write(
                summary
                or "Résumé non disponible."
            )


            # INFORMATIONS DÉTECTÉES
            st.subheader(
                "🔎 Informations détectées"
            )

            st.markdown(
                f"**Problème :** "
                f"{extracted.get('probleme') or 'Non précisé'}"
            )

            st.markdown(
                f"**Lieu :** "
                f"{extracted.get('lieu') or 'Non précisé'}"
            )

            st.markdown(
                f"**Moment souhaité :** "
                f"{extracted.get('moment') or 'Non précisé'}"
            )

            st.markdown(
                f"**Besoin du client :** "
                f"{extracted.get('besoin_client') or 'Non précisé'}"
            )

            st.markdown(
                f"**Intention du client :** "
                f"{extracted.get('intention_client') or 'Non précisé'}"
            )


            # INFORMATIONS MANQUANTES
            st.subheader(
                "⚠️ Informations manquantes"
            )

            if missing:

                for information in missing:

                    st.markdown(
                        f"- {information}"
                    )

            else:

                st.success(
                    "Aucune information importante "
                    "ne semble manquer."
                )


            # ACTION CONSEILLÉE
            st.subheader(
                "🎯 Action recommandée"
            )

            st.info(
                recommended_action
                or
                "Aucune action particulière recommandée."
            )


            # PRIORITÉ COMMERCIALE
            st.subheader(
                "💼 Priorité commerciale"
            )

            if commercial_priority.lower() == "haute":

                st.success(
                    "🔥 PRIORITÉ COMMERCIALE HAUTE"
                )

            elif commercial_priority.lower() == "moyenne":

                st.info(
                    "📈 PRIORITÉ COMMERCIALE MOYENNE"
                )

            else:

                st.write(
                    "Priorité commerciale faible"
                )

            if commercial_reason:

                st.write(
                    commercial_reason
                )


            # RÉPONSES
            st.subheader(
                "✉️ Réponses prêtes à envoyer"
            )

            if responses:

                for index, response in enumerate(
                    responses,
                    start=1
                ):

                    st.markdown(
                        f"### Option {index}"
                    )

                    st.text_area(
                        f"Réponse {index}",
                        value=response,
                        height=120,
                        key=f"response_{index}"
                    )

            else:

                st.write(
                    "Aucune réponse générée."
                )


            st.divider()

            st.caption(
                "LeadPilot utilise l'IA pour assister "
                "la réponse aux demandes clients. "
                "L'artisan garde toujours le contrôle final."
            )


        except Exception as error:

            st.error(
                f"Erreur lors de l'analyse : {error}"
            )
            