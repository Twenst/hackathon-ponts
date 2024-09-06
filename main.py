from flask import Flask, session, render_template, request, jsonify
import PyPDF2
import os
import openai
from openai import OpenAI

client = OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

UPLOAD_FOLDER = "uploads"


def gt3_completion(question_user):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": question_user}]
    )
    return response.choices[0].message.content


text = (
    "Les voitures électriques offrent plusieurs avantages par rapport aux "
    "voitures à moteur thermique : 1. **Zéro émissions locales :** Les "
    "voitures électriques ne produisent pas d'émissions d'échappement "
    "locales, réduisant ainsi la pollution de l'air et les effets sur la "
    "santé. 2. **Moins de dépendance aux combustibles fossiles :** Les "
    "voitures électriques utilisent l'électricité, qui peut provenir de "
    "sources renouvelables comme le soleil et le vent, réduisant la "
    "dépendance aux combustibles fossiles. 3. **Coûts de fonctionnement "
    "réduits :** Les voitures électriques ont moins de pièces mobiles et "
    "nécessitent moins d'entretien par rapport aux voitures à moteur "
    "thermique, ce qui peut réduire les coûts à long terme. 4. **Performance "
    "instantanée :** Les voitures électriques offrent un couple élevé dès le "
    "départ, ce qui signifie une accélération rapide et fluide sans la "
    "nécessité de changer de vitesses. 5. **Conduite silencieuse :** Les "
    "moteurs électriques sont beaucoup plus silencieux que les moteurs "
    "thermiques, offrant une expérience de conduite plus paisible. 6. "
    "**Amélioration de l'efficacité énergétique :** Les voitures électriques "
    "convertissent plus efficacement l'énergie électrique en mouvement par "
    "rapport aux moteurs à combustion interne. 7. **Réduction des émissions "
    "de gaz à effet de serre :** Même en tenant compte de l'émission de CO2 "
    "liée à la production d'électricité, les voitures électriques ont "
    "tendance à produire moins d'émissions de gaz à effet de serre sur leur "
    "cycle de vie par rapport aux voitures à essence. 8. **Innovation "
    "technologique :** Les voitures électriques stimulent le développement "
    "de nouvelles technologies, telles que les batteries plus performantes et "
    "les systèmes de recharge avancés. 9. **Réduction du bruit urbain :** La "
    "diminution du bruit des véhicules électriques contribue à réduire le "
    "niveau de bruit dans les zones urbaines. 10. **Subventions et "
    "incitations :** Dans de nombreux endroits, les voitures électriques "
    "bénéficient d'incitations gouvernementales, telles que des réductions "
    "fiscales ou des voies réservées."
)


def ask_question_to_pdf(question_user="Peux-tu me résumer ce texte ?"):
    print(gt3_completion(question_user + text))
    return None


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_SECURE"] = False

# Routes - VERSION texte cours de test ###################


@app.route("/")
def hello_world():
    session["conversation"] = []
    return render_template("index.html")


def read_pdf(filename):
    context = ""
    with open(filename, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(reader.pages)
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text().replace("\n", " ")
            context += page_text
    return context


def gt3_completion_historiq(historiq_conv):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=historiq_conv
    )
    return response.choices[0].message.content


@app.route("/file-transfer", methods=["POST"])
def interpret_file():
    if "file" not in request.files:
        return jsonify({"message": "Aucun fichier trouvé."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"message": "Aucun fichier sélectionné."}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        text = read_pdf(file_path)
        session["conversation"] = session["conversation"] + [
            {
                "role": "system",
                "content": (
                    f"Tu es un professeur spécialisé dans les questions autour de "
                    f"ce texte: {text}"
                ),
            }
        ]

    except Exception as e:
        return jsonify({"message": "Erreur lors du traitement du fichier.", "error": str(e)}), 500

    return jsonify({"message": "Fichier téléchargé et traité avec succès.", "filename": file.filename}), 200


@app.route("/prompt", methods=["POST"])
def handle_prompt():
    user_prompt = request.form["prompt"]

    session["conversation"] = session["conversation"] + [
        {"role": "user", "content": user_prompt}
    ]

    historiq_conv = session["conversation"]

    ai_response = gt3_completion_historiq(historiq_conv)

    session["conversation"] = session["conversation"] + [
        {"role": "assistant", "content": ai_response}
    ]

    return jsonify({"answer": ai_response})


@app.route("/question", methods=["GET"])
def handle_click_question_button():
    session["conversation"] = session["conversation"] + [
        {"role": "user", "content": "Pose moi une question sur le texte!"}
    ]

    historiq_conv = session["conversation"]

    ai_response = gt3_completion_historiq(historiq_conv)

    session["conversation"] = session["conversation"] + [
        {"role": "user", "content": ai_response}
    ]

    return jsonify({"answer": ai_response})


@app.route("/answer", methods=["POST"])
def answer_click_button():
    user_prompt = request.form["prompt"]

    session["conversation"] = session["conversation"] + [
        {"role": "user", "content": user_prompt}
    ]

    historiq_conv = session["conversation"]

    ai_response = gt3_completion_historiq(historiq_conv)

    session["conversation"] = session["conversation"] + [
        {"role": "user", "content": ai_response}
    ]

    return jsonify({"answer": ai_response})


@app.route("/delete-session-cookie", methods=["POST"])
def delete_session_cookie():
    session["conversation"] = []

    return "", 204
