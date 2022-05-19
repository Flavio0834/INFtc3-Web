import http.server
import socketserver
from VolcanDB import *

# Create personalised class to handle HTTP requests
class MyHandler(http.server.SimpleHTTPRequestHandler):
    # Add a static path
    static_dir='client/'
    # Override the do_GET method
    def do_GET(self):
        if self.path.startswith('/time'):
            self.send_time()
        elif self.path.startswith('/volcans'):
            self.send_volcans()
        else:
            self.path=self.static_dir+self.path
            super().do_GET()

    def send(self,body,headers=[]):
        # on encode la chaine de caractères à envoyer
        encoded = bytes(body, 'UTF-8')

        # on envoie la ligne de statut
        self.send_response(200)

        # on envoie les lignes d'entête et la ligne vide
        [self.send_header(*t) for t in headers]
        self.send_header('Content-Length',int(len(encoded)))
        self.end_headers()

        # on envoie le corps de la réponse
        self.wfile.write(encoded)

    def send_time(self):
        self.send("Voici l'heure du serveur : \n\n"+self.date_time_string(),[('Content-type','text/plain;charset=utf-8')])

    def send_volcans(self):
        db=VolcanDB("volcans/volcans.db")
        self.send(db.get_list_of_volcanos(),[('Content-type','text/plain;charset=utf-8')])

PORT = 8080

Handler = MyHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()