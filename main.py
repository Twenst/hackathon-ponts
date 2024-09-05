from flask import Flask, session
from flask import render_template
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import PyPDF2
import os

UPLOAD_FOLDER = 'uploads'


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialisation de Flask et SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='session', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10))  # 'user' ou 'assistant'
    content = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)


with app.app_context():
    db.create_all()

@app.route("/")
def hello_world():
    # Si une session est en cours, sauvegarder ses messages comme "terminée"
    if 'session_id' in session:
        current_session = Session.query.get(session['session_id'])
        if current_session:
            # La session actuelle est terminée, donc on peut la conserver telle quelle
            pass
    
    # Créer une nouvelle session
    new_session = Session()
    db.session.add(new_session)
    db.session.commit()

    # Réinitialiser la session Flask avec la nouvelle session et conversation vide
    session['session_id'] = new_session.id
    session['conversation'] = []

    # Récupérer toutes les sessions pour l'historique
    sessions = Session.query.order_by(Session.timestamp.desc()).all()

    return render_template('index.html', sessions=sessions)




@app.route('/prompt', methods=['POST'])
def handle_prompt():
    user_prompt = request.form['prompt']

    # Vérifier si 'conversation' existe dans la session, sinon l'initialiser
    if 'conversation' not in session:
        session['conversation'] = []

    # Vérifier si une session de conversation est active, sinon en créer une nouvelle
    if 'session_id' not in session:
        new_session = Session()
        db.session.add(new_session)
        db.session.commit()  # Sauvegarder la session
        session['session_id'] = new_session.id

    # Ajouter la question de l'utilisateur à la session 'conversation'
    session['conversation'].append({"role": "user", "content": user_prompt})

    # Appel à l'API OpenAI pour obtenir une réponse de l'IA
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=session['conversation'])
    assistant_response = response.choices[0].message.content

    # Ajouter la réponse de l'IA à la conversation
    session['conversation'].append({"role": "assistant", "content": assistant_response})

    # Sauvegarder la conversation dans la base de données sous forme de messages
    current_session = Session.query.get(session['session_id'])
    user_message = Message(role="user", content=user_prompt, session=current_session)
    assistant_message = Message(role="assistant", content=assistant_response, session=current_session)

    db.session.add(user_message)
    db.session.add(assistant_message)
    db.session.commit()

    # Retourner la réponse de l'IA au client
    return jsonify({"answer": assistant_response})



@app.route('/session/<int:id>', methods=['GET'])
def get_session(id):
    current_session = Session.query.get_or_404(id)
    messages = [{"role": msg.role, "content": msg.content} for msg in current_session.messages]
    return jsonify({"messages": messages})

# Fonction pour lire et interpréter un fichier PDF
def read_pdf(filename):
    context = ""
    with open(filename, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(reader.pages)
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text().replace("\n", " ")
            context += page_text
    return context

@app.route('/file-transfer', methods=['POST'])
def interpret_file():
    if 'file' not in request.files:
        return jsonify({'message': 'Aucun fichier trouvé.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'Aucun fichier sélectionné.'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        text = read_pdf(file_path)
        session['conversation'] = [{"role": "system", "content": f"Tu es un professeur spécialisé dans les questions autour de ce texte: {text}"}]
    except Exception as e:
        return jsonify({'message': 'Erreur lors du traitement du fichier.', 'error': str(e)}), 500

    return jsonify({
        'message': 'Fichier téléchargé et traité avec succès.',
        'filename': file.filename,
    }), 200





# Définition du modèle Conversation
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)


# Fonction pour générer une réponse avec OpenAI GPT-3.5
def gt3_completion(question_user):
    response = client.chat_completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question_user}]
    )
    return response.choices[0].message.content


text = "Les voitures électriques offrent plusieurs avantages par rapport aux voitures à moteur thermique : 1. **Zéro émissions locales :** Les voitures électriques ne produisent pas d'émissions d'échappement locales, réduisant ainsi la pollution de l'air et les effets sur la santé. 2. **Moins de dépendance aux combustibles fossiles :** Les voitures électriques utilisent l'électricité, qui peut provenir de sources renouvelables comme le soleil et le vent, réduisant la dépendance aux combustibles fossiles.3. **Coûts de fonctionnement réduits :** Les voitures électriques ont moins de pièces mobiles et nécessitent moins d'entretien par rapport aux voitures à moteur thermique, ce qui peut réduire les coûts à long terme. 4. **Performance instantanée :** Les voitures électriques offrent un couple élevé dès le départ, ce qui signifie une accélération rapide et fluide sans la nécessité de changer de vitesses. 5. **Conduite silencieuse :** Les moteurs électriques sont beaucoup plus silencieux que les moteurs thermiques, offrant une expérience de conduite plus paisible. 6. **Amélioration de l'efficacité énergétique :** Les voitures électriques convertissent plus efficacement l'énergie électrique en mouvement par rapport aux moteurs à combustion interne. 7. **Réduction des émissions de gaz à effet de serre :** Même en tenant compte de l'émission de CO2 liée à la production d'électricité, les voitures électriques ont tendance à produire moins d'émissions de gaz à effet de serre sur leur cycle de vie par rapport aux voitures à essence. 8. **Innovation technologique :** Les voitures électriques stimulent le développement de nouvelles technologies, telles que les batteries plus performantes et les systèmes de recharge avancés. 9. **Réduction du bruit urbain :** La diminution du bruit des véhicules électriques contribue à réduire le niveau de bruit dans les zones urbaines. 10. **Subventions et incitations :** Dans de nombreux endroits, les voitures électriques bénéficient d'incitations gouvernementales, telles que des réductions fiscales ou des voies réservées. Il est important de noter que la transition vers les voitures électriques implique également des défis, tels que l'infrastructure de recharge en expansion, la gestion des matériaux des batteries et l'autonomie limitée par rapport aux voitures à essence sur de longs trajets. Cependant, les avantages en matière d'environnement et d'efficacité continuent de renforcer l'attrait des voitures électriques pour l'avenir de la mobilité."

def ask_question_to_pdf(question_user = 'Peux-tu me résumer ce texte ?'):
    return gt3_completion(question_user + text)
###

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SECURE'] = False



@app.route('/conversation/<int:id>', methods=['GET'])
def get_conversation(id):
    conversation = Conversation.query.get_or_404(id)
    return jsonify({
        'question': conversation.question,
        'answer': conversation.answer
    })


################### version texte cours 

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

#     ai_response = ask_question_to_pdf(f'Analyse ma réponse {rep} par rapport à ta question {question}. Ma réponse à ta question est - elle correcte?')

#     return jsonify({"answer": ai_response})


################### version PDF unique ENPC 


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

#     ai_response = ask_question_to_pdf_bis(f'Analyse ma réponse {rep} par rapport à ta question {question}. Ma réponse à ta question est - elle correcte?')

#     return jsonify({"answer": ai_response})



################### version finale



def gt3_completion_historiq(historiq_conv):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=historiq_conv
    )
    return response.choices[0].message.content


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

#     ai_response = ask_question_to_pdf_bis(f'Analyse ma réponse {rep} par rapport à ta question {question}. Ma réponse à ta question est - elle correcte?')

#     return jsonify({"answer": ai_response})
