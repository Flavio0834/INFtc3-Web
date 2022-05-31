/*
** Initialisation d'un popup
**
** Rend le popup déplaçable et configure les éléments cliquables avec le gestionnaire
** d'événements permettant l'apparition et la disparition du popup
**
** Arguments :
** - container : élément (conteneur) principal du popup
** - header    : élément enfant du popup via lequel on peut déplacer le popup, ou null/undefined
** - show_btn  : élément sur lequel un clic provoquera l'apparition du popup, ou null/undefined
** - hide_btn  : élément sur lequel un clic provoquera la disparition du popup, ou null/undefined
**
*/
function init_popup(container, header, show_btn, hide_btn) {
  // les popups sont déplaçables
  header && draggable(container, header);

  // gestionnaire pour montrer le popup
  show_btn && show_btn.addEventListener('click', popup.bind(show_btn,container));

  // gestionnaire pour cacher le popup
  hide_btn && hide_btn.addEventListener('click', hide.bind(hide_btn,container));
}


/*
** Afichage d'un popup
**
** S'assure que le popup est visible, en tenant compte du scroll vertical
**
** Arguments :
** - elt : élément (conteneur) principal du popup
**
*/
function popup(elt) {
  let fields = elt.querySelectorAll('input, textarea');
  fields.forEach(f => f.value = '');
  elt.style.marginTop = window.scrollY + 'px';
  elt.style.display='block';
  elt.style.visibility='visible';
}


/*
** Désaffichage d'un popup
**
** Cache le popup
**
** Arguments:
** - elt : élément (conteneur) principal du popup
**
*/
function hide(elt) {
  elt.style.display='none';
}


/*
** Envoi d'une requête Ajax
**
** Emet une requête Ajax et appelle la fonction de traitement à réception de la réponse
**
** Arguments :
** - method  : méthode HTTP, typiquement 'GET' ou 'POST'
** - url     : URL vers laquelle sera effectuée la requête HTTP
** - body    : optionnel, chaîne de caractères avec le corps de la requête
** - headers : optionnel, objet (dictionnaire) avec les entêtes HTTP pour la requête 
** - cb      : fonction de traitement, appelée à réception de la réponse
*/
function ajax_request(method,url,body,headers,cb) {
  if ( arguments.length == 3 ) { cb = body, body = '', headers = {} };
  if ( arguments.length == 4 ) { cb = headers, headers = {} };
  var xhr = new XMLHttpRequest();
  xhr.onload = cb;
  xhr.open(method,url,true);
  for ( h in headers ) {
    xhr.setRequestHeader(h, headers[h]);
  }
  xhr.send(body);
}


/*
** Retire les éventuelles balises html d'un texte
**
** Arguments:
** - html : chaîne de caractère à analyser
**
** Renvoie:
** - la chaîne de caractères sans les éventuelles balises html qu'elle contenait
*/
function sanitize_html(html) {
  let fake_div = document.createElement('div');
  fake_div.innerHTML = html;
  return fake_div.textContent;
}


/*
** Rend un élément déplaçable
**
** Arguments:
** - element : l'élément qui pourra être déplacé par l'utilisateur (avec tout son contenu)
** - handle  : optionnel, élément (a priori enfant du précédent) via lequel on pourra déplacer
**             l'élément draggable. En l'absence de cet argument (null/undefined), toute la
               surface de l'élément déplaçable sera active.
*/
function draggable(element,handle) {
    var handle = handle || element
      , startX = 0 , startY = 0 , x = 0 , y = 0
      , startLeft, startTop, startWidth, startHeight
    ;

    //handle.css({ cursor: 'pointer' });

    handle.addEventListener('mousedown', function(event) {
      var style = window.getComputedStyle(element);

      if ( style.position == 'static' ) element.style.position = 'absolute';
      if ( ! style.zIndex ) element.style.zIndex = 500;

      // évite le déplacement de contenu sélectionné
      event.preventDefault();

      // position initiale, en "coordonnées CSS"
      startLeft = parseFloat(style.left);
      startTop = parseFloat(style.top);

      // position initiale en "coordonnées curseur"
      startX = event.pageX;
      startY = event.pageY;

      // enregistrement des gestionnaires pour le suivi et la fin du mouvement
      document.addEventListener('mousemove', mousemove);
      document.addEventListener('mouseup', mouseup);

      // appel éventuel d'une fonction externe pour signaler le début du mouvement
      if ( element.mousedown_hook ) {
        element.mousedown_hook(startX, startY, startLeft, startTop, startWidth, startHeight);
      }
    });

    // fonction de traitement du mouvement de l'élément déplaçable
    function mousemove(event) {
      if ( event.clientX > 0 && (!window.innerWidth || event.clientX < window.innerWidth)) {
        x = event.pageX - startX;
      }
      if ( event.clientY > 0 && (!window.innerHeight || event.clientY < window.innerHeight)) {
        y = event.pageY - startY;
      }
      element.style.top = (startTop + y) + 'px';
      element.style.left = (startLeft + x) + 'px';

      // déplacement éventuel d'éléments liés
      if ( element.handles ) element.handles.forEach(function(h){ h.move(); });

      // appel éventuel d'une fonction externe pour signaler le déplacement
      if ( element.mousemove_hook ) element.mousemove_hook();
    }

    // fonction de traitement de la fin du mouvement de l'élément déplaçable
    function mouseup() {
      document.removeEventListener('mousemove', mousemove);
      document.removeEventListener('mouseup', mouseup);

      // appel éventuel d'une fonction externe pour signaler la fin du mouvement
      if ( element.mouseup_hook ) element.mouseup_hook();
    }

// fin de la fonction qui rend un élément déplaçable
}


/*
** Permet le redimensionnement d'un container (a priori
** du type popup) via un textarea qu'il contient
**
** Arguments :
** - container : l'élément à rendre redimensionnable
** - textarea  : élément textarea, enfant du précédent
**
*/
function resize_with_textarea(container, textarea) {
  let rect = textarea.getBoundingClientRect()
    , s = getComputedStyle(container)
    , textarea_startWidth = rect.width
    , textarea_startHeight = rect.height
    , container_startWidth = parseFloat(s.width)
    , container_startHeight = parseFloat(s.height)
  ;
  new ResizeObserver(function(entries){
    let rect = textarea.getBoundingClientRect();
    for ( let entry of entries ) {
      container.style.width = container_startWidth + (rect.width - textarea_startWidth) + 'px';
      container.style.height = container_startHeight + (rect.height - textarea_startHeight) + 'px';
    }
  }).observe(textarea);

  textarea.style.width = textarea_startWidth + 'px';
  textarea.style.height = textarea_startHeight + 'px';
};


/*
** Initialisation automatique de tous les popups
**
** - Tous les éléments de la classe 'popup' (c'est-à-dire contenant le mot 'popup' dans
**   la valeur de leur attribut 'class') seront initialisés comme des popups.
** - Si ces éléments contiennent un élément de la classe 'handle', celui-ci permettra de
**   déplacer le popup.
** - S'il existe un élément de la classe 'show_popup' qui possède un attribut data-popup
**   dont la valeur correspond à l'id du popup, celui-ci sera configuré pour faire apparaître
**   le popup via un clic.
** - S'il existe un élément de la classe 'hide_popup' enfant du popup ou possédant un
**   attribut data-popup dont la valeur correspond à l'id eu popup, celui-ci sera configuré
**   pour cacher le popup via un clic.
**
** - Tous les éléments de la classe 'resizable' (a priori des popups) seront rendus
**   redimensionnables via leur textarea s'ils en contiennent un.
**
*/
window.addEventListener('load',e => {
  [...document.querySelectorAll('.popup')].forEach(p => {
    let handle = document.querySelector('#'+p.id+' .handle')
      , show_btn = document.querySelector('.show_popup[data-popup='+p.id+']')
      , hide_btn = document.querySelector('#'+p.id+' .hide_popup, .hide_popup[data-popup='+p.id+']')
    ; 
    init_popup(p, handle, show_btn, hide_btn);
  });

  [...document.querySelectorAll('.resizable')].forEach(p => {
    let textarea = document.querySelector('#'+p.id+' textarea');
    if ( textarea ) resize_with_textarea(p,textarea);
  });
});
