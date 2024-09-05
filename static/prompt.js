const promptForm = document.getElementById("prompt-form");
const submitButton = document.getElementById("submit-button");
const questionButton = document.getElementById("question-button");
const messagesContainer = document.getElementById("messages-container");

const appendHumanMessage = (message) => {
  const humanMessageElement = document.createElement("div");
  humanMessageElement.classList.add("message", "message-human");
  humanMessageElement.innerHTML = message;
  messagesContainer.appendChild(humanMessageElement);
};

const appendAIMessage = async (messagePromise) => {
  // Add a loader to the interface
  const loaderElement = document.createElement("div");
  loaderElement.classList.add("message");
  loaderElement.innerHTML =
    "<div class='loader'><div></div><div></div><div></div>";
  messagesContainer.appendChild(loaderElement);

  // Await the answer from the server
  const messageToAppend = await messagePromise();

  // Replace the loader with the answer
  loaderElement.classList.remove("loader");

  /////
  loaderElement.classList.add("fade-text");

  loaderElement.innerHTML = messageToAppend;

  /////
  applyFadeEffect(loaderElement);
};

const handlePrompt = async (event) => {
  event.preventDefault();
  // Parse form data in a structured object
  const data = new FormData(event.target);
  promptForm.reset();

  let url = "/prompt";
  if (questionButton.dataset.question !== undefined) {
    url = "/answer";
    data.append("question", questionButton.dataset.question);
    delete questionButton.dataset.question;
    questionButton.classList.remove("hidden");
    submitButton.innerHTML = "Message";
  }

  appendHumanMessage(data.get("prompt"));

  await appendAIMessage(async () => {
    const response = await fetch(url, {
      method: "POST",
      body: data,
    });
    const result = await response.json();
    return result.answer;
  });
};

promptForm.addEventListener("submit", handlePrompt);

const handleQuestionClick = async (event) => {
  appendAIMessage(async () => {
    const response = await fetch("/question", {
      method: "GET",
    });
    const result = await response.json();
    const question = result.answer;

    questionButton.dataset.question = question;
    questionButton.classList.add("hidden");
    submitButton.innerHTML = "Répondre à la question";
    return question;
  });
};

questionButton.addEventListener("click", handleQuestionClick);

document.getElementById('pdf-button').addEventListener('change', function () {
  var sendPdfButton = document.getElementById('send-pdf-button');
  var resetPdfButton = document.getElementById('reset-button');
  if (this.files.length > 0) {
    sendPdfButton.style.display = 'block'; // Affiche le bouton si un fichier est sélectionné
    resetPdfButton.style.display = 'block';
  } else {
    sendPdfButton.style.display = 'none'; // Cache le bouton si aucun fichier n'est sélectionné
    resetPdfButton.style.display = 'none';
  }
});


/* reset button */

document.getElementById('reset-button').addEventListener('click', function (event) {
  var sendPdfButton = document.getElementById('send-pdf-button');
  var resetPdfButton = document.getElementById('reset-button');
  var fileInput = document.getElementById('pdf-button');
  var fileInfo = document.getElementById('file-info');
  fileInput.value = ''; // Réinitialise la valeur de l'input file
  sendPdfButton.style.display = 'none'; // Cache le bouton si aucun fichier n'est sélectionné
  resetPdfButton.style.display = 'none';
  fileInfo.innerHTML = ``;

  fetch("/delete-session-cookie", {
    method: "POST",
    credentials: "same-origin",
  })
});


document.getElementById('send-pdf-button').addEventListener("click", function (event) {
  var fileInput = document.getElementById('pdf-button');
  var file = fileInput.files[0];

  /* Affichage */
  var fileInfo = document.getElementById('file-info');
  // Obtenir les informations sur le fichier
  var fileName = file.name;
  var fileSize = file.size; // Taille en octets

  // Afficher les informations sur le fichier
  fileInfo.innerHTML = `
       <strong>Nom du fichier :</strong> ${fileName}<br>
       <strong>Taille du fichier :</strong> ${fileSize} octets
   `;
  document.getElementById('send-pdf-button').style.display = 'none';

  /* Envoi du fichier */
  event.preventDefault();
  const data = new FormData(document.getElementById('pdf-form'));

  fetch("/file-transfer", {
    method: "POST",
    body: data
  });
});




/////////////////////////////////
const applyFadeEffect = (messageElement) => {
  const text = messageElement.innerText;
  messageElement.innerHTML = ''; // Efface le texte actuel

  // Diviser le texte en mots, en tenant compte des espaces
  const words = text.split(' ');

  words.forEach((word, index) => {
    const span = document.createElement('span');
    span.textContent = word; // Ajouter le mot entier
    span.style.setProperty('--word-index', index); // Définit l'index pour le délai de chaque mot
    messageElement.appendChild(span);

    // Ajouter un espace après chaque mot sauf le dernier
    if (index < words.length - 1) {
      messageElement.appendChild(document.createTextNode(' '));
    }
  });
};

