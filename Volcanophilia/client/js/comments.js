// N.B. CE MODULE SUPPOSE L'UTILISATION CONJOINTE DU MODULE apputils.js

/*
** Affichage de l'ensemble des messages
**
** Cette fonction nécessite que le serveur réponde correctement à la requête
** GET /commentaires/<nom-du-site> (cf. question 3.4)
**
*/
function display_messages() {
    // On efface le contenu du <div id="messages">
    messages.textContent = '';

    // On envoie une requête Ajax pour récupérer la liste des messages
    ajax_request('GET', '/commentaires/' + site_name, function () {

        // récupération des données renvoyées par le serveur
        let data = JSON.parse(this.responseText);

        // boucle sur les messages
        data.forEach(display_message);

    });
}


/*
** Affichage d'un message unique
**
** Cette fonction est appelée par la précédente, pour afficher les
** messages un à un, à la suite du contenu du <div id="messages">.
**
** Arguments:
** - msg : le message à afficher. On s'attend à ce que le message soit un
**         objet (dictionnaire) renvoyé par le serveur, avec notamment les
**         attributs 'id', 'pseud'o, 'timestamp', 'message', et 'date'
**         conformément à ce qui est décrit par la question 3.4.
*/
function display_message(msg) {

    // mise en forme du timestamp
    let d = new Date(parseInt(msg.timestamp, 10) * 1000)
        , date_options = {
            day: '2-digit',
            month: '2-digit',
            year: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }
        , s = d.toLocaleString('fr-FR', date_options)
        ;

    // préparation des parties du message
    let html = '<header>' + s + ' <b>[&thinsp;' + msg.pseudo + '&thinsp;]</b> ';
    if (msg.date) html += 'a visité ce site : ' + msg.date;
    html += '<span class="delete" title="supprimer ce message">x</span>';
    html += '</header>';
    html += '<p>' + msg.message + '</p>';

    // affichage du message
    let article = document.createElement('article');
    article.innerHTML = html;
    article.dataset.id = msg.id;
    messages.appendChild(article);

    // touche de suppression du message
    let span = article.querySelector('.delete')
    span.addEventListener('click', function () {

        // Affichage du popup de demande de mot de passe
        enter_pwd.value = '';
        pwd_request.style.marginTop = window.scrollY + 'px';
        pwd_request.style.display = 'block';
        pwd_request.style.visibility = 'visible';

        // Poursuite de l'opération après entrée du mot de passe
        confirm_pwd.addEventListener('click', function () {

            // On cache le popup
            pwd_request.style.display = 'none';

            // demande de suppression du message
            ajax_request('DELETE', '/commentaire/' + msg.id,
                JSON.stringify({
                    pseudo: msg.pseudo,
                    password: enter_pwd.value,
                }),
                { 'Content-Type': 'application/json' },
                function () {

                    // suppression du message
                    if (this.status == 204) {
                        article.parentNode.removeChild(article);
                        show_comments.style.visibility = n ? 'visible' : 'hidden';
                    }

                    // il y a eu un problème côté serveur
                    else {
                        alert(this.status + ' ' + this.statusText);
                        console.log(this.status, this.statusText);
                    }
                });
        }, { once: true });
    });
}


/*
** Création d'un message
**
** Fonction appelée par le popup de création d'un message.
** Effectue un appel AJAX pour la création du message correspondant
** aux informations entrées par l'utilisateur via les champs de
** formulaire présentés par le popup.
*/
function post_message() {

    // corps et entête HTTP du message
    let body = { site: site_name }
        , headers = { 'Content-Type': 'application/json' }
        ;
    ['pseudo', 'password', 'message', 'date'].forEach(k => {
        body[k] = window['input_' + k].value;
    });

    // requête AJAX et traitement de la réponse
    ajax_request('POST', '/commentaire', JSON.stringify(body), headers, function () {
        if (this.status == 200) {
            let msg = JSON.parse(this.responseText);
            message_editor.style.display = 'none';
            display_message(msg);
            show_comments.style.visibility = 'visible';
            display_messages();
        }
        else {
            let errmsg = (this.statusText == "Missing 'email'") ? 'Unknown user' : this.statusText
                , status = (this.statusText == "Missing 'email'") ? 401 : this.status
                ;
            alert(status + ' ' + errmsg);
            console.log(status, errmsg);
        }
    });
}
