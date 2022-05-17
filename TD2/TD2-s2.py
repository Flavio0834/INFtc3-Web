import http.server
import socketserver

# Create personalised class to handle HTTP requests
class MyHandler(http.server.SimpleHTTPRequestHandler):
    # Add a static path
    static_dir='client/'
    # Override the do_GET method
    def do_GET(self):
        self.path=self.static_dir+self.path
        # Call the original method
        super().do_GET()

PORT = 8080

Handler = MyHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()