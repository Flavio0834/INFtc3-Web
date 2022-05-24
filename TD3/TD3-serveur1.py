# TD3-serveur1.py

import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json


# définition du handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  # version du serveur
  server_version = 'TD3-serveur1.py/0.1'

  # on surcharge la méthode qui traite les requêtes GET
  def do_GET(self):
    self.init_params()

    # prénom et nom dans la chaîne de requête
    if self.path_info[0] == "toctoc":
      self.send_toctoc()

    # document statique ?
    else:
      self.send_static()


  # méthode pour traiter les requêtes HEAD
  def do_HEAD(self):
      self.send_static()


  # méthode pour traiter les requêtes POST
  def do_POST(self):
    self.init_params()

    # prénom et nom dans la chaîne de requête dans le corps
    if self.path_info[0] == "toctoc":
      self.send_toctoc()
      
    # Method not supported
    else:
      self.send_error(405)

  # On envoie un document avec le nom et le prénom
  def send_toctoc(self):    
    # on envoie un document HTML contenant un seul paragraphe
   self.send_html('<p>Bonjour {} {}</p>'.format(self.params['Prenom'],self.params['Nom']))


  # on envoie un document html dynamique
  def send_html(self,content):
     headers = [('Content-Type','text/html;charset=utf-8')]
     html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}' \
         .format(self.path_info[0],content)
     self.send(html,headers)


  # on envoie le document statique demandé
  def send_static(self):

    # on modifie le chemin d'accès en insérant le répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)


  # on envoie la réponse
  def send(self,body,headers=[]):
     encoded = bytes(body, 'UTF-8')

     self.send_response(200)

     [self.send_header(*t) for t in headers]
     self.send_header('Content-Length',int(len(encoded)))
     self.end_headers()

     self.wfile.write(encoded)


  #
  # analyse d'une chaîne de requête pour récupérer les paramètres
  #
  def parse_qs(self,query_string):
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
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.query_string = info.query
    self.parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.parse_qs(self.body)
      elif ctype == 'application/json' : 
        self.params = json.loads(self.body)
    else:
      self.body = ''
   
    # traces
    print('path_info =',self.path_info)
    print('body =',length,ctype,self.body)
    print('params =', self.params)



# instanciation et lancement du serveur
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
