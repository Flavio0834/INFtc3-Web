import http.server
import socketserver
import sqlite3
import json
import datetime

from urllib.parse import unquote_plus, urlparse, parse_qs, unquote_plus


#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

    # version du serveur
    server_version = "TD2-s7"

    # sous-répertoire racine des documents statiques
    static_dir = "/client"

    ROOT_LOGIN = "root"
    ROOT_PASSWORD = "toor"

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

    # méthode pour traiter les requêtes POST
    def do_POST(self):
        self.init_params()

        # prénom et nom dans la chaîne de requête dans le corps
        if self.path_info[0] == "toctoc":
            self.send_toctoc()

        elif self.path_info[0] == "commentaire":
            self.send_commentaire()

        # Method not supported
        else:
            self.send_error(405)

    # On envoie un document avec le nom et le prénom
    def send_toctoc(self):
        # on envoie un document HTML contenant un seul paragraphe
        self.send_html(
            "<p>Bonjour {} {}</p>".format(self.params["Prenom"], self.params["Nom"])
        )

    def send_commentaire(self):
        """Requête POST pour ajouter un commentaire"""

        data = self.params  # paramètres de la requête POST

        # On vérifie que les données sont de la bonne forme
        try:
            pseudo = data["pseudo"]
            password = data["password"]
            site_name = data["site"]
            message = data["message"]
            date = data["date"]
            timestamp = get_timestamp()
            assert pseudo != ""
            assert password != ""
            assert site_name != ""
            assert message != ""
            assert date != ""

        except Exception as InvalidComment:
            print(InvalidComment)
            self.send_error(
                422,
                "Body invalide",
                "Le corps de la requête ne correspond pas à la spécification il doit contenir les champs suivants : pseudo, password, site, message, date",
            )

        if self.est_connectee(pseudo, password):
            c = conn.cursor()
            try:
                sql = (
                    "INSERT INTO commentaires (pseudo, site, timestamp, message, date) VALUES (?,?,?,?,?)",
                    (pseudo, site_name, timestamp, message, date),
                )
                c.execute(*sql)
                conn.commit()
                self.send_response(200)
                self.send_json(data)
            except Exception as SQLError:
                print(SQLError)
                self.send_error(400, "Erreur SQL")

    # on envoie un document html dynamique
    def send_html(self, content):
        headers = [("Content-Type", "text/html;charset=utf-8")]
        html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}'.format(
            self.path_info[0], content
        )
        self.send(html, headers)

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
        c.execute("SELECT name, lat, lon FROM ?", (entity_list_name,))        
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
        c.execute("SELECT * FROM ? WHERE name=?", (entity_list_name, name))
        data = c.fetchone()

        # construction de la réponse
        if data == None:
            self.send_error(404, "{} {} non trouvée".format(entity_name, name))
        else:

            # on construit un document au format json
            data = dict(data)
            info = {
                "dbpedia": data["volcano"],
                "wiki": data["wiki"],
                "abstract": data["abstract"],
                "photo": data["photo"],
                "other": {
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "height": data["elevation"],
                    "date": data["eruption_date"],
                    "year": data["eruption_year"],
                },
            }
            # envoi de la réponse
            self.send_json(info)

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
    # analyse d'une chaîne de requête pour récupérer les paramètres
    #
    def parse_qs(self, query_string):
        self.params = parse_qs(query_string)
        for k in self.params:
            if len(self.params[k]) == 1:
                self.params[k] = self.params[k][0]

    #
    # on analyse la requête pour initialiser nos paramètres
    #
    def init_params(self):
        # analyse de l'adresse
        info = urlparse(self.path)
        self.path_info = [
            unquote_plus(v) for v in info.path.split("/")[1:]
        ]  # info.path.split('/')[1:]
        self.query_string = info.query
        self.parse_qs(info.query)

        # récupération du corps
        length = self.headers.get("Content-Length")
        ctype = self.headers.get("Content-Type")
        if length:
            self.body = str(self.rfile.read(int(length)), "utf-8")
            if ctype == "application/x-www-form-urlencoded":
                self.parse_qs(self.body)
            elif ctype == "application/json":
                self.params = json.loads(self.body)
        else:
            self.body = ""

        # traces
        print("path_info =", self.path_info)
        print("body =", length, ctype, self.body)
        print("params =", self.params)

    # Penser à vérifier que l'email est fournie à la création du compte

    def est_connectee(self, pseudo, password):
        """Vérifie si un utilisateur est connecté"""

        if pseudo == self.ROOT_LOGIN and self.ROOT_PASSWORD == password:
            # le compte root ne figure pas dans la bdd mais dans les attributs de la classe
            return True
        else:
            verified = True
            c = conn.cursor()
            try:
                sql = (
                    "SELECT * FROM utilisateurs WHERE pseudo = ? AND pwd = ?",
                    (pseudo, password),
                )
                c.execute(*sql)
                r = c.fetchone()
                if r is None:
                    sql = ("SELECT * FROM utilisateurs WHERE pseudo = ?", (pseudo,))
                    c.execute(*sql)
                    r = c.fetchone()
                    if r is None:
                        self.send_error(401, "Utilisateur inconnu")
                        verified = False
                    else:
                        self.send_error(401, "Mot de passe incorrect")
                        verified = False
            except Exception as SQLError:
                print(SQLError)
                self.send_error(400, "Erreur SQL")
                verified = False
            return verified


def get_timestamp():
    """Retourne le timestamp à l'heure de son activation"""
    return datetime.datetime.timestamp(datetime.datetime.now())
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
