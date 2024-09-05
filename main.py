from flask import Flask, session
from flask import render_template
from flask import request, jsonify
import PyPDF2
import os
import openai
from openai import OpenAI

UPLOAD_FOLDER = "uploads"
client = OpenAI()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")


def gt3_completion(question_user):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": question_user}]
    )
    return response.choices[0].message.content


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_SECURE"] = False


# version texte cours

# @app.route('/prompt', methods=['POST'])
# def answer():
#     error = None
#     ai_response = ask_question_to_pdf(request.form['prompt'])

#     return jsonify({"answer": ai_response})


# @app.route('/question', methods=['GET'])
# def handle_click_button():
#     error = None
#     ai_response = ask_question_to_pdf('Pose moi une question !')

#     return jsonify({"answer": ai_response})


# @app.route('/answer', methods=['POST'])
# def answer_click_button():
#     error = None
#     question = request.form['question']
#     rep = request.form['prompt']

#     ai_response = ask_question_to_pdf(f'Analyse ma réponse {rep} par rapport à ta
# question {question}. Ma réponse à ta question est - elle correcte?')

#     return jsonify({"answer": ai_response})


# version PDF unique ENPC


# def ask_question_to_pdf_bis(question_user='Peux-tu me résumer ce texte ?'):
#     list_string = ['texte', 'document', 'papier', 'pdf', 'cours', 'leçon', 'question']
#     if any(s in question_user.lower() for s in list_string):
#         text = read_pdf('filename.pdf')
#         assist_response = gt3_completion(question_user + text)
#     else:
#         assist_response = gt3_completion(question_user)
#     return assist_response


# @app.route('/prompt', methods=['POST'])
# def answer():
#     error = None
#     ai_response = ask_question_to_pdf_bis(request.form['prompt'])

#     return jsonify({"answer": ai_response})


# @app.route('/question', methods=['GET'])
# def handle_click_button():
#     error = None
#     ai_response = ask_question_to_pdf_bis('Pose moi une question !')

#     return jsonify({"answer": ai_response})


# @app.route('/answer', methods=['POST'])
# def answer_click_button():
#     error = None
#     question = request.form['question']
#     rep = request.form['prompt']

#     ai_response = ask_question_to_pdf_bis(f'Analyse ma réponse {rep} par rapport à ta
# question {question}. Ma réponse à ta question est - elle correcte?')

#     return jsonify({"answer": ai_response})


# version finale


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

    print(file_path)

    try:
        text = read_pdf(file_path)
        session["conversation"] = session["conversation"] + [
            {
                "role": "system",
                "content": f"Tu es un professeur spécialisé dans les questions autour de ce texte: {text}",
            }
        ]

    except Exception as e:
        return (
            jsonify(
                {"message": "Erreur lors du traitement du fichier.", "error": str(e)}
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": "Fichier téléchargé et traité avec succès.",
                "filename": file.filename,
            }
        ),
        200,
    )


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
