import http.server
import socketserver
import sqlite3
import json
import datetime

from urllib.parse import unquote_plus, urlparse, parse_qs


# Définition du nouveau handler


class RequestHandler(http.server.SimpleHTTPRequestHandler):

    # version du serveur
    server_version = "v1"

    # sous-répertoire racine des documents statiques
    static_dir = "/client"

    # credentials du super utilisateur
    ROOT_LOGIN = "root"
    ROOT_PASSWORD = "toor"

    def do_GET(self):
        """Cette méthode joue le rôle d'un routeur pour les requêtes GET
        (On surcharge la méthode qui traite les requêtes GET)"""
        self.init_params()

        # le chemin d'accès commence par /time
        if self.path.startswith("/time"):
            self.send_time()

        # le chemin d'accès commence par le nom de projet au pluriel
        elif len(self.path_info) > 0 and self.path_info[0] == entity_list_name:
            self.send_list()

        # le chemin d'accès commence par le nom du projet au singulier, suivi par un nom de lieu
        elif len(self.path_info) > 1 and self.path_info[0] == entity_name:
            self.send_data(self.path_info[1])

        # Sinon si le chemin d'accès commence par /commentaires/entity_name on renvoie le commentaire
        elif len(self.path_info) > 1 and self.path_info[0] == "commentaires":
            self.send_commentaires_json()

        else:
            self.send_static()

    def do_HEAD(self):
        """Surcharge la méthode qui traite les requêtes HEAD. Cette méthode renvoie les headers qu'une requête renvoie pour un endpoint précis."""
        self.send_static()

    def do_POST(self):
        """idem on route les requêtes POST vers leurs services respectifs (on surchage la méthode qui traite les requêtes POST)"""
        self.init_params()

        # Si le chemin d'accès commence par commentaires, suivi du point d'interêt on ajoute un commentaire
        if len(self.path_info) > 0 and self.path_info[0] == "commentaire":
            self.send_commentaire()
        elif len(self.path_info) > 0 and self.path_info[0] == "utilisateur":
            self.send_utilisateur()
        else:
            self.send_error(405)  # Méthode non supporté

    def do_DELETE(self):
        """routeurs des requêtes DELETE"""
        self.init_params()

        if len(self.path_info) > 1 and self.path_info[0] == "commentaire":
            self.delete_commentaire()
        else:
            self.send_error(404)  # Ressource non trouvée

    def send_html(self, content):
        headers = [("Content-Type", "text/html;charset=utf-8")]
        html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}'.format(
            self.path_info[0], content
        )
        self.send(html, headers)

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

    def send_static(self):

        # on modifie le chemin d'accès en insérant un répertoire préfixe
        self.path = self.static_dir + self.path

        # on appelle la méthode parent (do_GET ou do_HEAD)
        # à partir du verbe HTTP (GET ou HEAD)
        if self.command == "HEAD":
            http.server.SimpleHTTPRequestHandler.do_HEAD(self)
        else:
            http.server.SimpleHTTPRequestHandler.do_GET(self)

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

    def send_list(self):

        # on effectue une requête dans la base pour récupérer la liste des entités
        c = conn.cursor()
        c.execute("SELECT name, lat, lon FROM {}".format(entity_list_name))
        data = c.fetchall()

        # on construit la réponse en json
        info = [dict(d) for d in data]
        self.send_json(info)

    def send_data(self, name):

        # requête dans la base pour récupérer les infos de l'entité
        c = conn.cursor()
        c.execute("SELECT * FROM {} WHERE name=?".format(entity_list_name), (name,))
        data = c.fetchone()

        # construction de la réponse
        if data is None:
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

    def send_json(self, data):
        headers = [("Content-Type", "application/json")]
        self.send(json.dumps(data), headers)

    def send_commentaires_json(self):
        """Envoie la liste des commentaires d'un point d'intérêt au format json"""

        entity = self.path_info[1]
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM commentaires WHERE site = ?", (entity,))
            data = c.fetchall()

            body = json.dumps([dict(d) for d in data])  # réponse en json
            headers = [
                ("Content-Type", "application/json")
            ]  # précise au client quel type de données il doit traiter
            self.send_response(200)
            self.send(body, headers)

        except Exception as SQLError:
            print(SQLError)
            self.send_error(400, "Erreur SQL")

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

        if self.est_connectee(
            pseudo, password
        ):  # on vérifie que l'utilisateur est connecté
            c = conn.cursor()
            try:
                sql = (
                    "INSERT INTO commentaires (pseudo, site, timestamp, message, date) VALUES (?,?,?,?,?)",
                    (pseudo, site_name, timestamp, message, date),
                )
                c.execute(*sql)  # on insère le commentaire dans la base de données
                conn.commit()
                self.send_response(200)
                self.send_json(data)
            except Exception as SQLError:
                print(SQLError)
                self.send_error(400, "Erreur SQL")

    def send_utilisateur(self):
        """Requête POST pour ajouter un utilisateur à la base de données"""

        data = self.params

        # On vérifie que les données fournie correspondent bien à la requête
        try:
            assert data["user_pseudo"] != ""
            assert data["email"] != ""
            assert data["user_password"] != ""

        except Exception as InvalidUser:
            print(InvalidUser)
            self.send_error(
                422,
                "Body invalide",
                "Le corps de la requête ne correspond pas à la spécification il doit contenir les champs suivants : user_pseudo, email et user_password",
            )

        # On vérifie que l'utilisateur n'existe pas déjà

        if self.est_nouveau(data["user_pseudo"], data["email"]):
            c = conn.cursor()
            try:

                c.execute(
                    "INSERT INTO utilisateurs (pseudo, email, pwd) VALUES (?,?,?)",
                    [data["user_pseudo"], data["email"], data["user_password"]],
                )
                conn.commit()
                self.send_response(200)
            except Exception as SQLError:
                print(SQLError)
                self.send_error(
                    400,
                    "Erreur SQL",
                    "Le nouvel utilisateur n'a pas pu être ajouté",
                )

    def delete_commentaire(self):
        """Requête DELETE pour supprimer un commentaire"""

        data = self.params
        # On vérifie que les données fournie correspondent bien à la requête
        try:
            comment_id = self.path_info[1]
            pseudo = data["pseudo"]
            password = data["password"]
            assert comment_id != ""
            assert pseudo != ""
            assert password != ""

        except Exception as InvalidComment:
            print(InvalidComment)
            self.send_error(
                422,
                "Body invalide",
                "Le corps de la requête ne correspond pas à la spécification \
                il doit contenir les champs suivants : id, pseudo, password",
            )

        if self.est_connectee(pseudo, password) and self.appartient(
            comment_id, pseudo, password
        ):
            c = conn.cursor()
            try:
                sql = ("DELETE FROM commentaires WHERE id = ?", (comment_id,))
                c.execute(*sql)
                conn.commit()
                # on indique que la commande s'est bien effectuée (send_response ne fonctionne pas mais le status reste le bon)
                self.send_json({"Status": "Done"})
            except Exception as SQLError:
                print(SQLError)
                self.send_error(400, "Erreur SQL")

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

    def appartient(self, comment_id, pseudo, password):
        """Vérifie un utilisateur a les droits pour supprimer un commentaire"""

        if (
            pseudo == self.ROOT_LOGIN and password == self.ROOT_PASSWORD
        ):  # le super utilisateur à tous les droits
            return True

        else:
            b = True  # True si l'utilisateur a les droits sur le commentaire False sinon
            c = conn.cursor()
            try:
                # On vérifie si le commentaire existe
                req = ("SELECT * FROM commentaires WHERE id = ?", (comment_id,))
                c.execute(*req)
                r = c.fetchone()

                if r is None:
                    b = False
                    self.send_error(404, "Le commentaire n'existe pas")

                else:  # il existe
                    req = (
                        "SELECT * FROM commentaires WHERE id = ? AND pseudo = ?",
                        (comment_id, pseudo),
                    )

                    c.execute(*req)
                    r = c.fetchone()

                    if r is None:  # Le commentaire n'est pas celui de l'utilisateur
                        b = False
                        self.send_error(
                            401,
                            "Droits insuffisants",
                            "Vous n'avez pas la permission pour supprimer ce commentaire",
                        )
            except Exception as SQLError:
                print(SQLError)
                self.send_error(400, "Erreur SQL")
                b = False
            return b

    def est_nouveau(self, pseudo, email):
        """Vérifie si un utilisateur n'existe pas déjà.
        Dans ce programme, un utilisateur est défini par son pseudo et son email"""

        if pseudo == self.ROOT_LOGIN:
            return False
        else:
            nouveau = True
            c = conn.cursor()
            try:
                sql = (
                    "SELECT * FROM utilisateurs WHERE pseudo= ?",
                    (pseudo,),
                )  # On vérifie si le pseudo existe déjà
                c.execute(*sql)
                r = c.fetchone()  # on stocke le résultat dans r
                if r is not None:  # le pseudo est déjà attribué
                    nouveau = False
                    self.send_error(
                        401,
                        "Pseudo déjà utilisé",
                        "Ce pseudo existe déjà. Veuillez en choisir un autre",
                    )
                else:
                    sql = ("SELECT * FROM utilisateurs WHERE email= ?", (email,))
                    c.execute(*sql)
                    r = c.fetchone()
                    if r is not None:  # l'adresse email est déjà attribuée
                        nouveau = False
                        self.send_error(
                            401,
                            "Adresse mail déjà utilisée",
                            "Cette adresse-mail est déjà utilisée. Veuillez en choisir une autre",
                        )
            except Exception as SQL_error:
                print(SQL_error)
                nouveau = False
            return nouveau

    def parse_qs(self, query_string):
        """Parse la requête et renvoie un dictionnaire de paramètres"""
        self.params = parse_qs(query_string)
        for k in self.params:
            if len(self.params[k]) == 1:
                self.params[k] = self.params[k][0]

    def init_params(self):
        """Initialise les paramètres de la requête"""

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


def get_timestamp():
    """Retourne le timestamp à l'heure de son activation"""
    return datetime.datetime.timestamp(datetime.datetime.now())


def init_db():
    """
    Méthode qui initialise les tables utilisateurs et commentaires de la base de données
    """
    c = conn.cursor()
    try:
        c.execute(
            "CREATE TABLE IF NOT EXISTS commentaires (id INTEGER PRIMARY KEY AUTOINCREMENT, pseudo TEXT, site TEXT,  date TEXT, message TEXT, timestamp TIME)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS utilisateurs (pseudo TEXT, email TEXT, pwd TEXT)"
        )
    except Exception as CreateTableError:
        print(CreateTableError)


### PROGRAMME PRINCIPAL ###

if __name__ == "__main__":

    entity_list_name = "volcans"

    # on en déduit le nom des entités au singulier
    entity_name = entity_list_name[:-1]

    # Connexion à la base de données
    # conn est une variable globale

    dbname = "{}.db".format(entity_list_name)
    conn = sqlite3.connect(dbname)

    # pour récupérer les résultats sous forme d'un dictionnaire
    conn.row_factory = sqlite3.Row
    init_db()  # création des tables utilisateurs et commentaires si elles n'existent pas

    # Instanciation et lancement du serveur
    httpd = socketserver.TCPServer(("", 8081), RequestHandler)
    httpd.serve_forever()
