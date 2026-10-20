from http.server import BaseHTTPRequestHandler, HTTPServer

# Variabile globale che fa da "stato condiviso" tra Tor e VPN
last_token = ""

class TorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global last_token
        
        # Regola 1: GET / -> 200
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Onion Service OK")
            
        # Regola 2b: GET /claim -> restituisce l'ultimo token
        elif self.path == '/claim':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(last_token.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global last_token
        
        # Regola 2a: POST /claim -> salva il token dal body
        if self.path == '/claim':
            content_length = int(self.headers.get('Content-Length', 0))
            # Legge il body e lo salva nella variabile globale
            last_token = self.rfile.read(content_length).decode('utf-8')
            
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    # In ascolto su tutte le interfacce, porta 8090
    server_address = ('0.0.0.0', 8090)
    httpd = HTTPServer(server_address, TorHandler)
    print("Server in ascolto su porta 8090...")
    httpd.serve_forever()