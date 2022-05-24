# TD2-s7.py

import http.server
import socketserver
import sqlite3
import json

from urllib.parse import urlparse, parse_qs, unquote_plus


#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

    # version du serveur
    server_version = "TD2-s7"

    # sous-répertoire racine des documents statiques
    static_dir = "/client"

    #
    # On surcharge la méthode qui traite les requêtes GET
    #
    def do_GET(self):
        self.init_params()

        # le chemin d'accès commence par /time
        if self.path.startswith("/time"):
            self.send_time()

        # On se débarasse une bonne fois pour toutes du cas favicon.ico
        elif len(self.path_info) > 0 and self.path_info[0] == "favicon.ico":
            self.send_error(204)

        # le chemin d'accès commence par le nom de projet au pluriel
        elif len(self.path_info) > 0 and self.path_info[0] == entity_list_name:
            self.send_list()

        # le chemin d'accès commence par le nom du projet au singulier, suivi par un nom de lieu
        elif len(self.path_info) > 1 and self.path_info[0] == entity_name:
            self.send_data(self.path_info[1])

        # ou pas...
        else:
            self.send_static()

    #
    # On surcharge la méthode qui traite les requêtes HEAD
    #
    def do_HEAD(self):
        self.send_static()

    #
    # On envoie le document statique demandé
    #
    def send_static(self):

        # on modifie le chemin d'accès en insérant un répertoire préfixe
        self.path = self.static_dir + self.path

        # on appelle la méthode parent (do_GET ou do_HEAD)
        # à partir du verbe HTTP (GET ou HEAD)
        if self.command == "HEAD":
            http.server.SimpleHTTPRequestHandler.do_HEAD(self)
        else:
            http.server.SimpleHTTPRequestHandler.do_GET(self)

        # # solution alternative plus élégante :
        # method = 'do_{}'.format(self.command)
        # getattr(http.server.SimpleHTTPRequestHandler,method)(self)

    #
    # On envoie un document avec l'heure
    #
    def send_time(self):

        # on récupère l'heure
        time = self.date_time_string()

        # on génère un document au format html
        body = (
            "<!doctype html>"
            + '<meta charset="utf-8">'
            + "<title>l'heure</title>"
            + "<div>Voici l'heure du serveur :</div>"
            + "<pre>{}</pre>".format(time)
        )

        # pour prévenir qu'il s'agit d'une ressource au format html
        headers = [("Content-Type", "text/html;charset=utf-8")]

        # on envoie
        self.send(body, headers)

    #
    # On envoie la liste des entités
    #
    def send_list(self):

        # on effectue une requête dans la base pour récupérer la liste des entités
        c = conn.cursor()
        c.execute("SELECT name, lat, lon FROM {}".format(entity_list_name))
        data = c.fetchall()

        # on construit la réponse en json
        info = [dict(d) for d in data]
        self.send_json(info)

    #
    # On envoie un document au format json
    #
    def send_json(self, data):
        headers = [("Content-Type", "application/json")]
        self.send(json.dumps(data), headers)

    #
    # On envoie les infos d'une entité
    #
    def send_data(self, name):

        # requête dans la base pour récupérer les infos de l'entité
        c = conn.cursor()
        c.execute("SELECT * FROM {} WHERE name=?".format(entity_list_name), (name,))
        data = c.fetchone()

        # construction de la réponse
        if data == None:
            self.send_error(404, "{} {} non trouvée".format(entity_name, name))
        else:
            txt = "\n".join(["{}: {}".format(k, data[k]) for k in data.keys()])

            # envoi de la réponse
            headers = [("Content-Type", "text/plain;charset=utf-8")]
            self.send(txt, headers)

    #
    # On envoie les entêtes et le corps fourni
    #
    def send(self, body, headers=[]):

        # on encode la chaine de caractères à envoyer
        encoded = bytes(body, "UTF-8")

        # on envoie la ligne de statut
        self.send_response(200)

        # on envoie les lignes d'entête et la ligne vide
        [self.send_header(*t) for t in headers]
        self.send_header("Content-Length", int(len(encoded)))
        self.end_headers()

        # on envoie le corps de la réponse
        self.wfile.write(encoded)

    #
    # lecture des paramètres de la requête
    #
    def init_params(self):
        info = urlparse(self.path)
        self.path_info = [unquote_plus(v) for v in info.path.split("/")[1:]]

        self.query_string = info.query
        self.params = parse_qs(info.query)

        print("path_info : {}".format(self.path_info))
        print("params : {}".format(self.params))


#
# MODIFIER ICI EN FONCTION DU NOM DE VOTRE PROJET
#
# nom des entités traitées par votre projet, au pluriel
entity_list_name = "volcans"


# on en déduit le nom des entités au singulier
entity_name = entity_list_name[:-1]

#
# Connexion à la base de données
# conn est une variable globale
#
dbname = "{}.db".format(entity_list_name)
conn = sqlite3.connect(dbname)

# pour récupérer les résultats sous forme d'un dictionnaire
conn.row_factory = sqlite3.Row


#
# Instanciation et lancement du serveur
#
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
